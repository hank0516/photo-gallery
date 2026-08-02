# API Contract: Private Photo Gallery

**Base URL**: `https://cloud.hansu.tw/api/photo-gallery`
**Auth**: All endpoints require a valid JWT in `httpOnly` cookie (`pg_session`), except where noted.
**Format**: JSON request/response bodies. File uploads use `multipart/form-data`.

---

## Authentication

### `GET /auth/login`
Redirects browser to Google OAuth consent screen.
- **Auth required**: No
- **Response**: 302 redirect to Google

### `GET /auth/callback?code=&state=`
Google OAuth callback. Exchanges code for user profile, creates/updates user, issues JWT cookie.
- **Auth required**: No
- **Response**: 302 redirect to `/sites/photo-gallery/` with `pg_session` cookie set

### `POST /auth/logout`
Clears the session cookie.
- **Response**: `200 { "ok": true }`

### `GET /auth/me`
Returns current user's profile and global admin status.
- **Response**:
```json
{
  "id": 1,
  "email": "user@gmail.com",
  "name": "Hank",
  "avatar_url": "https://...",
  "is_admin": true
}
```

---

## Albums

### `GET /albums`
List all albums the caller has permission to see. Global admins see all albums.
- **Response**:
```json
[
  {
    "id": 1,
    "name": "Japan 2025",
    "description": "Trip to Tokyo and Kyoto",
    "cover_thumb_url": "https://...",
    "photo_count": 142,
    "my_role": "admin",
    "created_at": "2025-04-01T10:00:00Z"
  }
]
```

### `POST /albums`
Create a new album. Admin only.
- **Body**: `{ "name": "string", "description": "string|null" }`
- **Response**: `201` with created album object

### `GET /albums/{album_id}`
Get album details + paginated photos. 403 if no permission.
- **Query params**: `page=1`, `per_page=50`, `sort=uploaded_at|exif_date_taken`, `order=desc|asc`
- **Response**:
```json
{
  "album": { "id": 1, "name": "...", "my_role": "viewer" },
  "photos": [
    {
      "id": 10,
      "thumb_300_url": "https://...",
      "thumb_800_url": "https://...",
      "caption": "Sunset at Fushimi Inari",
      "exif_date_taken": "2025-04-03T17:22:00",
      "width": 4032,
      "height": 3024
    }
  ],
  "total": 142,
  "page": 1,
  "per_page": 50
}
```

### `PATCH /albums/{album_id}`
Update album name, description, or cover photo. Admin role on album required.
- **Body**: `{ "name"?: "string", "description"?: "string|null", "cover_photo_id"?: "int|null" }`
- **Response**: `200` with updated album object

### `DELETE /albums/{album_id}`
Soft-delete album and all its photos. Admin role on album required.
- **Response**: `204`

---

## Photos

### `POST /albums/{album_id}/photos`
Upload one or more photos. Uploader or admin role required.
- **Body**: `multipart/form-data` with one or more `files` fields
- **Response**: `201`
```json
{
  "uploaded": [
    { "id": 11, "filename": "IMG_001.jpg", "thumb_300_url": "https://..." }
  ],
  "failed": [
    { "filename": "doc.pdf", "reason": "Unsupported file type" }
  ]
}
```

### `GET /photos/{photo_id}`
Get single photo details including EXIF and original URL.
- **Response**:
```json
{
  "id": 10,
  "album_id": 1,
  "filename": "IMG_001.jpg",
  "caption": "...",
  "original_url": "https://... (pre-signed, 15min)",
  "thumb_300_url": "https://...",
  "thumb_800_url": "https://...",
  "file_size_bytes": 8421376,
  "width": 4032,
  "height": 3024,
  "exif_date_taken": "2025-04-03T17:22:00",
  "exif_camera": "Apple iPhone 15 Pro",
  "exif_gps_lat": 34.9671,
  "exif_gps_lon": 135.7727,
  "uploaded_at": "2025-04-10T09:00:00Z",
  "uploaded_by": { "id": 1, "name": "Hank" }
}
```

### `PATCH /photos/{photo_id}`
Update photo caption. Uploader or admin role required.
- **Body**: `{ "caption": "string|null" }`
- **Response**: `200` with updated photo object

### `DELETE /photos/{photo_id}`
Delete a photo (removes from storage + DB). Admin role on album required.
- **Response**: `204`

### `GET /photos/{photo_id}/download`
Returns a redirect to a short-lived pre-signed original download URL.
- **Response**: 302 redirect to pre-signed URL with `Content-Disposition: attachment`

---

## Albums — Downloads & Search

### `GET /albums/{album_id}/download`
Stream album as zip archive. Uploader or admin role required.
- **Response**: `application/zip` stream, `Content-Disposition: attachment; filename="<album-name>.zip"`

### `GET /search`
Search photos across all permitted albums.
- **Query params**: `q=keyword`, `album_id=int`, `date_from=YYYY-MM-DD`, `date_to=YYYY-MM-DD`, `page=1`, `per_page=50`
- **Response**: Same structure as album photo list, with additional `album` field per photo

---

## Permissions (Admin only)

### `GET /albums/{album_id}/permissions`
List all users with access to this album.
- **Response**: `[{ "user_id": 1, "email": "...", "name": "...", "role": "viewer", "granted_at": "..." }]`

### `PUT /albums/{album_id}/permissions/{user_id}`
Grant or update a user's role on an album. Creates if not exists, updates if exists.
- **Body**: `{ "role": "viewer|uploader|admin" }`
- **Response**: `200`

### `DELETE /albums/{album_id}/permissions/{user_id}`
Revoke a user's access to an album.
- **Response**: `204`

---

## Users (Admin only)

### `GET /users`
List all users who have ever signed in.
- **Response**: `[{ "id": 1, "email": "...", "name": "...", "is_admin": false, "last_login_at": "..." }]`

### `PATCH /users/{user_id}`
Update a user's global admin flag.
- **Body**: `{ "is_admin": true|false }`
- **Response**: `200`

---

## Share Links (Admin only)

### `GET /albums/{album_id}/share-links`
List all share links for an album.
- **Response**: `[{ "id": 1, "token": "uuid", "expires_at": "...", "is_revoked": false, "created_at": "..." }]`

### `POST /albums/{album_id}/share-links`
Generate a new share link.
- **Body**: `{ "expires_at": "2026-09-01T00:00:00Z" }`
- **Response**: `201 { "token": "uuid", "share_url": "https://cloud.hansu.tw/sites/photo-gallery/share/<token>", "expires_at": "..." }`

### `DELETE /share-links/{link_id}`
Revoke a share link immediately.
- **Response**: `204`

---

## Share Link Public Access (No auth required)

### `GET /share/{token}`
Validate share token and return album + photos. No authentication required.
- **Response**: Same structure as `GET /albums/{album_id}` but without `my_role`, permission, or upload controls
- **Errors**: `404` if token not found; `410 Gone` if expired or revoked

---

## Storage Info (Admin only)

### `GET /storage/summary`
Returns storage usage by album.
- **Response**:
```json
{
  "total_bytes": 10737418240,
  "albums": [
    { "album_id": 1, "name": "Japan 2025", "photo_count": 142, "size_bytes": 2147483648 }
  ]
}
```

---

## Error Responses

All errors return JSON:
```json
{ "detail": "Human-readable error message" }
```

| Status | Meaning |
|---|---|
| 400 | Bad request (validation error) |
| 401 | Not authenticated (no/invalid session) |
| 403 | Authenticated but no permission |
| 404 | Resource not found |
| 410 | Gone (expired share link) |
| 413 | File too large (> 50 MB) |
| 415 | Unsupported media type |
| 500 | Internal server error |
