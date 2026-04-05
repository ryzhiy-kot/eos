import os
import pytest
import pytest_asyncio

os.environ.setdefault("LLM_PROVIDER", "gemini")
os.environ.setdefault("GROQ_API_KEY", "test_key_for_ci")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
