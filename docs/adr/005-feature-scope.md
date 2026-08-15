# ADR 005: Native App 功能範圍

**狀態**: 已決定  
**日期**: 2026-08-15

## 背景

後端 API 功能完整（相簿管理、上傳、權限管理、搜尋、下載等）。Native app 不需要全部重做，要明確哪些是 P0、哪些是 nice-to-have、哪些繼續用 Web。

## 決定

### P0 — Viewer 核心功能（第一版必須有）

| 功能 | 對應 API |
|---|---|
| Google 登入 / 登出 | `/auth/login`, `/auth/callback`, `/auth/logout` |
| 相簿列表（只顯示有權限的） | `GET /albums` |
| 相簿內照片 / 影片 Grid | `GET /albums/{id}` |
| Lightbox 全螢幕瀏覽（滑動 / 縮放）| presigned URL |
| 影片播放（AVPlayer） | presigned URL |
| 照片 EXIF 資訊面板 | `GET /photos/{id}` |
| 下載單張照片到 Camera Roll | `GET /photos/{id}/download` |
| 搜尋（關鍵字 / 日期） | `GET /search` |
| 鎖定相簿密碼解鎖 | `POST /albums/{id}/unlock` |

### P2 — Admin 功能（第一版後，nice-to-have）

| 功能 | 說明 |
|---|---|
| 上傳照片 / 影片 | 從 Camera Roll 或相機直接上傳 |
| 建立 / 編輯相簿 | 含名稱、描述、鎖定設定 |
| 管理成員權限 | 新增 / 移除 viewer / uploader |

### 不在 Native App 內（Web 操作即可）

- 相簿 ZIP 下載（Admin 功能，Web 版已完成）
- 分享連結管理
- Audit log 查看

## 原因

第一版目標是讓家人能流暢瀏覽，Admin 功能對開發者而言 Web 版完全夠用，不值得為了 nice-to-have 拖延上線。
