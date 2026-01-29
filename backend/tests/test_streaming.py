import pytest
from unittest.mock import patch
from app.services.llm_providers import MockLLMProvider
import json

@pytest.mark.asyncio
async def test_chat_stream_integration(client):
    with patch("app.services.execution_service.get_llm_provider") as mock_get_provider:
        mock_provider = MockLLMProvider()
        mock_get_provider.return_value = mock_provider

        response = await client.post(
            "/api/v1/sessions/chat",
            json={
                "type": "chat",
                "session_id": "test_stream_session",
                "action": "Hello world",
                "stream": True
            }
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        # Read the stream
        chunks = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                chunks.append(data)

        assert len(chunks) > 0
        assert any(c["type"] == "text_delta" for c in chunks)

@pytest.mark.asyncio
async def test_chat_no_stream_integration(client):
    with patch("app.services.execution_service.get_llm_provider") as mock_get_provider:
        mock_provider = MockLLMProvider()
        mock_get_provider.return_value = mock_provider

        response = await client.post(
            "/api/v1/sessions/chat",
            json={
                "type": "chat",
                "session_id": "test_no_stream_session",
                "action": "Hello world",
                "stream": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["output_message"]["content"] is not None
