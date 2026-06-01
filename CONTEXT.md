# CONTEXT

> 這是 DDD 工作流程用的專案級上下文文件。請保持內容精簡且同步更新，讓後續功能、重構與修 bug 文件都能建立在共同語言上，而不是靠猜測。

## 名詞定義

**MiR State ID**: 由 MiR API 回傳的機器人執行期狀態識別值，是桌面 UI 顯示機器人狀態時的唯一真實來源。

**Status Label**: `MainWindow` 右上角的 `label_Status_1` 文字區塊，用來顯示機器人狀態名稱與目前任務文字。

**Map Ring**: 主地圖上圍繞機器人 marker 的圓形外框。它屬於機器人狀態的表現層，不是任務狀態指示器。

**Robot Marker**: 畫在 `label_car_overlay` 上、覆蓋於地圖圖片之上的車體圖示。

**Site Marker**: 由場域定義的地圖 marker，例如停車格長方形。它應屬於 configuration-driven 的場域資料，而不是依賴固定的 Qt Designer 幾何座標。

**Unknown/Offline State**: 當 UI 無法透過輪詢或狀態校正取得有效 MiR 狀態時，使用的畫面 fallback 狀態。

## 關係

`main.py` 中的 `MainWindow` 會向 `functions.py` 輪詢 MiR 狀態、任務文字、電量與位置，並將結果渲染到：

- the top-right status label
- the map robot marker and ring
- other task and notification widgets

任務執行狀態來自 persistence 與 scheduler 流程；但機器人狀態呈現應該以 MiR 狀態輪詢結果為準，而不是以任務表格狀態為準。

## 架構邊界

- `functions.py` 負責 MiR HTTP/API 細節，並回傳原始機器人狀態資料。
- `main.py` 負責 UI 呈現決策，包括狀態文字、地圖外圈渲染與 fallback 表現。
- `site/*.json` 負責 site 資產、site marker、marker 幾何資料與 location mapping，不是 MiR 狀態顏色語意的主要定義位置。
- `TaskDBManager.py` 與 `task_thread.py` 負責任務持久化與派送流程，不負責機器人燈號或狀態表現規則。

## 已標記的模糊點

- repository 內目前還沒有保存官方的、逐一對應 `state_id` 的顏色來源文件。
- 為了對比效果，Map Ring 顏色可能會刻意與 Status Label 文字顏色不同，但兩者仍應表達相同的狀態語意。
