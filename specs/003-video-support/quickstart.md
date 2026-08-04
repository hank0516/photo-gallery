# Quickstart Validation Guide: Video Upload & Playback

**Feature**: 003-video-support | **Date**: 2026-08-04

Use this guide to verify the feature works end-to-end after implementation.

---

## Prerequisites

1. **ffmpeg installed** on the server:
   ```bash
   which ffmpeg && ffmpeg -version
   ```
   If missing: `sudo apt install ffmpeg`

2. **Migration applied**:
   ```bash
   cd /home/hank/my_websites/photo-gallery/backend
   source venv_photo_galary/bin/activate
   alembic upgrade head
   ```
   Confirm new column exists:
   ```sql
   -- in MariaDB:
   DESCRIBE photos;
   -- should show: mime_type VARCHAR(100) NULL
   -- thumb_300_key and thumb_800_key should show NULL under "Null" column
   ```

3. **Backend restarted** after code changes:
   ```bash
   sudo systemctl restart photo-gallery-api
   sudo journalctl -u photo-gallery-api -n 20
   ```

4. **Frontend rebuilt** after component changes:
   ```bash
   cd /home/hank/my_websites/photo-gallery/frontend
   npm run build
   ```

---

## Scenario 1 — Upload an MP4 Video

**Goal**: Verify upload succeeds, thumbnail is extracted, and video appears in album grid.

1. Log in as admin at `https://cloud.hansu.tw/sites/photo-gallery/`
2. Open any album (or create a test album).
3. Open the upload zone.
4. Select a small MP4 file (< 100 MB).
5. Click Upload.

**Expected**:
- Progress bar appears and reaches 100%.
- Video card appears in the album grid with a thumbnail image and a play-button icon overlay.
- No `<img>` broken-image icon visible.

**Verify via API**:
```bash
curl -s -b "pg_session=<token>" \
  https://cloud.hansu.tw/api/photo-gallery/albums/<id> | \
  python3 -m json.tool | grep mime_type
# Should show: "mime_type": "video/mp4"
```

---

## Scenario 2 — Play a Video in Lightbox

**Goal**: Verify the lightbox shows a `<video>` player, not a broken `<img>`.

1. In the album grid, click the video card from Scenario 1.
2. Lightbox opens.

**Expected**:
- An HTML5 video player is visible (not a broken image).
- Clicking Play starts video playback.
- Volume control and fullscreen button work.
- Pressing the right arrow navigates to the next item; video pauses.
- Pressing Escape closes the lightbox.

---

## Scenario 3 — Upload with Unsupported Format

**Goal**: Verify unsupported files are rejected before upload.

1. Try to drag a `.mkv` file onto the upload zone.
2. Try to select a `.pdf` file via the file picker.

**Expected**:
- `.mkv` is filtered out and not added to the queue (frontend filter).
- `.pdf` is filtered out and not added to the queue.
- No network request is made for these files.

---

## Scenario 4 — Upload a Video Exceeding 500 MB

**Goal**: Verify the size limit is enforced.

1. Upload a video file larger than 500 MB.

**Expected**:
- Server returns `413` error.
- Upload zone shows an error state for that file.
- Other files in the same queue are unaffected.

---

## Scenario 5 — Photos Unaffected (Regression Check)

**Goal**: Verify existing photo upload and lightbox still work.

1. Upload a JPEG photo to the same album.
2. Click the photo card.

**Expected**:
- Photo card shows the thumbnail without a play-button overlay.
- Lightbox shows the photo as an `<img>`, not a `<video>`.
- EXIF details panel works as before.
- Download and delete buttons work as before.

---

## Scenario 6 — Search Returns Videos

**Goal**: Verify videos appear in search results.

1. Add a caption to the video uploaded in Scenario 1 (edit via lightbox).
2. Navigate to Search.
3. Search for a word from the caption.

**Expected**:
- Video appears in search results with play-button overlay.
- Clicking opens lightbox in video-player mode.

---

## Scenario 7 — Failed Thumbnail (Optional Manual Test)

**Goal**: Verify graceful fallback when ffmpeg cannot extract a thumbnail.

*(This is hard to trigger with a real file; simulate by temporarily breaking the ffmpeg path in code and uploading any video.)*

**Expected**:
- Upload completes (201 response).
- Video card shows a generic video placeholder icon in the grid (no broken image).
- Lightbox still plays the video (uses `original_url`, not thumbnail).

---

## Quick Log Check

```bash
# Watch backend logs during upload:
sudo journalctl -u photo-gallery-api -f

# Check for ffmpeg errors:
sudo journalctl -u photo-gallery-api --since "5 min ago" | grep -i ffmpeg
```
