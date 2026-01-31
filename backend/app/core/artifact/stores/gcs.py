import json
from typing import Any
import logging
from app.core.artifact.store import ArtifactStore
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class GCSArtifactStore(ArtifactStore):
    def __init__(self):
        self.settings = get_settings()
        self.bucket_name = self.settings.ARTIFACT_GCS_BUCKET
        try:
            from google.cloud import storage

            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
        except ImportError:
            logger.error("google-cloud-storage is not installed.")
            self.client = None
            self.bucket = None

    async def save(self, artifact_id: str, content: Any) -> str:
        if not self.bucket:
            raise RuntimeError("GCS client not initialized")

        blob_name = f"artifacts/{artifact_id}.json"
        blob = self.bucket.blob(blob_name)

        # Blobs upload isn't natively async in the official standard lib,
        # but for this size usually acceptable or we run in executor.
        # For true async high-perf, gcloud-aio-storage is better but
        # standard lib is safer default.
        blob.upload_from_string(json.dumps(content), content_type="application/json")
        return f"gs://{self.bucket_name}/{blob_name}"

    async def load(self, artifact_id: str, storage_key: str) -> Any:
        if not self.bucket:
            raise RuntimeError("GCS client not initialized")

        # Parse gs://.../artifacts/{id}.json or just use blob name
        if storage_key.startswith("gs://"):
            # gs://bucket/path
            path_parts = storage_key.replace(f"gs://{self.bucket_name}/", "")
            blob = self.bucket.blob(path_parts)
        else:
            blob = self.bucket.blob(storage_key)

        content = blob.download_as_text()
        return json.loads(content)
