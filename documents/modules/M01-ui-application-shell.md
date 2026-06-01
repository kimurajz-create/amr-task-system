# 介面應用殼層

## 範圍

主要檔案：`main.py`

輔助的 Qt 產生檔案：

- `ui_main.py`
- `ui_login_window.py`
- `ui_admin_panel.py`
- `ui_selected_map.py`

## 職責

介面應用殼層負責：

- 啟動桌面應用程式與主要視窗
- 將 Qt 產生的 UI 類別接上互動行為
- 保存共用執行期狀態，例如場域 profile、runtime maps、機器人狀態旗標與計時器
- 協調資料庫 manager、MiR API 呼叫與背景任務執行緒事件
- 把機器人與任務狀態反映到表格、標籤、通知與地圖 marker 上

## 主要執行期物件

| 物件 | 用途 |
|---|---|
| `LoginWindow` | 使用者登入入口與主系統的存取閘道 |
| `AdminPanel` | 管理者導向的使用者管理或維護介面 |
| `SelectedMap` | 互動式地圖選點視窗，用來挑選任務起點與目的地 |
| `MainWindow` | 任務派送、監看、狀態輪詢與地圖更新的主要操作主控台 |
| `DBWorker` | 處理 UI 觸發的非阻塞 DB/API 呼叫的輔助 worker thread |

## 主要依賴

- `functions.py`：MiR 機器人 API 操作
- `TaskDBManager.py`：任務資料
- `UserDBManager.py`：使用者資料
- `task_thread.py`：背景排程
- `site/*.json`：地點、任務、marker 與地圖資產定義
- `app_settings.json`：目前啟用的場域 profile

## 輸入

- 來自按鈕、下拉選單、對話框與表格的使用者操作
- 來自環境變數或 `app_settings.json` 的場域 profile
- 來自定期輪詢的 MiR 狀態
- 來自 PostgreSQL manager 的任務與使用者資料
- 來自 `TaskThread` 的任務完成事件

## 輸出

- 更新後的 UI 狀態標籤、通知、任務表格與地圖 marker
- 透過 `functions.py` 轉交給 MiR 的指令
- 透過 `TaskDBManager` 轉交的任務狀態更新
- 透過 `UserDBManager` 轉交的使用者管理操作

## 內部分區

### 1. 啟動與執行期設定

`main.py` 會解析執行路徑、載入 app settings、載入 `site/<profile>.json`，並建立跨 UI 與排程共用的 runtime maps。

### 2. 畫面組裝

Qt Designer 產生的類別會掛接到自訂 widget 類別上，由後者補上 `.ui` 檔沒有保存的互動行為。

### 3. 狀態輪詢

`MainWindow` 擁有多組計時器：

- 快速輪詢：MiR 運行狀態與機器人位置
- 慢速輪詢：電量與 room heartbeat
- 刷新輪詢：任務清單與 mission 對帳

### 4. 任務互動

`MainWindow` 負責建立、顯示、更新與收斂任務資訊，但把持久化與機器人實際執行委派給其他模組。

## 邊界

- 本模組應該負責協調，不應自己實作 MiR HTTP 細節。
- 本模組應該顯示任務狀態，不應自己擁有任務佇列的持久化規則。
- 目前仍有部分操作策略與 mapping 邏輯混在其中，後續可能值得抽離。

## 已知風險

- `MainWindow` 體積很大，幾乎確定是後續主要重構目標。
- `is_AMR_idle`、`is_low_battery` 這類共用可變旗標，會提高協調風險。
- UI 輪詢與 DB/API 對帳邏輯交織得很緊。

## 可重構接縫

- 將場域設定與 runtime mapping 抽成獨立模組。
- 將任務呈現邏輯從 `MainWindow` 抽離。
- 將狀態輪詢協調抽成獨立的 coordinator 或 service 層。
