# Feature: iOS Native App

## Overview

A native mobile app that gives family members a simple, tap-to-open experience for browsing the private photo gallery on iPhone and iPad — eliminating the need to navigate a web browser. Authentication is handled once by the admin; family members open the app and see their photos immediately.

## User Stories

1. As a Viewer (family member), I want to open a dedicated app icon on my iPhone or iPad to access the photo gallery, so that I don't need to know how to use a web browser.
2. As a Viewer, I want to stay logged in automatically after my first setup, so that I can browse photos without entering credentials each time.
3. As a Viewer, I want to see only the albums I have been granted access to, so that I don't see content not intended for me.
4. As a Viewer, I want to browse photos in a scrollable grid within an album, so that I can quickly scan through available photos.
5. As a Viewer, I want to tap a photo to view it fullscreen with swipe-left/right navigation, so that browsing feels natural on a touchscreen.
6. As a Viewer, I want to pinch-to-zoom on a fullscreen photo, so that I can see fine details.
7. As a Viewer, I want to watch videos inline in the fullscreen viewer, so that I can enjoy all media without leaving the app.
8. As a Viewer, I want to see EXIF information for a photo (date taken, camera model, GPS location), so that I can know when and where the photo was captured.
9. As a Viewer, I want to save a photo to my device's photo library, so that I can keep a personal copy of a favourite memory.
10. As a Viewer, I want to search photos by keyword or date range, so that I can find a specific memory quickly.
11. As a Viewer, I want to enter a password to unlock a password-protected album, so that I can access restricted content the admin has shared with me.
12. As an Admin, I want to install the app on family members' devices without requiring App Store access, so that I can distribute and update the app privately.

## Functional Requirements

- FR-001: Users must authenticate with their Google account before accessing any content.
- FR-002: The app must display only albums the authenticated user has been granted access to.
- FR-003: Album list must show: cover thumbnail, album name, photo/video count, and the user's role in the album.
- FR-004: Users must be able to browse all photos and videos in an album as a scrollable thumbnail grid.
- FR-005: Tapping a thumbnail must open a fullscreen viewer supporting swipe-left/swipe-right to navigate between items.
- FR-006: The fullscreen photo viewer must support pinch-to-zoom.
- FR-007: Videos must play inline within the fullscreen viewer with standard playback controls (play/pause, seek).
- FR-008: EXIF metadata — including capture date, camera model, and GPS location — must be viewable for each photo.
- FR-009: Users must be able to save an individual photo to the device's native photo library from the fullscreen viewer.
- FR-010: Users must be able to search photos by keyword (filename or caption) and/or date range; results are shown as a photo grid.
- FR-011: Password-protected albums must prompt for a password before their contents are revealed; entry is persisted for the session.
- FR-012: Authenticated sessions must persist across app launches and device restarts without requiring re-login.
- FR-013: The app must be installable on a registered device without App Store involvement (ad hoc distribution).
- FR-014: The app must run on iPhone and iPad as primary targets; macOS as a secondary target sharing the same codebase.

## Success Criteria

- SC-001: A family member unfamiliar with web browsers can find and view a photo within 10 seconds of opening the app.
- SC-002: An authenticated session survives a device restart — the user is taken directly to the album list, not a login screen.
- SC-003: Album grid thumbnails are visible within 3 seconds of opening an album on a standard home WiFi connection.
- SC-004: Swiping between photos in the fullscreen viewer is immediate with no perceptible lag.
- SC-005: The admin can install or update the app on a family member's device without that person needing an App Store account.
- SC-006: A keyword or date-range search over a library of 1,000+ photos returns results within 2 seconds.

## Out of Scope

- Uploading photos or videos from the app (Admin P2, deferred to a later phase)
- Creating, editing, or deleting albums from the app (Admin P2, deferred)
- Managing member permissions from the app (Admin P2, deferred)
- Album ZIP download
- Share link creation or management
- True offline mode (viewing photos with no network connection)
- Push notifications

## Assumptions

- All users already have a Google account configured on their device.
- The admin performs the first-time Google login on behalf of family members.
- The backend REST API is the authoritative data source; no content is stored permanently on-device (thumbnail caching for performance is acceptable).
- The distribution audience is small (fewer than 20 devices).
- The existing backend API is extended minimally to support the app (Bearer token auth); core business logic is unchanged.
