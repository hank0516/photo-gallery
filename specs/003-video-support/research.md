# Research: Video Upload & Playback

**Date**: 2026-08-04 | **Plan**: [plan.md](plan.md)

---

## Decision 1 — Video Thumbnail Extraction Tool

**Decision**: Use `ffmpeg` via Python `subprocess` (or `ffmpeg-python` wrapper) to extract the first frame.

**Rationale**:
- `ffmpeg` is the industry standard and handles all target formats (MP4, MOV, WebM, AVI) including edge cases.
- Already likely available on the Debian server; install with `apt install ffmpeg`.
- Extraction command: `ffmpeg -i input -frames:v 1 -f image2 output.jpg`
- Output is a JPEG, which Pillow can then resize to 300 px / 800 px thumbnails — reusing the existing `_make_thumbnail()` helper.
- `ffmpeg-python` package provides a cleaner API but adds a dependency for minimal gain. Direct `subprocess` is sufficient.

**Alternatives considered**:
- `moviepy`: Heavy dependency chain (requires ffmpeg anyway), slower. Rejected.
- `opencv-python`: Works but adds ~50 MB of C++ binaries for a single use case. Rejected.
- `Pillow` alone: Cannot decode video. Rejected.

**Failure handling**: If ffmpeg is not installed or extraction fails (corrupt file, unsupported codec),
the upload proceeds but `thumb_300_key` and `thumb_800_key` are stored as `None`. The frontend
displays a generic video placeholder icon when these are `None`.

---

## Decision 2 — Database Schema Change: `mime_type` Column

**Decision**: Add `mime_type VARCHAR(100) NULL` to the `photos` table via a new Alembic migration.

**Rationale**:
- The `Photo` model currently has NO `mime_type` field (verified by reading `models/models.py`).
  The spec assumption that it exists was incorrect.
- `mime_type` is the only reliable signal to distinguish video items from image items without
  inspecting filenames or adding a separate `media_type` enum.
- Existing rows get `NULL`, which the frontend treats as "image" (safe default; all existing items
  are images).

**Also in the same migration**: Make `thumb_300_key` and `thumb_800_key` nullable (`NULL` allowed).
- Current schema: `NOT NULL` — breaks if a video's thumbnail extraction fails.
- Existing rows are unaffected (they all have valid keys).
- The `Photo()` constructor call in upload code sets these fields only when thumbnails are generated.

**Migration filename prefix**: next after `a3f2c1d4e5b6` → use `b1c2d3e4f5a6` (arbitrary hex prefix, Alembic does not require sequential ordering).

---

## Decision 3 — Video File Size Limit

**Decision**: Add `max_video_mb: int = 500` to `Settings` in `config.py`. Apply separately from
the existing `max_upload_mb` (50 MB, for images) within the upload endpoint.

**Rationale**:
- A single setting (`max_upload_mb`) cannot serve both use cases cleanly.
- 500 MB covers common family video clips; very large files (>500 MB) are unusual for the target use case.
- The limit check happens after `await file.read()` — for very large files this could be memory-intensive.
  Acceptable for a private system with < 50 users. (Streaming validation would require a more complex
  multipart parser and is out of scope.)

---

## Decision 4 — Supported Video MIME Types

**Decision**: Accept the following MIME types for video upload:

| Extension | MIME type |
|-----------|-----------|
| `.mp4`    | `video/mp4` |
| `.mov`    | `video/quicktime` |
| `.webm`   | `video/webm` |
| `.avi`    | `video/x-msvideo` |

**Rationale**:
- These are the four formats specified in the feature requirements.
- Some browsers send `video/avi` instead of `video/x-msvideo`; both should be accepted.
- MIME type detection uses `file.content_type` (set by the browser/OS). As a defence-in-depth
  measure, the filename extension is also checked for `.mov` since Safari may send
  `video/quicktime` inconsistently.

---

## Decision 5 — Frontend Video Preview in Upload Queue

**Decision**: For video items in the `UploadZone` queue, display a generic video icon (SVG)
instead of an `<img>` with `URL.createObjectURL()`.

**Rationale**:
- `URL.createObjectURL()` on a video file returns a blob URL that works in a `<video>` tag but
  not as an `<img>` `src` (the current code uses `<img>`).
- Adding a `<video>` element to each queue row adds complexity and layout issues in the queue list.
- A simple file icon with the filename is sufficient UX for the upload queue.

---

## Decision 6 — Lightbox: Video Playback Strategy

**Decision**: For video items, the lightbox fetches `GET /photos/{id}` to obtain the presigned
`original_url`, then sets it as the `<video>` `src`. No pre-loading or "upgrade" pattern needed.

**Rationale**:
- The existing `watch(current, ...)` in `Lightbox.vue` already fetches `/photos/{id}` for images
  to get the original URL. The same fetch works for videos.
- The `mime_type` field returned by the API tells the component whether to render `<img>` or `<video>`.
- Videos should NOT preload their full content (`preload="metadata"` is sufficient).
- A `ref` to the `<video>` element is needed to call `.pause()` on navigation.

---

## Decision 7 — API Response: `mime_type` Field Propagation

**Decision**: Add `mime_type` to every API endpoint that returns photo items:
- `POST /albums/{id}/photos` (upload response)
- `GET /albums/{id}` (photo list items)
- `GET /photos/{id}` (photo detail)
- `GET /search` (search results)

**Rationale**: The frontend needs `mime_type` to conditionally render play overlays and the video
player. Omitting it from any response would require a second API call to determine the media type.

---

## Decision 8 — `photo_count` vs `media_count` in Album Response

**Decision**: Keep the existing `photo_count` field name in album responses. The count already
includes all non-deleted `Photo` records regardless of type.

**Rationale**: Renaming would break existing frontend code with no user-facing benefit. The count
label in the UI ("N 張") can be updated to "N 項" in a follow-up if desired.

---

## ffmpeg Installation Check

Verify ffmpeg is available on the server:
```bash
which ffmpeg && ffmpeg -version
```
If missing:
```bash
sudo apt install ffmpeg
```
Add `ffmpeg` to the backend's `requirements.txt` comment or deployment notes (it is a system
package, not a pip package).
