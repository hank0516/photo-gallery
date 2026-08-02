# Photo Gallery — 實作進度

**最後更新**: 2026-08-02

---

## 整體進度

| Phase | 內容 | 狀態 |
|---|---|---|
| Spec-Kit 設定 | constitution / spec / plan / tasks | ✅ 完成 |
| Phase 1: Setup | 目錄結構、依賴、gitignore | ✅ 完成 |
| Phase 2: Foundational | DB、ORM models、auth、storage client、FastAPI app | ✅ 完成 |
| Phase 3: US1 Auth | Google OAuth、JWT cookie、LoginPage | ✅ 完成 |
| Phase 4: US2 Browse | 相簿列表、照片 grid（3 種模式）、Lightbox | ✅ 完成 |
| Phase 5: US3 Upload | 拖拉上傳、縮圖生成、EXIF 擷取、Object Storage | ✅ 完成 |
| Phase 6: US4 Albums | 建立/編輯/刪除相簿 | ✅ 完成 |
| Phase 7: US5 Permissions | 相簿成員管理（新增/移除/改角色）| ✅ 完成 |
| Phase 8: US6 EXIF | 照片詳情、拍攝時間、相機型號、GPS | ✅ 完成 |
| Phase 9: US7 Share | 分享連結 | ⬜ 待實作 |
| Phase 10: US8 Download | 單張下載（✅）、相簿 ZIP（⬜）| 🔶 部分完成 |
| Phase 11: US9 Search | 搜尋與篩選 | ✅ 完成 |
| Phase 12: Polish | systemd、Apache、RWD | ✅ 完成 |

---

## 已部署

| 項目 | 位置 |
|---|---|
| 前端 URL | `https://cloud.hansu.tw/sites/photo-gallery/` |
| API URL | `https://cloud.hansu.tw/api/photo-gallery/` |
| API Docs | `https://cloud.hansu.tw/api/photo-gallery/docs` |
| Systemd | `photo-gallery-api.service`（port 8002，listen 127.0.0.1）|

---

## 已完成功能

### 後端 API

| 路由 | 說明 |
|---|---|
| `GET /auth/login` | Google OAuth 重導向 |
| `GET /auth/callback` | OAuth callback、JWT httpOnly cookie、bootstrap admin |
| `POST /auth/logout` | 清除 cookie |
| `GET /auth/me` | 當前使用者資訊 |
| `GET /users` | 列出所有已登入帳號（admin only）|
| `GET /albums` | 列出有權限的相簿 |
| `POST /albums` | 建立相簿（admin）|
| `GET /albums/{id}` | 相簿詳情 + 照片分頁（含 presigned URL）|
| `PATCH /albums/{id}` | 修改相簿名稱/描述 |
| `DELETE /albums/{id}` | 軟刪除相簿與所有照片 |
| `GET /albums/{id}/permissions` | 列出成員 |
| `PUT /albums/{id}/permissions/{user_id}` | 新增或修改權限 |
| `DELETE /albums/{id}/permissions/{user_id}` | 移除成員 |
| `POST /albums/{id}/photos` | 上傳照片（含 EXIF、縮圖、EXIF Orientation 修正）|
| `GET /photos/{id}` | 照片詳情 + presigned original URL |
| `PATCH /photos/{id}` | 修改 caption |
| `DELETE /photos/{id}` | 軟刪除（admin）|
| `GET /photos/{id}/download` | 下載（presigned Content-Disposition URL）|

### 前端元件

| 元件 | 說明 |
|---|---|
| `LoginPage.vue` | Google 登入按鈕 + Pending 畫面（無權限時）|
| `AlbumsPage.vue` | 相簿列表 grid + 建立相簿 modal |
| `AlbumPage.vue` | 相簿詳情、上傳 modal、管理成員 modal |
| `AlbumCard.vue` | 相簿卡片（封面縮圖、張數、角色 badge）|
| `ViewModeToggle.vue` | 小縮圖 / 大縮圖 / 列表 切換（localStorage 記憶）|
| `PhotoGrid.vue` | 三種 view mode，lazy loading |
| `Lightbox.vue` | 全螢幕瀏覽、←→ 鍵盤、詳情面板、下載、刪除 |
| `UploadZone.vue` | 拖拉 + 點擊上傳、多檔佇列、進度條 |
| `MembersModal.vue` | 新增/移除/修改成員角色 |

### 已修過的 Bug

| Bug | 原因 | 修法 |
|---|---|---|
| 上傳失敗（`uploader_id` invalid） | Photo model 欄位名稱是 `uploaded_by` | 修正欄位名 |
| GPS 資料截斷（`Data truncated`） | iPhone EXIF GPS 是 `Fraction` 物件，無法直接寫入 DECIMAL | `float()` 轉換後再存 |
| 照片旋轉 90 度 | Pillow 不自動套用 EXIF Orientation | `ImageOps.exif_transpose()` |
| 成員列表空白 | `users.py` 用了 `u.picture`，model 欄位是 `avatar_url` | 修正欄位名 |
| 頁面靠左不置中（Safari） | `#app` 未明確設 `width: 100%`，Safari 下 `margin: 0 auto` 失效 | App.vue 拆開 `#app` 規則並加 `width: 100%` |
| `/sites/photo-gallery`（無 slash）404 | Apache `Alias` 只配對帶 `/` 的路徑 | 加 `RedirectMatch ^/sites/photo-gallery$ /sites/photo-gallery/` |

### RWD 調整

- Lightbox：手機全螢幕，頂部工具列，詳情改為底部滑出
- PhotoGrid：手機 small-grid 3欄、large-grid 2欄
- AlbumPage / AlbumsPage header：flex-wrap，不溢出

---

## 待實作

### 搜尋（Phase 11）✅ 完成

- 後端 `GET /search`：支援 `q`（filename/caption LIKE）、`date_from`/`date_to`（EXIF 拍攝時間）、`album_id`，分頁，只回傳有權限的照片
- 前端 `SearchPage.vue`：關鍵字輸入、日期區間、相簿下拉、PhotoGrid + Lightbox
- AlbumsPage header 加搜尋圖示入口

---

### 分享連結（Phase 9）
- 後端 `share.py`：`POST /albums/{id}/share` 建立 token、`GET /share/{token}` 公開存取
- 前端 `SharedPage.vue`：無需登入可瀏覽的相簿頁

### 搜尋（Phase 11）
- 後端 `search.py`：by filename / caption / 拍攝日期區間
- 前端 `SearchPage.vue`

### 相簿 ZIP 下載（Phase 10）
- 後端串流 zip，打包相簿所有原圖

---

## 服務管理

```bash
# 查看即時 log
sudo journalctl -u photo-gallery-api -f

# 重啟後端（改 Python 後）
sudo systemctl restart photo-gallery-api

# 重新 build 前端（改 Vue 後，立刻生效）
cd /home/hank/my_websites/photo-gallery/frontend && npm run build
```
