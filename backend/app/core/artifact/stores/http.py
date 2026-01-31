import json
import httpx
from typing import Any
from app.core.artifact.store import ArtifactStore
from app.core.config import get_settings


class HTTPArtifactStore(ArtifactStore):
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ARTIFACT_HTTP_URL

    async def save(self, artifact_id: str, content: Any) -> str:
        if not self.base_url:
            raise ValueError("ARTIFACT_HTTP_URL is not configured")

        url = f"{self.base_url}/artifacts/{artifact_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=content)
            resp.raise_for_status()

        # Return URL as key
        return url

    async def load(self, artifact_id: str, storage_key: str) -> Any:
        async with httpx.AsyncClient() as client:
            # key is the full URL
            resp = await client.get(storage_key)
            resp.raise_for_status()
            return resp.json()
