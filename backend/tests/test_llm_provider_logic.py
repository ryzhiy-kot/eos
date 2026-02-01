import pytest
from app.services.llm_providers import HttpLLMProvider
from app.core.llm_protocol import LLMRequest
import os
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_llm_provider_token_priority():
    # Case 1: Configured API Key exists -> Use it
    # We patch os.getenv inside __init__ call? No, patch environment before init.
    with patch.dict(os.environ, {"LLM_API_KEY": "system_key", "LLM_SERVICE_URL": "http://mock"}):
        provider = HttpLLMProvider()
        req = LLMRequest(session_id="s1", messages=[], api_key="user_token")

        with patch("app.services.llm_providers.httpx.AsyncClient") as MockClient:
             mock_instance = MagicMock()
             MockClient.return_value.__aenter__.return_value = mock_instance

             mock_stream_ctx = MagicMock()
             mock_instance.stream.return_value = mock_stream_ctx

             mock_response = MagicMock()
             mock_stream_ctx.__aenter__.return_value = mock_response

             # Mock aiter_lines as async generator
             async def async_gen():
                 yield b""
             mock_response.aiter_lines.return_value = async_gen()

             async for _ in provider.generate_stream(req):
                 pass

             # Check arguments to client.stream
             args, kwargs = mock_instance.stream.call_args
             headers = kwargs.get("headers", {})
             assert headers["Authorization"] == "Bearer system_key"

    # Case 2: No Configured Key -> Use User Token
    with patch.dict(os.environ, {"LLM_API_KEY": "", "LLM_SERVICE_URL": "http://mock"}):
        # We need to reload provider to pick up empty env?
        # Actually HttpLLMProvider reads os.getenv in __init__.
        # So we create a new instance.
        provider = HttpLLMProvider()
        req = LLMRequest(session_id="s1", messages=[], api_key="user_token")

        with patch("app.services.llm_providers.httpx.AsyncClient") as MockClient:
             mock_instance = MagicMock()
             MockClient.return_value.__aenter__.return_value = mock_instance

             mock_stream_ctx = MagicMock()
             mock_instance.stream.return_value = mock_stream_ctx
             mock_response = MagicMock()
             mock_stream_ctx.__aenter__.return_value = mock_response

             async def async_gen():
                 yield b""
             mock_response.aiter_lines.return_value = async_gen()

             async for _ in provider.generate_stream(req):
                 pass

             args, kwargs = mock_instance.stream.call_args
             headers = kwargs.get("headers", {})
             assert headers["Authorization"] == "Bearer user_token"
