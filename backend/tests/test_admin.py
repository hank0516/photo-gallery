"""
Admin endpoints — user management, logs.

All admin endpoints require is_admin=True; non-admin → 403, anon → 401.
"""
from tests.conftest import anon_client, auth_client

BASE = "/api/photo-gallery"
ADMIN = f"{BASE}/admin"


# ── GET /admin/users ───────────────────────────────────────────────────────

def test_list_admin_users_as_admin(db, admin, viewer):
    r = auth_client(admin, db).get(f"{ADMIN}/users")
    assert r.status_code == 200
    emails = [u["email"] for u in r.json()]
    assert "admin@test.com" in emails


def test_list_admin_users_as_viewer_forbidden(db, viewer):
    r = auth_client(viewer, db).get(f"{ADMIN}/users")
    assert r.status_code == 403


def test_list_admin_users_unauthenticated(db):
    r = anon_client(db).get(f"{ADMIN}/users")
    assert r.status_code == 401


# ── GET /users (users router) ─────────────────────────────────────────────

def test_list_users_as_admin(db, admin):
    r = auth_client(admin, db).get(f"{BASE}/users")
    assert r.status_code == 200


def test_list_users_as_viewer_forbidden(db, viewer):
    r = auth_client(viewer, db).get(f"{BASE}/users")
    assert r.status_code == 403


# ── PATCH /admin/users/{id} ────────────────────────────────────────────────

def test_update_user_as_admin(db, admin, viewer):
    r = auth_client(admin, db).patch(f"{ADMIN}/users/{viewer.id}", json={"is_admin": True})
    assert r.status_code == 200
    assert r.json()["is_admin"] is True


def test_update_user_self_forbidden(db, admin):
    r = auth_client(admin, db).patch(f"{ADMIN}/users/{admin.id}", json={"is_admin": False})
    assert r.status_code == 400


def test_update_user_as_viewer_forbidden(db, viewer, outsider):
    r = auth_client(viewer, db).patch(f"{ADMIN}/users/{outsider.id}", json={"is_admin": True})
    assert r.status_code == 403


def test_update_nonexistent_user(db, admin):
    r = auth_client(admin, db).patch(f"{ADMIN}/users/99999", json={"is_admin": True})
    assert r.status_code == 404


# ── GET /admin/users/{id}/permissions ─────────────────────────────────────

def test_get_user_permissions_as_admin(db, admin, viewer, album_with_perms):
    r = auth_client(admin, db).get(f"{ADMIN}/users/{viewer.id}/permissions")
    assert r.status_code == 200
    roles = {p["album_id"]: p["role"] for p in r.json()}
    assert roles.get(album_with_perms.id) == "viewer"


def test_get_user_permissions_as_viewer_forbidden(db, viewer):
    r = auth_client(viewer, db).get(f"{ADMIN}/users/{viewer.id}/permissions")
    assert r.status_code == 403


# ── GET /admin/login-logs ─────────────────────────────────────────────────

def test_list_login_logs_as_admin(db, admin):
    r = auth_client(admin, db).get(f"{ADMIN}/login-logs")
    assert r.status_code == 200
    assert "items" in r.json()


def test_list_login_logs_as_viewer_forbidden(db, viewer):
    r = auth_client(viewer, db).get(f"{ADMIN}/login-logs")
    assert r.status_code == 403


# ── GET /admin/request-logs ───────────────────────────────────────────────

def test_list_request_logs_as_admin(db, admin):
    r = auth_client(admin, db).get(f"{ADMIN}/request-logs")
    assert r.status_code == 200
    assert "items" in r.json()


def test_list_request_logs_as_viewer_forbidden(db, viewer):
    r = auth_client(viewer, db).get(f"{ADMIN}/request-logs")
    assert r.status_code == 403
