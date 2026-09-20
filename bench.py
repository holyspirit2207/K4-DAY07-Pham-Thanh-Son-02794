from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore


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


def run_benchmark(
    corpus_dir: str = "data/ecommerce",
    queries_file: str = "data/benchmark_queries.json",
    chunk_size: int = 400,
) -> None:
    print("=" * 75)
    print("CHẠY BENCHMARK ĐÁNH GIÁ TRUY XUẤT (RETRIEVAL BENCHMARK — K4-L3B)")
    print("=" * 75)

    corpus_path = Path(corpus_dir)
    md_files = sorted(corpus_path.glob("*.md"))
    print(f"[*] Tìm thấy {len(md_files)} tài liệu trong thư mục '{corpus_dir}'")

    chunker = RecursiveChunker(chunk_size=chunk_size)
    store = EmbeddingStore(embedding_fn=_mock_embed)
    all_chunks: list[Document] = []

    for file_path in md_files:
        fm, body = parse_markdown_file(file_path)
        doc_id = fm.get("doc_id", file_path.stem)
        chunks = chunker.chunk(body)

        for i, chunk_text in enumerate(chunks):
            chunk_doc = Document(
                id=f"{doc_id}#{i}",
                content=chunk_text,
                metadata={
                    **fm,
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "source": str(file_path),
                },
            )
            all_chunks.append(chunk_doc)

    store.add_documents(all_chunks)
    print(f"[*] Đã nạp thành công {len(all_chunks)} chunks vào EmbeddingStore (Strategy: RecursiveChunker-{chunk_size})\n")

    queries_path = Path(queries_file)
    if not queries_path.exists():
        print(f"[!] Không tìm thấy file câu hỏi: {queries_file}")
        return

    with open(queries_path, "r", encoding="utf-8") as f:
        benchmark_queries = json.load(f)

    def dummy_llm(prompt: str) -> str:
        # Extract context block lines for preview
        lines = [line for line in prompt.split("\n") if line.startswith("[") or "năm" in line or "ngày" in line or "VNĐ" in line]
        preview = " | ".join(lines[:2])
        return f"Theo tài liệu trích dẫn: {preview}" if preview else "Đã tổng hợp câu trả lời từ ngữ cảnh."

    agent = KnowledgeBaseAgent(store=store, llm_fn=dummy_llm)

    total_correct = 0
    print("-" * 75)
    print(f"{'#':<3} | {'Query':<42} | {'Filter':<10} | {'Top-1 Doc ID':<28} | {'Relevant?':<9}")
    print("-" * 75)

    for q in benchmark_queries:
        q_id = q["id"]
        query_text = q["query"]
        filter_spec = q.get("metadata_filter")
        expected_id = q["expected_doc_id"]

        # Run with filter if available
        if filter_spec:
            results = store.search_with_filter(query_text, top_k=3, metadata_filter=filter_spec)
        else:
            results = store.search(query_text, top_k=3)

        top1_doc_id = results[0]["metadata"].get("doc_id", results[0]["id"]) if results else "N/A"
        retrieved_ids = [r["metadata"].get("doc_id", r["id"]) for r in results]
        
        is_relevant = any(expected_id in rid for rid in retrieved_ids)
        if is_relevant:
            total_correct += 1

        filter_str = str(filter_spec.get("audience")) if filter_spec else "None"
        rel_str = "Có (2/2)" if is_relevant else "Không (0)"
        
        print(f"{q_id:<3} | {query_text[:40]:<42} | {filter_str:<10} | {top1_doc_id[:28]:<28} | {rel_str:<9}")

    print("-" * 75)
    print(f"Tổng số câu hỏi trả về chunk liên quan trong Top-3: {total_correct}/{len(benchmark_queries)}")
    print("=" * 75)


if __name__ == "__main__":
    run_benchmark()
