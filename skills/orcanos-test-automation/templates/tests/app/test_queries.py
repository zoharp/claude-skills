"""
tests/app/test_queries.py
=========================
Main pytest test file for Orcanos project backends.

Standard test categories:
  TC-00  TestConnectivity         — /health, /documents (no LLM needed)
  TC-01  TestListQueries          — meta/listing queries
  TC-02  TestKeywordSearch        — full-text and fuzzy search
  TC-03  TestGeneralRAGQueries    — cross-document RAG questions
  TC-04  TestSpecificDocQueries   — questions about a named document
  TC-05  TestEdgeCases            — empty input, gibberish, very long queries
  TC-06  TestPerformance          — soft latency assertions (warn, don't fail hard)
         TestFromDefinitions      — JSON-driven parametrized tests

Add project-specific tests inside the existing classes, or add a new class and
register it in run_tests.py TC_MAP so the HTML report labels it correctly.
"""

import os
import json
import time
import pytest
import requests
from pathlib import Path

BACKEND_URL      = os.getenv("BACKEND_URL", "http://localhost:8000")
DEFINITIONS_PATH = Path(__file__).parent.parent / "test_definitions.json"

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get(endpoint: str, **kwargs) -> requests.Response:
    return requests.get(f"{BACKEND_URL}{endpoint}", timeout=30, **kwargs)


def post(endpoint: str, body: dict, **kwargs) -> requests.Response:
    return requests.post(f"{BACKEND_URL}{endpoint}", json=body, timeout=60, **kwargs)


def query(prompt: str) -> requests.Response:
    return post("/query", {"query": prompt})


# ─────────────────────────────────────────────────────────────────────────────
# TC-00  Connectivity / Sanity
# ─────────────────────────────────────────────────────────────────────────────

class TestConnectivity:

    def test_health_returns_200(self):
        resp = get("/health")
        assert resp.status_code == 200

    def test_health_has_status_ok(self):
        data = get("/health").json()
        assert data.get("status") == "ok"

    def test_documents_returns_list(self):
        resp = get("/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list) and len(data) >= 1, \
            f"Expected non-empty list, got {data!r}"


# ─────────────────────────────────────────────────────────────────────────────
# TC-01  List / Meta Queries
# ─────────────────────────────────────────────────────────────────────────────

class TestListQueries:

    def test_list_documents_query(self):
        resp = query("What documents are available?")
        assert resp.status_code == 200
        answer = resp.json().get("answer", "")
        assert len(answer) >= 20, f"Answer too short: {answer!r}"


# ─────────────────────────────────────────────────────────────────────────────
# TC-02  Keyword Search
# ─────────────────────────────────────────────────────────────────────────────

class TestKeywordSearch:

    def test_keyword_returns_answer(self):
        # Replace "requirement" with a keyword that exists in your document corpus
        resp = query("Find anything related to requirements")
        assert resp.status_code == 200
        assert len(resp.json().get("answer", "")) >= 20


# ─────────────────────────────────────────────────────────────────────────────
# TC-03  General RAG Queries
# ─────────────────────────────────────────────────────────────────────────────

class TestGeneralRAGQueries:

    def test_purpose_question(self):
        resp = query("What is the purpose of this system?")
        assert resp.status_code == 200
        answer = resp.json().get("answer", "")
        assert len(answer) >= 50, f"Answer too short ({len(answer)} chars): {answer[:100]}"

    def test_answer_not_empty(self):
        resp = query("Give me a summary of all documents.")
        assert resp.status_code == 200
        assert resp.json().get("answer", "").strip() != ""


# ─────────────────────────────────────────────────────────────────────────────
# TC-04  Specific Document Queries
# ─────────────────────────────────────────────────────────────────────────────

class TestSpecificDocQueries:

    def test_named_document_question(self):
        # Replace with a document name that exists in your corpus
        resp = query("What does the README say about installation?")
        assert resp.status_code == 200
        assert resp.json().get("answer", "").strip() != ""


# ─────────────────────────────────────────────────────────────────────────────
# TC-05  Edge Cases & Robustness
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_empty_query_does_not_crash(self):
        resp = post("/query", {"query": ""})
        assert resp.status_code != 500, f"Server crashed on empty query (HTTP {resp.status_code})"

    def test_gibberish_does_not_crash(self):
        resp = query("asdfghjkl qwerty zxcvbnm 12345 !!!")
        assert resp.status_code != 500

    def test_very_long_query_does_not_crash(self):
        long_q = "What is the meaning of life? " * 50
        resp = query(long_q)
        assert resp.status_code != 500

    def test_special_characters_do_not_crash(self):
        resp = query("'; DROP TABLE documents; --")
        assert resp.status_code != 500


# ─────────────────────────────────────────────────────────────────────────────
# TC-06  Performance (soft thresholds — warn, don't fail hard)
# ─────────────────────────────────────────────────────────────────────────────

class TestPerformance:

    @pytest.mark.slow
    def test_query_responds_within_30s(self):
        start = time.time()
        resp  = query("What is this system about?")
        elapsed = time.time() - start
        assert resp.status_code == 200
        if elapsed > 30:
            pytest.warns(UserWarning, match=f"Query took {elapsed:.1f}s — consider optimizing")

    @pytest.mark.slow
    def test_health_responds_within_1s(self):
        start   = time.time()
        resp    = get("/health")
        elapsed = time.time() - start
        assert resp.status_code == 200
        assert elapsed < 1.0, f"/health took {elapsed:.2f}s — should be instant"


# ─────────────────────────────────────────────────────────────────────────────
# JSON-driven  (reads test_definitions.json)
# ─────────────────────────────────────────────────────────────────────────────

def _load_definitions():
    if not DEFINITIONS_PATH.exists():
        return []
    return json.loads(DEFINITIONS_PATH.read_text(encoding="utf-8"))


class TestFromDefinitions:
    """
    JSON-driven test cases — add cases to test_definitions.json without
    touching this Python file.
    """

    @pytest.mark.parametrize("tc", _load_definitions(), ids=lambda tc: tc["id"])
    def test_case(self, tc):
        if tc["method"] == "GET":
            resp = get(tc["endpoint"])
        else:
            body = {"query": tc["prompt"]} if tc.get("prompt") else {}
            resp = post(tc["endpoint"], body)

        expected = tc.get("expected", {})

        if "http_status" in expected:
            assert resp.status_code == expected["http_status"], \
                f"[{tc['id']}] Expected HTTP {expected['http_status']}, got {resp.status_code}"

        if "http_status_not" in expected:
            assert resp.status_code != expected["http_status_not"], \
                f"[{tc['id']}] Expected status != {expected['http_status_not']}, got {resp.status_code}"

        if "result_min_count" in expected:
            data = resp.json()
            items = data if isinstance(data, list) else data.get("results", [])
            assert len(items) >= expected["result_min_count"], \
                f"[{tc['id']}] Expected ≥{expected['result_min_count']} items, got {len(items)}"

        if "answer_min_length" in expected:
            data   = resp.json()
            answer = data.get("answer", "")
            assert len(answer) >= expected["answer_min_length"], \
                f"[{tc['id']}] Answer too short ({len(answer)} chars): {answer[:100]}"
