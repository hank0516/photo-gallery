# Quickstart & Validation Guide: Private Photo Gallery

**Date**: 2026-08-02

This guide describes how to set up the development environment and validate that the system
works end-to-end. It is not the implementation itself — refer to `tasks.md` for step-by-step
build instructions.

---

## Prerequisites

- Python 3.12
- Node 20 + npm
- MariaDB running locally (already on this server)
- Linode Object Storage bucket created and access keys ready
- Google OAuth credentials (Client ID + Secret) from Google Cloud Console
- Apache configured (done in deployment step)

---

## Environment Setup

### 1. Backend `.env`

Create `backend/.env`:
```
DATABASE_URL=mysql+pymysql://hank:<password>@localhost/PhotoGallery
GOOGLE_CLIENT_ID=<from Google Cloud Console>
GOOGLE_CLIENT_SECRET=<from Google Cloud Console>
GOOGLE_REDIRECT_URI=https://cloud.hansu.tw/api/photo-gallery/auth/callback
LINODE_ACCESS_KEY=<Linode Object Storage key>
LINODE_SECRET_KEY=<Linode Object Storage secret>
LINODE_BUCKET=<bucket name>
LINODE_ENDPOINT=https://<cluster>.linodeobjects.com
SECRET_KEY=<random 32-byte hex string for JWT signing>
BOOTSTRAP_ADMIN_EMAIL=hank0516@gmail.com
MAX_UPLOAD_MB=50
```

### 2. Create database

```bash
mysql -u root -p -e "CREATE DATABASE PhotoGallery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON PhotoGallery.* TO 'hank'@'localhost';"
```

### 3. Backend install & migrate

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head       # creates all tables
uvicorn main:app --port 8002 --reload
```

### 4. Frontend install & dev server

```bash
cd frontend
npm install
npm run dev               # starts Vite dev server at http://localhost:5173
```

---

## Validation Scenarios

### Scenario 1: Authentication

1. Open `http://localhost:5173` in a browser
2. Click "Sign in with Google"
3. Complete Google OAuth (use `hank0516@gmail.com`)
4. **Expected**: Redirected to albums page; `GET /auth/me` returns `is_admin: true`
   (because `BOOTSTRAP_ADMIN_EMAIL` matches)
5. Open an incognito window, sign in with a different Google account
6. **Expected**: "Pending access" screen with no albums visible

### Scenario 2: Create Album & Upload Photos

1. As admin, click "New Album" → name it "Test Album" → save
2. **Expected**: Album appears on home page with placeholder cover
3. Open the album → drag 3 JPEG files onto the upload zone
4. **Expected**: Progress bars appear for each file; after completion, 3 photos appear in grid
5. Check Linode Object Storage bucket
6. **Expected**: `photos/<album_id>/<photo_id>/original.jpg`, `thumb_300.jpg`, `thumb_800.jpg`
   all exist for each uploaded photo

### Scenario 3: View Modes & Lightbox

1. Open an album with at least 10 photos
2. Toggle between small grid / large grid / list view
3. **Expected**: Layout changes immediately without network requests (use browser DevTools Network tab)
4. Click a photo
5. **Expected**: Lightbox opens with full-screen photo; press → to advance to next photo
6. Click "Details"
7. **Expected**: EXIF panel shows (date taken, camera — or "Not available" if no EXIF)

### Scenario 4: Permissions

1. As admin, open Admin Panel → Users
2. Find the second Google account (from Scenario 1) → grant `viewer` role on "Test Album"
3. Switch to the second account in incognito
4. **Expected**: "Test Album" now appears; upload zone is NOT visible
5. Back in admin, change the role to `uploader`
6. Refresh the second account's browser
7. **Expected**: Upload zone now appears in "Test Album"

### Scenario 5: Share Link

1. As admin, open "Test Album" → Generate Share Link → set expiry 1 day from now → copy link
2. Open the link in an incognito window (not logged in)
3. **Expected**: Album photos are visible; no upload/delete controls shown
4. Back in admin, revoke the link
5. Reload the incognito window
6. **Expected**: "Link expired or revoked" message

### Scenario 6: Download

1. In lightbox, click "Download" on a photo
2. **Expected**: Original-quality file downloads to device
3. As admin, click "Download Album" on "Test Album"
4. **Expected**: ZIP file downloads containing all photos

### Scenario 7: Search

1. Add a caption "Golden Pavilion" to a photo
2. Upload another photo without a caption
3. Use the search bar to search "Golden"
4. **Expected**: Only the captioned photo appears in results

---

## Deployment Validation

After running `npm run build` in `frontend/`:

1. Symlink frontend build: `ln -s /home/hank/my_websites/photo-gallery/frontend/dist /var/www/html/sites/photo-gallery`
2. Add Apache config (see `tasks.md` Apache configuration task)
3. Start systemd service: `sudo systemctl start photo-gallery-api`
4. Visit `https://cloud.hansu.tw/sites/photo-gallery/`
5. **Expected**: Login page loads; complete all Validation Scenarios above against production URL
