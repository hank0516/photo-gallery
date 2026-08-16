# iOS App 開發規格書

**最後更新**：2026-08-16  
**對應後端版本**：master branch（cloud.hansu.tw）  
**iOS 最低支援**：iOS 17 / macOS 14  
**Xcode**：16.4+

---

## 1. 架構總覽

| 層 | 技術 |
|---|---|
| 語言 | Swift 5.9+ |
| UI | SwiftUI Universal App（iPhone/iPad/macOS） |
| 架構 | MVVM，`@Observable`（iOS 17 Observation framework） |
| 網路 | URLSession（`APIClient` singleton） |
| 圖片快取 | Kingfisher 8.11.0 |
| 影片播放 | AVKit / AVPlayer |
| 認證 | ASWebAuthenticationSession + Keychain |

---

## 2. 認證

### 流程
1. `/auth/login?redirect=native` → 開啟 `ASWebAuthenticationSession`
2. Google OAuth 完成後 → 後端 redirect 到 `photogallery://auth/callback?token=<jwt>`
3. app 從 URL 取出 JWT → 存入 Keychain（key: `pg_session`，service: `tw.hansu.photogallery`）
4. 每次 API request 加入 Header：`Authorization: Bearer <token>`
5. 收到 401 → 清除 Keychain token → 導回登入頁

### JWT
- 演算法：HS256
- 有效期：24 小時
- Payload 包含：`user_id`（Int）、`email`（String）、`is_admin`（Bool）、`exp`

### 後端同時支援
- Cookie `pg_session`（Web 前端用）
- `Authorization: Bearer` Header（Native app 用）

---

## 3. API 規格

**Base URL**：`https://cloud.hansu.tw/api/photo-gallery`

### 3.1 Auth

| Method | Path | 說明 |
|---|---|---|
| GET | `/auth/login?redirect=native` | 啟動 Google OAuth |
| GET | `/auth/callback` | OAuth callback，`redirect=native` 時 redirect 到 custom scheme |
| POST | `/auth/logout` | 登出（清除 cookie） |
| GET | `/auth/me` | 取得目前使用者資訊 |

**GET /auth/me 回傳：**
```json
{
  "id": 1,
  "email": "user@gmail.com",
  "name": "Han Su",
  "avatar_url": "https://...",
  "is_admin": true
}
```

---

### 3.2 Albums

| Method | Path | 說明 | 權限 |
|---|---|---|---|
| GET | `/albums` | 相簿列表 | 登入 |
| POST | `/albums` | 建立相簿 | admin |
| GET | `/albums/{id}` | 相簿詳情 + 照片分頁 | 有權限 |
| PATCH | `/albums/{id}` | 修改相簿 | admin |
| DELETE | `/albums/{id}` | 軟刪除相簿 | admin |
| POST | `/albums/{id}/unlock` | 解鎖加密相簿 | 有權限 |
| GET | `/albums/{id}/permissions` | 列出成員 | admin |
| PUT | `/albums/{id}/permissions/{user_id}` | 新增/修改成員 | admin |
| DELETE | `/albums/{id}/permissions/{user_id}` | 移除成員 | admin |
| GET | `/albums/{id}/download-zip` | 下載整個相簿 ZIP | admin/uploader |

**GET /albums 回傳（陣列）：**
```json
{
  "id": 1,
  "name": "2026.07.28 嘉義旺萊山",
  "description": "...",
  "album_date": "2026-07-28",
  "cover_thumb_url": "https://presigned...",
  "photo_count": 18,
  "my_role": "admin",
  "is_locked": false,
  "created_at": "2026-07-28T10:00:00"
}
```

**GET /albums/{id} 查詢參數：**
- `page`（預設 1）
- `per_page`（預設 50）
- `sort`：`uploaded_at`（預設）或 `exif_date_taken`
- `order`：`desc`（預設）或 `asc`
- `unlock_token`：加密相簿解鎖後的 token（加在 Query String）

**GET /albums/{id} 回傳：**
```json
{
  "album": {
    "id": 1, "name": "...", "description": "...",
    "album_date": "2026-07-28", "cover_thumb_url": "...",
    "photo_count": 18, "my_role": "admin",
    "is_locked": false, "created_at": "..."
  },
  "photos": [
    {
      "id": 101,
      "filename": "IMG_001.jpg",
      "caption": null,
      "mime_type": "image/jpeg",
      "thumb_300_url": "https://presigned...",
      "thumb_800_url": "https://presigned...",
      "width": 4032,
      "height": 3024,
      "exif_date_taken": "2026-07-28T14:30:00"
    }
  ],
  "total": 18,
  "page": 1,
  "per_page": 50,
  "locked": false
}
```

**注意**：`mime_type` 可能為 `null`（影片處理中或舊資料）

**加密相簿未解鎖時回傳：**
```json
{
  "album": { ... },
  "photos": [],
  "total": 0,
  "page": 1,
  "per_page": 50,
  "locked": true
}
```

**POST /albums 請求：**
```json
{
  "name": "相簿名稱",
  "description": "選填",
  "album_date": "2026-07-28"
}
```

**POST /albums/{id}/unlock 請求/回傳：**
```json
// 請求
{ "password": "密碼" }

// 回傳（成功）
{ "unlock_token": "<jwt>" }

// 回傳（失敗）
{ "detail": "密碼錯誤" }  // HTTP 401
```

---

### 3.3 Photos

| Method | Path | 說明 | 權限 |
|---|---|---|---|
| POST | `/albums/{id}/photos` | 上傳照片/影片 | admin/uploader |
| GET | `/photos/{id}` | 照片詳情 + original URL | 有權限 |
| PATCH | `/photos/{id}` | 修改 caption | admin/uploader |
| DELETE | `/photos/{id}` | 軟刪除照片 | admin |
| GET | `/photos/{id}/download` | 下載（presigned Content-Disposition URL） | 有權限 |

**GET /photos/{id} 回傳：**
```json
{
  "id": 101,
  "album_id": 1,
  "filename": "IMG_001.jpg",
  "mime_type": "image/jpeg",
  "caption": null,
  "original_url": "https://presigned...",
  "thumb_300_url": "https://presigned...",
  "thumb_800_url": "https://presigned...",
  "file_size_bytes": 3145728,
  "width": 4032,
  "height": 3024,
  "exif_date_taken": "2026-07-28T14:30:00",
  "exif_camera": "iPhone 15 Pro",
  "exif_gps_lat": 25.0330199,
  "exif_gps_lon": 121.5654399,
  "uploaded_at": "2026-07-28T10:00:00",
  "uploaded_by": { "id": 1, "name": "Han Su" },
  "my_role": "admin"
}
```

**注意欄位名稱：**
- EXIF 相機：`exif_camera`（不是 `exif_camera_model`）
- EXIF GPS：`exif_gps_lat` / `exif_gps_lon`（不是 `exif_latitude` / `exif_longitude`）
- `mime_type` 可能為 `null`

**POST /albums/{id}/photos（Multipart Form Data）：**

| Field | Type | 說明 |
|---|---|---|
| `file` | File | 照片或影片檔案 |
| `caption` | String | 選填，預設空字串 |

回傳（成功）：
```json
{
  "id": 102,
  "thumb_300_url": "https://presigned...",
  "thumb_800_url": "https://presigned...",
  "mime_type": "image/jpeg",
  "filename": "photo.jpg",
  "caption": null,
  "width": 4032,
  "height": 3024,
  "exif_date_taken": "...",
  "uploaded_at": "..."
}
```

影片上傳回傳時 `thumb_300_url` / `thumb_800_url` 可能為 `null`（背景非同步處理中）。

---

### 3.4 Search

**GET /search 查詢參數：**

| 參數 | 型別 | 說明 |
|---|---|---|
| `q` | String | 關鍵字（filename 或 caption，模糊搜尋） |
| `album_id` | Int | 限定相簿 |
| `date_from` | String | `YYYY-MM-DD`，exif_date_taken 起始 |
| `date_to` | String | `YYYY-MM-DD`，exif_date_taken 結束 |
| `page` | Int | 預設 1 |
| `per_page` | Int | 預設 50，最大 200 |

**GET /search 回傳：**
```json
{
  "photos": [
    {
      "id": 101,
      "filename": "IMG_001.jpg",
      "mime_type": "image/jpeg",
      "caption": null,
      "thumb_300_url": "https://...",
      "thumb_800_url": "https://...",
      "exif_date_taken": "...",
      "width": 4032,
      "height": 3024,
      "album_id": 1,
      "album_name": "2026.07.28 嘉義旺萊山"
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 50
}
```

**注意**：回傳 key 是 `photos`，不是 `results`。

---

### 3.5 Users（Admin only）

**GET /users 回傳（陣列）：**
```json
{
  "id": 1,
  "email": "user@gmail.com",
  "name": "Han Su",
  "picture": "https://...",
  "is_admin": true
}
```

---

## 4. 檔案上傳限制

| 類型 | 最大大小 | 備註 |
|---|---|---|
| 圖片（JPG/PNG/WebP/HEIC）| **50 MB** | 後端設定 `max_upload_mb=50` |
| 影片（MP4/MOV/WebM/AVI）| **500 MB** | 後端設定 `max_video_mb=500` |

**影片處理**：上傳後後端立即回應 HTTP 201，thumbnail 由 ffmpeg 在背景非同步生成（最多 60 秒），期間 `thumb_300_url` / `thumb_800_url` 為 `null`。

---

## 5. URLSession Timeout 設定

| Session | Request Timeout | Resource Timeout | 用途 |
|---|---|---|---|
| `URLSession.shared` | 60 秒（系統預設）| 7 天（系統預設）| 一般 API 請求 |
| `APIClient.uploadSession` | **300 秒** | **600 秒** | 照片/影片上傳 |

---

## 6. 圖片快取（Kingfisher）

- 磁碟快取上限：**200 MB**（LRU 淘汰）
- Cache Key：去除 Query String 的 URL path（避免 presigned URL 輪換造成 cache miss）
- 縮圖快取：積極，長期保留
- 原圖（original_url）：下載後用完即棄，不寫入磁碟快取
- 影片：不快取，每次重新串流

**Presigned URL 有效期**：900 秒（15 分鐘）

---

## 7. Progressive Image Loading（Viewer）

1. 立刻顯示 `thumb_800_url`（已在相簿列表時預載）
2. 非同步呼叫 `GET /photos/{id}` 取得 `original_url`
3. Kingfisher 在背景下載原圖，完成後 `.fade(duration: 0.25)` 淡入
4. 切換照片時舊的 task 自動取消（`.task(id: photo.id)`）

---

## 8. 權限模型

| 角色 | 相簿列表 | 瀏覽 | 上傳 | 管理成員 | 刪除相簿/照片 |
|---|---|---|---|---|---|
| viewer | 有權限的相簿 | ✅ | ❌ | ❌ | ❌ |
| uploader | 有權限的相簿 | ✅ | ✅ | ❌ | ❌ |
| admin | 全部 | ✅ | ✅ | ✅ | ✅ |

**iOS app**：admin 功能（建立相簿、上傳、成員管理、刪除）僅在 `AppState.session?.isAdmin == true` 時顯示。

**加密相簿**：`is_locked: true` 的相簿在 app 中預設隱藏（MVP 決策，unlock flow 為 post-MVP）。

---

## 9. 音訊設定

影片播放時設定 `AVAudioSession.category = .playback`，確保靜音鍵不影響影片聲音。

---

## 10. Ad Hoc 發佈

- Apple Developer Program：Han Su（個人帳號）
- Bundle ID：`tw.hansu.photogallery`
- 發佈方式：OTA（itms-services://），manifest.plist 放於 `cloud.hansu.tw/apps/photo-gallery/`
- 裝置登記上限：100 台/年
- Trust 設定（安裝後一次）：設定 → 一般 → VPN 與裝置管理 → 信任開發者

---

## 11. 已知問題 / 待實作

| 項目 | 狀態 |
|---|---|
| EXIF 面板（拍攝時間/相機/GPS）| post-MVP |
| 儲存照片到 Camera Roll | post-MVP |
| 搜尋（關鍵字/日期）| post-MVP |
| 加密相簿解鎖流程 | post-MVP |
| iPad NavigationSplitView | post-MVP |
| 影片上傳進度顯示 | 待改善 |
| 上傳後即時顯示新照片（不需重新整理）| 待改善 |
