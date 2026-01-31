from typing import Any
from app.core.artifact.store import ArtifactStore


class DatabaseArtifactStore(ArtifactStore):
    """
    Pass-through store.

    When using the DB as the backend, the payload is stored directly
    in the `Artifact` table's JSON column by the service (SQLAlchemy).

    So `save` returns a marker, and `load` just returns None because
    the service layer expects the payload to already be on the object.

    However, to support a consistent interface, we can treat this as a no-op
    wrapper or actually implement logic if we wanted to store blobs separately
    in a text column, but for now it's consistent with existing behavior.
    """

    async def save(self, artifact_id: str, content: Any) -> str:
        # In DB mode, the service saves the content directly to the model.
        # We return a sentinel or empty string.
        return "db"

    async def load(self, artifact_id: str, storage_key: str) -> Any:
        # Service handles loading from the DB model directly for efficiency.
        # This might be used if we wanted to double-check, but usually
        # the storage_backend='db' check in service bypasses explicit load.
        # If called, we return None to indicate "no external data loaded".
        return None
