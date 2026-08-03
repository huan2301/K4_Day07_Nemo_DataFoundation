from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
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
        self._client = None
        self._next_index = 0

        if importlib.util.find_spec("chromadb") is not None:
            try:
                chromadb = importlib.import_module("chromadb")
                self._client = chromadb.PersistentClient(
                    path=str(Path(__file__).resolve().parent.parent / ".chromadb")
                )
                self._collection = self._client.get_or_create_collection(
                    name=self._collection_name
                )
                self._use_chroma = True
            except Exception:
                self._use_chroma = False
                self._collection = None
                self._client = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": dict(doc.metadata or {}),
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        query_embedding = self._embedding_fn(query)
        scored = []

        for record in records:
            score = _dot(query_embedding, record["embedding"])
            scored.append(
                {
                    "content": record["content"],
                    "score": score,
                    "metadata": record["metadata"],
                    "id": record["id"],
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict = None
    ) -> list[dict]:
        if metadata_filter is None:
            return self.search(query, top_k=top_k)

        filtered = []
        for record in self._store:
            if all(
                record.get("metadata", {}).get(k) == v
                for k, v in metadata_filter.items()
            ):
                filtered.append(record)

        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        before = len(self._store)
        self._store = [
            record
            for record in self._store
            if record.get("id") != doc_id
            and record.get("metadata", {}).get("doc_id") != doc_id
        ]
        return len(self._store) < before
