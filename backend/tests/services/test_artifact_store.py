import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import os
from app.core.artifact.stores.database import DatabaseArtifactStore
from app.core.artifact.stores.filesystem import FilesystemArtifactStore
from app.core.artifact.stores.http import HTTPArtifactStore
from app.core.artifact.factory import get_artifact_store
from app.services.artifact_service import ArtifactService
from app.schemas.artifact import Artifact as ArtifactSchema


@pytest.mark.asyncio
async def test_database_store():
    store = DatabaseArtifactStore()
    key = await store.save("id1", {"data": "test"})
    assert key == "db"
    content = await store.load("id1", key)
    assert content is None


@pytest.mark.asyncio
async def test_filesystem_store(tmp_path):
    with patch("app.core.artifact.stores.filesystem.get_settings") as mock_settings:
        mock_settings.return_value.ARTIFACT_STORAGE_PATH = str(tmp_path)
        store = FilesystemArtifactStore()
        payload = {"data": "file_test"}

        # Test Save
        key = await store.save("id_file", payload)
        assert os.path.exists(key)
        assert str(tmp_path) in key

        # Test Load
        loaded = await store.load("id_file", key)
        assert loaded == payload


@pytest.mark.asyncio
async def test_http_store():
    with patch("app.core.artifact.stores.http.get_settings") as mock_settings:
        mock_settings.return_value.ARTIFACT_HTTP_URL = "http://mock-service"
        store = HTTPArtifactStore()
        payload = {"data": "http_test"}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            key = await store.save("id_http", payload)
            assert key == "http://mock-service/artifacts/id_http"
            mock_post.assert_called_once()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response_get = MagicMock()
            mock_response_get.status_code = 200
            mock_response_get.json.return_value = payload
            mock_get.return_value = mock_response_get

            loaded = await store.load("id_http", key)
            assert loaded == payload
            mock_get.assert_called_once_with(key)


@pytest.mark.asyncio
async def test_factory():
    with patch("app.core.artifact.factory.get_settings") as mock_settings:
        # DB
        mock_settings.return_value.ARTIFACT_STORAGE_BACKEND = "db"
        get_artifact_store.cache_clear()
        assert isinstance(get_artifact_store(), DatabaseArtifactStore)

        # File
        mock_settings.return_value.ARTIFACT_STORAGE_BACKEND = "file"
        mock_settings.return_value.ARTIFACT_STORAGE_PATH = "/tmp"
        get_artifact_store.cache_clear()
        assert isinstance(get_artifact_store(), FilesystemArtifactStore)


@pytest.mark.asyncio
async def test_service_integration_db(db_session):
    # Ensure default DB behavior
    with patch("app.services.artifact_service.get_settings") as mock_settings:
        mock_settings.return_value.ARTIFACT_STORAGE_BACKEND = "db"
        get_artifact_store.cache_clear()  # Reset factory cache

        artifact_in = ArtifactSchema(
            id="test_db_integration",
            type="text",
            payload={"content": "stored_in_db"},
            session_id="session_1",
            metadata={},
        )

        # Create
        created = await ArtifactService.create_or_update_artifact(
            db_session, artifact_in
        )
        assert created.storage_backend == "db"
        assert created.payload == {"content": "stored_in_db"}

        # Retrieve
        retrieved = await ArtifactService.get_artifact(db_session, created.id)
        assert retrieved.payload == {"content": "stored_in_db"}


@pytest.mark.asyncio
async def test_service_integration_file(db_session, tmp_path):
    # Test file offloading
    with (
        patch("app.services.artifact_service.get_settings") as mock_settings,
        patch("app.core.artifact.stores.filesystem.get_settings") as mock_fs_settings,
        patch("app.core.artifact.factory.get_settings") as mock_factory_settings,
    ):
        # Setup settings for all components
        for m in [mock_settings, mock_fs_settings, mock_factory_settings]:
            m.return_value.ARTIFACT_STORAGE_BACKEND = "file"
            m.return_value.ARTIFACT_STORAGE_PATH = str(tmp_path)

        get_artifact_store.cache_clear()

        artifact_in = ArtifactSchema(
            id="test_file_integration",
            type="text",
            payload={"content": "stored_in_file"},
            session_id="session_1",
            metadata={},
        )

        # Create
        created = await ArtifactService.create_or_update_artifact(
            db_session, artifact_in
        )
        assert created.storage_backend == "file"
        assert created.storage_key.startswith(str(tmp_path))
        # Internally payload should be stored, but implementation returns hydrated object
        assert created.payload == {"content": "stored_in_file"}

        # Verify DB state (should be None)
        # We need to refresh the object from DB to see what's actually stored,
        # because the service layer manually sets payload on the instance before returning.
        await db_session.refresh(created)

        assert created.storage_backend == "file"
        assert created.payload is None

        # Retrieve via Service (should rehydrate)
        retrieved = await ArtifactService.get_artifact(db_session, created.id)
        assert retrieved.payload == {"content": "stored_in_file"}
