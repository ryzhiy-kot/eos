import pytest
from unittest.mock import patch
from app.services.llm_providers import MockLLMProvider

@pytest.mark.asyncio
async def test_execute_chat_integration(client):
    with patch("app.services.execution_service.get_llm_provider") as mock_get_provider:
        mock_provider = MockLLMProvider()
        mock_get_provider.return_value = mock_provider

        response = await client.post(
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
