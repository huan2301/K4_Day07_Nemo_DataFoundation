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

    def answer(
    self,
    question: str,
    top_k: int = 3,
    ) -> str:
        results = self.store.search(
            question,
            top_k=top_k,
        )

        if not results:
            return (
                "Không tìm thấy thông tin phù hợp "
                "trong cơ sở tri thức."
            )

        context_parts: list[str] = []

        for index, result in enumerate(results, start=1):
            doc_id = result["metadata"].get(
                "doc_id",
                result["id"],
            )

            context_parts.append(
                f"[{index}] Source: {doc_id}\n"
                f"{result['content']}"
            )

        context = "\n\n".join(context_parts)

        prompt = (
            "Instruction: Chỉ trả lời dựa trên context được cung cấp. "
            "Nếu context không đủ thông tin, hãy nói rõ rằng "
            "không đủ thông tin để trả lời.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        return self.llm_fn(prompt)
