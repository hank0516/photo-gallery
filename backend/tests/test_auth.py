from tests.conftest import anon_client, auth_client

BASE = "/api/photo-gallery"


def test_me_unauthenticated(db):
    r = anon_client(db).get(f"{BASE}/auth/me")
    assert r.status_code == 401


def test_me_returns_user_info(db, admin):
    r = auth_client(admin, db).get(f"{BASE}/auth/me")
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "admin@test.com"
    assert data["is_admin"] is True


def test_me_viewer(db, viewer):
    r = auth_client(viewer, db).get(f"{BASE}/auth/me")
    assert r.status_code == 200
    assert r.json()["is_admin"] is False


def test_logout(db, admin):
    r = auth_client(admin, db).post(f"{BASE}/auth/logout")
    assert r.status_code == 200
    assert r.json()["ok"] is True
