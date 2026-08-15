# ADR 004: Ad Hoc 發佈流程

**狀態**: 已決定  
**日期**: 2026-08-15

## 背景

App 不上 App Store，需要用 Apple 的 ad hoc 發佈方式安裝到家人裝置。Ad hoc 上限是 100 台裝置（每年 Apple Developer Program）。

## 決定

採用 **OTA（Over-the-Air）下載頁** 方式，步驟如下：

1. **收集 UDID**：用 Apple Configurator 2 或讓家人裝置連電腦，取得裝置 UDID。
2. **登記裝置**：在 Apple Developer Portal 新增裝置 UDID。
3. **建立 Provisioning Profile**：Ad Hoc profile，包含所有已登記裝置。
4. **打包 IPA**：Xcode Archive → Export → Ad Hoc。
5. **上傳 IPA**：放到現有伺服器（`cloud.hansu.tw`），搭配 `manifest.plist`。
6. **安裝連結**：提供 `itms-services://?action=download-manifest&url=https://...manifest.plist` 連結，家人在 Safari 點擊即可安裝（需 HTTPS）。

## 更新流程

每次 app 更新只需重新 export IPA 並上傳覆蓋，家人點同一個連結重新安裝即可（不需要重新登記 UDID）。

## 信任設定（一次性）

家人裝置安裝後需到「設定 → 一般 → VPN 與裝置管理」信任開發者，由 Admin 代為操作。

## 已排除的替代方案

- **TestFlight**：需要 App Store Connect 審核，且 90 天到期需重裝，不適合長期使用。
- **Xcode 插線直接安裝**：需要每次拿到裝置實體，OTA 頁面更方便（遠端也能更新）。
