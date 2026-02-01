from abc import ABC, abstractmethod
from typing import Any, Optional


class ArtifactStore(ABC):
    @abstractmethod
    async def save(self, artifact_id: str, content: Any, token: Optional[str] = None) -> str:
        """
        Persist the content and return a storage key/path.

        Args:
            artifact_id: Unique identifier for the artifact
            content: The data to store (dict, list, string, etc.)
            token: Optional authentication token for remote stores

        Returns:
            str: Identifier/Key for future retrieval
        """
        pass

    @abstractmethod
    async def load(self, artifact_id: str, storage_key: str, token: Optional[str] = None) -> Any:
        """
        Retrieve content using the storage key.

        Args:
            artifact_id: Unique identifier for the artifact
            storage_key: The key returned by save()
            token: Optional authentication token for remote stores

        Returns:
            Any: The stored content
        """
        pass
