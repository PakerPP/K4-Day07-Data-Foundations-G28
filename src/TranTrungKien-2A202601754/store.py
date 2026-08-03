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
            import chromadb

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Embed a document's content and build a normalized stored record."""
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": dict(doc.metadata) if doc.metadata else {},
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        """Embed the query and rank the given records by dot-product similarity."""
        if not records or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        scored = [
            (_dot(query_embedding, record["embedding"]), record) for record in records
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)

        results: list[dict[str, Any]] = []
        for score, record in scored[:top_k]:
            results.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    "metadata": record["metadata"],
                    "score": score,
                }
            )
        return results

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        if self._use_chroma and self._collection is not None:
            ids, contents, embeddings, metadatas = [], [], [], []
            for doc in docs:
                ids.append(doc.id)
                contents.append(doc.content)
                embeddings.append(self._embedding_fn(doc.content))
                metadatas.append(dict(doc.metadata) if doc.metadata else {"_empty": True})
            self._collection.add(
                ids=ids,
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        else:
            for doc in docs:
                self._store.append(self._make_record(doc))

        self._next_index += len(docs)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            raw = self._collection.query(
                query_embeddings=[query_embedding], n_results=top_k
            )
            return self._format_chroma_results(raw)

        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict = None
    ) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k)

        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            raw = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=metadata_filter,
            )
            return self._format_chroma_results(raw)

        filtered = [
            record
            for record in self._store
            if all(
                record["metadata"].get(key) == value
                for key, value in metadata_filter.items()
            )
        ]
        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            # A doc_id may refer either to a chunk's own id (single-Document-
            # per-document case) or to a metadata["doc_id"] shared by several
            # chunks (multi-chunk ingestion pipeline case). Match both.
            ids_to_delete: set[str] = set()

            by_id = self._collection.get(ids=[doc_id])
            ids_to_delete.update(by_id.get("ids", []) or [])

            by_metadata = self._collection.get(where={"doc_id": doc_id})
            ids_to_delete.update(by_metadata.get("ids", []) or [])

            if not ids_to_delete:
                return False
            self._collection.delete(ids=list(ids_to_delete))
            return True

        original_len = len(self._store)
        self._store = [
            record
            for record in self._store
            if record["id"] != doc_id and record["metadata"].get("doc_id") != doc_id
        ]
        return len(self._store) < original_len

    @staticmethod
    def _format_chroma_results(raw: dict) -> list[dict[str, Any]]:
        """Normalize a ChromaDB query() response into the store's record format."""
        ids = raw.get("ids", [[]])[0]
        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]

        results = []
        for i in range(len(ids)):
            results.append(
                {
                    "id": ids[i],
                    "content": documents[i],
                    "metadata": metadatas[i] if metadatas[i] else {},
                    "score": distances[i],
                }
            )
        return results