# Tasks: Private Photo Gallery

**Input**: Design documents from `specs/001-photo-gallery/`

**References**: [spec.md](spec.md) | [plan.md](plan.md) | [data-model.md](data-model.md) | [contracts/api.md](contracts/api.md) | [research.md](research.md)

**Format**: `- [ ] [TaskID] [P?] [Story?] Description — file path`
- **[P]**: Can run in parallel (touches different files, no incomplete dependencies)
- **[USn]**: Maps to User Story n from spec.md

---

## Phase 1: Setup

**Purpose**: Create project skeleton and configure tooling

- [ ] T001 Create `backend/` and `frontend/` directory structure per plan.md Project Structure
- [ ] T002 Create `backend/requirements.txt` with: fastapi, uvicorn, sqlalchemy, pymysql, alembic, authlib, httpx, boto3, pillow, pillow-heif, python-jose[cryptography], python-multipart, python-dotenv
- [ ] T003 Create `backend/venv`, install requirements: `python3 -m venv backend/venv && backend/venv/bin/pip install -r backend/requirements.txt`
- [ ] T004 [P] Create `frontend/package.json` and initialise Vue 3 + Vite project: `npm create vite@latest frontend -- --template vue`, then add dependencies: vue-router, pinia, axios
- [ ] T005 [P] Create `.gitignore` — exclude: `backend/venv/`, `frontend/node_modules/`, `frontend/dist/`, `**/.env`, `**/__pycache__/`, `*.pyc`
- [ ] T006 Create `backend/.env.example` with all required keys from quickstart.md (no real values); copy to `backend/.env` and fill in real credentials

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure required before any user story can be built

**⚠️ CRITICAL**: Complete this entire phase before starting any Phase 3+ work

- [ ] T007 Create `backend/app/core/config.py` — load all env vars using `pydantic-settings` or `python-dotenv`; expose typed settings object
- [ ] T008 Create `backend/app/models/models.py` — define all SQLAlchemy ORM models: `User`, `Album`, `Photo`, `Permission`, `ShareLink` per data-model.md (all tables, columns, indexes, constraints)
- [ ] T009 Initialise Alembic: `cd backend && alembic init alembic`; configure `alembic/env.py` to use `DATABASE_URL` from config and import all models
- [ ] T010 Create first Alembic migration: `alembic revision --autogenerate -m "initial schema"`; verify generated migration matches data-model.md; run `alembic upgrade head`
- [ ] T011 Create MariaDB database: `CREATE DATABASE PhotoGallery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;` and grant access to `hank` user
- [ ] T012 Create `backend/app/core/storage.py` — boto3 S3 client configured with Linode endpoint; expose functions: `upload_file(key, file_obj)`, `generate_presigned_url(key, expiry_seconds)`, `delete_file(key)`
- [ ] T013 Create `backend/app/core/auth.py` — JWT functions: `create_access_token(payload)`, `decode_access_token(token)`, `get_current_user(request)` FastAPI dependency; read/write `pg_session` httpOnly cookie
- [ ] T014 Create `backend/main.py` — FastAPI app with CORS middleware (allow `https://cloud.hansu.tw`), include all routers under prefix `/api/photo-gallery`, configure cookie settings
- [ ] T015 Create `backend/app/api/` directory with empty `__init__.py` files for: `auth.py`, `albums.py`, `photos.py`, `users.py`, `share.py`, `search.py`, `storage_info.py`
- [ ] T016 [P] Create `frontend/src/services/api.js` — Axios instance with `baseURL=/api/photo-gallery`, `withCredentials: true` (to send cookies), global 401 interceptor that redirects to `/login`
- [ ] T017 [P] Create `frontend/src/router/index.js` — Vue Router with routes: `/` (AlbumsPage), `/albums/:id` (AlbumPage), `/login` (LoginPage), `/admin` (AdminPage), `/share/:token` (SharedPage); add navigation guard that checks auth store before entering any non-login, non-share route

---

## Phase 3: User Story 1 — Authenticate & Access (Priority: P1) 🎯 MVP

**Goal**: Users can log in with Google, see their permitted albums, and be blocked if they have no access.

**Independent Test**: Visit the site → Google OAuth completes → permitted user sees albums → unpermitted user sees "pending" screen. Run `quickstart.md` Scenario 1.

### Implementation

- [ ] T018 [US1] Implement `GET /auth/login` in `backend/app/api/auth.py` — use `authlib` to generate Google OAuth authorization URL with `openid email profile` scopes; return redirect response
- [ ] T019 [US1] Implement `GET /auth/callback` in `backend/app/api/auth.py` — exchange code for token, fetch Google user info, upsert `User` record, set `is_admin=True` if email matches `BOOTSTRAP_ADMIN_EMAIL`, issue JWT in `pg_session` httpOnly cookie, redirect to `/sites/photo-gallery/`
- [ ] T020 [US1] Implement `POST /auth/logout` in `backend/app/api/auth.py` — clear `pg_session` cookie
- [ ] T021 [US1] Implement `GET /auth/me` in `backend/app/api/auth.py` — return current user from JWT; return 401 if no valid session
- [ ] T022 [P] [US1] Create `frontend/src/stores/auth.js` — Pinia store: `user` state, `fetchMe()` action (calls `GET /auth/me`), `isLoggedIn` getter, `isAdmin` getter
- [ ] T023 [P] [US1] Create `frontend/src/pages/LoginPage.vue` — show app logo, "Sign in with Google" button that calls `GET /auth/login` (navigates browser to backend URL); show "Pending access" state if user is logged in but has no albums (detected after albums list returns empty and user is not admin)
- [ ] T024 [US1] Wire `frontend/src/App.vue` to call `auth.fetchMe()` on mount; update router guard in `frontend/src/router/index.js` to redirect unauthenticated users to `/login`

**Checkpoint**: `quickstart.md` Scenario 1 passes ✓

---

## Phase 4: User Story 2 — Browse Albums & Photos (Priority: P2)

**Goal**: Logged-in users see their permitted albums, open albums, switch view modes, and use lightbox.

**Independent Test**: Seed albums + permissions, log in as viewer, verify grid + lightbox work in all 3 view modes. Run `quickstart.md` Scenario 3.

### Implementation

- [ ] T025 [US2] Implement `GET /albums` in `backend/app/api/albums.py` — query albums where caller has a `Permission` row OR `is_admin=True`; return list with `cover_thumb_url` (pre-signed), `photo_count`, `my_role`
- [ ] T026 [US2] Implement `GET /albums/{album_id}` in `backend/app/api/albums.py` — verify caller has permission; return album details + paginated photos with `thumb_300_url` and `thumb_800_url` (pre-signed URLs, 15min expiry); 403 if no permission
- [ ] T027 [US2] Implement `GET /photos/{photo_id}` in `backend/app/api/photos.py` — return full photo details including `original_url` (pre-signed), EXIF fields; 403 if caller has no access to the album
- [ ] T028 [P] [US2] Create `frontend/src/stores/albums.js` — Pinia store: `albums` list, `currentAlbum`, `photos` for current album, `fetchAlbums()`, `fetchAlbum(id, page)` actions
- [ ] T029 [P] [US2] Create `frontend/src/pages/AlbumsPage.vue` — fetch and display album grid using `AlbumCard.vue`; show "No albums yet" empty state
- [ ] T030 [P] [US2] Create `frontend/src/components/AlbumCard.vue` — shows cover thumbnail (300px), album name, photo count; links to `/albums/:id`
- [ ] T031 [US2] Create `frontend/src/pages/AlbumPage.vue` — fetches album + photos; renders `PhotoGrid.vue`; includes `ViewModeToggle.vue` and `UploadZone.vue` (conditionally shown if role allows)
- [ ] T032 [US2] Create `frontend/src/components/ViewModeToggle.vue` — 3-button toggle (small grid / large grid / list); saves selected mode to `localStorage` key `pg_view_mode`; emits `change` event
- [ ] T033 [US2] Create `frontend/src/components/PhotoGrid.vue` — renders photos in current view mode (CSS grid for small/large, flex list for list view); implements `IntersectionObserver` for lazy-loading thumbnails; emits `photo-click` to open lightbox
- [ ] T034 [US2] Create `frontend/src/components/Lightbox.vue` — full-screen overlay; shows `thumb_800_url` first, then swaps to `original_url` when loaded; left/right navigation (buttons + arrow keys); keyboard Escape to close; expandable details panel (caption + EXIF); Download button

**Checkpoint**: `quickstart.md` Scenario 3 passes ✓

---

## Phase 5: User Story 3 — Upload Photos (Priority: P3)

**Goal**: Uploader/admin can drag-drop or select photos; thumbnails auto-generated; photos appear immediately.

**Independent Test**: Open album as uploader, drag 3 JPEGs onto upload zone, verify progress bars, photos appear, thumbnails exist in Object Storage. Run `quickstart.md` Scenario 2.

### Implementation

- [ ] T035 [US3] Create `backend/app/services/thumbnail.py` — `generate_thumbnails(file_bytes, ext)` function using Pillow: convert HEIC→JPEG (via pillow-heif), generate 300px and 800px versions (preserve aspect ratio), return dict of `{original, thumb_300, thumb_800}` as BytesIO objects
- [ ] T036 [US3] Create `backend/app/services/photo_service.py` — `process_and_store_photo(album_id, uploader_id, filename, file_bytes)`: extract EXIF, generate thumbnails, upload all 3 to Object Storage using keys from research.md, insert `Photo` record to DB, return Photo
- [ ] T037 [US3] Implement `POST /albums/{album_id}/photos` in `backend/app/api/photos.py` — accept `multipart/form-data` with multiple files; reject non-image types (return in `failed` list); call `photo_service.process_and_store_photo()` for each valid file; return `{uploaded, failed}`
- [ ] T038 [P] [US3] Create `frontend/src/stores/photos.js` — Pinia store: `uploadQueue`, `uploadProgress` map, `uploadPhotos(albumId, files)` action that POSTs each file with `onUploadProgress` callback
- [ ] T039 [P] [US3] Create `frontend/src/components/UploadZone.vue` — drag-and-drop area + "Select files" button; shows per-file progress bars during upload; emits `upload-complete` with new photo list when all done; only rendered if `my_role` is `uploader` or `admin`

**Checkpoint**: `quickstart.md` Scenario 2 passes ✓

---

## Phase 6: User Story 4 — Manage Albums (Priority: P4)

**Goal**: Admin can create, rename, change cover, and delete albums.

**Independent Test**: Create album, rename it, set cover photo, delete it — verify state persists and deletion removes photos. Run `quickstart.md` Scenario 2 (album creation part).

### Implementation

- [ ] T040 [US4] Implement `POST /albums` in `backend/app/api/albums.py` — admin only (`is_admin=True`); create `Album` record; return 403 for non-admins
- [ ] T041 [US4] Implement `PATCH /albums/{album_id}` in `backend/app/api/albums.py` — require admin role on album; update `name`, `description`, `cover_photo_id` (any combination)
- [ ] T042 [US4] Implement `DELETE /albums/{album_id}` in `backend/app/api/albums.py` — require admin role; soft-delete album (`is_deleted=True`) and all its photos; queue Object Storage deletion (or delete immediately)
- [ ] T043 [US4] Add "New Album" button to `frontend/src/pages/AlbumsPage.vue` — only visible to global admins; opens inline modal or form with name + description fields; calls `POST /albums`; refreshes album list on success
- [ ] T044 [US4] Add edit/delete controls to `frontend/src/pages/AlbumPage.vue` — visible only if `my_role === 'admin'`; edit opens modal to change name, description, cover photo; delete shows confirmation dialog before calling `DELETE /albums/{id}`

**Checkpoint**: Full album lifecycle works for admin users ✓

---

## Phase 7: User Story 5 — Manage Users & Permissions (Priority: P5)

**Goal**: Admin can see all users and assign/revoke per-album roles.

**Independent Test**: Grant viewer role to test user, verify they see the album; revoke, verify album disappears. Run `quickstart.md` Scenario 4.

### Implementation

- [ ] T045 [US5] Implement `GET /users` in `backend/app/api/users.py` — global admin only; return all users sorted by last_login_at desc
- [ ] T046 [US5] Implement `PATCH /users/{user_id}` in `backend/app/api/users.py` — global admin only; update `is_admin` flag
- [ ] T047 [US5] Implement `GET /albums/{album_id}/permissions` in `backend/app/api/albums.py` — admin role on album required; return user list with roles
- [ ] T048 [US5] Implement `PUT /albums/{album_id}/permissions/{user_id}` in `backend/app/api/albums.py` — upsert `Permission` record; admin role on album required
- [ ] T049 [US5] Implement `DELETE /albums/{album_id}/permissions/{user_id}` in `backend/app/api/albums.py` — delete `Permission` record; admin role required
- [ ] T050 [US5] Create `frontend/src/pages/AdminPage.vue` — two tabs: "Users" and "Album Permissions"; Users tab lists all users with admin toggle; Album Permissions tab has album selector then user/role table with add/remove controls; link from nav bar visible only to `isAdmin`

**Checkpoint**: `quickstart.md` Scenario 4 passes ✓

---

## Phase 8: User Story 6 — Photo Details & EXIF (Priority: P6)

**Goal**: Users see EXIF metadata in lightbox; uploader/admin can add/edit captions; admin can delete photos.

**Independent Test**: Upload photo with known EXIF, open lightbox, verify data panel. Add caption, verify it persists.

### Implementation

- [ ] T051 [US6] Implement `PATCH /photos/{photo_id}` in `backend/app/api/photos.py` — uploader or admin role required; update `caption` field
- [ ] T052 [US6] Implement `DELETE /photos/{photo_id}` in `backend/app/api/photos.py` — admin role on album required; soft-delete Photo record; delete all 3 Object Storage objects (original + both thumbs)
- [ ] T053 [US6] Update `frontend/src/components/Lightbox.vue` — add expandable details panel showing: caption (editable text input if role allows), exif_date_taken, exif_camera, GPS coordinates (as `lat, lon` or "Not available"); add delete button visible only to admins; save caption on blur or Enter key

**Checkpoint**: Photo details panel works in lightbox; caption saves; delete removes photo from grid ✓

---

## Phase 9: User Story 7 — Share Links (Priority: P7)

**Goal**: Admin can generate time-limited share links; unauthenticated users can view shared albums.

**Independent Test**: Generate link, open in incognito, verify photos visible without login; expire/revoke and verify access denied. Run `quickstart.md` Scenario 5.

### Implementation

- [ ] T054 [US7] Implement `GET /albums/{album_id}/share-links` in `backend/app/api/share.py` — admin role required; list share links for album
- [ ] T055 [US7] Implement `POST /albums/{album_id}/share-links` in `backend/app/api/share.py` — generate UUID token, insert `ShareLink` record with `expires_at`; return full share URL
- [ ] T056 [US7] Implement `DELETE /share-links/{link_id}` in `backend/app/api/share.py` — set `is_revoked=True`
- [ ] T057 [US7] Implement `GET /share/{token}` in `backend/app/api/share.py` — **no auth required**; validate token (exists, not revoked, not expired, album not deleted); return album + photos with pre-signed thumbnail URLs; 410 if expired/revoked
- [ ] T058 [US7] Create `frontend/src/pages/SharedPage.vue` — route `/share/:token`; call `GET /share/:token`; render photo grid (view-only, no upload/delete/lightbox-edit controls); show expiry info in header
- [ ] T059 [US7] Add share link management UI to `frontend/src/pages/AlbumPage.vue` — "Share" button visible to admins; opens panel listing existing links with revoke button and a form to generate new link with date picker for expiry

**Checkpoint**: `quickstart.md` Scenario 5 passes ✓

---

## Phase 10: User Story 8 — Download (Priority: P8)

**Goal**: Users download individual photos; uploader/admin downloads whole album as zip.

**Independent Test**: Download single photo, verify it matches original. Download album zip, verify all photos included.

### Implementation

- [ ] T060 [US8] Implement `GET /photos/{photo_id}/download` in `backend/app/api/photos.py` — generate pre-signed URL with `ResponseContentDisposition=attachment`; return 302 redirect to pre-signed URL
- [ ] T061 [US8] Implement `GET /albums/{album_id}/download` in `backend/app/api/albums.py` — uploader or admin required; stream zip archive using Python `zipfile` + streaming response; fetch each original from Object Storage and add to zip; set `Content-Disposition: attachment; filename="<album-name>.zip"`
- [ ] T062 [US8] Add Download button to `frontend/src/components/Lightbox.vue` — calls `GET /photos/:id/download` (opens in new tab to trigger browser download)
- [ ] T063 [US8] Add "Download Album" button to `frontend/src/pages/AlbumPage.vue` — visible to uploaders and admins; triggers `GET /albums/:id/download`

**Checkpoint**: `quickstart.md` Scenario 6 passes ✓

---

## Phase 11: User Story 9 — Search & Filter (Priority: P9)

**Goal**: Users search by keyword and filter by date range across all their permitted albums.

**Independent Test**: Upload photos with known captions, search for keyword, verify only matching photos appear.

### Implementation

- [ ] T064 [US9] Implement `GET /search` in `backend/app/api/search.py` — filter photos to caller's permitted albums; support `q` (LIKE match on caption + filename), `album_id`, `date_from`, `date_to`; paginate results; each result includes album info
- [ ] T065 [US9] Create `frontend/src/pages/SearchPage.vue` — search bar + date range pickers + optional album dropdown filter; display results as photo grid using `PhotoGrid.vue`; add route `/search` in router
- [ ] T066 [US9] Add search icon/bar to global navigation in `frontend/src/App.vue` — navigates to `/search` with `?q=` query param pre-filled

**Checkpoint**: `quickstart.md` Scenario 7 passes ✓

---

## Phase 12: Polish & Deployment

**Purpose**: Cross-cutting concerns, error handling, and production deployment

- [ ] T067 [P] Implement `GET /storage/summary` in `backend/app/api/storage_info.py` — global admin only; sum `file_size_bytes` per album from DB; return total + per-album breakdown
- [ ] T068 [P] Add storage summary panel to `frontend/src/pages/AdminPage.vue` — new "Storage" tab showing total usage and per-album bar chart or table
- [ ] T069 [P] Add global error handling to `frontend/src/App.vue` — catch Axios errors; show toast notifications for 403 (no access), 413 (file too large), 415 (wrong file type), 500 (server error)
- [ ] T070 [P] Create `frontend/src/pages/NotFoundPage.vue` — 404 page; add `/:pathMatch(.*)*` catch-all route in router
- [ ] T071 [P] Add loading skeleton states to `frontend/src/components/PhotoGrid.vue` and `frontend/src/pages/AlbumsPage.vue` — show placeholder cards while fetching
- [ ] T072 Create `backend/photo-gallery-api.service` systemd unit file — `User=hank`, `WorkingDirectory=/home/hank/my_websites/photo-gallery/backend`, `ExecStart=.../uvicorn main:app --host 0.0.0.0 --port 8002`, `Restart=always`; install: `sudo cp photo-gallery-api.service /etc/systemd/system/ && sudo systemctl enable photo-gallery-api`
- [ ] T073 Add Apache proxy config to `/etc/apache2/sites-enabled/cloud.hansu.tw.conf` — add `ProxyPass /api/photo-gallery/ http://127.0.0.1:8002/api/photo-gallery/` and `ProxyPassReverse` before the existing `/api/` catch-all; add `FallbackResource /sites/photo-gallery/index.html` for SPA routing
- [ ] T074 Build frontend and create symlink: `cd frontend && npm run build`; `ln -s /home/hank/my_websites/photo-gallery/frontend/dist /var/www/html/sites/photo-gallery`
- [ ] T075 Start services and reload Apache: `sudo systemctl start photo-gallery-api && sudo systemctl reload apache2`
- [ ] T076 Run full `quickstart.md` validation against `https://cloud.hansu.tw/sites/photo-gallery/` — execute all 7 scenarios; verify each passes
- [ ] T077 [P] Update `/home/hank/my_websites/CLAUDE.md` — add `photo-gallery/` entry to the Projects section with tech stack summary, port (8002), DB name, and deployment notes

---

## Phase 13: Album Date Sorting (FR-037, FR-038)

**Goal**: Albums sorted by event date; date auto-parsed from title (`yyyy-mm-dd` / `yyyy.mm.dd`) or entered manually.

- [ ] T078 Add Alembic migration: `alembic revision --autogenerate -m "add album_date to albums"`; verify generated SQL adds `album_date DATE NULL`; run `alembic upgrade head`
- [ ] T079 [P] Update `GET /albums` in `backend/app/api/albums.py` — change `order_by` to `Album.album_date.desc().nullslast(), Album.created_at.desc()`; add `album_date` field to `_album_response()`
- [ ] T080 [P] Update `POST /albums` in `backend/app/api/albums.py` — accept optional `album_date` in body; before saving, attempt to parse date from `name` using regex `r'(\d{4})[.\-](\d{2})[.\-](\d{2})'`; if matched, use parsed date as `album_date` (body value takes precedence if also provided)
- [ ] T081 [P] Update `PATCH /albums/{album_id}` in `backend/app/api/albums.py` — accept optional `album_date` in body and update the column
- [ ] T082 Update create album modal in `frontend/src/pages/AlbumsPage.vue` — watch `newName` input; if it matches `yyyy-mm-dd` or `yyyy.mm.dd` pattern, auto-fill a hidden `newDate` field and hide the date picker; otherwise show a `<input type="date">` picker for manual entry; send `album_date` to `POST /albums`
- [ ] T083 [P] Show album date on `frontend/src/components/AlbumCard.vue` — display `album_date` (formatted as `yyyy.mm.dd`) below the album name if present
- [ ] T084 Update `frontend/src/pages/AlbumsPage.vue` — replace flat albums grid with year-grouped layout: compute `groupedAlbums` computed property that groups albums by `album_date` year (descending by default); albums without `album_date` go into an "未分類" group always rendered last; render each group as a `<section>` with `<h2>` year header followed by the album grid
- [ ] T085 [P] Add sort direction toggle to `frontend/src/pages/AlbumsPage.vue` header — a button showing "↓ 最新優先" / "↑ 最舊優先"; toggling flips the year group order and the album order within each group; state stored in `localStorage` key `pg_album_sort`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Start immediately — no dependencies
- **Phase 2 (Foundational)**: Requires Phase 1 — blocks all user story phases
- **Phase 3–11 (User Stories)**: All require Phase 2; stories can be done sequentially P1→P9
- **Phase 12 (Polish)**: Requires all desired user stories complete

### User Story Dependencies

| Story | Depends On | Notes |
|---|---|---|
| US1 Auth (P1) | Phase 2 | Must be first — all other stories need a logged-in user |
| US2 Browse (P2) | US1 | Needs auth + at least one album with photos |
| US3 Upload (P3) | US2 | Upload zone is inside album view |
| US4 Manage Albums (P4) | US1 | Can be done in parallel with US2/US3 |
| US5 Users & Perms (P5) | US1 | Admin panel — independent from browse/upload |
| US6 Photo Details (P6) | US2 | Extends lightbox |
| US7 Share Links (P7) | US2 | Extends album view |
| US8 Download (P8) | US2 | Extends lightbox and album view |
| US9 Search (P9) | US2 | Needs photos to search |

### Parallel Opportunities Per Story

```
Phase 2 — run in parallel:
  T007 config.py  |  T008 models.py  |  T012 storage.py  |  T013 auth.py  |  T016 api.js  |  T017 router.js

Phase 3 (US1) — run in parallel after T018–T021 complete:
  T022 auth store  |  T023 LoginPage.vue

Phase 4 (US2) — run in parallel after T025–T027 complete:
  T028 albums store  |  T029 AlbumsPage  |  T030 AlbumCard  |  T032 ViewModeToggle
```

---

## Implementation Strategy

### MVP Scope (Phases 1–4 only)

Complete US1 (auth) + US2 (browse) to get a working read-only gallery:

1. Phase 1: Setup
2. Phase 2: Foundational
3. Phase 3: US1 — Login works
4. Phase 4: US2 — Albums and photos visible with lightbox
5. **Validate**: Run quickstart Scenarios 1 and 3
6. Deploy and use

Then add US3 (upload), US4 (albums), US5 (users) to get a fully operational system.

### Incremental Delivery Order

```
MVP:   Phase 1 → 2 → 3 (US1) → 4 (US2)     ← read-only gallery live
Core:  → 5 (US3 upload) → 6 (US4 albums) → 7 (US5 permissions)
Extra: → 8 (US6 EXIF) → 9 (US7 share) → 10 (US8 download) → 11 (US9 search)
Done:  → Phase 12 (polish + deploy)
```

---

## Notes

- `[P]` tasks touch different files and can run concurrently
- Each User Story phase ends with a named Checkpoint — stop and validate before proceeding
- Secrets in `backend/.env` only — never commit real credentials
- When adding Apache config (T073), add the new ProxyPass **before** the existing `/api/` catch-all, or it will be shadowed
- After T074 (symlink), verify Apache has `FollowSymLinks` enabled for the sites directory (it does, per existing config)
