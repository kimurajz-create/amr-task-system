---
author: Codex
date: 2026-05-25
title: 主畫面地圖骨架重組
uuid: 665d0d866b8e449ca854f15554af3655
version: v1
planning: documents/planning/P01-main-window-map-overlay-redesign.md
status: completed
---

# R01 主畫面地圖骨架重組

## 1. 背景

P01 的第一階段目標是把主畫面的主要內容區改成由主地圖主導的視覺骨架，但不改背後任務邏輯、MiR API 流程與既有 signal/slot。

目前主畫面依賴 `ui_main.py` 中大量固定 `QRect` 幾何與固定尺寸：

- `frame_map` 固定為 1168x1048
- `label_map_1` 固定為 1072x608
- 右側狀態與任務區塊使用另一套固定座標
- `main.py` 另外在初始化後用 `_adjust_status_area_layout()` 再次手動改幾何

這讓地圖無法成為整個主畫面的主視覺，也讓後續 overlay 佈局無法在一致容器內進行。

## 2. 使用者故事

- **作為** 主畫面操作人員
- **我希望** 主地圖成為整個主畫面主要內容區的骨架背景
- **如此一來** 後續右上、右下、左下浮層可以疊在同一個地圖視覺容器上，而不必維持現在左右分離的拼接版面

## 3. 模組地圖與範疇確認

### 相關模組地圖

| 模組 / 檔案 | 角色 | 與本次 R01 的關係 |
|---|---|---|
| `ui_main.py` | Qt Designer 產生的主畫面 widget 與固定幾何 | 本次主要重構來源，需調整主內容容器與地圖承載骨架 |
| `main.py` / `MainWindow` | 主畫面行為整合層 | 需要配合新的骨架調整 widget 幾何、初始化順序與地圖容器引用 |
| `main.py` / `label_car_overlay` | 地圖 marker 疊圖層 | 必須維持跟隨主地圖容器，不改 marker 業務邏輯 |
| `main.py` / `mousePressEvent`, `draw_car_position` | 地圖點擊與 marker 繪製 | 屬於相鄰耦合點，本階段只要求不被骨架改壞，不主動重寫 |
| `functions.py` | MiR API adapter | 非本階段範圍，只是狀態與位置資料來源 |
| `task_thread.py`, `TaskDBManager.py`, `UserDBManager.py` | 任務排程與資料來源 | 非本階段範圍，不改資料流與行為 |

### 呼叫與依賴關係

1. `ui_main.py` 定義主畫面 widget 與初始幾何。
2. `MainWindow` 在 `main.py` 中載入地圖 pixmap，掛到 `label_map_1`。
3. `MainWindow` 建立 `label_car_overlay` 疊在 `label_map_1` 上。
4. MiR 狀態與位置輪詢會更新 marker，但 marker 仍依賴 `label_map_1` / `label_car_overlay` 的幾何。

### 本次範疇

本文件只處理以下事情：

- 重組主畫面內容骨架，讓主地圖可承接整個主要內容區
- 建立後續 overlay 會依附的主地圖容器
- 保持既有主畫面可啟動、可顯示地圖、可顯示 marker

本文件不處理以下事情：

- 不搬動右上、右下、左下區塊到 overlay 最終位置
- 不做半透明視覺主題
- 不新增地圖滾輪縮放、拖曳平移、雙擊 reset
- 不改任務新增、任務列表、通知資料流、MiR API、DB、排程邏輯
- 不主動重寫地圖點擊與座標轉換公式

## 4. 重構目標

| ID | 目標 | 成功條件 | 風險提醒 |
|---|---|---|---|
| R1 | 建立單一主內容骨架 | 主地圖接手主要內容區，不再侷限於原本左側固定框 | 舊有固定幾何可能互相覆蓋 |
| R2 | 保留地圖載入邏輯 | `label_map_1` 或其等價承載元件仍能顯示既有地圖資產 | 若承載元件改動過大，可能影響 marker |
| R3 | 保留 marker 疊圖層掛載點 | `label_car_overlay` 仍附著在主地圖容器上 | 幾何不同步會讓 marker 偏移 |
| R4 | 建立 overlay 預留區 | 後續 P2 可以把右上、右下、左下區塊疊入，不需再次重做骨架 | 若此階段不先統一容器，P2 會反覆拆改 |

## 5. 驗收標準

- **情境 1：主地圖成為主內容骨架**
  - **前提** 使用者啟動主畫面
  - **當** 主畫面完成初始化並顯示
  - **則** 地圖區域應成為主畫面的主要背景，不再只是左側固定框中的局部區塊

- **情境 2：視窗尺寸改變仍維持骨架**
  - **前提** 主畫面已開啟並顯示地圖
  - **當** 使用者最大化或還原主視窗
  - **則** 主地圖仍維持主視覺骨架，不會被原本左右拼接式版面切開

- **情境 3：Marker 顯示未被骨架改壞**
  - **前提** 主畫面已顯示且 MiR 位置輪詢正常
  - **當** 主畫面顯示機器人位置
  - **則** marker 仍能出現在地圖上，而不是消失或落在地圖容器外

- **情境 4：不影響既有初始化流程**
  - **前提** 使用者正常登入並進入主畫面
  - **當** 主畫面載入既有 site config 與地圖資產
  - **則** 不需改動任務資料流即可完成主畫面載入

## 6. 測試場景 / 驗證表

| ID | 情境 | 前提 | 動作 | 預期結果 | 優先級 |
|---|---|---|---|---|---|
| TC1 | 地圖骨架滿版 | 主畫面可正常開啟 | 進入主畫面 | 地圖成為主要內容區背景 | High |
| TC2 | 視窗最大化 / 還原 | 主畫面已顯示地圖 | 切換視窗大小 | 地圖骨架不崩壞、不露大片空白 | High |
| TC3 | Marker 仍可顯示 | 主畫面已進入輪詢 | 等待位置更新 | marker 仍顯示在地圖範圍內 | High |
| TC4 | 不影響登入後進入主畫面 | 使用有效帳號登入 | 開啟主畫面 | 主畫面正常載入，不因骨架重組報錯 | Medium |
| TC5 | 不提前變更任務區功能 | 主畫面已載入 | 不操作任務區 | 任務區仍可存在，但此階段不要求最終 overlay 樣式 | Medium |

## 7. 可能受影響的檔案 / 模組

- `main.py`
- `ui_main.py`
- 視需要調整的 Qt Designer 對應 `.ui` 檔：`main.ui`
- 相關規劃文件：`documents/planning/P01-main-window-map-overlay-redesign.md`

## 8. 實作方向備註

- 優先重構容器與佈局層級，不重寫業務互動。
- 盡量保留既有 widget 名稱，降低 `MainWindow` 中 signal/slot 與屬性引用改動量。
- 若必須引入新的骨架容器，應讓 `label_map_1` 與 `label_car_overlay` 在新容器內保持幾何同步。
- `_adjust_status_area_layout()` 這類後設幾何修補邏輯，若與新骨架衝突，應只做最小必要收斂，不擴大到 P2。

## 9. 假設、開放問題、非目標

### 假設

- 使用者接受 P1 完成後，右上右下左下仍可能保留舊樣式，只要主地圖骨架已建立即可。
- 此階段可接受為了骨架重組而調整 widget parent、layout 或 size policy，但不應改變資料邏輯。

### 開放問題

- 主地圖骨架在 P1 是否採用單一新容器包住 `label_map_1` 與未來 overlay anchor，還是直接重整現有 `frame_map`。
- `main.ui` 是否需要同步整理，或先在 `main.py` 中以程式方式完成過渡。

### 非目標

- 不處理右上狀態區、右下待執行任務清單、左下通知區的最終視覺位置
- 不做半透明樣式
- 不改地圖互動模式
- 不改 MiR / DB / Task scheduler 邏輯

## 10. 建議後續模組文檔更新

若 R01 後續實作完成，建議同步更新：

- `documents/modules/M01-ui-application-shell.md`

若 P2 開始實作且 overlay 容器職責變得明確，建議新增一份主畫面視覺骨架或地圖畫布相關模組文檔。

---

## 11. 實作紀錄

### 最終行為

- The main map now fills the primary content area and acts as the P1 shell background.
- `label_car_overlay` now follows the resized map container geometry.
- Map click conversion and robot marker scaling now derive from the displayed map size instead of fixed constants.

### 異動檔案

- `main.py`

### 驗證

- Syntax validation passed for `main.py`, `ui_main.py`, and `functions.py` using in-memory compilation.
- Manual UI check confirmed the map now occupies the main content area.
- Manual UI check confirmed the existing right-side controls still render and initialize.

### 已知限制

- The top-right, bottom-right, and bottom-left sections still use the old visual grouping and are not yet true overlays.
- Transparency styling and panel-scale behavior are still deferred to P2 and P3.

### 下一步

- Proceed to P2 and re-host the right-top, right-bottom, and left-bottom sections into overlay containers.

## TDD 重構流程

1. 先為主畫面骨架重組補上可手動驗收的檢查點，避免直接動手改 layout。
2. 以最小範圍調整主容器與地圖承載層，確認主畫面仍可啟動。
3. 驗證 marker 與地圖載入沒有被破壞。
4. 保持系統可運行後，再交由下一份 RXX 處理 overlay 區塊重新掛載。
