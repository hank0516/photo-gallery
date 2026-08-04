# Tasks: Video Upload & Playback

**Input**: Design documents from `specs/003-video-support/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/api.md ✓, quickstart.md ✓

**Tests**: Not included (no automated test suite in this project).

**Organization**: Grouped by user story. Phase 2 (Foundational) includes all backend response changes
so every frontend user story phase can proceed cleanly in sequence.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other [P] tasks in same phase (different files)
- **[Story]**: User story this task belongs to (US1–US5 from spec.md)

---

## Phase 1: Setup (Pre-Flight)

**Purpose**: Confirm system dependencies before writing any code.

- [x] T001 Verify `ffmpeg` is installed on the server: run `which ffmpeg && ffmpeg -version`; if missing, run `sudo apt install ffmpeg`

**Checkpoint**: ffmpeg available → proceed to Phase 2.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: DB schema, ORM model, config, and API response propagation. ALL user story phases depend on this completing first.

**⚠️ CRITICAL**: No frontend story work can begin until this phase is complete (frontend needs `mime_type` in API responses).

- [x] T002 Write Alembic migration `b1c2d3e4f5a6_add_mime_type_and_nullable_thumbs.py` in `backend/alembic/versions/`: add `mime_type VARCHAR(100) NULL` column to `photos` table; change `thumb_300_key` and `thumb_800_key` from NOT NULL to NULL
- [x] T003 [P] Update `Photo` ORM model in `backend/app/models/models.py`: add `mime_type = Column(String(100), nullable=True)` after the `filename` field; change `thumb_300_key` and `thumb_800_key` to `nullable=True`
- [x] T004 [P] Add `max_video_mb: int = 500` to `Settings` class in `backend/app/core/config.py`
- [x] T005 Apply migration on the server: `cd backend && source venv_photo_galary/bin/activate && alembic upgrade head`; verify with `DESCRIBE photos` in MariaDB
- [x] T006 [P] Add `"mime_type": p.mime_type` to each photo dict in `GET /albums/{album_id}` response in `backend/app/api/albums.py` (the `photo_list` loop); also handle null thumb keys: generate presigned URL only when key is not None, else return `null`
- [x] T007 [P] Add `"mime_type": photo.mime_type` to the response dict in `GET /photos/{photo_id}` in `backend/app/api/photos.py`; also handle null thumb keys in presigned URL generation
- [x] T008 [P] Add `"mime_type": photo.mime_type` to each photo dict in `GET /search` results in `backend/app/api/search.py`; also handle null thumb keys
- [x] T009 Restart backend service: `sudo systemctl restart photo-gallery-api`; verify no startup errors with `sudo journalctl -u photo-gallery-api -n 30`

**Checkpoint**: `GET /albums/{id}` response items now include `"mime_type": null` for existing photos. Foundation ready.

---

## Phase 3: User Story 1 — Upload a Video to an Album (Priority: P1) 🎯 MVP

**Goal**: Uploaders can drag/select MP4, MOV, WebM, or AVI files into the existing upload zone. The backend extracts a first-frame thumbnail via ffmpeg, stores the video and thumbnails in Object Storage, and the new entry appears in the album grid.

**Independent Test** (Quickstart Scenario 1): Upload an MP4 to an album; confirm the video card appears in the grid with a thumbnail and no broken image.

### Backend — upload logic

- [x] T010 Expand `ALLOWED_TYPES` set in `backend/app/api/photos.py` to add: `"video/mp4"`, `"video/quicktime"`, `"video/webm"`, `"video/x-msvideo"`, `"video/avi"`
- [x] T011 Add `max_video_bytes` limit check in `upload_photo()` in `backend/app/api/photos.py`: after reading `raw`, if MIME type starts with `"video/"` and `len(raw) > settings.max_video_mb * 1024 * 1024`, raise HTTP 413
- [x] T012 Implement `_extract_video_thumbnail(raw_bytes: bytes, ext: str) -> bytes | None` function in `backend/app/api/photos.py`: write raw bytes to a temp file (`/tmp/<uuid>.<ext>`), call `subprocess.run(["ffmpeg", "-i", input_path, "-frames:v", "1", "-f", "image2", output_path])`, read the JPEG output; delete both temp files in a `finally` block; return `None` on any exception
- [x] T013 Add video branch in `upload_photo()` in `backend/app/api/photos.py`: if MIME type starts with `"video/"`, call `_extract_video_thumbnail()`, use `_make_thumbnail()` to resize result to 300 px and 800 px (or keep keys as `None` if extraction failed), skip Pillow image open / EXIF / width+height; set `mime_type` from `file.content_type`
- [x] T014 Update image branch in `upload_photo()` in `backend/app/api/photos.py`: set `mime_type=file.content_type` in the `Photo()` constructor call (previously `mime_type` was not set)
- [x] T015 Update upload response dict in `upload_photo()` in `backend/app/api/photos.py`: add `"mime_type": photo.mime_type`; generate presigned URL for thumb keys only when they are not `None`
- [x] T016 Restart backend: `sudo systemctl restart photo-gallery-api`

### Frontend — UploadZone

- [x] T017 [P] Update `accept` attribute on the hidden `<input>` in `frontend/src/components/UploadZone.vue` from `"image/*,.heic,.heif"` to `"image/*,.heic,.heif,video/mp4,video/quicktime,video/webm,video/x-msvideo,.mp4,.mov,.webm,.avi"`
- [x] T018 Update `addFiles()` filter in `frontend/src/components/UploadZone.vue`: extend the `if` condition to also pass through files where `f.type.startsWith('video/')` or filename matches `/\.(mp4|mov|webm|avi)$/i`
- [x] T019 Add video queue item preview in `frontend/src/components/UploadZone.vue`: in the queue item template, replace `<img :src="item.preview">` with a conditional — for video items (`item.file.type.startsWith('video/')`) show a generic video icon `<div class="q-thumb q-thumb-video">` with an SVG play icon; for image items keep the `<img>` as-is. Also skip `URL.createObjectURL()` for video items in `addFiles()` (set `preview: null`)
- [x] T020 Update hint text in `frontend/src/components/UploadZone.vue`: change the hint `<span>` from `"支援 JPG / PNG / WebP / HEIC，最大 {{ maxMb }} MB"` to `"圖片：JPG / PNG / WebP / HEIC（最大 {{ maxMb }} MB）｜影片：MP4 / MOV / WebM / AVI（最大 500 MB）"`
- [x] T021 [P] Add CSS for `.q-thumb-video` in `frontend/src/components/UploadZone.vue`: same 48×48 dimensions as `.q-thumb`, dark background, center the SVG icon
- [x] T022 Rebuild frontend: `cd frontend && npm run build`

**Checkpoint**: Upload an MP4 → video card appears in album grid (thumbnail or placeholder). US1 complete.

---

## Phase 4: User Story 2 — Play a Video in Lightbox (Priority: P2)

**Goal**: Clicking a video card in the album grid opens the lightbox with an HTML5 `<video>` player instead of a broken `<img>`. Play/pause/volume/fullscreen work. Video pauses automatically when navigating away or closing.

**Independent Test** (Quickstart Scenario 2): Click the uploaded video card; lightbox shows a working video player; arrow navigation pauses the video.

- [x] T023 Add `isVideo` computed helper in `frontend/src/components/Lightbox.vue`: `const isVideo = computed(() => current.value?.mime_type?.startsWith('video/'))`
- [x] T024 Add `videoEl` ref in `frontend/src/components/Lightbox.vue`: `const videoEl = ref(null)` — to call `.pause()` programmatically
- [x] T025 Update `watch(current, ...)` in `frontend/src/components/Lightbox.vue`: add a branch — if `isVideo.value`, skip the "upgrade to original" image preload; simply call `api.get('/photos/${photo.id}')` and set `displayUrl.value = data.original_url` (the presigned video URL); if not video, keep existing image preload logic unchanged
- [x] T026 Replace the `<div class="lb-img-wrap">` contents in `frontend/src/components/Lightbox.vue`: wrap with `<template v-if="isVideo">` rendering `<video ref="videoEl" :src="displayUrl" controls preload="metadata" class="lb-video" />` and `<template v-else>` keeping the existing `<img>` + spinner unchanged
- [x] T027 Add `.pause()` call in `go()` function in `frontend/src/components/Lightbox.vue` before changing `currentIndex`: `videoEl.value?.pause()`
- [x] T028 Add `.pause()` call when lightbox closes — in the `watch(() => props.visible, ...)` handler in `frontend/src/components/Lightbox.vue`: when `v` becomes false, call `videoEl.value?.pause()`
- [x] T029 Add CSS for `.lb-video` in `frontend/src/components/Lightbox.vue`: `max-width: 100%; max-height: 100%; object-fit: contain;` — mirrors `.lb-img` sizing
- [x] T030 Rebuild frontend: `cd frontend && npm run build`

**Checkpoint**: Click video card → video player renders and plays. Arrow key navigation pauses the video. Photos still show correctly as `<img>`. US2 complete.

---

## Phase 5: User Story 3 — Distinguish Videos from Photos in Grid (Priority: P3)

**Goal**: In all three view modes (small-grid, large-grid, list), video cards show a play-button icon overlay. Cards with no thumbnail show a generic placeholder instead of a broken image.

**Independent Test** (Quickstart Scenario 2 + visual check in all 3 modes): An album with both photos and videos — video cards have a play icon, photo cards do not; switching view modes preserves the overlay.

- [x] T031 Add `isVideo(item)` helper function in `frontend/src/components/PhotoGrid.vue`: `function isVideo(item) { return item.mime_type?.startsWith('video/') }`
- [x] T032 Update grid-item template in `frontend/src/components/PhotoGrid.vue`: add `<div v-if="isVideo(photo)" class="play-overlay">▶</div>` inside `.grid-item`; replace `<img :src="photo.thumb_300_url">` with `<img v-if="photo.thumb_300_url" ... />` plus `<div v-else class="thumb-placeholder">🎬</div>`
- [x] T033 Update list-item template in `frontend/src/components/PhotoGrid.vue`: add `<div v-if="isVideo(photo)" class="play-badge">▶</div>` next to `.list-thumb`; also handle null `thumb_300_url` with a placeholder `<div>` in list mode
- [x] T034 Add CSS in `frontend/src/components/PhotoGrid.vue` for `.play-overlay` (centered, semi-transparent circle with ▶ icon, pointer-events: none, 36px font size), `.thumb-placeholder` (same dimensions as the img, dark bg, centered icon), and `.play-badge` (small inline badge for list view)
- [x] T035 Rebuild frontend: `cd frontend && npm run build`

**Checkpoint**: Album grid shows play icons on video cards. Missing-thumbnail fallback renders without errors. US3 complete.

---

## Phase 6: User Story 4 — Download and Delete Videos (Priority: P4)

**Goal**: Download and delete from the lightbox work identically for videos as for photos — no new API endpoints needed.

**Independent Test** (Quickstart Scenarios 1+2 side effects): Download a video from the lightbox and confirm the file downloads. Delete a video as admin and confirm it disappears from the grid.

- [x] T036 Verify download in `frontend/src/components/Lightbox.vue`: the existing `<a :href="\`/api/photo-gallery/photos/${current?.id}/download\`">` anchor already triggers a presigned download redirect for any storage key — confirm no changes needed by manually downloading an uploaded video
- [x] T037 Verify delete in `frontend/src/components/Lightbox.vue`: the `deletePhoto()` function calls `DELETE /photos/{id}` which performs a soft-delete regardless of file type — confirm no changes needed by deleting a test video and verifying it disappears from the grid

*Note: If both verifications pass without code changes, T036–T037 are completed as read-only confirmations. No rebuild required.*

**Checkpoint**: Download and delete work for videos via existing code paths. US4 complete.

---

## Phase 7: User Story 5 — Search Returns Video Results (Priority: P5)

**Goal**: Search results include videos. Video cards in search results show the play-icon overlay (already handled by Phase 5). No backend search query changes needed — `search.py` already queries all `Photo` records.

**Independent Test** (Quickstart Scenario 6): Upload a video with a caption, search for a word from that caption, confirm the video appears in results with a play icon.

- [x] T038 Verify `frontend/src/pages/SearchPage.vue` passes API response photo items directly to `<PhotoGrid>` without filtering or remapping — confirm `mime_type` flows through automatically to `PhotoGrid.vue` (read the file, no code change expected)
- [x] T039 Confirm `search.py` `GET /search` response already includes `"mime_type"` from Phase 2 T008 — no additional backend changes needed
- [x] T040 Manually test: add a caption to an uploaded video, search for it, verify the play icon appears on the result card and the lightbox plays the video

*Note: If T038 confirms SearchPage passes items as-is, this phase is complete without rebuilding.*

**Checkpoint**: Video items appear in search with play overlay. US5 complete.

---

## Phase 8: Polish & Validation

**Purpose**: Run the full quickstart validation guide and update project records.

- [x] T041 [P] Run all 7 scenarios from `specs/003-video-support/quickstart.md` on the live site; document any failures
- [x] T042 [P] Update `PROGRESS.md` in `photo-gallery/`: add Phase 17 (Video Support / Phase 3 US1–US5) as complete with today's date
- [x] T043 Update `specs/001-photo-gallery/spec.md` note in Assumptions: change "Video files are out of scope for v1" to reference 003-video-support spec

**Checkpoint**: All quickstart scenarios pass. PROGRESS.md updated.

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
  └─→ Phase 2 (Foundational) — BLOCKS all user stories
        ├─→ Phase 3 (US1: Upload)      ← MVP
        │     └─→ Phase 4 (US2: Lightbox)
        │           └─→ Phase 6 (US4: Download/Delete)
        ├─→ Phase 5 (US3: Grid Display) — can start after Phase 2
        └─→ Phase 7 (US5: Search)      — can start after Phase 2 + Phase 5
              └─→ Phase 8 (Polish)
```

### User Story Dependencies

| Story | Depends On | Reason |
|---|---|---|
| US1 (Upload) | Phase 2 | Needs mime_type column + config |
| US2 (Lightbox) | Phase 2, US1 | Needs a video to exist in the system |
| US3 (Grid) | Phase 2 | Needs mime_type in album response |
| US4 (Download/Delete) | US2 | Needs the lightbox to render videos |
| US5 (Search) | Phase 2, US3 | Needs mime_type in search response + play overlay in grid |

### Parallel Opportunities

Within Phase 2: T003, T004, T006, T007, T008 can all run in parallel (different files).
Within Phase 3 frontend: T017, T018, T019, T020, T021 can run after T016 (backend restart confirms API shape).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: T001 — confirm ffmpeg
2. Phase 2: T002–T009 — schema + API foundation
3. Phase 3: T010–T022 — video upload backend + upload zone UI
4. **STOP**: Upload a video → confirm it appears in grid (may show broken image until US3)
5. Demonstrate upload working; proceed to playback

### Recommended Sequence (single developer)

1. Phase 1 → Phase 2 → Phase 3 (US1) — Upload works end-to-end
2. Phase 4 (US2) — Lightbox plays videos
3. Phase 5 (US3) — Grid shows play icons
4. Phase 6 (US4) — Verify download/delete (fast)
5. Phase 7 (US5) — Verify search (fast)
6. Phase 8 — Full validation + docs update

---

## Notes

- After any backend Python change: `sudo systemctl restart photo-gallery-api`
- After any frontend Vue/JS change: `cd frontend && npm run build` (no service restart needed)
- ffmpeg temp files use `/tmp/<uuid>` — always cleaned up in `finally` block
- `mime_type=None` in existing photo rows is safe: `None?.startsWith('video/')` → falsy → treated as image
- AVI browser compatibility note: Safari/Firefox may not play `.avi` natively; download still works
