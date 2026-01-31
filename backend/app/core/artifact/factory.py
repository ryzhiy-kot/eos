from functools import lru_cache
from app.core.config import get_settings
from app.core.artifact.store import ArtifactStore
from app.core.artifact.stores.database import DatabaseArtifactStore
from app.core.artifact.stores.filesystem import FilesystemArtifactStore
from app.core.artifact.stores.gcs import GCSArtifactStore
from app.core.artifact.stores.http import HTTPArtifactStore


@lru_cache()
def get_artifact_store() -> ArtifactStore:
    settings = get_settings()
    backend = settings.ARTIFACT_STORAGE_BACKEND.lower()

    if backend == "file":
        return FilesystemArtifactStore()
    elif backend == "gcs":
        return GCSArtifactStore()
    elif backend == "http":
        return HTTPArtifactStore()
    else:
        # Default to DB
        return DatabaseArtifactStore()
