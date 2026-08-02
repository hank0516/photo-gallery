# Data Model: Private Photo Gallery

**Date**: 2026-08-02 | **Database**: MariaDB, database name `PhotoGallery`

---

## Entity: `users`

Stores every Google account that has ever authenticated.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INT | PK, AUTO_INCREMENT | |
| `google_id` | VARCHAR(128) | UNIQUE, NOT NULL | Google sub claim |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | |
| `name` | VARCHAR(255) | NOT NULL | Display name from Google |
| `avatar_url` | VARCHAR(512) | NULL | Google profile picture URL |
| `is_admin` | BOOLEAN | NOT NULL, DEFAULT FALSE | Global admin flag |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW() | First login |
| `last_login_at` | DATETIME | NOT NULL, DEFAULT NOW() | Updated on each login |

**Notes**:
- First user to log in after bootstrap is set as admin via server-side config (`BOOTSTRAP_ADMIN_EMAIL` env var)
- `is_admin = TRUE` grants full access to all albums and the admin panel

---

## Entity: `albums`

A named collection of photos.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INT | PK, AUTO_INCREMENT | |
| `name` | VARCHAR(255) | NOT NULL | |
| `description` | TEXT | NULL | |
| `cover_photo_id` | INT | FK → photos.id, NULL | Set by admin; NULL uses first photo |
| `created_by` | INT | FK → users.id, NOT NULL | |
| `album_date` | DATE | NULL | Event/trip date; used for homepage sort |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW() | |
| `updated_at` | DATETIME | NOT NULL, DEFAULT NOW() ON UPDATE NOW() | |
| `is_deleted` | BOOLEAN | NOT NULL, DEFAULT FALSE | Soft delete |

**Notes**:
- Soft delete: `is_deleted = TRUE` hides album from all queries; photos remain in storage until hard-delete job runs
- `cover_photo_id` allows circular FK; resolve with deferred constraint or application-level logic

---

## Entity: `photos`

A single image file with its metadata.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INT | PK, AUTO_INCREMENT | |
| `album_id` | INT | FK → albums.id, NOT NULL | |
| `uploaded_by` | INT | FK → users.id, NOT NULL | |
| `filename` | VARCHAR(512) | NOT NULL | Original filename |
| `caption` | TEXT | NULL | User-editable |
| `storage_key` | VARCHAR(1024) | NOT NULL | Object Storage key for original |
| `thumb_300_key` | VARCHAR(1024) | NOT NULL | Object Storage key for 300px thumb |
| `thumb_800_key` | VARCHAR(1024) | NOT NULL | Object Storage key for 800px thumb |
| `file_size_bytes` | BIGINT | NOT NULL | Original file size |
| `width` | INT | NULL | Original image width in px |
| `height` | INT | NULL | Original image height in px |
| `exif_date_taken` | DATETIME | NULL | From EXIF DateTimeOriginal |
| `exif_camera` | VARCHAR(255) | NULL | e.g. "Apple iPhone 15 Pro" |
| `exif_gps_lat` | DECIMAL(10,7) | NULL | Latitude |
| `exif_gps_lon` | DECIMAL(10,7) | NULL | Longitude |
| `uploaded_at` | DATETIME | NOT NULL, DEFAULT NOW() | |
| `is_deleted` | BOOLEAN | NOT NULL, DEFAULT FALSE | Soft delete |

**Notes**:
- Object Storage keys follow pattern: `photos/<album_id>/<photo_id>/original.<ext>`
- Thumbnails use same prefix with `thumb_300` / `thumb_800` suffix
- `exif_*` fields populated at upload time from Pillow's EXIF extraction; NULL if not present

---

## Entity: `permissions`

Per-user, per-album access control.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INT | PK, AUTO_INCREMENT | |
| `user_id` | INT | FK → users.id, NOT NULL | |
| `album_id` | INT | FK → albums.id, NOT NULL | |
| `role` | ENUM('viewer','uploader','admin') | NOT NULL | |
| `granted_by` | INT | FK → users.id, NOT NULL | Admin who granted this |
| `granted_at` | DATETIME | NOT NULL, DEFAULT NOW() | |

**Unique constraint**: `(user_id, album_id)` — one role per user per album.

**Role capabilities**:
| Action | viewer | uploader | admin |
|---|---|---|---|
| View album & photos | ✓ | ✓ | ✓ |
| Upload photos | ✗ | ✓ | ✓ |
| Add/edit captions | ✗ | ✓ | ✓ |
| Download album zip | ✗ | ✓ | ✓ |
| Delete photos | ✗ | ✗ | ✓ |
| Edit/delete album | ✗ | ✗ | ✓ |
| Manage permissions | ✗ | ✗ | ✓ |
| Generate share links | ✗ | ✗ | ✓ |

**Notes**:
- Global admin (`users.is_admin = TRUE`) bypasses this table entirely and has full access
- Changing a role updates the existing row (no history kept in v1)

---

## Entity: `share_links`

Time-limited tokens granting anonymous read access to one album.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INT | PK, AUTO_INCREMENT | |
| `token` | CHAR(36) | UNIQUE, NOT NULL | UUID v4 |
| `album_id` | INT | FK → albums.id, NOT NULL | |
| `created_by` | INT | FK → users.id, NOT NULL | Admin who generated it |
| `expires_at` | DATETIME | NOT NULL | |
| `is_revoked` | BOOLEAN | NOT NULL, DEFAULT FALSE | |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW() | |

**Notes**:
- Access allowed only if: `is_revoked = FALSE` AND `expires_at > NOW()` AND album not soft-deleted
- One album can have multiple active share links (e.g., different expiry for different recipients)

---

## Relationships Diagram

```
users ──┬── (created_by) ──→ albums ──── (album_id) ──→ photos
        │                       │                          │
        ├── (user_id) ─────→ permissions ←── (album_id) ──┘
        │                       │
        └── (created_by) ──→ share_links ←── (album_id)
```

---

## Indexes

| Table | Index | Columns | Reason |
|---|---|---|---|
| `users` | `idx_users_google_id` | `google_id` | OAuth login lookup |
| `users` | `idx_users_email` | `email` | Admin lookup by email |
| `photos` | `idx_photos_album_id` | `album_id` | Album photo listing |
| `photos` | `idx_photos_exif_date` | `album_id, exif_date_taken` | Date filter |
| `permissions` | `idx_perm_user_album` | `user_id, album_id` | Permission check (UNIQUE) |
| `permissions` | `idx_perm_album` | `album_id` | Listing album members |
| `share_links` | `idx_share_token` | `token` | Token lookup (UNIQUE) |
| `share_links` | `idx_share_album` | `album_id` | List album's share links |
