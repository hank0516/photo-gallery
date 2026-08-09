"""
Album endpoints — CRUD, permission matrix, locked album, ZIP download.

Permission matrix for album-level operations:
  Operation              admin  uploader  viewer  outsider  anon
  ─────────────────────────────────────────────────────────────
  GET /albums            200    200       200     200(0)    401
  POST /albums           201    403       403     403       401
  GET /albums/{id}       200    200       200     403       401
  PATCH /albums/{id}     200    403       403     403       401
  DELETE /albums/{id}    204    403       403     403       401
  GET /{id}/permissions  200    403       403     403       401
  PUT /{id}/perms/{uid}  200    403       403     403       401
  DEL /{id}/perms/{uid}  204    403       403     403       401
  GET /{id}/download-zip 200    200       403     403       401
  POST /{id}/unlock      200    200       200     403       401
"""
from tests.conftest import anon_client, auth_client

BASE = "/api/photo-gallery"


# ── List albums ────────────────────────────────────────────────────────────

def test_list_albums_unauthenticated(db):
    r = anon_client(db).get(f"{BASE}/albums")
    assert r.status_code == 401


def test_list_albums_admin_sees_all(db, admin, album_with_perms):
    r = auth_client(admin, db).get(f"{BASE}/albums")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_list_albums_viewer_sees_permitted_only(db, viewer, album_with_perms):
    r = auth_client(viewer, db).get(f"{BASE}/albums")
    assert r.status_code == 200
    ids = [a["id"] for a in r.json()]
    assert album_with_perms.id in ids


def test_list_albums_outsider_sees_empty(db, outsider, album_with_perms):
    r = auth_client(outsider, db).get(f"{BASE}/albums")
    assert r.status_code == 200
    assert r.json() == []


# ── Create album ───────────────────────────────────────────────────────────

def test_create_album_unauthenticated(db):
    r = anon_client(db).post(f"{BASE}/albums", json={"name": "New"})
    assert r.status_code == 401


def test_create_album_as_admin(db, admin):
    r = auth_client(admin, db).post(f"{BASE}/albums", json={"name": "My Album"})
    assert r.status_code == 201
    assert r.json()["name"] == "My Album"


def test_create_album_as_viewer_forbidden(db, viewer, album_with_perms):
    r = auth_client(viewer, db).post(f"{BASE}/albums", json={"name": "Hack"})
    assert r.status_code == 403


def test_create_album_as_uploader_forbidden(db, uploader, album_with_perms):
    r = auth_client(uploader, db).post(f"{BASE}/albums", json={"name": "Hack"})
    assert r.status_code == 403


def test_create_locked_album_requires_password(db, admin):
    r = auth_client(admin, db).post(f"{BASE}/albums", json={"name": "Locked", "is_locked": True})
    assert r.status_code == 400


def test_create_locked_album_with_password(db, admin):
    r = auth_client(admin, db).post(
        f"{BASE}/albums", json={"name": "Locked", "is_locked": True, "password": "abc123"}
    )
    assert r.status_code == 201
    assert r.json()["is_locked"] is True


# ── Get album ──────────────────────────────────────────────────────────────

def test_get_album_unauthenticated(db, album_with_perms):
    r = anon_client(db).get(f"{BASE}/albums/{album_with_perms.id}")
    assert r.status_code == 401


def test_get_album_as_admin(db, admin, album_with_perms):
    r = auth_client(admin, db).get(f"{BASE}/albums/{album_with_perms.id}")
    assert r.status_code == 200
    assert r.json()["album"]["id"] == album_with_perms.id


def test_get_album_as_uploader(db, uploader, album_with_perms):
    r = auth_client(uploader, db).get(f"{BASE}/albums/{album_with_perms.id}")
    assert r.status_code == 200


def test_get_album_as_viewer(db, viewer, album_with_perms):
    r = auth_client(viewer, db).get(f"{BASE}/albums/{album_with_perms.id}")
    assert r.status_code == 200


def test_get_album_as_outsider_forbidden(db, outsider, album_with_perms):
    r = auth_client(outsider, db).get(f"{BASE}/albums/{album_with_perms.id}")
    assert r.status_code == 403


def test_get_nonexistent_album(db, admin):
    r = auth_client(admin, db).get(f"{BASE}/albums/99999")
    assert r.status_code == 404


# ── Update album ───────────────────────────────────────────────────────────

def test_update_album_as_admin(db, admin, album_with_perms):
    r = auth_client(admin, db).patch(
        f"{BASE}/albums/{album_with_perms.id}", json={"name": "Renamed"}
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"


def test_update_album_as_uploader_forbidden(db, uploader, album_with_perms):
    r = auth_client(uploader, db).patch(
        f"{BASE}/albums/{album_with_perms.id}", json={"name": "Hack"}
    )
    assert r.status_code == 403


def test_update_album_as_viewer_forbidden(db, viewer, album_with_perms):
    r = auth_client(viewer, db).patch(
        f"{BASE}/albums/{album_with_perms.id}", json={"name": "Hack"}
    )
    assert r.status_code == 403


def test_update_album_as_outsider_forbidden(db, outsider, album_with_perms):
    r = auth_client(outsider, db).patch(
        f"{BASE}/albums/{album_with_perms.id}", json={"name": "Hack"}
    )
    assert r.status_code == 403


# ── Delete album ───────────────────────────────────────────────────────────

def test_delete_album_as_admin(db, admin, album_with_perms):
    r = auth_client(admin, db).delete(f"{BASE}/albums/{album_with_perms.id}")
    assert r.status_code == 204


def test_delete_album_as_uploader_forbidden(db, uploader, album_with_perms):
    r = auth_client(uploader, db).delete(f"{BASE}/albums/{album_with_perms.id}")
    assert r.status_code == 403


def test_delete_album_as_viewer_forbidden(db, viewer, album_with_perms):
    r = auth_client(viewer, db).delete(f"{BASE}/albums/{album_with_perms.id}")
    assert r.status_code == 403


# ── Download ZIP ───────────────────────────────────────────────────────────

def test_download_zip_as_admin(db, admin, album_with_perms):
    r = auth_client(admin, db).get(f"{BASE}/albums/{album_with_perms.id}/download-zip")
    assert r.status_code == 200
    assert "zip" in r.headers.get("content-type", "")


def test_download_zip_as_uploader(db, uploader, album_with_perms):
    r = auth_client(uploader, db).get(f"{BASE}/albums/{album_with_perms.id}/download-zip")
    assert r.status_code == 200


def test_download_zip_as_viewer_forbidden(db, viewer, album_with_perms):
    r = auth_client(viewer, db).get(f"{BASE}/albums/{album_with_perms.id}/download-zip")
    assert r.status_code == 403


def test_download_zip_as_outsider_forbidden(db, outsider, album_with_perms):
    r = auth_client(outsider, db).get(f"{BASE}/albums/{album_with_perms.id}/download-zip")
    assert r.status_code == 403


def test_download_zip_unauthenticated(db, album_with_perms):
    r = anon_client(db).get(f"{BASE}/albums/{album_with_perms.id}/download-zip")
    assert r.status_code == 401


# ── Locked album ───────────────────────────────────────────────────────────

def test_locked_album_returns_locked_flag_without_token(db, viewer, locked_album_with_perms):
    r = auth_client(viewer, db).get(f"{BASE}/albums/{locked_album_with_perms.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["locked"] is True
    assert data["photos"] == []


def test_locked_album_unlock_correct_password(db, viewer, locked_album_with_perms):
    c = auth_client(viewer, db)
    r = c.post(f"{BASE}/albums/{locked_album_with_perms.id}/unlock", json={"password": "pass123"})
    assert r.status_code == 200
    assert "unlock_token" in r.json()


def test_locked_album_unlock_wrong_password(db, viewer, locked_album_with_perms):
    c = auth_client(viewer, db)
    r = c.post(f"{BASE}/albums/{locked_album_with_perms.id}/unlock", json={"password": "wrong"})
    assert r.status_code == 401


def test_locked_album_unlock_outsider_forbidden(db, outsider, locked_album_with_perms):
    r = auth_client(outsider, db).post(
        f"{BASE}/albums/{locked_album_with_perms.id}/unlock", json={"password": "pass123"}
    )
    assert r.status_code == 403


def test_locked_album_with_valid_unlock_token_shows_photos(db, viewer, locked_album_with_perms):
    c = auth_client(viewer, db)
    unlock_r = c.post(
        f"{BASE}/albums/{locked_album_with_perms.id}/unlock", json={"password": "pass123"}
    )
    token = unlock_r.json()["unlock_token"]
    r = c.get(f"{BASE}/albums/{locked_album_with_perms.id}?unlock_token={token}")
    assert r.status_code == 200
    assert r.json().get("locked") is not True


def test_locked_album_with_invalid_unlock_token_stays_locked(db, viewer, locked_album_with_perms):
    c = auth_client(viewer, db)
    r = c.get(f"{BASE}/albums/{locked_album_with_perms.id}?unlock_token=bad-token")
    assert r.status_code == 200
    assert r.json()["locked"] is True


# ── Permissions management ─────────────────────────────────────────────────

def test_list_permissions_as_admin(db, admin, album_with_perms):
    r = auth_client(admin, db).get(f"{BASE}/albums/{album_with_perms.id}/permissions")
    assert r.status_code == 200
    assert len(r.json()) >= 2  # uploader + viewer


def test_list_permissions_as_viewer_forbidden(db, viewer, album_with_perms):
    r = auth_client(viewer, db).get(f"{BASE}/albums/{album_with_perms.id}/permissions")
    assert r.status_code == 403


def test_list_permissions_as_outsider_forbidden(db, outsider, album_with_perms):
    r = auth_client(outsider, db).get(f"{BASE}/albums/{album_with_perms.id}/permissions")
    assert r.status_code == 403


def test_set_permission_as_admin(db, admin, album_with_perms, outsider):
    r = auth_client(admin, db).put(
        f"{BASE}/albums/{album_with_perms.id}/permissions/{outsider.id}",
        json={"role": "viewer"},
    )
    assert r.status_code == 200


def test_set_permission_as_viewer_forbidden(db, viewer, album_with_perms, outsider):
    r = auth_client(viewer, db).put(
        f"{BASE}/albums/{album_with_perms.id}/permissions/{outsider.id}",
        json={"role": "viewer"},
    )
    assert r.status_code == 403


def test_revoke_permission_as_admin(db, admin, album_with_perms, viewer):
    r = auth_client(admin, db).delete(
        f"{BASE}/albums/{album_with_perms.id}/permissions/{viewer.id}"
    )
    assert r.status_code == 204


def test_revoke_permission_as_viewer_forbidden(db, viewer, album_with_perms, outsider):
    r = auth_client(viewer, db).delete(
        f"{BASE}/albums/{album_with_perms.id}/permissions/{outsider.id}"
    )
    assert r.status_code == 403
