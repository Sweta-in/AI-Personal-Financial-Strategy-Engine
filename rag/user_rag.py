"""
User-specific RAG — ChromaDB per-user collections for insurance policies.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from loguru import logger

from rag.ingest import chunk_text


class UserRAG:
    """Per-user document retrieval using ChromaDB."""

    def __init__(self, persist_dir: str = "./rag/chroma_db"):
        self._persist_dir = persist_dir
        self._client = None

    def _get_client(self):
        """Lazy-load ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                self._client = chromadb.PersistentClient(path=self._persist_dir)
                logger.info(f"ChromaDB client initialized at {self._persist_dir}")
            except ImportError:
                logger.warning("chromadb not installed — using in-memory fallback")
                self._client = "fallback"
        return self._client

    def _collection_name(self, user_id: int) -> str:
        """Generate collection name for a user."""
        return f"user_{user_id}_policies"

    def ingest_user_policy(self, user_id: int, pdf_text: str, metadata: dict | None = None) -> int:
        """
        Ingest a user's insurance policy document.

        Args:
            user_id: User ID
            pdf_text: Extracted text from the policy PDF
            metadata: Optional metadata (policy name, provider, etc.)

        Returns:
            Number of chunks ingested
        """
        client = self._get_client()
        chunks = chunk_text(pdf_text, chunk_size=512, overlap=64)

        if not chunks:
            return 0

        if client == "fallback":
            # In-memory fallback
            if not hasattr(self, "_fallback_store"):
                self._fallback_store = {}
            self._fallback_store.setdefault(user_id, []).extend(chunks)
            return len(chunks)

        collection = client.get_or_create_collection(
            name=self._collection_name(user_id),
            metadata={"hnsw:space": "cosine"},
        )

        ids = [f"chunk_{user_id}_{collection.count() + i}" for i in range(len(chunks))]
        metadatas = [metadata or {} for _ in chunks]

        collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas,
        )

        logger.info(f"Ingested {len(chunks)} chunks for user {user_id}")
        return len(chunks)

    def retrieve_user_policy(self, user_id: int, query: str, top_k: int = 3) -> list[str]:
        """
        Retrieve relevant policy chunks for a user.

        Args:
            user_id: User ID
            query: Search query
            top_k: Number of results

        Returns:
            List of relevant text chunks
        """
        client = self._get_client()

        if client == "fallback":
            # Simple keyword search fallback
            if not hasattr(self, "_fallback_store"):
                return []
            user_chunks = self._fallback_store.get(user_id, [])
            if not user_chunks:
                return []
            # Score by keyword overlap
            query_words = set(query.lower().split())
            scored = []
            for chunk in user_chunks:
                chunk_words = set(chunk.lower().split())
                score = len(query_words & chunk_words)
                scored.append((score, chunk))
            scored.sort(reverse=True)
            return [chunk for _, chunk in scored[:top_k]]

        try:
            collection = client.get_collection(self._collection_name(user_id))
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
            )
            return results.get("documents", [[]])[0]
        except Exception:
            return []


# Global instance
user_rag = UserRAG()
