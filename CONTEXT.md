# Photo Gallery — Domain Context

## 這個系統是什麼

一個私人家庭相簿平台。管理者（開發者本人）負責上傳、整理相簿、管理成員權限。家人（viewer）透過 app 瀏覽相片和影片。

---

## 核心使用者

| 角色 | 裝置 | 主要動作 |
|---|---|---|
| **Admin**（開發者） | iPhone / iPad / MacBook | 上傳照片、建立相簿、管理成員、看所有相簿 |
| **Viewer**（家人） | iPhone / iPad（主）| 瀏覽有權限的相簿、看照片影片、下載單張、搜尋 |

家人大多是老人家，不熟悉瀏覽器操作。App icon 是他們最熟悉的入口。

---

## 現有系統（Web）

| 層 | 技術 |
|---|---|
| 後端 API | FastAPI (Python)，部署於 `https://cloud.hansu.tw/api/photo-gallery/` |
| 資料庫 | PostgreSQL + SQLAlchemy + Alembic |
| 儲存 | S3-compatible Object Storage（照片、影片、縮圖） |
| Web 前端 | Vue 3 + Vite，部署於 `https://cloud.hansu.tw/sites/photo-gallery/` |
| Auth | Google OAuth 2.0 + JWT（httpOnly cookie） |

### 已完成功能（後端 API）
- 相簿 CRUD、軟刪除
- 照片 / 影片上傳（縮圖、EXIF、Orientation 修正、ffmpeg）
- 相簿成員權限（uploader / viewer per album）
- 分享連結（無需登入可瀏覽）
- 鎖定相簿（密碼保護 + unlock JWT）
- ZIP 下載（整個相簿）
- 搜尋（filename / caption / 拍攝日期 / album）
- Audit log（login_logs, request_logs）

---

## Native App（本次開發目標）

### 存在原因
Web 版對老人家來說「開瀏覽器」這個動作就是障礙。Native app 提供一個可以點的 icon，登入由開發者代為完成一次，家人幾乎不需要再操作。

### 平台優先順序
1. **iPhone**（最高，家人主要裝置）
2. **iPad**（家人第二裝置）
3. **macOS**（Admin 自用，低優先度，nice-to-have）

### 技術選型
- SwiftUI Universal App — 一份 code，跑 iPhone / iPad / Mac
- 消費現有 FastAPI REST API，後端不做大改動
- 發佈方式：Ad hoc（不上 App Store）

### Native App 功能範圍

**Viewer 功能（家人需要，P0）：**
- 相簿列表（只顯示有權限的）
- 照片 / 影片 Grid 瀏覽
- Lightbox（全螢幕、滑動、縮放）
- 照片 EXIF 資訊
- 下載單張照片到裝置 Camera Roll
- 搜尋（關鍵字 / 日期）

**Admin 功能（P2，nice-to-have）：**
- 上傳照片
- 建立 / 管理相簿
- 管理成員權限
- 相簿 ZIP 下載

**不在 Native App 內：**
- 相簿 ZIP 下載（Viewer 用途，保留在 Web）
- 分享連結管理（Admin Web 操作即可）

---

## 關鍵術語

| 術語 | 定義 |
|---|---|
| **Album** | 相簿，有名稱、描述、可選密碼鎖定 |
| **Photo** | 照片或影片，屬於一個 Album |
| **Permission** | 使用者對特定 Album 的角色：`uploader` 或 `viewer` |
| **Share Link** | 無需登入即可瀏覽相簿的 token URL |
| **Presigned URL** | Object Storage 暫時存取 URL，後端簽發給前端直接拉原圖 |
| **Ad hoc** | Apple 的非 App Store 發佈方式，需要預先登記裝置 UDID |
