# Research: iOS Native App

## Auth — Bearer Token Support

- **Decision**: Extend `get_current_user` dependency to read JWT from `Authorization: Bearer <token>` header in addition to the existing `pg_session` cookie.
- **Rationale**: Native app uses `URLSession` which cannot reliably share httpOnly cookies across launches. Storing the JWT in Keychain and sending it as a Bearer header is the standard native pattern. The cookie path continues to work for the Web frontend unchanged.
- **Alternatives considered**: Sharing the cookie via `HTTPCookieStorage` — works within a session but does not survive app termination reliably; `WKWebView`-based OAuth — shares cookies but gives a degraded native experience.

## Auth — OAuth Callback for Native App

- **Decision**: Add a `?redirect=native` query parameter to `/auth/login`. When present, `/auth/callback` redirects to `photogallery://auth/callback?token=<jwt>` instead of the web URL. The native app opens via its registered custom URL scheme and extracts the token.
- **Rationale**: `ASWebAuthenticationSession` handles the Google OAuth flow in a secure in-app browser and captures the custom-scheme redirect automatically. No new OAuth client registration is required — the same Google client is reused.
- **Alternatives considered**: Deep link via Universal Links — requires HTTPS association file on the server; more complex setup for a private app.

## Auth — Token Lifetime & Refresh

- **Decision**: Keep the existing 24-hour JWT expiry. When the app receives a 401, silently re-trigger the OAuth flow (ASWebAuthenticationSession) to obtain a fresh token. For family members, the admin performs this re-auth when needed.
- **Rationale**: Implementing a refresh-token flow requires backend changes (refresh token table, rotation logic). Given the small user base and the admin managing devices, re-auth on 401 is acceptable.
- **Alternatives considered**: Longer-lived tokens (7-day, 30-day) — reduces re-auth frequency but increases risk if a token is compromised.

## Image Caching

- **Decision**: Use **Kingfisher** (Swift package) for thumbnail caching. Disk cache capped at 200 MB with LRU eviction. Original-size images are memory-only (not persisted). Videos are streamed, not cached.
- **Rationale**: Kingfisher is a mature, SwiftUI-native image loading library with built-in disk/memory cache, placeholder support, and smooth lazy loading. Presigned URLs change on every API call, so Kingfisher is configured to use the URL path (minus query string) as the cache key.
- **Alternatives considered**: `AsyncImage` (built-in) — no disk cache, poor performance for grids; `SDWebImageSwiftUI` — equally capable but larger dependency.

## Ad Hoc Distribution

- **Decision**: OTA (Over-the-Air) install page hosted at `https://cloud.hansu.tw/apps/photo-gallery/`. Admin uploads a new IPA + `manifest.plist`; family members tap an `itms-services://` link in Safari to install.
- **Rationale**: OTA requires only HTTPS (already available) and one-time UDID registration per device. Updates are push-free — admin uploads and family installs at their convenience.
- **Alternatives considered**: Xcode direct install — requires physical access every update; TestFlight — 90-day expiry, requires App Store Connect review.

## CORS — Native App Origin

- **Decision**: Native app requests have no `Origin` header (not a browser). The existing CORS middleware on FastAPI passes through requests with no `Origin`, so no CORS change is needed.
- **Rationale**: CORS is a browser-enforced mechanism; `URLSession` does not send `Origin` and is not subject to CORS restrictions.
