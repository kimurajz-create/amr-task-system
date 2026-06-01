# MiR API 介接層

## 範圍

主要檔案：`functions.py`

輔助設定：

- `config.json`

## 職責

本模組封裝 MiR HTTP API 呼叫，並對 UI 與排程器提供可直接呼叫的 Python 函式。

主要職責包括：

- 載入與保存 MiR 連線設定
- 組裝請求授權標頭
- 查詢機器人狀態與 mission 文字
- 讀取目前地圖與位置資料
- 派送機器人任務與相對移動
- 檢查 mission queue 狀態
- 清除機器人錯誤狀態
- 觸發裝置端動作，例如音效與升降

## 主要能力分組

| 能力 | 代表函式 |
|---|---|
| 設定 | `load_config`, `save_config`, `load_ip`, `save_ip` |
| 驗證 | `get_auth_headers` |
| 狀態 | `check_MiR_status`, `check_api_status_v3`, `get_battery_level` |
| 地圖與位置 | `check_MiR_status_position`, `get_curmaps_positions_cmb`, `post_position` |
| 任務查詢 | `get_mission_id`, `get_mission_groups_id_cmb`, `get_mission_point_uuid` |
| 任務派送 | `move_to_position`, `move_to_position_multi_var`, `run_combo_location_multi_var` |
| 任務佇列監看 | `get_mission_queue_max_id`, `get_mission_queue_id_state` |
| 回復與操作 | `clear_MiR_error`, `stop_the_mission`, `set_lift_position`, `play_sound` |

## 使用者

- `main.py` 內的 `MainWindow`
- `task_thread.py` 內的 `TaskThread`

## 輸入

- 來自 `config.json` 或執行期更新的 MiR base URL
- 目前寫在模組常數中的靜態帳密
- 來自 runtime maps 或 UI 選擇的 mission / location 識別碼

## 輸出

- 解析後的 JSON 狀態資料
- 電量、`state_id` 等純量狀態欄位
- mission queue 識別碼與狀態
- 透過 HTTP 請求直接作用在機器人上的副作用

## 邊界

- 本模組應該理解 MiR API 細節。
- 本模組不應決定業務優先序或 UI 呈現方式。
- 其他模組應把它當成機器人 HTTP 操作的單一入口。

## 已知風險

- 依賴 `MIR_IP`、`Full_IP` 這類模組層級可變全域變數。
- 帳密寫死在程式裡，操作風險較高。
- 錯誤處理不一致：有的函式回傳 `None`，有的回傳 `1`，有的直接丟出例外。
- timeout 雖然存在，但不是每一種請求都一致處理。

## 可重構接縫

- 用具型別的 client 物件取代模組全域變數。
- 將錯誤處理正規化成單一策略。
- 依照狀態、任務、佇列與設定分拆成更明確的類別或子模組。
