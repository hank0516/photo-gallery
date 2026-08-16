# Feature: Delete Album UI + Query String Log（Phase 16）

> 狀態：已實作（2026-08-09）

## Overview

兩個小改進合併為一個 phase：Admin 可從相簿頁直接刪除相簿；request log 補上 query string 讓路徑記錄更完整。

## User Stories

1. As an Admin, I want a delete button on the album page, so that I can remove an album without navigating away.
2. As an Admin, I want request logs to include query strings, so that I can see the full URL when debugging.

## Functional Requirements

### Delete Album UI
- FR-001: 相簿頁（AlbumPage.vue）Admin 角色顯示「刪除相簿」按鈕。
- FR-002: 點擊刪除顯示確認 dialog，說明操作不可復原且照片一併刪除。
- FR-003: 確認後呼叫 `DELETE /albums/{id}`（軟刪除），成功後導回相簿列表。
- FR-004: 刪除中按鈕顯示 disabled 狀態，防止重複點擊。

### Query String Log
- FR-005: `request_logs.path` 從單純 path 改為 `path?query_string`（例如 `GET /albums/1?page=2&per_page=50`）。
- FR-006: 若無 query string 則只記錄 path，不加 `?`。

## Implementation

### AlbumPage.vue 改動
```vue
<button v-if="isAdmin" class="btn-danger" @click="handleDeleteAlbum">
  刪除相簿
</button>
```
`handleDeleteAlbum()` 呼叫 `api.delete('/albums/${albumId}')` 後 `router.push('/')`。

### Middleware 改動（app/middleware.py）
```python
qs = scope.get("query_string", b"").decode()
path = scope.get("path", "")
full_path = f"{path}?{qs}" if qs else path
# 記錄 full_path 而非 path
```

## Out of Scope

- 批次刪除多個相簿
- 刪除前備份或匯出
- 復原（undelete）功能
