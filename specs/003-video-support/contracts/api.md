# API Contract Changes: Video Upload & Playback

**Feature**: 003-video-support | **Date**: 2026-08-04

All endpoints are under the prefix `/api/photo-gallery/`. Authentication via `pg_session` cookie is required on all endpoints (unchanged).

---

## Changed Endpoints

### `POST /albums/{album_id}/photos` — Upload media file

**Change**: Now accepts video files in addition to images.

**Request** (unchanged multipart/form-data):
```
file: binary      — image OR video file
caption: string   — optional caption (default "")
```

**Accepted MIME types** (expanded):
```
# Images (unchanged)
image/jpeg, image/jpg, image/png, image/gif, image/webp, image/heic, image/heif

# Videos (new)
video/mp4, video/quicktime, video/webm, video/x-msvideo, video/avi
```

**File size limits**:
- Images: 50 MB (unchanged, from `max_upload_mb`)
- Videos: 500 MB (new, from `max_video_mb`)

**Success response** `201 Created` — **new field `mime_type`**:
```json
{
  "id": 42,
  "thumb_300_url": "https://...",
  "thumb_800_url": "https://...",
  "thumb_300_url": null,
  "thumb_800_url": null,
  "mime_type": "video/mp4",
  "filename": "holiday.mp4",
  "caption": null,
  "width": null,
  "height": null,
  "exif_date_taken": null,
  "uploaded_at": "2026-08-04T10:00:00"
}
```

Note: `thumb_300_url` and `thumb_800_url` are `null` when thumbnail extraction fails.

**Error responses** (unchanged codes, updated conditions):
- `400` — unsupported file type or corrupt file
- `403` — caller has no uploader/admin role
- `404` — album not found
- `413` — file exceeds size limit (images > 50 MB, videos > 500 MB)

---

### `GET /albums/{album_id}` — Album detail with photo list

**Change**: Each item in `photos[]` now includes `mime_type`.

**Response** — `photos[]` item shape **adds `mime_type`**:
```json
{
  "id": 42,
  "thumb_300_url": "https://... or null",
  "thumb_800_url": "https://... or null",
  "mime_type": "video/mp4",
  "caption": null,
  "exif_date_taken": null,
  "width": null,
  "height": null,
  "filename": "holiday.mp4"
}
```

All other response fields unchanged.

---

### `GET /photos/{photo_id}` — Photo/video detail

**Change**: Response now includes `mime_type`.

**Response** — **adds `mime_type`**:
```json
{
  "id": 42,
  "album_id": 7,
  "filename": "holiday.mp4",
  "caption": null,
  "original_url": "https://...",
  "thumb_300_url": "https://... or null",
  "thumb_800_url": "https://... or null",
  "mime_type": "video/mp4",
  "file_size_bytes": 104857600,
  "width": null,
  "height": null,
  "exif_date_taken": null,
  "exif_camera": null,
  "exif_gps_lat": null,
  "exif_gps_lon": null,
  "uploaded_at": "2026-08-04T10:00:00",
  "uploaded_by": {"id": 1, "name": "Hank"},
  "my_role": "admin"
}
```

---

### `GET /search` — Search

**Change**: Each item in `photos[]` now includes `mime_type`.

**Response** — `photos[]` item shape **adds `mime_type`**:
```json
{
  "id": 42,
  "filename": "holiday.mp4",
  "caption": null,
  "thumb_300_url": "https://... or null",
  "thumb_800_url": "https://... or null",
  "mime_type": "video/mp4",
  "exif_date_taken": null,
  "width": null,
  "height": null,
  "album_id": 7,
  "album_name": "2026 澳洲"
}
```

---

## Unchanged Endpoints

| Endpoint | Reason |
|---|---|
| `PATCH /photos/{id}` | Caption edit works identically for videos |
| `DELETE /photos/{id}` | Soft-delete works identically for videos |
| `GET /photos/{id}/download` | Presigned download URL works for any storage key |
| All album/permission/auth endpoints | No changes |

---

## Frontend API Assumptions

- `mime_type === null` → treat as image (all existing records before migration)
- `mime_type?.startsWith('video/')` → video item
- `thumb_300_url === null` → show placeholder (no thumbnail)
- The `original_url` from `GET /photos/{id}` is used as the `<video src>` in the lightbox
