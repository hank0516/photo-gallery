# Implementation Plan: iOS Native App

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Swift 5.9+ | |
| UI Framework | SwiftUI | Universal (iOS / iPadOS / macOS) |
| Architecture | MVVM | `@Observable` (iOS 17 Observation framework) |
| Networking | URLSession | Built-in; no third-party HTTP library needed |
| Image caching | Kingfisher | Disk cache 200 MB, cache key = URL path without query string |
| Video playback | AVKit / AVPlayer | Built-in |
| Auth | ASWebAuthenticationSession | Google OAuth → custom URL scheme |
| Keychain | Security framework | Raw `SecItem` API or a thin wrapper |
| Minimum OS | iOS 17, macOS 14 | |
| Xcode | 15+ | |

## Project Structure

```
ios/                                   ← Xcode project root (new directory in repo)
  PhotoGallery.xcodeproj
  PhotoGallery/
    App/
      PhotoGalleryApp.swift            ← @main, URL scheme handler
      AppState.swift                   ← @Observable root state (session, nav)
    Core/
      Network/
        APIClient.swift                ← URLSession wrapper, injects Bearer token
        Endpoints.swift                ← All API endpoint definitions
      Auth/
        AuthService.swift              ← ASWebAuthenticationSession, Keychain R/W
        KeychainHelper.swift
      Cache/
        ImageCache.swift               ← Kingfisher config (disk limit, cache key)
    Models/
      Album.swift
      MediaItem.swift
      EXIF.swift
      SearchResult.swift
      Page.swift                       ← Generic pagination wrapper
    Features/
      Auth/
        LoginView.swift
        LoginViewModel.swift
      Albums/
        AlbumListView.swift
        AlbumListViewModel.swift
        AlbumCard.swift
      AlbumDetail/
        AlbumDetailView.swift
        AlbumDetailViewModel.swift
        MediaGrid.swift
      Viewer/
        MediaViewerView.swift          ← Fullscreen photo/video viewer
        PhotoView.swift                ← Zoomable image
        VideoPlayerView.swift
        EXIFPanel.swift
      Search/
        SearchView.swift
        SearchViewModel.swift
      Unlock/
        UnlockView.swift               ← Password prompt for locked albums
```

## Architecture Rules

- **ViewModels** are `@Observable` classes; Views observe them directly.
- **APIClient** is a singleton injected via SwiftUI `Environment`.
- **AuthService** owns the Keychain token; all other services read from it via `AppState`.
- Presigned URLs are never cached as strings — only the downloaded image data is cached by Kingfisher.
- Each Feature folder is self-contained: View + ViewModel + any feature-local subviews.

## Backend Changes Required

1. `app/core/auth.py` — `get_current_user`: also accept `Authorization: Bearer <token>`.
2. `app/api/auth.py` — `/auth/callback`: when `redirect=native` query param present, redirect to `photogallery://auth/callback?token=<jwt>`.
