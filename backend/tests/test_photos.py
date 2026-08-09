"""
Photo endpoints — permission matrix.

  Operation              admin  uploader  viewer  outsider  anon
  ─────────────────────────────────────────────────────────────
  GET /photos/{id}       200    200       200     403       401
  PATCH /photos/{id}     200    200       403     403       401
  DELETE /photos/{id}    204    403       403     403       401
  GET /{id}/download     307    307       307     403       401
"""
from tests.conftest import anon_client, auth_client

BASE = "/api/photo-gallery"


# ── GET /photos/{id} ───────────────────────────────────────────────────────

def test_get_photo_unauthenticated(db, photo):
    r = anon_client(db).get(f"{BASE}/photos/{photo.id}")
    assert r.status_code == 401


def test_get_photo_as_admin(db, admin, photo):
    r = auth_client(admin, db).get(f"{BASE}/photos/{photo.id}")
    assert r.status_code == 200
    assert r.json()["id"] == photo.id


def test_get_photo_as_uploader(db, uploader, photo):
    r = auth_client(uploader, db).get(f"{BASE}/photos/{photo.id}")
    assert r.status_code == 200


def test_get_photo_as_viewer(db, viewer, photo):
    r = auth_client(viewer, db).get(f"{BASE}/photos/{photo.id}")
    assert r.status_code == 200


def test_get_photo_as_outsider_forbidden(db, outsider, photo):
    r = auth_client(outsider, db).get(f"{BASE}/photos/{photo.id}")
    assert r.status_code == 403


def test_get_nonexistent_photo(db, admin):
    r = auth_client(admin, db).get(f"{BASE}/photos/99999")
    assert r.status_code == 404


# ── PATCH /photos/{id} ────────────────────────────────────────────────────

def test_update_photo_as_admin(db, admin, photo):
    r = auth_client(admin, db).patch(f"{BASE}/photos/{photo.id}", json={"caption": "Nice shot"})
    assert r.status_code == 200
    assert r.json()["caption"] == "Nice shot"


def test_update_photo_as_uploader(db, uploader, photo):
    r = auth_client(uploader, db).patch(f"{BASE}/photos/{photo.id}", json={"caption": "By uploader"})
    assert r.status_code == 200


def test_update_photo_as_viewer_forbidden(db, viewer, photo):
    r = auth_client(viewer, db).patch(f"{BASE}/photos/{photo.id}", json={"caption": "Hack"})
    assert r.status_code == 403


def test_update_photo_as_outsider_forbidden(db, outsider, photo):
    r = auth_client(outsider, db).patch(f"{BASE}/photos/{photo.id}", json={"caption": "Hack"})
    assert r.status_code == 403


# ── DELETE /photos/{id} ───────────────────────────────────────────────────

def test_delete_photo_as_admin(db, admin, photo):
    r = auth_client(admin, db).delete(f"{BASE}/photos/{photo.id}")
    assert r.status_code == 204


def test_delete_photo_as_uploader_forbidden(db, uploader, photo):
    r = auth_client(uploader, db).delete(f"{BASE}/photos/{photo.id}")
    assert r.status_code == 403


def test_delete_photo_as_viewer_forbidden(db, viewer, photo):
    r = auth_client(viewer, db).delete(f"{BASE}/photos/{photo.id}")
    assert r.status_code == 403


def test_delete_photo_as_outsider_forbidden(db, outsider, photo):
    r = auth_client(outsider, db).delete(f"{BASE}/photos/{photo.id}")
    assert r.status_code == 403


def test_delete_photo_unauthenticated(db, photo):
    r = anon_client(db).delete(f"{BASE}/photos/{photo.id}")
    assert r.status_code == 401


# ── GET /photos/{id}/download ─────────────────────────────────────────────

def test_download_photo_as_viewer_redirects(db, viewer, photo):
    r = auth_client(viewer, db).get(f"{BASE}/photos/{photo.id}/download", follow_redirects=False)
    assert r.status_code == 307


def test_download_photo_as_admin_redirects(db, admin, photo):
    r = auth_client(admin, db).get(f"{BASE}/photos/{photo.id}/download", follow_redirects=False)
    assert r.status_code == 307


def test_download_photo_as_outsider_forbidden(db, outsider, photo):
    r = auth_client(outsider, db).get(f"{BASE}/photos/{photo.id}/download", follow_redirects=False)
    assert r.status_code == 403


def test_download_photo_unauthenticated(db, photo):
    r = anon_client(db).get(f"{BASE}/photos/{photo.id}/download", follow_redirects=False)
    assert r.status_code == 401
