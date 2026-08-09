"""
Share link endpoints — creation, revocation, public access, locked albums.

Authenticated endpoints (admin only):
  POST   /albums/{id}/share      → 201 (admin) / 403 (non-admin)
  GET    /albums/{id}/share      → 200 (admin) / 403 (non-admin)
  DELETE /share/{token}          → 204 (admin) / 403 (non-admin)

Public endpoints (no auth):
  GET  /share/{token}            → 200 / 404 / 410
  POST /share/{token}/unlock     → 200 / 401 / 410
"""
from app.core.security import create_share_unlock_token
from tests.conftest import anon_client, auth_client

BASE = "/api/photo-gallery"


# ── POST /albums/{id}/share ────────────────────────────────────────────────

def test_create_share_link_as_admin(db, admin, album_with_perms):
    r = auth_client(admin, db).post(
        f"{BASE}/albums/{album_with_perms.id}/share", json={"expires_days": 7}
    )
    assert r.status_code == 201
    data = r.json()
    assert "token" in data
    assert data["is_revoked"] is False
    assert data["is_expired"] is False


def test_create_share_link_as_viewer_forbidden(db, viewer, album_with_perms):
    r = auth_client(viewer, db).post(
        f"{BASE}/albums/{album_with_perms.id}/share", json={"expires_days": 7}
    )
    assert r.status_code == 403


def test_create_share_link_as_uploader_forbidden(db, uploader, album_with_perms):
    r = auth_client(uploader, db).post(
        f"{BASE}/albums/{album_with_perms.id}/share", json={"expires_days": 7}
    )
    assert r.status_code == 403


def test_create_share_link_unauthenticated(db, album_with_perms):
    r = anon_client(db).post(
        f"{BASE}/albums/{album_with_perms.id}/share", json={"expires_days": 7}
    )
    assert r.status_code == 401


def test_create_share_link_invalid_days(db, admin, album_with_perms):
    r = auth_client(admin, db).post(
        f"{BASE}/albums/{album_with_perms.id}/share", json={"expires_days": 400}
    )
    assert r.status_code == 400


def test_create_share_link_nonexistent_album(db, admin):
    r = auth_client(admin, db).post(f"{BASE}/albums/99999/share", json={"expires_days": 7})
    assert r.status_code == 404


# ── GET /albums/{id}/share ────────────────────────────────────────────────

def test_list_share_links_as_admin(db, admin, share_link):
    r = auth_client(admin, db).get(f"{BASE}/albums/{share_link.album_id}/share")
    assert r.status_code == 200
    tokens = [l["token"] for l in r.json()]
    assert share_link.token in tokens


def test_list_share_links_as_viewer_forbidden(db, viewer, share_link):
    r = auth_client(viewer, db).get(f"{BASE}/albums/{share_link.album_id}/share")
    assert r.status_code == 403


def test_list_share_links_unauthenticated(db, share_link):
    r = anon_client(db).get(f"{BASE}/albums/{share_link.album_id}/share")
    assert r.status_code == 401


# ── DELETE /share/{token} ─────────────────────────────────────────────────

def test_revoke_share_link_as_admin(db, admin, share_link):
    r = auth_client(admin, db).delete(f"{BASE}/share/{share_link.token}")
    assert r.status_code == 204


def test_revoke_share_link_as_viewer_forbidden(db, viewer, share_link):
    r = auth_client(viewer, db).delete(f"{BASE}/share/{share_link.token}")
    assert r.status_code == 403


def test_revoke_share_link_unauthenticated(db, share_link):
    r = anon_client(db).delete(f"{BASE}/share/{share_link.token}")
    assert r.status_code == 401


def test_revoke_nonexistent_share_link(db, admin):
    r = auth_client(admin, db).delete(f"{BASE}/share/no-such-token")
    assert r.status_code == 404


# ── GET /share/{token} — public ───────────────────────────────────────────

def test_get_shared_album_valid_token(db, share_link):
    r = anon_client(db).get(f"{BASE}/share/{share_link.token}")
    assert r.status_code == 200
    data = r.json()
    assert data["album"]["id"] == share_link.album_id
    assert "photos" in data
    assert "expires_at" in data


def test_get_shared_album_expired_token(db, expired_share_link):
    r = anon_client(db).get(f"{BASE}/share/{expired_share_link.token}")
    assert r.status_code == 410


def test_get_shared_album_revoked_token(db, revoked_share_link):
    r = anon_client(db).get(f"{BASE}/share/{revoked_share_link.token}")
    assert r.status_code == 410


def test_get_shared_album_nonexistent_token(db):
    r = anon_client(db).get(f"{BASE}/share/no-such-token")
    assert r.status_code == 404


# ── Locked album via share link ────────────────────────────────────────────

def test_locked_shared_album_returns_locked_flag(db, locked_share_link):
    r = anon_client(db).get(f"{BASE}/share/{locked_share_link.token}")
    assert r.status_code == 200
    data = r.json()
    assert data["locked"] is True
    assert data["photos"] == []


def test_locked_shared_album_unlock_correct_password(db, locked_share_link):
    r = anon_client(db).post(
        f"{BASE}/share/{locked_share_link.token}/unlock", json={"password": "pass123"}
    )
    assert r.status_code == 200
    assert "unlock_token" in r.json()


def test_locked_shared_album_unlock_wrong_password(db, locked_share_link):
    r = anon_client(db).post(
        f"{BASE}/share/{locked_share_link.token}/unlock", json={"password": "wrong"}
    )
    assert r.status_code == 401


def test_locked_shared_album_with_valid_unlock_token_shows_photos(db, locked_share_link):
    c = anon_client(db)
    unlock_r = c.post(
        f"{BASE}/share/{locked_share_link.token}/unlock", json={"password": "pass123"}
    )
    unlock_token = unlock_r.json()["unlock_token"]
    r = c.get(f"{BASE}/share/{locked_share_link.token}?unlock_token={unlock_token}")
    assert r.status_code == 200
    assert r.json().get("locked") is not True


def test_locked_share_unlock_token_is_share_token_bound(db, locked_share_link, album_with_perms, admin):
    """An unlock token for one share link must not work for a different share link."""
    from datetime import timedelta
    from app.models.models import ShareLink
    from datetime import datetime

    # Create another share link for a different (non-locked) album — irrelevant,
    # what matters is a different share_token value
    other_token = create_share_unlock_token(locked_share_link.album_id, "different-share-token")

    r = anon_client(db).get(
        f"{BASE}/share/{locked_share_link.token}?unlock_token={other_token}"
    )
    assert r.status_code == 200
    assert r.json()["locked"] is True  # token bound to different share_token, rejected


def test_unlock_expired_share_link_returns_410(db, expired_share_link):
    r = anon_client(db).post(
        f"{BASE}/share/{expired_share_link.token}/unlock", json={"password": "pass123"}
    )
    assert r.status_code == 410


def test_unlock_revoked_share_link_returns_410(db, revoked_share_link):
    r = anon_client(db).post(
        f"{BASE}/share/{revoked_share_link.token}/unlock", json={"password": "pass123"}
    )
    assert r.status_code == 410
