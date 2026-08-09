"""
Search endpoint — permission filtering and param validation.
"""
from app.models.models import Photo
from tests.conftest import anon_client, auth_client

BASE = "/api/photo-gallery"


def test_search_unauthenticated(db):
    r = anon_client(db).get(f"{BASE}/search?q=test")
    assert r.status_code == 401


def test_search_no_params_returns_400(db, admin):
    r = auth_client(admin, db).get(f"{BASE}/search")
    assert r.status_code == 400


def test_search_returns_results(db, admin, photo):
    r = auth_client(admin, db).get(f"{BASE}/search?q=photo")
    assert r.status_code == 200
    data = r.json()
    assert "photos" in data
    assert "total" in data


def test_search_admin_sees_all_albums(db, admin, photo):
    r = auth_client(admin, db).get(f"{BASE}/search?q=photo")
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()["photos"]]
    assert photo.id in ids


def test_search_viewer_sees_permitted_albums_only(db, viewer, photo, album_with_perms):
    r = auth_client(viewer, db).get(f"{BASE}/search?q=photo")
    assert r.status_code == 200
    # viewer has permission to album_with_perms, so photo should appear
    ids = [p["id"] for p in r.json()["photos"]]
    assert photo.id in ids


def test_search_outsider_sees_nothing(db, outsider, photo):
    r = auth_client(outsider, db).get(f"{BASE}/search?q=photo")
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_search_with_permitted_album_id(db, viewer, photo, album_with_perms):
    r = auth_client(viewer, db).get(f"{BASE}/search?album_id={album_with_perms.id}")
    assert r.status_code == 200


def test_search_with_forbidden_album_id(db, outsider, album_with_perms):
    r = auth_client(outsider, db).get(f"{BASE}/search?album_id={album_with_perms.id}")
    assert r.status_code == 403


def test_search_by_date_range(db, admin, photo):
    r = auth_client(admin, db).get(f"{BASE}/search?date_from=2020-01-01&date_to=2030-12-31")
    assert r.status_code == 200


def test_search_no_match_returns_empty(db, viewer, album_with_perms):
    r = auth_client(viewer, db).get(f"{BASE}/search?q=zzznomatch")
    assert r.status_code == 200
    assert r.json()["total"] == 0
