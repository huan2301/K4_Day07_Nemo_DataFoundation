from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            self._use_chroma = False
            self._collection = None
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata)

        # doc_id dùng để nhận biết tất cả chunk thuộc cùng tài liệu gốc.
        # Nếu ingest đã cung cấp doc_id thì giữ nguyên giá trị đó.
        metadata.setdefault(
            "doc_id",
            doc.id.split("::chunk_")[0],
        )

        record = {
            "id": f"{doc.id}:{self._next_index}",
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

        return record


    def _search_records(
        self,
        query: str,
        records: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []

        # Chỉ embedding query một lần.
        query_embedding = self._embedding_fn(query)

        results: list[dict[str, Any]] = []

        for record in records:
            score = _dot(
                query_embedding,
                record["embedding"],
            )

            results.append({
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": score,
            })

        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)
            self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
         return self._search_records(
        query=query,
        records=self._store,
        top_k=top_k,
    )

    def get_collection_size(self) -> int:
        return len(self._store)

    def search_with_filter(
    self,
    query: str,
    top_k: int = 3,
    metadata_filter: dict | None = None,
    ) -> list[dict]:
        if metadata_filter is None:
            return self._search_records(
                query=query,
                records=self._store,
                top_k=top_k,
            )

        filtered_records = [
            record
            for record in self._store
            if all(
                record["metadata"].get(key) == expected_value
                for key, expected_value in metadata_filter.items()
            )
        ]

        return self._search_records(
            query=query,
            records=filtered_records,
            top_k=top_k,
        )

    def delete_document(self, doc_id: str) -> bool:
        size_before = len(self._store)

        self._store = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") != doc_id
        ]

        size_after = len(self._store)

        return size_after < size_before
