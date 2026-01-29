import pytest
import os
import json
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.llm_providers import HttpLLMProvider, MockLLMProvider, get_llm_provider
from app.core.llm_protocol import LLMRequest, LLMMessage, TextDeltaEvent, ArtifactStartEvent

@pytest.mark.asyncio
async def test_mock_llm_provider():
    provider = MockLLMProvider()
    request = LLMRequest(
        session_id="test",
        messages=[LLMMessage(role="user", content="hello")]
    )

    events = []
    async for event in provider.generate_stream(request):
        events.append(event)

    assert len(events) > 0
    assert any(isinstance(e, TextDeltaEvent) for e in events)

@pytest.mark.asyncio
async def test_get_llm_provider():
    with patch.dict(os.environ, {"LLM_PROVIDER": "http"}):
        assert isinstance(get_llm_provider(), HttpLLMProvider)

    with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}):
        assert isinstance(get_llm_provider(), MockLLMProvider)

@pytest.mark.asyncio
async def test_http_llm_provider():
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        # Mock response
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()

        async def mock_aiter_lines():
            yield json.dumps({"type": "text_delta", "content": "Hello"})
            yield json.dumps({"type": "text_delta", "content": " World"})

        mock_response.aiter_lines = mock_aiter_lines

        # Mock stream context manager
        mock_stream_context = MagicMock()
        mock_stream_context.__aenter__.return_value = mock_response
        mock_stream_context.__aexit__.return_value = None

        # Ensure client.stream returns the context manager, not a coroutine
        mock_instance.stream = MagicMock(return_value=mock_stream_context)

        provider = HttpLLMProvider()
        request = LLMRequest(
            session_id="test",
            messages=[LLMMessage(role="user", content="hello")]
        )

        events = []
        async for event in provider.generate_stream(request):
            events.append(event)

        assert len(events) == 2
        assert events[0].content == "Hello"
        assert events[1].content == " World"
