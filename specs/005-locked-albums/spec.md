# Feature: Locked Albums（Phase 15）

> 狀態：已實作（2026-08-09）

## Overview

相簿可設定密碼鎖定，未解鎖的使用者看不到照片內容。解鎖後產生 session-only 的 unlock token，同一 session 內不需再次輸入密碼。

## User Stories

1. As an Admin, I want to password-protect an album, so that only people who know the password can view its contents.
2. As a Viewer, I want to enter a password to unlock a protected album, so that I can access content the admin has shared with me.
3. As a Viewer, I want the album to stay unlocked within my session, so that I don't have to re-enter the password every time I navigate back.

## Functional Requirements

- FR-001: 建立相簿時可設定 `is_locked=true` + `password`（必填）。
- FR-002: 密碼以 PBKDF2-SHA256（260,000 次迭代）+ random salt 雜湊儲存，明文不儲存。
- FR-003: `GET /albums/{id}` 若相簿已鎖且未提供有效 unlock_token，回傳 `locked: true` + 空照片列表（HTTP 200，不是 403）。
- FR-004: `POST /albums/{id}/unlock` 驗證密碼，成功回傳 `unlock_token`（JWT，24 小時有效）。
- FR-005: unlock_token 以 query string 傳遞給後續 `GET /albums/{id}?unlock_token=...`。
- FR-006: Web 前端將 unlock_token 存在 session store（`useUnlockStore`），頁面重整後需重新輸入密碼。
- FR-007: 相簿列表（`GET /albums`）仍顯示加密相簿，只是內容被保護（`is_locked: true`）。
- FR-008: Admin 可 PATCH `/albums/{id}` 修改 `is_locked` 和 `password`。

## Implementation

### 資料表欄位（albums）

| 欄位 | 型別 | 說明 |
|---|---|---|
| is_locked | TINYINT(1) | 預設 0 |
| password_hash | VARCHAR(255, nullable）| `{salt}:{pbkdf2_hex}` 格式 |

### Unlock Token JWT Payload

```json
{
  "album_id": 1,
  "user_id": 1,
  "purpose": "album_unlock",
  "exp": "<24小時後>"
}
```

### Web 前端行為

- Lock gate UI：進入加密相簿顯示密碼輸入表單
- 解鎖後用 `useUnlockStore` 儲存 token（session only，重整即清除）
- 加密相簿在列表顯示鎖頭 icon（`is_locked: true`）

### iOS app 行為（MVP）

- `is_locked: true` 的相簿在列表中隱藏（暫時 workaround）
- Unlock flow 為 post-MVP

## Out of Scope

- 分享連結的加密相簿解鎖（另有 `share_unlock_token`，獨立機制）
- 密碼修改通知
- 錯誤次數限制 / 鎖定防暴力破解
