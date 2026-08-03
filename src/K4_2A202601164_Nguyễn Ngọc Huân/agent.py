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
        # store references
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # If store empty, return clear message
        if self.store.get_collection_size() == 0:
            return "Knowledge base is empty. No information to answer the question."
        results = self.store.search(question, top_k=top_k)
        # Build context
        context_parts = []
        for idx, r in enumerate(results, start=1):
            md = r.get("metadata", {}) or {}
            doc_id = md.get("doc_id") or md.get("id") or r.get("id")
            content = r.get("content", "")
            context_parts.append(f"[{idx}]\ndoc_id: {doc_id}\ncontent: {content}")
        context = "\n\n".join(context_parts)
        prompt = (
            "Instruction:\nOnly use the provided context to answer the question. "
            "If the context does not contain enough information, respond that there is insufficient data.\n\n"
            "Context:\n" + context + "\n\nQuestion:\n" + question + "\n\nAnswer:\n"
        )
        return self.llm_fn(prompt)
