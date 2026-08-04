# Feature Specification: Video Upload & Playback

**Feature Branch**: `003-video-support`

**Created**: 2026-08-04

**Status**: Draft

**Input**: User description: "支援上傳影片並在網頁上播放。允許上傳 MP4、MOV、WebM、AVI，自動擷取縮圖，在 PhotoGrid 顯示播放圖示，在 Lightbox 用 HTML5 video 播放。"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Upload a Video to an Album (Priority: P1)

A user with uploader or admin permission opens an album and uploads one or more video files. They drag
MP4, MOV, WebM, or AVI files onto the upload zone (or click to select). Each file shows its own
progress bar. After upload completes, the video appears in the album grid with a thumbnail image and
a play icon overlay, visually distinguishing it from photos.

**Why this priority**: Without upload, no videos exist in the system. Every other story depends on
this one. It also contains the highest implementation risk (file size, thumbnail extraction).

**Independent Test**: Open an album as an uploader, drag an MP4 file onto the upload zone, observe
the progress indicator, then confirm the video card appears in the grid with a thumbnail and play icon.

**Acceptance Scenarios**:

1. **Given** a user with uploader access opens an album, **When** they open the upload dialog,
   **Then** the file selector accepts `.mp4`, `.mov`, `.webm`, and `.avi` files in addition to images.
2. **Given** a user drags a valid video file onto the upload zone, **When** upload begins,
   **Then** a progress indicator is shown for that file.
3. **Given** a video upload completes successfully, **When** the album grid refreshes,
   **Then** the video appears as a card with its extracted thumbnail and a distinct play-button overlay.
4. **Given** a user uploads a file larger than 500 MB, **When** they attempt to submit,
   **Then** an error message is shown before the file is transmitted and the upload is rejected.
5. **Given** a user uploads an unsupported file type (e.g., `.mkv`, `.flv`),
   **When** they attempt to submit, **Then** a clear error message is shown and the file is rejected.
6. **Given** a user has only viewer access, **When** they open an album, **Then** no upload zone
   is shown (same as photos; no change to existing behaviour).

---

### User Story 2 — Play a Video in Lightbox (Priority: P2)

A user browsing an album clicks on a video card. The lightbox opens and displays an HTML5 video
player with the video ready to play. The user can play, pause, seek, and adjust volume. They can
also open the video in full-screen mode. Left/right navigation in the lightbox continues to work,
moving between adjacent items (photos or videos). The video pauses automatically when the user
navigates away.

**Why this priority**: Playback is the primary value of video support — without it, uploading
serves no purpose.

**Independent Test**: Upload an MP4 to an album, click its card in the grid, verify the lightbox
shows a video player (not a broken image), confirm play/pause/volume/fullscreen all work, and
navigate to adjacent items with arrow keys.

**Acceptance Scenarios**:

1. **Given** a user clicks a video card in the album grid, **When** the lightbox opens,
   **Then** an HTML5 video player is shown (not an `<img>` tag) with playback controls visible.
2. **Given** the lightbox is showing a video, **When** the user clicks Play,
   **Then** the video begins streaming from the presigned URL.
3. **Given** the lightbox is showing a video, **When** the user clicks the fullscreen button,
   **Then** the video expands to fullscreen.
4. **Given** the lightbox is showing a video, **When** the user presses the right arrow key or
   clicks Next, **Then** the video pauses and the next item (photo or video) is loaded.
5. **Given** the lightbox is showing a photo, **When** the user navigates to it from a video,
   **Then** the photo is displayed correctly using the existing `<img>` viewer (no regression).
6. **Given** the user is on mobile, **When** they tap a video card and the lightbox opens,
   **Then** the video player is full-width and native mobile playback controls are accessible.

---

### User Story 3 — Distinguish Videos from Photos in the Grid (Priority: P3)

A user browsing an album grid can immediately tell which items are videos without opening them.
Videos display their extracted thumbnail alongside a play-button icon overlay in all three view
modes (small grid, large grid, list). The overlay is large enough to be visible on mobile.

**Why this priority**: Clear visual differentiation prevents confusion and sets accurate user
expectations before a tap/click.

**Independent Test**: Upload at least one video and one photo to the same album. View the album
in all three view modes and confirm videos are visually distinct from photos.

**Acceptance Scenarios**:

1. **Given** an album contains both photos and videos, **When** a user views the album in
   small-thumbnail grid mode, **Then** video cards show a play-button overlay on their thumbnail.
2. **Given** an album contains both photos and videos, **When** a user switches to large-thumbnail
   mode or list view, **Then** the play-button overlay is still visible on video cards.
3. **Given** a video whose thumbnail could not be extracted, **When** it is shown in the grid,
   **Then** a generic video placeholder icon is displayed instead of a broken image.

---

### User Story 4 — Download and Delete Videos (Priority: P4)

A user can download a video at its original quality from the lightbox. An admin can soft-delete a
video from the lightbox the same way they delete a photo. Deleted videos no longer appear in the
album or search results. These actions behave identically to how they work for photos.

**Why this priority**: Core media management parity with photos. No new interaction patterns;
this is an extension of existing flows.

**Independent Test**: Open a video in the lightbox, click Download and verify the original file is
downloaded. Log in as admin, delete a video, confirm it disappears from the grid and cannot be
accessed via its original URL.

**Acceptance Scenarios**:

1. **Given** a user opens a video in the lightbox, **When** they click "Download,"
   **Then** the original video file is downloaded via a presigned URL.
2. **Given** an admin opens a video in the lightbox, **When** they click "Delete" and confirm,
   **Then** the video is removed from the album grid and its storage objects are marked deleted.
3. **Given** a viewer (non-admin) opens a video in the lightbox, **When** they view the toolbar,
   **Then** no delete button is visible.

---

### User Story 5 — Search Returns Video Results (Priority: P5)

A user searching by keyword or date range can find videos alongside photos. Search results show
video cards with the play-button overlay, identical to the album grid. Clicking a video in search
results opens the lightbox video player.

**Why this priority**: Videos are first-class media items; omitting them from search would create
a confusing gap in discoverability.

**Independent Test**: Upload a video with a known caption, search for that caption, confirm the
video appears in search results with the play overlay, and click it to verify the lightbox opens.

**Acceptance Scenarios**:

1. **Given** a video has a caption matching a search keyword, **When** a user searches for that
   keyword, **Then** the video appears in the results grid with a play-button overlay.
2. **Given** a video was uploaded on a specific date, **When** a user filters by that date range,
   **Then** the video is included in the results.
3. **Given** a search result set contains both photos and videos, **When** the user clicks a video
   result, **Then** the lightbox opens in video-player mode.

---

### Edge Cases

- What happens when thumbnail extraction fails (corrupt file, unsupported codec)?
- What if a 500 MB video upload is interrupted mid-way due to a network error?
- What happens if the presigned URL for a video expires while the user is mid-playback?
- How does the system behave if ffmpeg is not installed on the server?
- What if a user uploads a file with a `.mp4` extension that is actually a different format?
- What happens when an album mixes many videos and photos — does lazy loading still work efficiently?
- What if Linode Object Storage is temporarily unavailable during a large video upload?

---

## Requirements *(mandatory)*

### Functional Requirements

**Video Upload**

- **FR-V001**: The system MUST accept video uploads in the following formats: MP4, MOV, WebM, AVI.
- **FR-V002**: The system MUST enforce a maximum video file size of 500 MB per file and reject oversized files with a clear error before transmission to storage.
- **FR-V003**: The system MUST reject video files with unsupported extensions or MIME types and display a descriptive error message.
- **FR-V004**: The upload endpoint and upload zone MUST handle video files through the same interface as photos (same `POST /albums/{id}/photos` endpoint, same `UploadZone` component).
- **FR-V005**: On upload, the system MUST automatically extract the first frame of the video and store it as a thumbnail (at 300 px and 800 px sizes) on Linode Object Storage.
- **FR-V006**: If thumbnail extraction fails (corrupt file, unsupported codec), the system MUST still complete the upload and store a `null` thumbnail key; a fallback placeholder MUST be displayed in the UI.
- **FR-V007**: The `Photo` record MUST store the video's MIME type in the existing `mime_type` field so the frontend can distinguish videos from images without additional API fields.

**Video Playback**

- **FR-V008**: The lightbox MUST detect when the current item is a video (via `mime_type`) and render an HTML5 `<video>` element instead of an `<img>` element.
- **FR-V009**: The video player MUST use a presigned URL for the video source; no raw storage credentials may be exposed to the client.
- **FR-V010**: The video player MUST support native browser playback controls: play, pause, seek, volume, and fullscreen.
- **FR-V011**: When the user navigates away from a video in the lightbox (next/previous or close), the video MUST pause automatically.
- **FR-V012**: The lightbox `<img>` rendering path for photos MUST remain unchanged (no regression).

**Grid Display**

- **FR-V013**: In all three view modes (small grid, large grid, list), video items MUST display their extracted thumbnail alongside a visible play-button overlay icon.
- **FR-V014**: If a video has no extracted thumbnail (`null`), a generic video placeholder icon MUST be shown in the grid.

**Download & Delete**

- **FR-V015**: Users MUST be able to download the original video file from the lightbox via a presigned URL with a `Content-Disposition: attachment` header.
- **FR-V016**: Admin users MUST be able to soft-delete a video from the lightbox using the same delete action as for photos.

**Search**

- **FR-V017**: The search endpoint MUST include videos in results when their caption or filename matches the query or their upload date falls within the date range filter.
- **FR-V018**: Video items in search results MUST be rendered with the play-button overlay, consistent with the album grid.

**Update to Existing Requirement**

- **FR-013** *(amended)*: The system MUST reject uploads of unsupported file types. Supported types are: still images (JPEG, PNG, WEBP, HEIC, GIF) and videos (MP4, MOV, WebM, AVI). Any other file type MUST be rejected with a clear error message before the file is transmitted to storage.

### Key Entities

- **Photo** *(extended)*: The existing `Photo` entity now represents any media item (photo or video). The `mime_type` field already exists and is the discriminator. For videos, `thumb_300_key` and `thumb_800_key` store the extracted first-frame thumbnails; `original_key` stores the video file. No schema changes are required unless a `duration` field is added in future.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-V001**: A 100 MB MP4 video can be uploaded to an album and appear in the grid (with thumbnail) in under 90 seconds on a standard broadband connection.
- **SC-V002**: A video in the lightbox begins playing within 3 seconds of the user clicking its card, on a standard broadband connection.
- **SC-V003**: 100% of upload attempts with unsupported file types are rejected with an error message before any data is sent to storage.
- **SC-V004**: 100% of upload attempts exceeding 500 MB are rejected with a clear error before transmission.
- **SC-V005**: Navigating between photos and videos in the lightbox (next/previous) takes under 1 second for the UI transition.
- **SC-V006**: An album grid containing a mix of photos and videos loads within the same performance envelope as a photo-only album of the same count (no regression to SC-002).
- **SC-V007**: When thumbnail extraction fails, the upload still completes successfully and the item is accessible in the grid with a fallback placeholder — 0% silent failures.

---

## Assumptions

- Videos are played directly via presigned URL using the browser's native HTML5 video capabilities. No transcoding, adaptive bitrate streaming (HLS/DASH), or server-side re-encoding is required.
- `ffmpeg` (or `ffmpeg-python`) is available on the server for first-frame thumbnail extraction. If not pre-installed, it must be installed as part of this feature's deployment step.
- The existing `Photo` DB model and `mime_type` column are sufficient to represent video items. No new DB table or migration is required beyond what is already present.
- AVI files may not play in all browsers natively (Safari, Firefox have limited AVI support). This is acceptable for v1; the download path still works for AVI. Future work could add format guidance to the UI.
- Video EXIF/metadata extraction (duration, resolution, codec) is out of scope for this feature. Only the first-frame thumbnail is extracted.
- Caption editing for videos uses the existing `PATCH /photos/{id}` endpoint with no changes.
- The 500 MB per-file limit applies to videos; the existing 50 MB per-file limit continues to apply to images.
- Bulk video upload (multiple videos at once) uses the same queue mechanism as bulk photo upload.
- ZIP album download (Phase 10, not yet implemented) will include videos when that feature is built; that is out of scope here.
- The share-link feature (Phase 9, not yet implemented) will naturally include videos when built; that is out of scope here.
