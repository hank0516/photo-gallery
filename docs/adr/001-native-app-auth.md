# ADR 001: Native App 認證方式

**狀態**: 已決定  
**日期**: 2026-08-15

## 背景

後端使用 Google OAuth 2.0 + JWT（httpOnly cookie）。Native app 需要在 iOS/macOS 上完成同樣的登入流程，並長期保持登入狀態（家人幾乎不需要重新登入）。

## 決定

1. **OAuth 流程**：使用 `ASWebAuthenticationSession` 呼叫現有後端 `/auth/login` → Google → `/auth/callback`。後端 callback 完成後 redirect 到 custom URL scheme（`photogallery://auth/callback?token=xxx`），app 從 URL 取得 JWT。

2. **Token 儲存**：JWT 存入 iOS **Keychain**（`kSecClassGenericPassword`），跨 app launch 保持登入狀態。

3. **API 呼叫**：每次 request 將 JWT 放入 `Authorization: Bearer <token>` header。

4. **登入由 Admin 代操作**：家人第一次使用由開發者幫忙完成 Google 登入，之後 token 留在 Keychain，家人打開 app 直接進主畫面。

## 後端需調整

- `/auth/callback` 支援 redirect 到 custom URL scheme（`photogallery://auth/callback?token=xxx`）
- API middleware 同時接受 `Authorization: Bearer` header（現只接受 cookie）

## 已排除的替代方案

- **WKWebView 做 OAuth**：httpOnly cookie 無法跨 WKWebView / URLSession 共享，體驗差。
- **Email / 密碼**：後端不支援，且老人家記不住密碼。
