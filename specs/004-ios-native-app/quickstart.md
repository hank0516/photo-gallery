# Quickstart Validation Guide: iOS Native App

This guide validates the app end-to-end. Run these scenarios in order after each build.

## Prerequisites

- Xcode 15+, iOS 17+ simulator or physical device
- Backend running at `https://cloud.hansu.tw/api/photo-gallery/`
- At least one album with photos in the backend
- A second Google account to act as "family member" (viewer)
- `photogallery://` custom URL scheme registered in `Info.plist`

---

## Scenario 1 — First-time Login (Admin setup)

1. Launch the app fresh (no token in Keychain).
2. App shows login screen with "Sign in with Google" button.
3. Tap the button → `ASWebAuthenticationSession` opens Google OAuth.
4. Complete Google sign-in → browser redirects to `photogallery://auth/callback?token=xxx`.
5. App closes the auth session, stores token in Keychain, navigates to album list.

**Expected**: Album list loads with albums the user has access to. No login screen on subsequent launches.

---

## Scenario 2 — Persistent Session

1. With a valid token in Keychain, force-quit and relaunch the app.

**Expected**: App goes directly to album list, no login prompt.

---

## Scenario 3 — Album List

1. From the album list, verify each card shows: cover thumbnail, name, photo count, role badge.
2. Confirm locked albums show a lock icon.
3. Confirm only albums the user has permission to see are listed.

**Expected**: List matches what `GET /albums` returns for this user.

---

## Scenario 4 — Photo Grid

1. Tap an album → photo grid loads.
2. Scroll down — additional photos lazy-load as they come into view.
3. Previously loaded thumbnails remain visible while scrolling back up (cached).

**Expected**: Grid is smooth; thumbnails appear within 3 seconds on WiFi.

---

## Scenario 5 — Fullscreen Viewer

1. Tap a photo in the grid → fullscreen viewer opens.
2. Swipe left/right to navigate between photos.
3. Pinch to zoom in on a photo; double-tap to reset.
4. Swipe down or tap Back to dismiss.

**Expected**: Navigation is immediate with no lag. Zoom works correctly.

---

## Scenario 6 — Video Playback

1. Open an album containing a video.
2. Tap the video thumbnail → fullscreen viewer opens with video player.
3. Tap play → video plays. Tap pause → video pauses. Seek using scrubber.

**Expected**: Video plays inline without leaving the app.

---

## Scenario 7 — EXIF Info

1. In fullscreen viewer, tap the info button (ⓘ).
2. EXIF panel shows: capture date, camera model, GPS coordinates (if available).
3. For photos without EXIF, fields show "—".

**Expected**: Data matches `GET /photos/{id}` response.

---

## Scenario 8 — Save to Camera Roll

1. In fullscreen viewer, tap the download/save button.
2. If app lacks Photos permission, system prompt appears → grant it.
3. Photo is saved to device Camera Roll.

**Expected**: Photo appears in device Photos app immediately.

---

## Scenario 9 — Search

1. Tap the search icon → search screen.
2. Enter a keyword that matches a filename or caption → results appear as a photo grid.
3. Clear keyword, set a date range → results filter by date.
4. Tap a result → fullscreen viewer opens for that photo.

**Expected**: Results appear within 2 seconds. Tapping a result opens the correct photo.

---

## Scenario 10 — Locked Album

1. Tap a locked album → password prompt appears.
2. Enter wrong password → error shown, album stays locked.
3. Enter correct password → album contents load.
4. Navigate away and return to the album within the same session → no password prompt again.

**Expected**: Lock gate works; session unlock is remembered.

---

## Scenario 11 — Viewer Account (Family Member)

1. Log in with a Google account that has viewer-only access.
2. Confirm only permitted albums are visible (no admin-only albums).
3. Confirm no upload, create-album, or manage-members controls are visible.

**Expected**: UI is read-only; no admin controls exposed.

---

## Scenario 12 — Ad Hoc Install

1. Admin exports IPA with ad hoc provisioning profile.
2. Upload IPA + `manifest.plist` to `https://cloud.hansu.tw/apps/photo-gallery/`.
3. On a registered family member device, open Safari and tap the `itms-services://` install link.
4. Confirm install prompt appears → install completes → app icon appears on home screen.
5. Open app → login flow works as Scenario 1.

**Expected**: App installs and runs without App Store involvement.
