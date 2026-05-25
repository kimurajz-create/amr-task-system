---
author: Codex
date: 2026-05-25
title: Main Window Overlay Container Rehost
uuid: 7f7e4f3452f4478c9c0ff26b28c5d5ad
version: v1
planning: documents/planning/P01-main-window-map-overlay-redesign.md
status: completed
---

# R02 主畫面 Overlay 容器重掛

## 1. 背景

P01 的 P2 階段要求把目前散落在主畫面不同固定座標區域的資訊與控制區，重新掛入同一張主地圖之上的 overlay 容器。  
R01 已完成主地圖骨架重整，讓 `frame_map` 成為可承載 overlay 的主容器，但右上任務設定區、右下待辦任務清單區、以及左下通知與狀態列仍停留在舊有 parent/geometry 結構。

若直接進入 P3 樣式與縮放調整，這些區塊仍會分散在 `centralwidget` 與 `frame_map` 的不同層級，會讓樣式套用、幾何同步與後續尺寸規則更加脆弱。

## 2. 使用者故事

- **As a** 主畫面操作人員
- **I want** 右上、右下與左下資訊面板都成為疊在主地圖上的 overlay 容器
- **So that** 後續樣式、尺寸規則與互動區域可以用容器為單位一致管理，而不必再分散修改個別 widget

## 3. 重構範圍與邊界

| 區塊 / 元件 | 現況 | R02 調整 |
|---|---|---|
| `main.py` / `MainWindow` | 已有主地圖骨架、marker overlay、右側任務控制與左下狀態列 | 建立三個 overlay 容器、重掛既有 widget、保留原有互動行為 |
| `ui_main.py` | Designer 產生固定座標 widget | 不直接修改，仍保留生成檔作為原始 widget 定義 |
| `label_map_1` / `label_car_overlay` | 依賴主地圖容器幾何 | 必須維持原有掛載與點擊/marker 對齊 |
| MiR API / DB / Task Thread | 提供任務與機器人狀態 | 不改商業邏輯，只維持 UI 連線可用 |

### 本次涵蓋

1. 建立右上 overlay 容器，承載任務設定與任務建立控制。
2. 建立右下 overlay 容器，承載待辦任務標題、啟停按鈕與待辦清單。
3. 建立左下 overlay 容器，承載通知區、地圖下方狀態列、心跳顯示與地圖點擊控制。
4. 讓 `_adjust_status_area_layout()` 可在 overlay 重掛後繼續正確設定相關 widget 幾何。

### 本次不涵蓋

- 不改變任務建立、停止、送點、通知、心跳與待辦清單的業務邏輯。
- 不重寫 `ui_main.py` 或 Qt Designer `.ui` 配置。
- 不在此階段處理 overlay 的自適應縮放與比例規則，該責任仍屬 P3。
- 不變更 marker 點位、MiR 輪詢、座標轉換或資料來源。

## 4. 約束條件

| ID | 約束 | 說明 | 風險 |
|---|---|---|---|
| R1 | 保持既有 widget instance | 不能新建替代 widget，避免既有 signal/slot 與 `findChild` 參考失效 | 若改成新 widget，現有事件線路容易斷裂 |
| R2 | 保持地圖點擊行為 | `label_map_1` 與 `label_car_overlay` 的邏輯不可被 overlay 容器破壞 | 若層級錯誤，marker 或點擊位置會偏移 |
| R3 | 只調整視覺掛載層級 | 任務、通知、待辦清單資料流保持不變 | 若連動資料邏輯，回歸面會過大 |
| R4 | 讓幾何調整方法可重入 | 既有 `_adjust_status_area_layout()` 不能再假設所有 widget 都掛在 `centralwidget` | 若忽略此點，重掛後會出現座標錯位 |

## 5. 驗收情境

- **Scenario 1: 右上任務區進入 overlay**
  - **Given** 主畫面完成初始化
  - **When** 右上任務設定 widgets 被重掛
  - **Then** 這些 widgets 應共同位於同一個半透明 overlay 容器內，且原本按鈕與下拉選單仍可操作

- **Scenario 2: 右下待辦清單維持可用**
  - **Given** 待辦任務區已載入表格與按鈕
  - **When** 待辦區被重掛到 overlay 容器
  - **Then** 清單內容、刪除按鈕與啟停按鈕仍可正常顯示與觸發

- **Scenario 3: 左下通知與狀態列維持可用**
  - **Given** 左下通知與地圖下方狀態列已建立
  - **When** 它們被包入 overlay 容器
  - **Then** 通知清單、心跳標籤、點擊模式 checkbox 與送點按鈕都仍可正常更新

- **Scenario 4: 地圖點擊與 marker 不受影響**
  - **Given** 主地圖與 marker overlay 已建立
  - **When** 畫面完成 overlay 重掛
  - **Then** 地圖點擊、marker 重繪與機器人位置更新仍依附 `label_map_1` / `label_car_overlay` 正常運作

## 6. 影響檔案

- `main.py`
- 相關規劃文件：`documents/planning/P01-main-window-map-overlay-redesign.md`

## 7. 風險與回滾點

- 風險一：若 widget 重掛後仍有程式碼以舊 parent 的絕對座標直接 `setGeometry()`，畫面會錯位。
- 風險二：若 overlay 層級沒有正確 raise，可能蓋住 marker 或反過來被地圖吃掉。
- 風險三：若左下區塊邊界抓取錯誤，可能使通知清單或地圖點擊控制被裁切。

回滾點：

1. 保持 `ui_main.py` 不變，若需回退，只需撤回 `main.py` 的 overlay 建立與重掛邏輯。
2. 因未改動資料流與 DB/API 邏輯，回退不涉及任務資料修復。

## 8. 實作摘要

1. 以 `frame_map` 為單一 overlay anchor，在 `main.py` 動態建立三個 `QFrame` overlay 容器。
2. 以既有 widget 的當前幾何聯集計算每個 overlay 的外框，再把 widget 重新設定 parent 到對應容器內。
3. 保留所有既有 widget 實例與 signal/slot，只改掛載層級與局部幾何。
4. 將 `_adjust_status_area_layout()` 改為可同時支援重掛前後的座標設定。

## 9. Implementation Record

### Final Behavior

- The top-right task controls now render inside a shared map overlay container.
- The bottom-right pending-mission header, action buttons, and list now render inside a shared map overlay container.
- The bottom-left notification and map status strip now render inside a shared map overlay container.
- Map click handling and robot marker rendering continue to use `label_map_1` and `label_car_overlay`.

### Changed Files

- `main.py`
- `documents/planning/P01-main-window-map-overlay-redesign.md`

### Verification

- Syntax validation passes for `main.py`.
- Overlay rehost logic preserves the existing widget instances instead of replacing them.
- The map overlay layer still raises above the map and below the foreground panels.

### Next Step

- Proceed to P3 to unify overlay visual style details and define panel scaling / responsive geometry rules.

## TDD Refactoring Workflow

1. 先鎖定不變的資料流與 widget 實例，再處理 parent/geometry 重掛。
2. 先讓容器可建立與可承載，再逐區塊搬移既有 widget。
3. 每次移動後都保留 `label_map_1` / `label_car_overlay` 的幾何同步邏輯。
4. 完成重掛後再進行語法驗證與互動回歸確認，避免把視覺重構擴大成業務回歸。
