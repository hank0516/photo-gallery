# Tasks: iOS Native App

Total: 47 tasks across 11 phases.

## MVP Scope (Phase 1–6 + Phase 11)

Phase 1–6 + Phase 11 covers: project setup, auth, album list, photo grid, fullscreen viewer, zoom, video playback, and polish (iPad layout, error states, caching, logout, ad hoc distribution). This is the first version for family members.

Deferred to post-MVP: Phase 7 (EXIF), Phase 8 (Save to Camera Roll), Phase 9 (Search), Phase 10 (Locked Album).

---

## Phase 1 — Setup

- [ ] T001 Create `ios/` directory and Xcode project `PhotoGallery.xcodeproj` targeting iOS 17 / macOS 14 as a SwiftUI Universal App
- [ ] T002 Add Kingfisher via Swift Package Manager (`https://github.com/onevcat/Kingfisher`)
- [ ] T003 Register `photogallery` custom URL scheme in `ios/PhotoGallery/Info.plist`
- [ ] T004 Add `NSPhotoLibraryAddUsageDescription` to `Info.plist` (required for Camera Roll save)
- [ ] T005 Create folder structure per plan: `App/`, `Core/`, `Models/`, `Features/`

---

## Phase 2 — Foundational (blocking all features)

- [ ] T006 Create `Core/Network/Endpoints.swift` — define base URL constant and all API path strings
- [ ] T007 Create `Core/Auth/KeychainHelper.swift` — `save(token:)`, `loadToken()`, `deleteToken()` using `SecItem` API
- [ ] T008 Create `Core/Network/APIClient.swift` — `URLSession` wrapper that reads token from Keychain and injects `Authorization: Bearer` header on every request; generic `fetch<T: Decodable>` method
- [ ] T009 Create `Models/Album.swift`, `Models/MediaItem.swift`, `Models/EXIF.swift`, `Models/SearchResult.swift`, `Models/Page.swift` — `Codable` structs matching API contracts in `contracts/api.md`
- [ ] T010 Create `App/AppState.swift` — `@Observable` class holding `session: Session?` and top-level navigation state
- [ ] T011 Create `App/PhotoGalleryApp.swift` — `@main` entry; on launch check Keychain for token, set AppState; handle `photogallery://auth/callback` URL scheme

---

## Phase 3 — US1 & US2: Authentication & Persistent Session

_User Stories: "open app to access gallery" + "stay logged in automatically"_

- [ ] T012 [US1] **Backend**: extend `app/core/auth.py` `get_current_user` to also accept `Authorization: Bearer <token>` header (cookie takes precedence if both present)
- [ ] T013 [US1] **Backend**: extend `app/api/auth.py` `/auth/callback` — when `?redirect=native` present, redirect to `photogallery://auth/callback?token=<jwt>` instead of web URL
- [ ] T014 [P] [US1] Create `Core/Auth/AuthService.swift` — `signIn()` launches `ASWebAuthenticationSession` to `/auth/login?redirect=native`, captures callback URL, extracts token, saves to Keychain; `signOut()` deletes token
- [ ] T015 [P] [US1] Create `Features/Auth/LoginViewModel.swift` — calls `AuthService.signIn()`, updates `AppState.session` on success
- [ ] T016 [US1] Create `Features/Auth/LoginView.swift` — "Sign in with Google" button; shown when `AppState.session == nil`
- [ ] T017 [US2] Verify token persists across app restart: `AppState` reads Keychain on init, skips `LoginView` if valid token found; call `GET /auth/me` to validate token on launch

---

## Phase 4 — US3: Album List

_User Story: "see only albums I have access to"_

- [ ] T018 [P] [US3] Create `Features/Albums/AlbumListViewModel.swift` — calls `GET /albums`, exposes `albums: [Album]`, `isLoading`, `error`
- [ ] T019 [P] [US3] Create `Features/Albums/AlbumCard.swift` — shows cover thumbnail (Kingfisher), name, photo count, role badge, lock icon if `isLocked`
- [ ] T020 [US3] Create `Features/Albums/AlbumListView.swift` — `LazyVGrid` of `AlbumCard`; pull-to-refresh; logout button in toolbar

---

## Phase 5 — US4 & US5 & US6: Album Detail + Fullscreen Viewer

_User Stories: "browse photos in a grid" + "swipe fullscreen" + "pinch-to-zoom"_

- [ ] T021 [P] [US4] Create `Features/AlbumDetail/AlbumDetailViewModel.swift` — calls `GET /albums/{id}?page=&per_page=50`, infinite-scroll pagination, exposes `items: [MediaItem]`
- [ ] T022 [P] [US4] Create `Features/AlbumDetail/MediaGrid.swift` — `LazyVGrid` of thumbnail images using Kingfisher; shows play-icon overlay for videos; triggers load-more at last item
- [ ] T023 [US4] Create `Features/AlbumDetail/AlbumDetailView.swift` — hosts `MediaGrid`, navigation title, passes tapped item to viewer
- [ ] T024 [P] [US5] Create `Features/Viewer/MediaViewerView.swift` — `TabView` in `.page` style for swipe-between-items; hosts `PhotoView` or `VideoPlayerView` per item type
- [ ] T025 [P] [US6] Create `Features/Viewer/PhotoView.swift` — zoomable photo using `MagnificationGesture` + `DragGesture`; double-tap to reset zoom
- [ ] T026 [US5] Wire `AlbumDetailView` → `MediaViewerView`: tapping a grid item opens viewer at correct index

---

## Phase 6 — US7: Video Playback

_User Story: "watch videos inline"_

- [ ] T027 [P] [US7] Create `Features/Viewer/VideoPlayerView.swift` — `AVPlayerViewController` wrapped in `UIViewControllerRepresentable`; fetches `original_url` from `GET /photos/{id}` on appear; shows play/pause/seek controls
- [ ] T028 [US7] Show video play-icon overlay on `MediaGrid` thumbnails for `media_type == "video"`

---

## Phase 7 — US8: EXIF Info

_User Story: "see EXIF information"_

- [ ] T029 [P] [US8] Create `Features/Viewer/EXIFPanel.swift` — displays capture date, camera model, GPS coordinates (map link if lat/lng present); shows "—" for missing fields
- [ ] T030 [US8] Add info button (ⓘ) to `MediaViewerView` toolbar; toggle `EXIFPanel` as a sheet or bottom drawer; fetch `GET /photos/{id}` on first open to load EXIF

---

## Phase 8 — US9: Save to Camera Roll

_User Story: "save a photo to my device photo library"_

- [ ] T031 [P] [US9] Create save-to-library function in `Core/Network/APIClient.swift` — calls `GET /photos/{id}/download` to get presigned URL, downloads data, saves via `PHPhotoLibrary.shared().performChanges`
- [ ] T032 [US9] Add download/save button to `MediaViewerView` toolbar; request `NSPhotoLibraryAddUsageDescription` permission on first use; show success/error toast

---

## Phase 9 — US10: Search

_User Story: "search photos by keyword or date range"_

- [ ] T033 [P] [US10] Create `Features/Search/SearchViewModel.swift` — debounced calls to `GET /search?q=&date_from=&date_to=`, exposes `results: [SearchResult]`, `isLoading`
- [ ] T034 [P] [US10] Create `Features/Search/SearchView.swift` — keyword text field, date-range pickers, results as `MediaGrid`; tapping result opens `MediaViewerView`
- [ ] T035 [US10] Add search icon to `AlbumListView` toolbar → navigate to `SearchView`

---

## Phase 10 — US11: Locked Album Unlock

_User Story: "enter a password to unlock a locked album"_

- [ ] T036 [P] [US11] Create `Features/Unlock/UnlockView.swift` — password field + "Unlock" button; calls `POST /albums/{id}/unlock`; on success stores `unlock_token` in memory (AppState or ViewModel) for this session
- [ ] T037 [US11] In `AlbumDetailViewModel`: if album `isLocked` and no in-memory unlock token, show `UnlockView` as a sheet before loading photos; include `X-Unlock-Token` header in subsequent requests for that album
- [ ] T038 [US11] On wrong password show inline error; on correct password dismiss sheet and load album

---

## Phase 11 — Polish & Cross-cutting Concerns

- [ ] T039 [P] iPad layout: in `AlbumListView` and `AlbumDetailView` use `NavigationSplitView` when `horizontalSizeClass == .regular` (iPad / Mac)
- [ ] T040 [P] Loading states: add `ProgressView` placeholders in `AlbumCard`, `MediaGrid`, and `MediaViewerView` while network requests are in flight
- [ ] T041 [P] Error states: show retry-able error banner in `AlbumListView`, `AlbumDetailView`, and `SearchView` on network failure
- [ ] T042 [P] Configure Kingfisher disk cache: 200 MB limit, cache key strips query-string from presigned URL, in `Core/Cache/ImageCache.swift`; apply globally in `PhotoGalleryApp`
- [ ] T043 [P] Logout: `POST /auth/logout` + delete Keychain token + reset `AppState.session` → return to `LoginView`
- [ ] T044 [P] Session expiry: on 401 response from any API call, clear session and navigate to `LoginView` with "Session expired" message
- [ ] T045 [P] macOS: verify app launches and is usable on macOS 14 (Mac Catalyst or native); fix any layout issues in `AlbumListView` and `MediaViewerView`
- [ ] T046 Ad hoc distribution: export IPA with ad hoc provisioning profile; create `manifest.plist`; upload to `https://cloud.hansu.tw/apps/photo-gallery/`; verify `itms-services://` install link works on a registered device
- [ ] T047 Run all 12 quickstart validation scenarios from `quickstart.md` and confirm pass
