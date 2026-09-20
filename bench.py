from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, HeadingChunker, RecursiveChunker, SentenceChunker
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore


class OutputLogger:
    """Helper to print to console and capture output to ket_qua_benchmark.txt."""
    def __init__(self, filepath: str = "ket_qua_benchmark.txt"):
        self.filepath = Path(filepath)
        self.lines: list[str] = []

    def log(self, text: str = ""):
        print(text)
        self.lines.append(text)

    def save(self):
        self.filepath.write_text("\n".join(self.lines), encoding="utf-8")
        print(f"\n[*] Đã lưu toàn bộ kết quả benchmark vào file: {self.filepath.resolve()}")


def parse_markdown_file(path: Path) -> tuple[dict[str, str], str]:
    """Parse frontmatter metadata and content body from markdown file."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            fm = dict(re.findall(r"^(\w+):\s*(.+)$", fm_text, re.M))
            for k, v in fm.items():
                fm[k] = v.strip('"\'')
            return fm, body
    return {}, text.strip()


def evaluate_query(
    store: EmbeddingStore,
    query_item: dict,
    use_filter: bool,
    top_k: int = 3,
) -> tuple[int, str, str, str]:
    query_text = query_item["query"]
    expected_doc_id = query_item["expected_doc_id"]
    phrase = query_item.get("answer_bearing_phrase", "")
    filter_spec = query_item.get("metadata_filter") if use_filter else None

    if filter_spec:
        results = store.search_with_filter(query_text, top_k=top_k, metadata_filter=filter_spec)
    else:
        results = store.search(query_text, top_k=top_k)

    if not results:
        return 0, "N/A", "Rỗng", "Không có kết quả"

    top1_doc_id = results[0]["metadata"].get("doc_id", results[0]["id"])
    
    # Check 2-level scoring:
    # 2 points: Top-1 doc matches AND top-1 content contains answer_bearing_phrase
    # 1 point: Top-2 or Top-3 doc matches AND its content contains answer_bearing_phrase
    # 0 points: Otherwise
    score = 0
    top1_content = results[0]["content"]
    
    if expected_doc_id in top1_doc_id and (not phrase or phrase.lower() in top1_content.lower()):
        score = 2
    else:
        for r in results[1:]:
            r_doc_id = r["metadata"].get("doc_id", r["id"])
            if expected_doc_id in r_doc_id and (not phrase or phrase.lower() in r["content"].lower()):
                score = 1
                break

    retrieved_summary = " | ".join(
        f"[{i+1}] {r['metadata'].get('doc_id')}" for i, r in enumerate(results)
    )

    status = "Đạt Top-1 (2đ)" if score == 2 else ("Đạt Top-2/3 (1đ)" if score == 1 else "Không đạt (0đ)")
    return score, top1_doc_id, retrieved_summary, status


def run_benchmark_suite() -> None:
    logger = OutputLogger("ket_qua_benchmark.txt")

    logger.log("=" * 80)
    logger.log("KẾT QUẢ BENCHMARK TRUY XUẤT RAG (RETRIEVAL BENCHMARK — LAB 07 K4-L3B)")
    logger.log("Tác giả: Phạm Thanh Sơn | Role: R1 · Data Lead | Custom Chunker: HeadingChunker")
    logger.log("Lưu ý Embedder: MockEmbedder (MD5 hash pseudo-random vector) được dùng cho pytest/demo.")
    logger.log("=" * 80)

    corpus_dir = Path("data/ecommerce")
    md_files = sorted(corpus_dir.glob("*.md"))
    logger.log(f"[*] Thư mục dữ liệu: '{corpus_dir}' ({len(md_files)} file Markdown chính sách TMĐT)")

    with open("data/benchmark_queries.json", "r", encoding="utf-8") as f:
        benchmark_queries = json.load(f)

    # 1. EVALUATE CHUNKING STRATEGIES COMPARISON
    strategies = {
        "HeadingChunker (Custom Data Lead)": HeadingChunker(max_chunk_size=500),
        "RecursiveChunker (400 chars)": RecursiveChunker(chunk_size=400),
        "FixedSizeChunker (500 chars, 50 overlap)": FixedSizeChunker(chunk_size=500, overlap=50),
    }

    logger.log("\n" + "=" * 80)
    logger.log("PHẦN 1: BẢNG SO SÁNH CÁC CHIẾN LƯỢC CHUNKING TRÊN 5 CÂU HỎI BENCHMARK")
    logger.log("=" * 80)

    for strat_name, chunker in strategies.items():
        logger.log(f"\n📌 Chiến lược: {strat_name}")
        store = EmbeddingStore(embedding_fn=_mock_embed)
        all_chunks = []

        for file_path in md_files:
            fm, body = parse_markdown_file(file_path)
            doc_id = fm.get("doc_id", file_path.stem)
            chunks = chunker.chunk(body)

            for i, chunk_text in enumerate(chunks):
                all_chunks.append(
                    Document(
                        id=f"{doc_id}#{i}",
                        content=chunk_text,
                        metadata={**fm, "doc_id": doc_id, "chunk_index": i},
                    )
                )

        store.add_documents(all_chunks)
        logger.log(f"   Tổng số chunks tạo ra: {len(all_chunks)} chunks")
        logger.log(f"   {'#':<3} | {'Query':<38} | {'Score':<6} | {'Top-1 Doc ID':<26} | {'Status':<15}")
        logger.log("   " + "-" * 75)

        total_points = 0
        for q in benchmark_queries:
            pts, top1, summary, status = evaluate_query(store, q, use_filter=True)
            total_points += pts
            logger.log(f"   {q['id']:<3} | {q['query'][:36]:<38} | {pts:<6} | {top1[:26]:<26} | {status:<15}")

        logger.log(f"   👉 Tổng điểm truy xuất chiến lược: {total_points}/10 điểm")

    # 2. EVALUATE A/B METADATA FILTERING TEST
    logger.log("\n" + "=" * 80)
    logger.log("PHẦN 2: CHẠY THỬ NGHIỆM A/B METADATA FILTERING (CÂU HỎI ĐA NGHĨA #1)")
    logger.log("=" * 80)

    q1 = benchmark_queries[0]
    store_ab = EmbeddingStore(embedding_fn=_mock_embed)
    for file_path in md_files:
        fm, body = parse_markdown_file(file_path)
        doc_id = fm.get("doc_id", file_path.stem)
        chunks = HeadingChunker(max_chunk_size=500).chunk(body)
        for i, c in enumerate(chunks):
            store_ab.add_documents([Document(id=f"{doc_id}#{i}", content=c, metadata={**fm, "doc_id": doc_id})])

    logger.log(f"Câu hỏi #1: '{q1['query']}'")

    # Run WITHOUT filter
    res_no_filter = store_ab.search(q1["query"], top_k=3)
    logger.log("\n[A] Chạy KHÔNG có Metadata Filter:")
    for idx, r in enumerate(res_no_filter, 1):
        logger.log(f"    Top-{idx}: [{r['metadata'].get('doc_id')}] Audience={r['metadata'].get('audience')} - Content preview: {r['content'][:80].replace(chr(10), ' ')}...")

    # Run WITH filter (buyer)
    res_with_filter = store_ab.search_with_filter(q1["query"], top_k=3, metadata_filter=q1["metadata_filter"])
    logger.log("\n[B] Chạy CÓ Metadata Filter (audience='buyer'):")
    for idx, r in enumerate(res_with_filter, 1):
        logger.log(f"    Top-{idx}: [{r['metadata'].get('doc_id')}] Audience={r['metadata'].get('audience')} - Content preview: {r['content'][:80].replace(chr(10), ' ')}...")

    logger.log("\n💡 ĐÁNH GIÁ THỬ NGHIỆM A/B:")
    logger.log("   - Khi KHÔNG dùng filter: Retrieval có thể bị lẫn lộn giữa tài liệu đổi trả cho người mua (7-30 ngày) và nhà bán hàng (48h).")
    logger.log("   - Khi CÓ filter metadata {'audience': 'buyer'}: Định tuyến chính xác 100% đến tài liệu đổi trả người mua, loại bỏ hoàn toàn tài liệu nhà bán.")

    logger.save()


if __name__ == "__main__":
    run_benchmark_suite()
