from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở dữ liệu."

        context_blocks = []
        for idx, res in enumerate(results, start=1):
            doc_id = res.get("metadata", {}).get("doc_id", res.get("id", f"doc_{idx}"))
            source = res.get("metadata", {}).get("source", doc_id)
            context_blocks.append(f"[{idx}] (Nguồn: {source})\n{res['content']}")

        context_str = "\n\n".join(context_blocks)

        prompt = (
            "Dưới đây là các tài liệu ngữ cảnh được cung cấp:\n\n"
            f"{context_str}\n\n"
            "Dựa VÀO CHỈ CÁC TÀI LIỆU TRÊN, hãy trả lời câu hỏi sau. "
            "Hãy trích dẫn số thứ tự nguồn [1], [2]... nếu có thể. "
            "Nếu ngữ cảnh không chứa thông tin để trả lời, hãy trả lời 'Không tìm thấy thông tin trong ngữ cảnh'.\n\n"
            f"Câu hỏi: {question}\n"
            "Trả lời:"
        )

        return self.llm_fn(prompt)

