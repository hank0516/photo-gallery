# Data Model: Video Upload & Playback

**Feature**: 003-video-support | **Date**: 2026-08-04

---

## Schema Changes

### `photos` table — migration `b1c2d3e4f5a6`

Two changes to the existing table:

#### 1. New column: `mime_type`

```sql
ALTER TABLE photos
  ADD COLUMN mime_type VARCHAR(100) NULL AFTER filename;
```

| Attribute | Value |
|-----------|-------|
| Column    | `mime_type` |
| Type      | `VARCHAR(100)` |
| Nullable  | YES |
| Default   | `NULL` |

- Populated on every new upload (image or video).
- Existing rows remain `NULL` → treated by the frontend as image items (safe default).
- Values for images: `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `image/heic`, `image/heif`.
- Values for videos: `video/mp4`, `video/quicktime`, `video/webm`, `video/x-msvideo`.

#### 2. Modified columns: `thumb_300_key`, `thumb_800_key`

```sql
ALTER TABLE photos
  MODIFY COLUMN thumb_300_key VARCHAR(1024) NULL,
  MODIFY COLUMN thumb_800_key VARCHAR(1024) NULL;
```

| Attribute | Before | After |
|-----------|--------|-------|
| Nullable  | NO | YES |

- Allows storing `NULL` when video thumbnail extraction fails.
- Existing rows all have non-null values; no data loss.
- The frontend checks for `null` values and displays a placeholder.

---

## ORM Model Changes (`backend/app/models/models.py`)

### `Photo` class — additions and modifications

```python
# New field (add after `filename`):
mime_type = Column(String(100), nullable=True)

# Modified fields (remove `nullable=False`):
thumb_300_key = Column(String(1024), nullable=True)
thumb_800_key = Column(String(1024), nullable=True)
```

No other model changes. The `Photo` entity serves as the unified record for both images and videos.

---

## Config Changes (`backend/app/core/config.py`)

```python
max_upload_mb: int = 50    # existing — images only
max_video_mb: int = 500    # new — videos
```

---

## Discriminator Logic

The `mime_type` field drives all branching:

| `mime_type` value | Treatment |
|---|---|
| `NULL` or starts with `image/` | Image item: `<img>` in lightbox, no play icon |
| starts with `video/` | Video item: `<video>` in lightbox, play icon overlay in grid |

Helper function (frontend, shared across `PhotoGrid` and `Lightbox`):

```js
function isVideo(item) {
  return item.mime_type?.startsWith('video/')
}
```

---

## No New Tables

Videos use the existing `photos` table. No join tables, no separate `videos` table.
Permission model, album membership, soft-delete, and search all apply to video records unchanged.
