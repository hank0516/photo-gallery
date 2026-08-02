# Research: Private Photo Gallery

**Phase**: 0 | **Date**: 2026-08-02

---

## Decision 1: Google OAuth 2.0 Integration (Backend)

**Decision**: Use `authlib` library with FastAPI's dependency injection for the OAuth flow.

**Rationale**: `authlib` is the most maintained Python OAuth2 client, has first-class Google
support, and integrates cleanly with Starlette (FastAPI's foundation). The flow:
1. Frontend redirects user to `/api/photo-gallery/auth/login` (backend generates Google auth URL)
2. Google redirects back to `/api/photo-gallery/auth/callback`
3. Backend exchanges code for Google tokens, fetches user profile, creates/updates DB user record
4. Backend issues a signed JWT to the frontend (stored in `httpOnly` cookie or `localStorage`)

**Alternatives considered**:
- `google-auth` library: lower-level, requires more manual wiring
- Frontend-only OAuth (implicit flow): deprecated by Google; backend flow is more secure

---

## Decision 2: Session Management

**Decision**: JWT access tokens stored in `httpOnly` cookies.

**Rationale**: `httpOnly` cookies are not accessible to JavaScript (mitigates XSS), are sent
automatically by the browser (no manual header management), and work well with SPA architectures.
Token payload contains: `user_id`, `email`, `is_admin`, `exp` (24h expiry).

**Alternatives considered**:
- `localStorage` JWT: simpler but XSS-vulnerable
- Server-side sessions (Redis): requires Redis dependency and session store management; overkill
  for < 50 users

---

## Decision 3: Linode Object Storage Integration

**Decision**: Use `boto3` with a custom endpoint pointing to Linode's S3-compatible API.

**Rationale**: Linode Object Storage is fully S3-compatible. `boto3` is the standard Python AWS
SDK and works with any S3-compatible storage by setting `endpoint_url`. This avoids a separate
Linode-specific SDK.

**Configuration**:
```
endpoint_url = https://<cluster>.linodeobjects.com
aws_access_key_id = LINODE_ACCESS_KEY
aws_secret_access_key = LINODE_SECRET_KEY
bucket = LINODE_BUCKET
```

**Object key structure**:
```
photos/<album_id>/<photo_id>/original.<ext>
photos/<album_id>/<photo_id>/thumb_300.<ext>
photos/<album_id>/<photo_id>/thumb_800.<ext>
```

**URL access**: Generate pre-signed URLs (15-minute expiry) for all media access. This ensures
storage credentials are never exposed to the browser.

**Alternatives considered**:
- Linodeclient Python SDK: does not support object storage directly
- Public bucket URLs: exposes all photos without auth control — violates Constitution II + IV

---

## Decision 4: Thumbnail Generation

**Decision**: Synchronous Pillow processing on upload, before returning the API response.

**Rationale**: For a small system (< 50 users, infrequent uploads), synchronous thumbnail
generation is simpler and avoids a background job queue. A 10 MB JPEG typically generates
thumbnails in < 2 seconds with Pillow.

**Thumbnail sizes**:
- `thumb_300`: 300px on the longest side (small grid view, album covers)
- `thumb_800`: 800px on the longest side (large grid view, lightbox loading state)
- Original: stored as-is (lightbox full view, download)

**Format**: Convert HEIC → JPEG on server-side (using `pillow-heif`). Preserve JPEG/PNG/WEBP as-is.

**Alternatives considered**:
- Celery + Redis async tasks: necessary at scale, but adds complexity for this use case
- Client-side thumbnail generation: cannot guarantee consistency and adds frontend complexity

---

## Decision 5: Frontend Framework & Build

**Decision**: Vue 3 + Vite, deployed as a static SPA served by Apache.

**Rationale**: Vue 3 has a gentler learning curve than React, excellent documentation, and ships
with Composition API for clean reactive state. Vite provides fast development HMR and optimized
production builds. The built `dist/` folder is symlinked under `/var/www/html/sites/photo-gallery/`
following the existing server pattern.

**State management**: Pinia (Vue 3's official store) — simpler API than Vuex.

**HTTP client**: Axios — consistent error handling, automatic JSON parsing, request interceptors
for attaching auth cookies.

**Alternatives considered**:
- React: higher learning curve for the project owner who has limited frontend experience
- Plain HTML + Alpine.js: insufficient for lightbox, drag-drop upload, and reactive photo grids

---

## Decision 6: Database Schema Approach

**Decision**: Use SQLAlchemy 2 ORM with Alembic for migrations on the existing MariaDB instance.

**Rationale**: Consistent with the existing `expense-tracker` approach (SQLAlchemy on MariaDB).
Alembic provides version-controlled schema migrations. A new database `PhotoGallery` is created
to avoid conflicts with `AccountingBook`.

**Alternatives considered**:
- Separate MariaDB instance: unnecessary overhead for a single-server setup
- SQLite: not suitable for concurrent access and lacks production reliability for long-term use

---

## Decision 7: Apache Integration

**Decision**: New systemd service `photo-gallery-api` on port **8002**. Apache proxies:
- `/api/photo-gallery/` → `http://127.0.0.1:8002/api/photo-gallery/`
- `/sites/photo-gallery/` → static SPA files (Vue build output)

**Rationale**: Follows the exact same pattern as `expense-tracker` (port 8000) and `dynamic-api`
(port 8001). No conflicts with existing services.

**SPA routing**: Apache `FallbackResource /sites/photo-gallery/index.html` so that Vue Router
deep links work correctly (same pattern as `mdeditor`).

---

## Decision 8: Share Links

**Decision**: Generate a random UUID token stored in the `share_links` table with an expiry
timestamp. No login required for share link access; the token itself is the credential.

**Rationale**: Simple and stateless — no session management needed for shared views.
The share link endpoint checks: token exists + not revoked + not expired + album not deleted.

**Alternatives considered**:
- Signed JWT share tokens: no DB lookup needed, but cannot be revoked before expiry
