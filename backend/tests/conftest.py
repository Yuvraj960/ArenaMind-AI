"""Pytest configuration + FastAPI TestClient fixtures.

A `TestClient` is created WITHOUT actually starting uvicorn, so these tests
run without any Docker services running (Postgres, Qdrant, etc.)
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Set KB path before any app imports
import os

project_root = Path(__file__).resolve().parent.parent.parent  # tests/ → backend/ → arenamind/ → project root
kb_path = str(project_root / "knowledge_base")
assert os.path.exists(kb_path), f"knowledge_base not at {kb_path}"
os.environ["KNOWLEDGE_BASE_PATH"] = kb_path


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def client():
    """Sync FastAPI test client — all route tests go through this."""
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc


@pytest.fixture
def async_client():
    """Async client for agents that need `async with`."""
    import asyncio
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=30)


@pytest.fixture(autouse=True)
def reset_cached_instances():
    """Reset singleton state between tests."""
    import app.core.llm_client as lc
    import app.rag.retriever as rg
    import app.agents.master_agent as ma
    lc._client = None
    rg._local_index = None
    ma._master = None
    yield
    lc._client = None
    rg._local_index = None
    ma._master = None