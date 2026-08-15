# ADR 002: 平台優先順序

**狀態**: 已決定  
**日期**: 2026-08-15

## 背景

SwiftUI Universal App 理論上可以一份 code 跑 iPhone / iPad / macOS，但三個平台的 UI 行為差異很大（macOS 有 sidebar、多視窗；iPad 有 split view；iPhone 是 stack navigation）。需要明確優先順序避免過早投資在低優先平台。

## 決定

| 優先級 | 平台 | 原因 |
|---|---|---|
| P0 | iPhone | 家人主要裝置，最高使用頻率 |
| P1 | iPad | 家人第二裝置，大螢幕適合瀏覽相片 |
| P2 | macOS | 只有 Admin（開發者）使用，Catalyst / Mac Idiom 的 UI quirk 較多 |

## 實作影響

- Navigation 結構以 `NavigationStack`（iPhone stack）為主，iPad 可加 `NavigationSplitView`。
- macOS 版初期接受「放大版 iPad UI」，不需要刻意做 macOS native menubar / toolbar。
- Layout breakpoint 優先考慮 iPhone（375pt 起），iPad 用 `horizontalSizeClass` 做彈性調整。
