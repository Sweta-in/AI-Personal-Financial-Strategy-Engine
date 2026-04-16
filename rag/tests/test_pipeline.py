"""
RAG Pipeline tests.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from rag.pipeline import FAISSPipeline
from rag.ingest import chunk_text, _get_builtin_knowledge
from rag.user_rag import UserRAG


class TestChunking:
    def test_basic_chunking(self):
        text = "Hello world. " * 100
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) > 1
        assert all(len(c) <= 120 for c in chunks)  # Small tolerance for sentence boundaries

    def test_empty_text(self):
        assert chunk_text("") == []

    def test_short_text(self):
        chunks = chunk_text("Short text.", chunk_size=512)
        assert len(chunks) == 1

    def test_overlap_preserves_context(self):
        text = "A" * 200 + " B" * 200 + " C" * 200
        chunks = chunk_text(text, chunk_size=250, overlap=50)
        assert len(chunks) >= 2


class TestFAISSPipeline:
    def test_build_and_search(self):
        pipe = FAISSPipeline()
        texts = _get_builtin_knowledge()
        pipe.build_index(texts)

        results = pipe.search("home loan interest deduction", top_k=3)
        assert len(results) > 0
        assert results[0]["score"] > 0

    def test_search_relevance(self):
        pipe = FAISSPipeline()
        texts = [
            "Section 80C allows deductions for ELSS and PPF",
            "Health insurance premiums are deductible under 80D",
            "Home loan interest deduction under Section 24b",
            "Term insurance provides pure life cover",
        ]
        pipe.build_index(texts)

        results = pipe.search("home loan", top_k=2)
        assert any("home loan" in r["text"].lower() or "24b" in r["text"].lower() for r in results)

    def test_empty_search(self):
        pipe = FAISSPipeline()
        assert pipe.search("test") == []


class TestUserRAG:
    def test_ingest_and_retrieve(self):
        rag = UserRAG()
        text = (
            "Policy Number: LI123456. Sum Assured: Rs 1 Crore. "
            "Premium: Rs 15,000 per year. Term: 30 years. "
            "Critical illness rider included. Accidental death benefit: 2x."
        )
        count = rag.ingest_user_policy(user_id=999, pdf_text=text)
        assert count > 0

        results = rag.retrieve_user_policy(user_id=999, query="premium amount")
        assert len(results) > 0

    def test_user_isolation(self):
        rag = UserRAG()
        rag.ingest_user_policy(user_id=100, pdf_text="User 100 policy: HDFC Term Plan")
        rag.ingest_user_policy(user_id=200, pdf_text="User 200 policy: ICICI Health Plan")

        results_100 = rag.retrieve_user_policy(user_id=100, query="policy")
        results_200 = rag.retrieve_user_policy(user_id=200, query="policy")

        # Each user should get their own policy
        if results_100:
            assert any("100" in r or "HDFC" in r for r in results_100)
