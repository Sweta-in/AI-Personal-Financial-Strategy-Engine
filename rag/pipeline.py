"""
RAG Pipeline — FAISS-based vector search for financial knowledge.

Uses SentenceTransformer("all-MiniLM-L6-v2") for embeddings.
"""

from __future__ import annotations

import os
import pickle
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from loguru import logger


class FAISSPipeline:
    """FAISS-based retrieval pipeline for financial knowledge."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None
        self._index = None
        self._texts: list[str] = []

    def _load_model(self):
        """Lazy-load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self._model_name)
                logger.info(f"Loaded SentenceTransformer: {self._model_name}")
            except ImportError:
                logger.warning("sentence-transformers not installed — using fallback embeddings")
                self._model = "fallback"

    def _encode(self, texts: list[str]) -> np.ndarray:
        """Encode texts to embeddings."""
        self._load_model()
        if self._model == "fallback":
            # Fallback: simple TF-IDF-like hash-based embeddings
            dim = 384
            embeddings = np.zeros((len(texts), dim), dtype=np.float32)
            for i, text in enumerate(texts):
                words = text.lower().split()
                for j, word in enumerate(words[:dim]):
                    embeddings[i, j % dim] += hash(word) % 1000 / 1000.0
            # Normalize
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1
            embeddings = embeddings / norms
            return embeddings
        else:
            return self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)

    def build_index(self, texts: list[str], save_path: str | None = None) -> None:
        """
        Build a FAISS index from text chunks.

        Args:
            texts: List of text chunks to index
            save_path: Optional path to save index + texts
        """
        try:
            import faiss
        except ImportError:
            logger.warning("faiss-cpu not installed — using numpy-based search fallback")
            self._texts = texts
            self._index = "numpy"
            if save_path:
                os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
                with open(save_path + ".texts.pkl", "wb") as f:
                    pickle.dump(texts, f)
                np.save(save_path + ".embeddings.npy", self._encode(texts))
            return

        embeddings = self._encode(texts)
        dim = embeddings.shape[1]

        index = faiss.IndexFlatIP(dim)  # Inner product (cosine similarity with normalized vectors)
        index.add(embeddings.astype(np.float32))

        self._index = index
        self._texts = texts

        if save_path:
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            faiss.write_index(index, save_path + ".faiss")
            with open(save_path + ".texts.pkl", "wb") as f:
                pickle.dump(texts, f)

        logger.info(f"Built FAISS index with {len(texts)} chunks, dim={dim}")

    def load_index(self, load_path: str) -> None:
        """Load a previously saved FAISS index."""
        try:
            import faiss
            self._index = faiss.read_index(load_path + ".faiss")
        except ImportError:
            self._index = "numpy"

        with open(load_path + ".texts.pkl", "rb") as f:
            self._texts = pickle.load(f)

        logger.info(f"Loaded FAISS index with {len(self._texts)} chunks")

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Search the index for the most relevant chunks.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of {text, score} dicts
        """
        if not self._texts:
            return []

        query_emb = self._encode([query])

        if self._index == "numpy":
            # Numpy fallback
            all_emb_path = None
            # Compute cosine similarity manually
            text_embs = self._encode(self._texts)
            scores = np.dot(text_embs, query_emb.T).flatten()
            top_indices = np.argsort(scores)[-top_k:][::-1]
            return [
                {"text": self._texts[i], "score": float(scores[i]), "source": "faiss"}
                for i in top_indices
            ]
        else:
            scores, indices = self._index.search(query_emb.astype(np.float32), min(top_k, len(self._texts)))
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0:
                    results.append({
                        "text": self._texts[idx],
                        "score": float(score),
                        "source": "faiss",
                    })
            return results


# Global pipeline instance
pipeline = FAISSPipeline()
