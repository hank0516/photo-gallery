"""
Shared fixtures for all tests.

Strategy:
- SQLite in-memory DB with StaticPool (all sessions share one connection)
- Override get_db → SQLite session, get_current_user → test user
- Mock all S3/storage calls and middleware request logging
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.security import hash_password
from app.models.models import Album, Base, Permission, Photo, ShareLink, User
from main import app

# ── Test database ──────────────────────────────────────────────────────────

ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(ENGINE)
    Base.metadata.create_all(ENGINE)
    yield
    Base.metadata.drop_all(ENGINE)


@pytest.fixture
def db():
    session = TestingSession()
    yield session
    session.close()


# ── Global mocks ───────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_storage():
    s3 = MagicMock()
    s3.download_fileobj.return_value = None

    with (
        patch("app.core.storage.get_client", return_value=s3),
        patch("app.api.albums.get_client", return_value=s3),
        patch("app.core.storage.upload_file"),
        patch("app.api.photos.upload_file"),
        patch("app.core.storage.delete_file"),
        patch("app.api.photos.delete_file"),
        patch("app.core.storage.generate_presigned_url", return_value="https://mock.s3/file"),
        patch("app.api.albums.generate_presigned_url", return_value="https://mock.s3/file"),
        patch("app.api.photos.generate_presigned_url", return_value="https://mock.s3/file"),
        patch("app.api.photos.generate_presigned_download_url", return_value="https://mock.s3/dl"),
        patch("app.api.search.generate_presigned_url", return_value="https://mock.s3/file"),
        patch("app.api.share.generate_presigned_url", return_value="https://mock.s3/file"),
        patch("app.middleware._write_log"),   # prevent middleware from hitting real DB
    ):
        yield


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


# ── User fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def admin(db):
    u = User(google_id="g_admin", email="admin@test.com", name="Admin", is_admin=True)
    db.add(u); db.commit(); db.refresh(u)
    return u


@pytest.fixture
def uploader(db):
    u = User(google_id="g_uploader", email="uploader@test.com", name="Uploader", is_admin=False)
    db.add(u); db.commit(); db.refresh(u)
    return u


@pytest.fixture
def viewer(db):
    u = User(google_id="g_viewer", email="viewer@test.com", name="Viewer", is_admin=False)
    db.add(u); db.commit(); db.refresh(u)
    return u


@pytest.fixture
def outsider(db):
    """User with no permission on any album."""
    u = User(google_id="g_outsider", email="outsider@test.com", name="Outsider", is_admin=False)
    db.add(u); db.commit(); db.refresh(u)
    return u


# ── Album fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def album(db, admin):
    a = Album(name="Test Album", created_by=admin.id)
    db.add(a); db.commit(); db.refresh(a)
    return a


@pytest.fixture
def locked_album(db, admin):
    a = Album(
        name="Locked Album", created_by=admin.id,
        is_locked=True, password_hash=hash_password("pass123"),
    )
    db.add(a); db.commit(); db.refresh(a)
    return a


@pytest.fixture
def album_with_perms(db, album, admin, uploader, viewer):
    """album + uploader/viewer permissions."""
    db.add(Permission(user_id=uploader.id, album_id=album.id, role="uploader", granted_by=admin.id))
    db.add(Permission(user_id=viewer.id, album_id=album.id, role="viewer", granted_by=admin.id))
    db.commit()
    return album


@pytest.fixture
def locked_album_with_perms(db, locked_album, admin, uploader, viewer):
    db.add(Permission(user_id=uploader.id, album_id=locked_album.id, role="uploader", granted_by=admin.id))
    db.add(Permission(user_id=viewer.id, album_id=locked_album.id, role="viewer", granted_by=admin.id))
    db.commit()
    return locked_album


# ── Photo fixture ──────────────────────────────────────────────────────────

@pytest.fixture
def photo(db, album_with_perms, admin):
    p = Photo(
        album_id=album_with_perms.id,
        uploaded_by=admin.id,
        filename="photo.jpg",
        storage_key="albums/1/uuid/original.jpg",
        thumb_300_key="albums/1/uuid/thumb_300.jpg",
        thumb_800_key="albums/1/uuid/thumb_800.jpg",
        file_size_bytes=2048,
        mime_type="image/jpeg",
    )
    db.add(p); db.commit(); db.refresh(p)
    return p


# ── Share link fixtures ────────────────────────────────────────────────────

@pytest.fixture
def share_link(db, album_with_perms, admin):
    sl = ShareLink(
        token="valid-token",
        album_id=album_with_perms.id,
        created_by=admin.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(sl); db.commit(); db.refresh(sl)
    return sl


@pytest.fixture
def expired_share_link(db, album_with_perms, admin):
    sl = ShareLink(
        token="expired-token",
        album_id=album_with_perms.id,
        created_by=admin.id,
        expires_at=datetime.utcnow() - timedelta(days=1),
    )
    db.add(sl); db.commit(); db.refresh(sl)
    return sl


@pytest.fixture
def revoked_share_link(db, album_with_perms, admin):
    sl = ShareLink(
        token="revoked-token",
        album_id=album_with_perms.id,
        created_by=admin.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=True,
    )
    db.add(sl); db.commit(); db.refresh(sl)
    return sl


@pytest.fixture
def locked_share_link(db, locked_album_with_perms, admin):
    sl = ShareLink(
        token="locked-token",
        album_id=locked_album_with_perms.id,
        created_by=admin.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(sl); db.commit(); db.refresh(sl)
    return sl


# ── Client helpers ─────────────────────────────────────────────────────────

def auth_client(user: User, db_session) -> TestClient:
    """TestClient authenticated as the given user."""
    def _get_user():
        return user

    def _get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = _get_user
    app.dependency_overrides[get_db] = _get_db
    return TestClient(app, raise_server_exceptions=False)


def anon_client(db_session) -> TestClient:
    """Unauthenticated TestClient (no pg_session cookie)."""
    def _get_db():
        yield db_session

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides[get_db] = _get_db
    return TestClient(app, raise_server_exceptions=False)
