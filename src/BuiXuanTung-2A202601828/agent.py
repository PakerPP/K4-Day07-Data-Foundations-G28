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

    NO_CONTEXT_MESSAGE = "Không tìm thấy thông tin liên quan trong cơ sở tri thức."

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return self.NO_CONTEXT_MESSAGE

        context = "\n\n".join(
            f"[{index}] (source={result['metadata'].get('source', result['metadata'].get('doc_id', 'unknown'))}, "
            f"score={result['score']:.3f})\n{result['content']}"
            for index, result in enumerate(results, start=1)
        )
        prompt = (
            "Trả lời câu hỏi CHỈ dựa trên ngữ cảnh được cung cấp bên dưới.\n"
            "Nếu ngữ cảnh không đủ thông tin, hãy nói rõ là không biết.\n"
            "Trích dẫn số hiệu đoạn ([1], [2], ...) cho các thông tin bạn sử dụng.\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {question}\n\n"
            "TRẢ LỜI:"
        )
        return self.llm_fn(prompt)
