"""
tests/conftest.py — shared pytest config and fixtures.
Fail fast: if the backend is unreachable at session start, abort immediately.
"""

import os
import pytest
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with -m 'not slow')")
    config.addinivalue_line("markers", "integration: marks tests that require a live backend")


def pytest_sessionstart(session):
    """Abort the entire run if the backend is not reachable."""
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
        resp.raise_for_status()
    except Exception as e:
        pytest.exit(
            f"\n❌ Backend not reachable at {BACKEND_URL}.\n"
            f"   Start it with: uvicorn backend.api:app --reload\n"
            f"   Error: {e}",
            returncode=1,
        )
