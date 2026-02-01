import json
import httpx
from typing import Any, Optional
from app.core.artifact.store import ArtifactStore
from app.core.config import get_settings


class HTTPArtifactStore(ArtifactStore):
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ARTIFACT_HTTP_URL

    async def save(self, artifact_id: str, content: Any, token: Optional[str] = None) -> str:
        if not self.base_url:
            raise ValueError("ARTIFACT_HTTP_URL is not configured")

        url = f"{self.base_url}/artifacts/{artifact_id}"

        headers = {}
        # Prioritize passed token, then configured API key (if any? Settings doesn't have ARTIFACT_API_KEY but assuming pattern)
        # Settings only has AUTH_API_KEY.
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=content, headers=headers)
            resp.raise_for_status()

        # Return URL as key
        return url

    async def load(self, artifact_id: str, storage_key: str, token: Optional[str] = None) -> Any:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient() as client:
            # key is the full URL
            resp = await client.get(storage_key, headers=headers)
            resp.raise_for_status()
            return resp.json()
