# Feature: Audit Log（Phase 14）

> 狀態：已實作（2026-08-09）

## Overview

記錄使用者登入事件與所有 HTTP 請求，供管理者查閱操作軌跡與排查異常。

## User Stories

1. As an Admin, I want to know who logged in and when, so that I can detect unauthorized access.
2. As an Admin, I want to see all API requests with user, path, status, and response time, so that I can debug performance issues and trace actions.

## Functional Requirements

- FR-001: 每次 Google OAuth 登入成功，記錄一筆 `login_logs`（user_id、email、IP、user_agent、logged_in_at）。
- FR-002: 每個 HTTP request（成功或失敗）記錄一筆 `request_logs`（user_id、email、method、path、status_code、response_time_ms、ip_address）。
- FR-003: Path 包含 query string（例如 `GET /albums/1?page=2` 完整記錄）。
- FR-004: 寫入 log 不阻塞 HTTP response（非同步寫入，使用 ThreadPoolExecutor）。
- FR-005: user_id 可為 null（未登入的 public 請求）。
- FR-006: IP 優先取 `X-Forwarded-For` header（Apache reverse proxy 環境）。

## Implementation

### 資料表

**login_logs**
| 欄位 | 型別 | 說明 |
|---|---|---|
| id | INT PK | |
| user_id | INT FK（nullable）| |
| email | VARCHAR(255) | |
| ip_address | VARCHAR(64) | |
| user_agent | TEXT | |
| logged_in_at | DATETIME | |

**request_logs**
| 欄位 | 型別 | 說明 |
|---|---|---|
| id | INT PK | |
| user_id | INT FK（nullable）| |
| email | VARCHAR(255, nullable）| |
| method | VARCHAR(10) | GET/POST/… |
| path | VARCHAR(512) | 含 query string |
| status_code | INT | |
| response_time_ms | INT | |
| ip_address | VARCHAR(64) | |
| requested_at | DATETIME | |

### Middleware

`RequestLoggingMiddleware`（`app/middleware.py`）掛在 FastAPI app 最外層，記錄所有 http scope 的請求。

## Out of Scope

- Log 查詢 API / 管理介面（只寫入，不提供查詢 endpoint）
- Log 清理 / 保留期限設定
- 敏感欄位遮罩（如密碼）
