import os
import json
import aiofiles
from typing import Any
from app.core.artifact.store import ArtifactStore
from app.core.config import get_settings


class FilesystemArtifactStore(ArtifactStore):
    def __init__(self):
        self.settings = get_settings()
        self.base_path = self.settings.ARTIFACT_STORAGE_PATH
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)

    async def save(self, artifact_id: str, content: Any) -> str:
        file_path = os.path.join(self.base_path, f"{artifact_id}.json")
        async with aiofiles.open(file_path, mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(content, ensure_ascii=False, indent=2))
        return file_path

    async def load(self, artifact_id: str, storage_key: str) -> Any:
        # storage_key here is the file path
        if not os.path.exists(storage_key):
            # Fallback: check if it's relative or in base path
            potential_path = os.path.join(self.base_path, f"{artifact_id}.json")
            if os.path.exists(potential_path):
                storage_key = potential_path
            else:
                return None

        async with aiofiles.open(storage_key, mode="r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)
