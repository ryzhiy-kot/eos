import os
import pytest
import pytest_asyncio

os.environ.setdefault("LLM_PROVIDER", "gemini")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
