# 模組總覽

## 目的

本專案是一套以 PySide6 建置的桌面應用程式，用來派送 MiR 機器人任務、追蹤任務執行狀態，並把機器人與任務狀態反映到操作介面上。

## 目前模組地圖

| 模組 | 主要檔案 | 職責 |
|---|---|---|
| 介面應用殼層 | `main.py`, `ui_main.py`, `ui_login_window.py`, `ui_admin_panel.py`, `ui_selected_map.py` | 組合畫面、綁定 widget、處理計時器，並協調資料庫、MiR API 與背景執行緒 |
| 場域設定與執行期對映 | `main.py`, `site/*.json`, `app_settings.json` | 載入場域 profile、地圖資產、校正資料、地點名稱、任務名稱、marker 對映與充電站規則 |
| MiR API 介接層 | `functions.py`, `config.json` | 封裝 MiR HTTP API，提供狀態查詢、任務送出、地圖位置、升降與音效等操作 |
| 任務排程器 | `task_thread.py` | 從資料庫提取待辦任務、送出 MiR 任務、等待 mission queue 完成並處理充電回退 |
| 持久化層 | `TaskDBManager.py`, `UserDBManager.py` | 讀寫任務佇列、使用者資料、排序、執行狀態與 room heartbeat 相關資料 |

## 高層執行流程

1. `main.py` 啟動應用程式、建立資料庫 manager，並進入登入流程。
2. `MainWindow` 載入場域設定，產生 UI 顯示名稱與 MiR 識別碼之間的執行期對映。
3. UI 計時器定期輪詢 MiR 狀態、電量、房間狀態、任務清單與 mission 對帳結果。
4. `TaskThread` 持續從 PostgreSQL 取得最高優先序的待辦任務。
5. `TaskThread` 透過 `functions.py` 送出 MiR 任務並監看 mission queue 狀態。
6. `TaskDBManager` 持久化任務生命週期變化，例如 `Pending`、`Executing`、`Completed` 與 `Aborted`。

## 邊界

- `main.py` 目前同時扮演應用殼層與功能協調層。
- `functions.py` 是 MiR 外部整合層。
- `task_thread.py` 擁有背景排程行為。
- `TaskDBManager.py` 與 `UserDBManager.py` 擁有資料庫存取職責。
- `site/*.json` 與 `app_settings.json` 提供不改程式碼即可切換的環境與場域差異。

## 目前架構風險

- `main.py` 職責過多，是目前最大的協調熱點。
- `functions.py` 依賴 MiR IP 與帳密等模組層級全域變數，耦合度偏高。
- UI 邏輯、執行期對映與操作策略部分混在 `main.py` 中。
- 排程器同時依賴 MiR API 狀態與 DB 對帳結果，失敗情境不容易看出來。

## 建議下一步文件

- 若團隊會持續調整 UI，可為主要畫面各自建立更細的模組文件。
- 補一份任務生命週期文件，描述所有任務狀態與轉換。
- 補一份 `site/*.json` 與 `app_settings.json` 的場域設定結構文件。
