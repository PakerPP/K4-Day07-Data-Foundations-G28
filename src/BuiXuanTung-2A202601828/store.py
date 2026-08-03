from __future__ import annotations

import math
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
            import chromadb

            client = chromadb.EphemeralClient()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Normalize one Document into the dict shape kept in the store."""
        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)
        record = {
            # uid keeps every added chunk distinct even if two docs share an id.
            "uid": f"{doc.id}#{self._next_index}",
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Rank `records` by cosine similarity against `query` and keep the best top_k."""
        if not records or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        query_norm = math.sqrt(_dot(query_embedding, query_embedding))

        scored: list[dict[str, Any]] = []
        for record in records:
            embedding = record["embedding"]
            norm = math.sqrt(_dot(embedding, embedding))
            score = 0.0 if query_norm == 0.0 or norm == 0.0 else _dot(query_embedding, embedding) / (query_norm * norm)
            scored.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    "metadata": dict(record["metadata"]),
                    "score": score,
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store

        Note: self._store is always the source of truth for reads, so that results
        stay identical with or without ChromaDB installed. When ChromaDB is
        available the same chunks are mirrored into the collection as well.
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]
        self._store.extend(records)

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[r["uid"] for r in records],
                    documents=[r["content"] for r in records],
                    embeddings=[r["embedding"] for r in records],
                    metadatas=[self._flatten_metadata(r["metadata"]) for r in records],
                )
            except Exception:
                # A ChromaDB hiccup must not break the lab: keep the in-memory store.
                self._use_chroma = False

    @staticmethod
    def _flatten_metadata(metadata: dict) -> dict:
        """ChromaDB only accepts scalar metadata values."""
        return {
            key: value if isinstance(value, (str, int, float, bool)) else str(value)
            for key, value in metadata.items()
        }

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self._search_records(query, self._store, top_k)

        candidates = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        remaining = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]
        removed = len(self._store) - len(remaining)
        if removed == 0:
            return False

        self._store = remaining
        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(where={"doc_id": doc_id})
            except Exception:
                self._use_chroma = False
        return True
