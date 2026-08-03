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

    def _format_context(self, chunks: list[dict]) -> str:
        if not chunks:
            return "(Không có thông tin liên quan trong kho tri thức.)"
        lines = []
        for index, chunk in enumerate(chunks, start=1):
            source = chunk.get("metadata", {}).get("doc_id", chunk.get("id", "unknown"))
            lines.append(f"[{index}] (nguồn: {source}) {chunk['content']}")
        return "\n".join(lines)

    def answer(self, question: str, top_k: int = 3) -> str:
        retrieved = self.store.search(question, top_k=top_k)
        context = self._format_context(retrieved)
        prompt = (
            "Bạn là trợ lý chăm sóc khách hàng. Chỉ dùng thông tin trong phần Ngữ cảnh "
            "dưới đây để trả lời; nếu ngữ cảnh không đủ thông tin thì nói rõ là không biết.\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi: {question}\n"
            "Trả lời:"
        )
        return self.llm_fn(prompt)
