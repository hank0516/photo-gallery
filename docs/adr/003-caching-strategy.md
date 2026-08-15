# ADR 003: 圖片快取策略

**狀態**: 已決定  
**日期**: 2026-08-15

## 背景

照片和影片來自 Object Storage 的 presigned URL。完全不快取會導致每次瀏覽都重新下載，在行動網路上體驗差。但激進快取會佔用裝置儲存空間，對老人家的裝置不友善。

## 決定

使用 **URLCache + SDWebImageSwiftUI 或 Kingfisher** 做縮圖層快取：

1. **縮圖（thumbnails）**：積極快取在磁碟，保留最近瀏覽的相簿縮圖，讓相簿列表和 grid 快速載入。
2. **原圖（originals）**：只做 in-memory cache，不寫入磁碟（檔案大，presigned URL 有時效性）。
3. **影片**：不快取，每次串流播放。

## 快取大小上限

- 磁碟快取（縮圖）：最多 200 MB，LRU 淘汰。
- Memory cache：系統預設，收到 memory warning 自動清空。

## 離線行為

接受「沒網路看不到新內容」，但已快取的縮圖可以顯示（album grid 不會空白）。這個體驗對家人可接受。

## 已排除的替代方案

- **Core Data + 完整離線**：工程量大，目前需求不需要真正的離線模式。
- **完全不快取**：行動網路下 grid 滾動體驗太差。
