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

            # TODO: initialize chromadb client + collection
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # Build a stored record that contains id, content, metadata (including doc_id), and embedding
        metadata = dict(doc.metadata) if doc.metadata is not None else {}
        metadata = dict(metadata)  # copy
        metadata.setdefault("doc_id", doc.id)
        embedding = self._embedding_fn(doc.content)
        rec_id = f"{doc.id}-{self._next_index}"
        return {"id": rec_id, "content": doc.content, "metadata": metadata, "embedding": embedding}

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []
        query_embedding = self._embedding_fn(query)
        scored: list[dict[str, Any]] = []
        for rec in records:
            score = _dot(query_embedding, rec.get("embedding", []))
            scored.append({"id": rec.get("id"), "content": rec.get("content"), "metadata": rec.get("metadata"), "score": score})
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[: max(0, top_k)]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if self._use_chroma and self._collection is not None:
            # Not implemented in tests; keep placeholder
            ids = []
            documents = []
            embeddings = []
            for doc in docs:
                rec = self._make_record(doc)
                ids.append(rec["id"])
                documents.append(rec["content"])
                embeddings.append(rec["embedding"])
                self._next_index += 1
            try:
                self._collection.add(ids=ids, documents=documents, embeddings=embeddings)
            except Exception:
                # fallback to in-memory if chroma fails
                for doc in docs:
                    rec = self._make_record(doc)
                    self._store.append(rec)
                    self._next_index += 1
        else:
            for doc in docs:
                rec = self._make_record(doc)
                self._store.append(rec)
                self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            try:
                results = self._collection.query(query_texts=[query], n_results=top_k)
                # Not used in tests; fallback to in-memory mapping if needed
                hits = []
                for res in results["results"]:
                    for idx, score in zip(res.get("ids", []), res.get("distances", [])):
                        hits.append({"id": idx, "content": None, "metadata": None, "score": score})
                return hits[:top_k]
            except Exception:
                pass
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            try:
                return len(self._collection.get(include=['ids'])['ids'])
            except Exception:
                pass
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if metadata_filter is None:
            return self.search(query, top_k=top_k)
        # filter records where all items in metadata_filter match
        filtered = []
        for rec in self._store:
            md = rec.get("metadata", {}) or {}
            ok = True
            for k, v in metadata_filter.items():
                if md.get(k) != v:
                    ok = False
                    break
            if ok:
                filtered.append(rec)
        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        original_len = len(self._store)
        self._store = [rec for rec in self._store if rec.get("metadata", {}).get("doc_id") != doc_id]
        return len(self._store) < original_len
