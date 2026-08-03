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
            context = "(Không tìm thấy thông tin liên quan trong knowledge base.)"
        else:
            context = "\n\n".join(
                f"[{i}] {result['content']}" for i, result in enumerate(results, start=1)
            )

        prompt = (
            "Bạn là một trợ lý trả lời câu hỏi dựa trên ngữ cảnh được cung cấp bên dưới.\n"
            "Chỉ dùng thông tin trong phần Ngữ cảnh để trả lời. Nếu ngữ cảnh không chứa "
            "thông tin liên quan, hãy nói rõ là bạn không có đủ thông tin.\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi: {question}\n\n"
            "Trả lời:"
        )

        return self.llm_fn(prompt)