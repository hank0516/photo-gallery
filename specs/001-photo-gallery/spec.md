# Feature Specification: Private Photo Gallery

**Feature Branch**: `001-photo-gallery`

**Created**: 2026-08-02

**Status**: Draft

**Input**: User description: "A private photo gallery website with Google login, album management,
photo upload, multiple view modes (thumbnail/grid/list), per-user permissions per album, and
Linode Object Storage for photos."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Authenticate & Access (Priority: P1)

A user visits the gallery URL and is shown a login page. They click "Sign in with Google," complete
the OAuth flow, and are redirected back to the gallery. If they have been granted access by an
admin, they see their permitted albums. If they have not been granted access yet, they see a
"Pending access" message.

**Why this priority**: Without authentication, nothing else works. This is the entry gate to the
entire system.

**Independent Test**: Can be fully tested by visiting the site, completing Google login, and
verifying that a known-permitted user sees albums while an unpermitted user sees the access-pending
screen.

**Acceptance Scenarios**:

1. **Given** a user is not logged in, **When** they visit any page, **Then** they are redirected to
   the login page.
2. **Given** a user clicks "Sign in with Google," **When** they complete the OAuth flow,
   **Then** they are returned to the gallery and their identity is recognized.
3. **Given** a user has logged in but has no permissions, **When** they view the home page,
   **Then** they see a clear "waiting for access" message and no albums.
4. **Given** a logged-in user closes the browser and returns later, **When** the session is still
   valid, **Then** they remain logged in without repeating the OAuth flow.

---

### User Story 2 — Browse Albums & Photos (Priority: P2)

A permitted user opens the gallery, sees all albums they have access to displayed as a grid of
cover photos. They click an album and see its photos. They can switch between view modes:
small thumbnails grid, large thumbnails grid, and list view. They click a photo to open a
full-screen lightbox, then navigate left/right between photos.

**Why this priority**: Viewing is the primary day-to-day use case for most users.

**Independent Test**: Can be tested by seeding albums and photos into the system, then verifying
all view modes and lightbox work correctly for a viewer-role user.

**Acceptance Scenarios**:

1. **Given** a user has viewer access to 3 albums, **When** they open the gallery home,
   **Then** they see exactly those 3 albums with their cover photo and name.
2. **Given** a user opens an album, **When** the album loads, **Then** photos are displayed in
   small-thumbnail grid mode by default.
3. **Given** a user is in small-thumbnail mode, **When** they switch to large-thumbnail mode,
   **Then** the photos re-render at a larger size without a page reload.
4. **Given** a user clicks a photo, **When** the lightbox opens, **Then** the photo fills most
   of the screen and the user can navigate left/right with arrow keys or buttons.
5. **Given** a user has no access to an album, **When** they try to access it directly via URL,
   **Then** they see a "not found or no access" error.

---

### User Story 3 — Upload Photos (Priority: P3)

A user with uploader or admin permission opens an album and uploads one or more photos. They can
drag files onto the upload area or click to select. A progress bar shows upload status for each
file. After upload, new photos appear in the album immediately.

**Why this priority**: Without upload, the gallery has no content. This is the primary write action.

**Independent Test**: Can be tested by opening an album with uploader permissions and uploading
single and multiple files, then verifying they appear and are viewable.

**Acceptance Scenarios**:

1. **Given** a user has uploader access, **When** they open an album, **Then** they see an upload
   area (drag-drop zone and file selector button).
2. **Given** a user drags 5 photos onto the upload zone, **When** upload begins, **Then** each
   file shows its own progress indicator.
3. **Given** all uploads complete, **When** the user looks at the album, **Then** the 5 new photos
   appear without manually refreshing the page.
4. **Given** a user uploads a photo, **When** it is processed, **Then** the system automatically
   creates thumbnail previews for that photo.
5. **Given** a user has only viewer access, **When** they open an album, **Then** no upload area
   is shown.

---

### User Story 4 — Manage Albums (Priority: P4)

An admin or authorized user creates a new album with a name, optional description, and optional
cover photo. They can later rename the album, change its cover, update its description, or delete
it (along with all its photos).

**Why this priority**: Albums are the organizing structure for all photos.

**Independent Test**: Can be tested by creating, editing, and deleting albums through the UI and
verifying state changes persist correctly.

**Acceptance Scenarios**:

1. **Given** an admin is logged in, **When** they click "New Album," **Then** they can enter a
   name, optional description, and optional album date; the album is created.
2. **Given** an admin enters a title containing a date in `yyyy-mm-dd` or `yyyy.mm.dd` format,
   **When** the album is created, **Then** the system automatically populates the album date from
   the title without requiring the admin to enter it separately.
3. **Given** an admin enters a title with no recognisable date, **When** the create form is shown,
   **Then** a date picker field is presented so the admin can set the album date manually.
4. **Given** an album exists, **When** an admin edits it, **Then** changes to name, description,
   cover photo, and album date are saved and reflected immediately.
5. **Given** an admin deletes an album, **When** they confirm the action, **Then** the album and
   all its photos are permanently removed.
6. **Given** a non-admin user, **When** they view the albums list, **Then** they do not see
   create/edit/delete controls.
7. **Given** albums with various dates, **When** a user views the albums homepage, **Then** albums
   are grouped by year with year headers, sorted by album date descending (newest first) by default;
   albums with no date appear in an "未分類" section at the end.
8. **Given** the albums homepage, **When** a user clicks the sort direction toggle, **Then** the
   year groups and albums within each group reverse order (ascending ↔ descending), and the toggle
   visually reflects the current direction.

---

### User Story 5 — Manage Users & Permissions (Priority: P5)

An admin opens the admin panel and sees a list of users who have ever logged in. For each user,
the admin can assign or revoke access to specific albums and set their role (viewer or uploader).
The admin can also promote another user to admin.

**Why this priority**: Access control is fundamental to privacy. Without this, the system cannot
enforce who sees what.

**Independent Test**: Can be tested by having a second test user log in, then granting and revoking
album access from the admin panel and verifying the second user's visible albums change accordingly.

**Acceptance Scenarios**:

1. **Given** an admin opens the admin panel, **When** it loads, **Then** they see a list of all
   users who have signed in.
2. **Given** an admin selects a user, **When** they assign viewer role to an album, **Then** that
   user can immediately see that album after their next page load.
3. **Given** an admin revokes a user's access to an album, **When** the user refreshes,
   **Then** that album no longer appears for them.
4. **Given** an admin promotes another user to admin, **When** that user logs in, **Then**
   they have full admin capabilities.

---

### User Story 6 — Photo Details & EXIF (Priority: P6)

A user opens a photo in the lightbox and can see its metadata: filename, upload date, and EXIF
data if available (date taken, camera model, location if embedded). They can also add or edit a
caption for the photo.

**Why this priority**: Enhances the browsing experience; useful for remembering when and where
photos were taken.

**Independent Test**: Can be tested by uploading a photo with known EXIF data and verifying the
details panel shows correct information.

**Acceptance Scenarios**:

1. **Given** a user opens a photo with EXIF data in the lightbox, **When** they expand the
   details panel, **Then** they see date taken, camera model, and GPS location (if present).
2. **Given** a user with uploader/admin access, **When** they add a caption to a photo,
   **Then** the caption is saved and displayed under the photo in the lightbox.

---

### User Story 7 — Share Album (Priority: P7)

An admin generates a shareable link for an album. The link has an expiry date. Anyone with the
link can view that album's photos without needing to log in (read-only, no upload or delete).

**Why this priority**: Occasionally useful for sharing with people who don't have gallery accounts
(e.g., sharing holiday photos with family).

**Independent Test**: Can be tested by generating a share link, opening it in an incognito window,
and verifying read-only photo access.

**Acceptance Scenarios**:

1. **Given** an admin generates a share link for an album with a 7-day expiry, **When** someone
   opens the link before it expires, **Then** they see the album photos without logging in.
2. **Given** a share link has expired, **When** someone opens it, **Then** they see a clear
   "link expired" message.
3. **Given** a shared album view, **When** the visitor tries to upload or delete photos,
   **Then** those actions are not available.

---

### User Story 8 — Download Photos (Priority: P8)

A user can download an individual photo at its original quality. An admin or uploader can also
download an entire album as a zip file.

**Why this priority**: Common expectation for any photo management tool.

**Independent Test**: Can be tested by downloading a single photo and verifying it matches the
original upload, then downloading an album zip and verifying all photos are included.

**Acceptance Scenarios**:

1. **Given** a user views a photo in the lightbox, **When** they click "Download," **Then** the
   original-quality photo file is downloaded to their device.
2. **Given** an admin or uploader views an album, **When** they click "Download Album,"
   **Then** a zip file containing all photos in the album is downloaded.

---

### User Story 9 — Search & Filter (Priority: P9)

A user can search for photos by keyword (caption, filename), filter by date range, or filter by
album. Results are shown as a photo grid.

**Why this priority**: As the gallery grows, finding specific photos becomes important.

**Independent Test**: Can be tested by uploading photos with known captions/dates and verifying
search returns the correct results.

**Acceptance Scenarios**:

1. **Given** a user searches for a keyword, **When** results load, **Then** only photos whose
   caption or filename matches are shown.
2. **Given** a user filters by date range, **When** results load, **Then** only photos taken or
   uploaded within that range appear.

---

### User Story 10 — Activity Audit Log (Priority: P10)

The system silently records every Google login and every API request to the database. Records
include timestamp, email, API path, HTTP method, status code, response time, and client IP.
This allows the admin to review access history and diagnose issues without relying solely on
server logs.

**Why this priority**: Operational visibility and security auditing; useful for understanding
usage patterns and detecting unauthorized access attempts.

**Independent Test**: Log in with a test account, make several API calls, then query the
`login_logs` and `request_logs` tables directly to verify records are present and fields are
populated correctly.

**Acceptance Scenarios**:

1. **Given** a user completes Google OAuth, **When** the callback succeeds, **Then** a record is
   inserted in `login_logs` with the user's email, user_id, IP address, user agent, and timestamp.
2. **Given** any API request is made, **When** it completes, **Then** a record is inserted in
   `request_logs` with method, path, status code, response time, IP, and (if authenticated)
   the user's email and user_id.
3. **Given** an unauthenticated request, **When** it is logged, **Then** `user_id` and `email`
   are NULL but all other fields are populated.
4. **Given** a logging error occurs, **When** the record cannot be written, **Then** the original
   API response is still returned to the client (logging must not affect normal operation).

---

### Edge Cases

- What happens when a user tries to upload a non-image file (e.g., PDF, video)?
- How does the system handle an upload that fails midway (network error)?
- What if an album is deleted while another user is viewing it?
- What if a share link is accessed after the album has been deleted?
- What happens if EXIF data contains a GPS location that the owner would prefer private?
- What if a user uploads a photo that is identical to one already in the album?
- How does the system behave if Linode Object Storage is temporarily unavailable?
- What is the maximum upload file size?

---

## Requirements *(mandatory)*

### Functional Requirements

**Authentication & Access**
- **FR-001**: The system MUST require Google OAuth 2.0 login before granting access to any page or resource.
- **FR-002**: The system MUST deny access to users who have not been granted a role by an admin, and MUST display a "pending access" message to such users.
- **FR-003**: The system MUST maintain user sessions so that users do not need to re-authenticate on every visit within the session validity period.
- **FR-004**: The system MUST record every user who signs in via Google, even if they have no permissions yet.

**Album Management**
- **FR-005**: Admin users MUST be able to create albums with a name, optional description, optional cover photo, and optional album date.
- **FR-006**: Admin users MUST be able to edit an album's name, description, cover photo, and album date.
- **FR-007**: Admin users MUST be able to delete an album, which permanently removes the album and all its photos.
- **FR-008**: Albums MUST display a cover photo (or a placeholder if none is set) in the albums listing view.
- **FR-037**: When creating an album, the system MUST automatically parse the album date from the title if the title begins with a date in `yyyy-mm-dd` or `yyyy.mm.dd` format; otherwise the admin is prompted to enter the date manually via a date picker.
- **FR-038**: The albums homepage MUST group albums by year, with each year displayed as a section header. Within each year, albums are sorted by album date. A toggle allows switching between descending (newest first, default) and ascending (oldest first) order. Albums without an album date are grouped under a separate "未分類" section at the end regardless of sort order.

**Photo Upload & Storage**
- **FR-009**: Users with uploader or admin role MUST be able to upload one or more photos at a time via drag-and-drop or file selection.
- **FR-010**: The system MUST display per-file upload progress during multi-file uploads.
- **FR-011**: The system MUST automatically generate at least two thumbnail sizes for every uploaded photo.
- **FR-012**: The system MUST store all original photos and thumbnails on Linode Object Storage; no media files may be stored on the application server.
- **FR-013**: The system MUST reject uploads of non-image file types and display a clear error message.
- **FR-014**: The system MUST enforce a maximum file size per upload (default: 50 MB per file).
- **FR-015**: The system MUST extract and store available EXIF metadata from uploaded photos.

**Photo Browsing & Viewing**
- **FR-016**: The system MUST offer at least three view modes for album contents: small-thumbnail grid, large-thumbnail grid, and list view.
- **FR-017**: The system MUST remember the user's last selected view mode across sessions.
- **FR-018**: Clicking a photo MUST open a full-screen lightbox viewer.
- **FR-019**: The lightbox MUST support left/right navigation between photos via buttons and keyboard arrow keys.
- **FR-020**: The lightbox MUST display the photo's caption (if set) and EXIF metadata (if available) in an expandable details panel.

**Photo Management**
- **FR-021**: Admin and uploader users MUST be able to add or edit a caption for any photo in albums they have access to.
- **FR-022**: Admin users MUST be able to delete individual photos from an album.
- **FR-023**: Users MUST be able to download an individual photo at its original quality.
- **FR-024**: Admin and uploader users MUST be able to download an entire album as a zip archive.

**Permissions**
- **FR-025**: Admins MUST be able to assign one of three roles per user per album: `viewer`, `uploader`, or `admin`.
- **FR-026**: Users with no role on an album MUST NOT be able to see or access that album by any means, including direct URL.
- **FR-027**: Admins MUST be able to revoke a user's role on any album at any time, with immediate effect.
- **FR-028**: The system MUST support at least one global admin role that grants management access across all albums.

**Sharing**
- **FR-029**: Admins MUST be able to generate a time-limited shareable link for any album.
- **FR-030**: Share links MUST provide read-only access (view and download only) without requiring login.
- **FR-031**: Share links MUST become inaccessible after their expiry date/time.
- **FR-032**: Admins MUST be able to revoke a share link before its expiry.

**Search**
- **FR-033**: Users MUST be able to search for photos by keyword across captions and filenames.
- **FR-034**: Users MUST be able to filter photos by date range (upload date or date taken).

**Storage & Performance**
- **FR-035**: The system MUST display a storage usage summary (total used, per album) visible to admins.
- **FR-036**: All photo grid views MUST use lazy loading so that only visible thumbnails are requested.

**Audit Logging**
- **FR-039**: The system MUST record every successful Google OAuth login in a `login_logs` table, including: user_id, email, IP address, user agent, and timestamp.
- **FR-040**: The system MUST record every API request in a `request_logs` table, including: user_id (nullable), email (nullable), HTTP method, path, status code, response time (ms), IP address, and timestamp.
- **FR-041**: Logging failures MUST NOT affect the response returned to the client.

---

### Key Entities

- **User**: A person who has authenticated via Google OAuth. Has a name, email, Google ID, and
  admin flag. May have roles assigned on zero or more albums.

- **Album**: A named collection of photos. Has a name, description, cover photo, creation date,
  and owner. Can have multiple users with different roles.

- **Photo**: An image file stored in object storage. Belongs to one album. Has a filename, upload
  date, caption, EXIF metadata, original storage path, and thumbnail paths.

- **Permission**: A record linking a User to an Album with a specific role (`viewer`, `uploader`,
  `admin`).

- **ShareLink**: A time-limited token granting read-only access to a specific album without login.
  Has an expiry date and a revoked flag.

- **LoginLog**: A record of a completed Google OAuth login. Has user_id (FK), email, IP address,
  user agent, and timestamp.

- **RequestLog**: A record of a single API request. Has user_id (nullable FK), email (nullable),
  HTTP method, path, status code, response time in ms, IP address, and timestamp.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can complete Google login and reach the albums page in under 15 seconds on a standard broadband connection.
- **SC-002**: An album with 200 photos loads its thumbnail grid in under 3 seconds, with additional photos loading progressively as the user scrolls.
- **SC-003**: A 10 MB photo upload completes and appears in the album in under 30 seconds on a standard broadband connection.
- **SC-004**: Switching between view modes (small grid / large grid / list) takes less than 0.5 seconds with no additional network requests.
- **SC-005**: Permission changes made by an admin take effect within 5 seconds without requiring the affected user to log out and back in.
- **SC-006**: A share link accessed by an unauthenticated user loads the shared album in under 5 seconds.
- **SC-007**: Search results across a library of 1,000 photos return in under 2 seconds.
- **SC-008**: 100% of non-image file upload attempts are rejected with a clear error message before the file is transmitted to storage.

---

## Assumptions

- All users are trusted individuals known to the admin; there is no public self-registration flow.
- The system is used by a small team (under 50 users); it does not need to support thousands of concurrent users.
- Mobile-responsive design is required (the site must be usable on a phone), but a dedicated mobile app is out of scope.
- Video files are out of scope for v1; only still image formats (JPEG, PNG, WEBP, HEIC, GIF) are supported.
- The admin is also the person who manages the server (i.e., Hank), so the first admin account can be bootstrapped via server configuration rather than an in-app flow.
- Bulk photo operations (move photos between albums, bulk delete) are out of scope for v1.
- Photo editing (crop, rotate, filters) is out of scope for v1.
- GPS location from EXIF is displayed as coordinates or a map link; no embedded map rendering is required for v1.
- The system will be accessed only over HTTPS; HTTP access is not a concern.
