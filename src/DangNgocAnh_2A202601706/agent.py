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
        self._store = store
        self._llm_fn = llm_fn

    def _build_prompt(self, question: str, chunks: list[dict]) -> str:
        if not chunks:
            context = "(Không tìm thấy ngữ cảnh liên quan trong kho tri thức.)"
        else:
            context = "\n\n".join(
                f"[Nguồn {i}] {chunk['content']}" for i, chunk in enumerate(chunks, start=1)
            )
        return (
            "Bạn là trợ lý trả lời câu hỏi dựa CHỈ vào ngữ cảnh dưới đây. "
            "Nếu ngữ cảnh không đủ thông tin, hãy nói rõ là không biết.\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi: {question}\n"
            "Trả lời:"
        )

    def answer(self, question: str, top_k: int = 3) -> str:
        chunks = self._store.search(question, top_k=top_k)
        prompt = self._build_prompt(question, chunks)
        return self._llm_fn(prompt)
