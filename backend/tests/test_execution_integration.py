import pytest
from unittest.mock import patch
from app.services.llm_providers import MockLLMProvider
import json

@pytest.mark.asyncio
async def test_execute_chat_integration(authenticated_client):
    with patch("app.services.execution_service.get_llm_provider") as mock_get_provider:
        mock_provider = MockLLMProvider()
        mock_get_provider.return_value = mock_provider

        response = await authenticated_client.post(
            "/api/v1/sessions/execute",
            json={
                "type": "chat",
                "session_id": "test_int_session",
                "action": "Hello world"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["output_message"]["content"] is not None

@pytest.mark.asyncio
async def test_execute_chat_streaming(authenticated_client):
    with patch("app.services.execution_service.get_llm_provider") as mock_get_provider:
        mock_provider = MockLLMProvider()
        mock_get_provider.return_value = mock_provider

        async with authenticated_client.stream(
            "POST",
            "/api/v1/sessions/execute",
            json={
                "type": "chat",
                "session_id": "test_stream_session",
                "action": "Stream me",
                "stream": True
            }
        ) as response:
            assert response.status_code == 200
            events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    events.append(line)

            assert len(events) > 0
            # Check for final message
            assert any('final_message' in e for e in events)

            # Verify we can parse JSON
            last_event = events[-1]
            data = json.loads(last_event[6:])
            assert data["type"] == "final_message"
