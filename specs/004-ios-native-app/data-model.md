# Data Model: iOS Native App

This describes the **client-side** data model — the structures the app holds in memory and passes between views. Backend DB schema is unchanged.

---

## Session

Represents the authenticated user's login state, persisted in Keychain.

| Field | Type | Notes |
|---|---|---|
| `token` | String | JWT, stored in Keychain key `pg_session` |
| `userId` | Int | Decoded from JWT payload |
| `email` | String | Decoded from JWT payload |
| `isAdmin` | Bool | Decoded from JWT payload |
| `expiresAt` | Date | Decoded from JWT `exp` claim |

**State transitions**:
- `unauthenticated` → `authenticated`: OAuth flow completes, token stored in Keychain
- `authenticated` → `unauthenticated`: logout, or 401 re-auth fails
- `authenticated` → `refreshing`: 401 received, re-auth in progress

---

## Album

| Field | Type | Notes |
|---|---|---|
| `id` | Int | |
| `name` | String | |
| `description` | String? | |
| `albumDate` | Date? | |
| `coverThumbURL` | URL? | Presigned, fetched fresh each load |
| `photoCount` | Int | |
| `myRole` | String | `"admin"`, `"uploader"`, or `"viewer"` |
| `isLocked` | Bool | |
| `createdAt` | Date | |
| `isUnlocked` | Bool | Client-only; true after password entry this session |

---

## MediaItem

Represents either a photo or a video within an album.

| Field | Type | Notes |
|---|---|---|
| `id` | Int | |
| `albumId` | Int | |
| `filename` | String | |
| `caption` | String? | |
| `mediaType` | Enum | `.photo` / `.video` |
| `thumbURL` | URL | 300px presigned thumbnail |
| `originalURL` | URL? | Presigned original; fetched on demand (detail view) |
| `width` | Int? | |
| `height` | Int? | |
| `fileSizeBytes` | Int? | |
| `uploadedAt` | Date | |
| `exif` | EXIF? | Loaded separately on detail view |

---

## EXIF

Embedded in MediaItem detail response.

| Field | Type | Notes |
|---|---|---|
| `takenAt` | Date? | `exif_taken_at` |
| `cameraModel` | String? | `exif_camera_model` |
| `latitude` | Double? | |
| `longitude` | Double? | |

---

## SearchResult

Returned by the search endpoint; structurally identical to MediaItem but may span multiple albums.

| Field | Type | Notes |
|---|---|---|
| `item` | MediaItem | |
| `albumName` | String | Album the item belongs to |

---

## Pagination

All list endpoints use cursor-style pagination via `page` + `per_page`.

| Field | Type |
|---|---|
| `page` | Int |
| `perPage` | Int |
| `total` | Int |
| `items` | [T] |
