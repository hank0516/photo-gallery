# API Contracts: iOS Native App

Base URL: `https://cloud.hansu.tw/api/photo-gallery`

All authenticated requests send: `Authorization: Bearer <jwt>`

---

## Auth

### GET /auth/login?redirect=native
Initiates Google OAuth. The `redirect=native` parameter causes the callback to redirect to the custom URL scheme instead of the web URL.

Opens in `ASWebAuthenticationSession`. No request body.

### GET /auth/callback
_Existing endpoint — backend change required._

When `redirect=native` was passed to `/auth/login`, responds with:
```
302 → photogallery://auth/callback?token=<jwt>
```
Otherwise behaves as before (web redirect).

### GET /auth/me
Returns the authenticated user's profile.

**Response**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "Family Member",
  "avatar_url": "https://...",
  "is_admin": false
}
```

### POST /auth/logout
Clears server-side session (cookie). Native app also deletes token from Keychain.

---

## Backend Change: Bearer Token Support

_Required change to `app/core/auth.py` → `get_current_user`_

Accept JWT from either source (cookie wins if both present):
1. `pg_session` cookie (existing — web frontend)
2. `Authorization: Bearer <token>` header (new — native app)

---

## Albums

### GET /albums
Returns albums the authenticated user has access to.

**Response**
```json
[
  {
    "id": 1,
    "name": "Family Trip 2025",
    "description": "Summer vacation",
    "album_date": "2025-07-15",
    "cover_thumb_url": "https://presigned...",
    "photo_count": 42,
    "my_role": "viewer",
    "is_locked": false,
    "created_at": "2025-07-16T10:00:00"
  }
]
```

### GET /albums/{id}?page=1&per_page=50
Returns album detail and paginated media items.

**Response**
```json
{
  "id": 1,
  "name": "Family Trip 2025",
  "description": "...",
  "my_role": "viewer",
  "is_locked": false,
  "photos": [
    {
      "id": 10,
      "filename": "IMG_001.jpg",
      "caption": null,
      "media_type": "photo",
      "thumb_url": "https://presigned-thumb...",
      "width": 4032,
      "height": 3024,
      "file_size_bytes": 3145728,
      "uploaded_at": "2025-07-16T11:00:00"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 50
}
```

### POST /albums/{id}/unlock
Unlock a password-protected album for this session.

**Request**
```json
{ "password": "secret" }
```
**Response 200**
```json
{ "unlock_token": "<jwt>" }
```
Subsequent requests to this album include: `X-Unlock-Token: <jwt>`

---

## Photos

### GET /photos/{id}
Returns photo detail including EXIF and presigned original URL.

**Response**
```json
{
  "id": 10,
  "filename": "IMG_001.jpg",
  "caption": null,
  "media_type": "photo",
  "original_url": "https://presigned-original...",
  "thumb_url": "https://presigned-thumb...",
  "width": 4032,
  "height": 3024,
  "file_size_bytes": 3145728,
  "exif_taken_at": "2025-07-15T14:30:00",
  "exif_camera_model": "iPhone 15 Pro",
  "exif_latitude": 25.0330,
  "exif_longitude": 121.5654,
  "uploaded_at": "2025-07-16T11:00:00"
}
```

### GET /photos/{id}/download
Returns presigned URL with `Content-Disposition: attachment`. Native app fetches the URL, downloads the file, and saves to Camera Roll using `PHPhotoLibrary`.

**Response**
```json
{ "download_url": "https://presigned-download..." }
```

---

## Search

### GET /search?q=&date_from=&date_to=&album_id=&page=1&per_page=50

| Param | Type | Notes |
|---|---|---|
| `q` | String? | Matches filename or caption |
| `date_from` | Date? | `YYYY-MM-DD`, filters by EXIF taken_at |
| `date_to` | Date? | `YYYY-MM-DD` |
| `album_id` | Int? | Scope to one album |
| `page` | Int | Default 1 |
| `per_page` | Int | Default 50 |

**Response**
```json
{
  "results": [
    {
      "id": 10,
      "filename": "IMG_001.jpg",
      "thumb_url": "https://presigned...",
      "media_type": "photo",
      "album_id": 1,
      "album_name": "Family Trip 2025",
      "exif_taken_at": "2025-07-15T14:30:00"
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 50
}
```

---

## Custom URL Scheme

The app registers `photogallery://` as its URL scheme.

| URL | Trigger |
|---|---|
| `photogallery://auth/callback?token=<jwt>` | OAuth flow complete; app extracts and stores token |
