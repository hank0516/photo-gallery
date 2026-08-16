# Feature: Upload Duplicate Detection（Phase 18）

> 狀態：待實作

## Overview

上傳照片或影片時，在使用者選取檔案後、按下上傳前，自動比對目的相簿中是否已有相同檔案。若有重複，在上傳列表中標示衝突，並讓使用者逐一決定處理方式。

## User Stories

1. As an Uploader, I want to know if a file I'm about to upload already exists in the album, so that I don't accidentally create duplicates without realising it.
2. As an Uploader, I want to choose how to handle each duplicate individually (skip / replace / keep both), so that I have full control over what ends up in the album.

## Functional Requirements

- FR-001: 使用者選取檔案後，立即比對目的相簿的現有檔案清單。
- FR-002: 重複判定條件：**filename 相同 且 exif_date_taken 相同**（兩者皆符合才視為重複）。
- FR-003: 降級規則：若其中一方 `exif_date_taken` 為 null（無 EXIF），則退回只比對 filename。
- FR-004: 若某檔案被判定為重複，在上傳列表中標示「⚠️ 已存在」並顯示衝突的原有照片資訊（filename、拍攝時間）。
- FR-005: 每個衝突檔案顯示一個 single choice（預設「兩者並存」）：
  - **不上傳**：跳過此檔案，不執行任何操作。
  - **覆蓋原檔**：上傳新檔案後，刪除舊檔案（`DELETE /photos/{id}`）。
  - **兩者並存**：直接上傳，允許同名檔案共存（後端預設行為）。
- FR-006: 未發生衝突的檔案不顯示 choice，直接排入上傳佇列。
- FR-007: 使用者點擊「上傳 N 個項目」時，選擇「不上傳」的檔案不計入 N。
- FR-008: 「覆蓋原檔」執行順序：先上傳新檔案成功，再刪除舊檔案；若上傳失敗則不刪除。
- FR-009: 比對發生在 client 端（利用已載入的相簿照片列表），不新增後端 endpoint。
- FR-010: 上傳前從選取的檔案中讀取 EXIF 拍攝時間，與相簿現有照片的 `exif_date_taken` 比對。

## Success Criteria

- SC-001: 選取的檔案中有重複時，使用者在點擊上傳前就能看到衝突標示。
- SC-002: 三種選項皆可正確執行，最終相簿狀態符合使用者預期。
- SC-003: 「覆蓋原檔」後相簿中只有新版本（舊檔案已刪除）。
- SC-004: 「兩者並存」後相簿中同時存在新舊兩個同名檔案。
- SC-005: 選擇「不上傳」的檔案不出現在相簿中。
- SC-006: 無 EXIF 的檔案（如截圖）退回 filename-only 比對，不誤判。

## Assumptions

- **比對依據**：filename + exif_date_taken（精確到秒）；任一方為 null 時退回 filename-only。
- **file_size 不做比對**：iOS PhotosPicker 在載入時可能對 HEIC 轉 JPEG 或影片轉碼，導致同一份原始檔產生不同 byte 數，因此 file_size 不可靠。
- **相簿照片資料來源**：`AlbumDetailViewModel.photos`（已在記憶體中），不額外打 API。
- **分頁限制**：若相簿照片數量超過已載入的單頁（per_page=50），只比對已載入部分；完整比對需分頁載入全部，屬 post-MVP 優化。
- **EXIF 讀取**：從 `PhotosPickerItem` 載入的 Data 中讀取 EXIF，或透過 `PHAsset` 取得 `creationDate`。

## Out of Scope

- Content hash 比對（相同內容但不同檔名）
- file_size 比對
- 批次設定所有衝突的統一策略（例如「全部覆蓋」一鍵套用）
- Web 版前端（此功能目前只在 iOS app 上實作）
