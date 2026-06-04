---
author: Codex
date: 2026-06-04
title: MiR 營運績效頁第一版：任務量與起點/目的地熱區
status: draft
version: v1
uuid: c3b7302c6b7d4e3cb9a298ed58b3c4f1
---

# P04 MiR 營運績效頁第一版：任務量與起點/目的地熱區

## 1. 背景與問題

目前專案的主體仍是 MiR 任務派送與監控 GUI，主畫面的核心價值是讓操作人員可以快速建立任務、監看機器人狀態、查看待派送任務與處理異常。這些操作型需求與營運績效檢視是不同性質的工作。

現況問題如下：

- 主畫面已經承載任務建立、任務清單、MiR 狀態、地圖標記、heartbeat 顯示、通知訊息與多組 polling 流程，`main.py` 已是目前最大的協調熱點。
- 使用者雖然需要看營運表現，但現行畫面沒有提供一個可直接回答「現在任務多不多」「最常從哪裡出發」「最常送去哪裡」的視圖。
- 若把績效資訊直接塞回主控台主區塊，會提高既有操作畫面的干擾，也會增加重新調整版面與互動流程的風險。

第一版先只做「任務量」與「起點/目的地熱區」，原因如下：

- 這兩類統計最接近目前 `tasks` 資料表已經存在的欄位，落地成本最低。
- 這兩類統計不需要先補完整事件時間軸，也不需要額外對 MiR API 做長期歷史蒐集。
- 這兩類統計可以先用數字卡片與表格呈現，不必一開始就導入複雜圖表或地圖熱圖。

暫時不碰其他 KPI 的原因如下：

- 任務等待時間、任務執行時間、SLA、準時率、機器人利用率都依賴更完整的時間戳與定義，目前從已觀察到的程式碼與查詢 methods 無法直接確認資料基礎已完整。
- 電量分析、heartbeat 統計、MiR API 可靠度報表屬於另一組資料來源與監控語意，不適合和第一版的任務統計一起擴張。
- 長期趨勢分析需要先確認 `tasks` 保留週期、時間欄位可用性與查詢成本，否則容易做成表面有數字、實際定義不穩的頁面。

本次選擇「主畫面新增入口按鈕，開啟獨立績效頁」而不是改動現行主控台畫面，原因如下：

- 可以維持既有主畫面操作習慣，不重新設計目前主操作區 layout。
- 可以把績效頁的刷新節奏與資料查詢邏輯和主畫面高頻輪詢解耦。
- 可以讓第一版先小而穩，降低 UI regression 風險。

## 2. 目標

本次 P04 的目標如下：

- 在不大改現有架構的前提下，增加一個可從 GUI 進入的績效頁。
- 現行主畫面維持既有版面與操作方式，不重新設計主控制台。
- 透過一顆入口按鈕，打開獨立的新頁面或新視窗。
- 第一版先提供可立即反映營運狀況的基本統計。
- 優先使用目前程式已經有的資料來源與狀態欄位。
- 將本次方案明確限定為「先做任務量與起點/目的地熱區」，不在同一輪擴張成完整 BI 或多 KPI 系統。

## 3. In Scope / Out of Scope

### In Scope

- 主畫面新增一顆「績效分析」或同等語意的入口按鈕。
- 按鈕開啟獨立的新頁面或新視窗。
- 顯示任務量統計。
- 顯示起點熱區與目的地熱區。
- 顯示常見路線組合 Top N，前提是現有 `tasks` 資料保留量足以形成可讀結果。
- 規劃績效頁資料來源、查詢邏輯與刷新策略。
- 規劃 `TaskDBManager.py` 的統計查詢擴充方向。

### Out of Scope

- 調整現有主畫面大版面配置。
- 把績效資訊直接塞進目前主控台主區域。
- 任務執行時間類 KPI。
- 任務等待時間類 KPI。
- SLA / 準時率。
- 電量報表。
- heartbeat 報表。
- MiR API 可靠度分析。
- 匯出 CSV / Excel。
- 後台管理編輯功能。
- 複雜圖表系統或外部 BI 工具整合。
- 跨站點彙整分析。

## 4. 現況盤點

### 4.1 `main.py` 目前的 UI timer / task refresh / notification / status polling

依目前 `MainWindow` 已觀察到的流程，主畫面已經同時承擔多組高頻與中頻輪詢：

| 類型 | 週期 | 主要職責 | 備註 |
|---|---|---|---|
| `poll_timer` | 5 秒 | `poll_room_status()`，進一步透過 worker 檢查 API 狀態與 room error | 偏監控 / 健康檢查 |
| `fast_timer` | 0.3 秒 | `query_mir_info()`、`poll_mir_position()` | 高頻更新 MiR 狀態、mission text、機器人位置 |
| `slow_timer` | 10 秒 | `query_battery_status()`、`update_room_heartbeat_status()` | 電量與房間 heartbeat 顯示 |
| `refresh_timer` | 2 秒 | `refresh_task_list()`、`query_mir_status_db()` | 任務清單刷新與執行中任務狀態對帳 |
| `loop_test_timer` | 測試用，預設未啟用 | `add_test_batch_missions()` | 非正式營運流程 |

除 polling 外，`main.py` 也已經有多種操作型通知：

- 任務完成通知。
- 任務中止通知。
- 低電量與電量恢復通知。
- API / room heartbeat 異常相關狀態提示。

這代表績效頁若直接掛在主畫面主區塊，會與既有高頻刷新與操作通知更緊密耦合。第一版應避免走這條路。

### 4.2 `TaskDBManager.py` 目前 `tasks` 資料可支援的基礎

從目前已觀察到的 `TaskDBManager.py` methods，可確認 `tasks` 相關欄位或語意至少包含：

| 項目 | 目前可觀察情況 | 對第一版統計的意義 |
|---|---|---|
| `start_point` | 任務建立時寫入 | 可做起點熱區 |
| `target_point` | 任務建立時寫入 | 可做目的地熱區 |
| `mission_content` | 任務建立時寫入 | 可做任務類型分組 |
| `status` | 已觀察到 `Pending`、`Executing`、`Completed`、`Aborted` | 可做任務量卡片 |
| `mq_id` | 任務送出後綁定 MiR mission queue id | 可供執行對帳，但不是第一版 KPI 主欄位 |
| `room_id` | 部分任務建立時帶入 | 可作後續擴充，但本版不作主要統計軸 |
| `sequence` | 未完成任務排序使用 | 供排程，不是績效主欄位 |
| `mir_command_sent` | 任務送出旗標 | 可作內部狀態輔助，不作第一版主視圖 |

另外可保守推定但需確認的欄位：

- `created_at`
  - `TaskDBManager.py` 的插入註解提到 DB default 會處理 `created_at`。
  - 但目前查詢 methods 沒有把 `created_at` 讀出，也沒有看到以它做條件或聚合的查詢。
  - 若之後要加「今日任務量」「近 7 日趨勢」等條件，需先確認實際 schema 與資料品質。

目前尚未在已觀察程式碼中看到的欄位或查詢能力：

- `started_at`
- `completed_at`
- `aborted_at`
- `wait_seconds`
- `execution_seconds`
- `scheduled_at`
- `deadline_at`

因此第一版不宜直接承諾時間型 KPI。

### 4.3 `task_thread.py` 與 `main.py` 的任務狀態流轉

目前任務狀態流轉大致如下：

1. `main.py` 透過 `add_new_task()`、`add_batch_tasks()`、`emergency_insert_task()` 建立任務，初始狀態為 `Pending`。
2. `TaskThread` 透過 `get_highest_priority_task()` 取出下一筆 `Pending` 任務。
3. 任務送往 MiR 後，`TaskThread` 將任務更新為 `Executing`，並嘗試綁定 `mq_id`。
4. 任務完成時，可能由 `TaskThread.finished_task` 直接通知 UI，也可能由 `main.py` 的 `query_mir_status_db()` 做狀態對帳。
5. 最終透過 `transition_task_status()` 將任務由 `Executing` 轉為 `Completed` 或 `Aborted`。

這條流程對第一版績效頁的意義是：

- `status` 是目前最穩定的統計切面。
- `start_point` 與 `target_point` 在任務建立時就已經存在，不必額外向 MiR API 回溯。
- `mission_content` 在任務建立時也已存在，可作為可選分組。
- 任務完成後並沒有在觀察到的程式碼中自動刪除歷史列，代表只要 DB 沒有額外清理機制，就有機會把 `tasks` 表當作第一版的保守歷史來源。

### 4.4 哪些數據今天就能算

依目前已觀察到的資料與流程，今天就能保守落地的統計包括：

- 目前 `Pending` 數。
- 目前 `Executing` 數。
- `Completed` 數。
- `Aborted` 數。
- 總任務數。
- 依 `mission_content` 分組的任務數。
- 依 `start_point` 分組的起點 Top N。
- 依 `target_point` 分組的目的地 Top N。
- 依 `start_point + target_point` 分組的路線組合 Top N。

需要加註限制的地方如下：

- `Completed` / `Aborted` / `Total` 比較像「目前資料表保留的累積任務量」，不是正式定義過的長期報表口徑。
- 若資料表有人工刪除、清表或歸檔，這些數字就會反映「保留中的歷史」，而不是永久完整歷史。

### 4.5 哪些數據目前資料基礎不足

目前不建議納入第一版的統計包括：

- 任務等待時間。
- 任務執行時間。
- SLA / 準時率。
- 機器人利用率。
- 電量趨勢。
- room heartbeat 統計。
- MiR API 成功率 / 失敗率。
- 長期歷史趨勢圖。

原因不是這些指標不重要，而是從目前程式碼可見範圍內，尚未看到足夠穩定的事件時間戳、抽樣歷史或報表定義。

## 5. 建議統計項目

### 5.1 A. 任務量

第一版建議至少顯示以下卡片或摘要值：

- 目前 Pending 數。
- 目前 Executing 數。
- 已完成數。
- 已中止數。
- 總任務數。

可選但不強制的補充項目：

- 依 `mission_content` 分組的任務數 Top N。

資料來源與呈現方式建議如下：

| 項目 | 資料來源 | 建議口徑 | 呈現方式 |
|---|---|---|---|
| Pending 數 | `tasks.status` | `status = 'Pending'` | 數字卡片 |
| Executing 數 | `tasks.status` | `status = 'Executing'` | 數字卡片 |
| 已完成數 | `tasks.status` | `status = 'Completed'` | 數字卡片 |
| 已中止數 | `tasks.status` | `status = 'Aborted'` | 數字卡片 |
| 總任務數 | `tasks` 全表保留列數 | 以保留中的任務列為準 | 數字卡片 |
| 任務類型分組 | `tasks.mission_content` | `GROUP BY mission_content` | 表格 |

第一版建議口徑：

- 先用「目前 DB 保留資料」作為任務量統計基礎。
- 不先做日期區間切換。
- 不先做趨勢線。

### 5.2 B. 起點 / 目的地熱區

第一版建議至少顯示以下 Top N：

- 最常出發的起點 Top N。
- 最常前往的目的地 Top N。

可選補充項目：

- 起點 -> 目的地 路線組合 Top N。

資料來源與呈現方式建議如下：

| 項目 | 資料來源 | 建議口徑 | 呈現方式 |
|---|---|---|---|
| 起點 Top N | `tasks.start_point` | `GROUP BY start_point` | 表格 |
| 目的地 Top N | `tasks.target_point` | `GROUP BY target_point` | 表格 |
| 路線組合 Top N | `tasks.start_point`, `tasks.target_point` | `GROUP BY start_point, target_point` | 表格 |

第一版建議先用表格而不是熱圖，原因如下：

- 現況最穩的是文字欄位統計，不是地圖座標型統計。
- 地圖熱圖會牽涉另一套視覺化座標與圖層規劃，風險不必要地擴大。
- 表格可以更快對齊真實資料定義，也更容易驗算。

若要更保守，第一版甚至可以只做：

- `Top N 名稱`
- `count`

百分比、排序箭頭、熱度色階都可以晚一點再補。

## 6. GUI 方案比較

本次只比較「不改現行主畫面配置」的三種做法。

| 方案 | 對現有主控台干擾程度 | 開發成本 | 後續擴充性 | 與目前 `main.py` 結構相容性 | 是否容易保持主畫面不動 | 評語 |
|---|---|---|---|---|---|---|
| 主畫面新增按鈕，開啟獨立子視窗 | 低 | 低到中 | 高 | 高 | 高 | 最符合本次目標 |
| 主畫面新增按鈕，開啟獨立 dialog / secondary window | 低 | 低 | 中 | 高 | 高 | 適合短暫查看，不一定適合長時間開著監看 |
| 主畫面新增按鈕，切換到獨立的績效頁視圖 | 中到高 | 中到高 | 中 | 中 | 低 | 需要改主畫面視圖切換結構，違背「主畫面維持不動」 |

### 第一版推薦方案

第一版推薦：

- 主畫面新增按鈕，開啟獨立子視窗。

推薦理由如下：

- 最能維持現行主控台版面與操作方式不變。
- 和目前 `SelectedMap` 的互動模式相近，使用者心智負擔低。
- 績效頁可以有自己的 refresh timer，不必綁進主畫面既有的 0.3 秒 / 2 秒輪詢。
- 後續若要增加其他 KPI、分區塊或切換頁籤，獨立視窗比 dialog 更有延展性。

對於 dialog / secondary window，本次不列為首選的原因不是不能做，而是：

- 績效頁更像一個可持續查看的讀取面板，不像一次性填表對話框。
- 若未來要加更多統計區塊，dialog 很快會長成半個正式頁面。

## 7. 技術策略

### 7.1 資料讀取策略

第一版建議直接從 `tasks` table 做聚合查詢，不引入新的中介儲存或快取表。

原因如下：

- 本次只做讀取型統計。
- 統計口徑可直接依賴目前已存在的 `status`、`start_point`、`target_point`、`mission_content`。
- 先避免為了報表頁過早新增額外同步機制。

### 7.2 `TaskDBManager.py` 擴充方向

建議在 `TaskDBManager.py` 新增統計查詢 methods，而不是把 SQL 聚合寫進 `main.py`。

建議方法方向如下：

- `get_task_status_summary()`
- `get_task_volume_by_mission(limit=None)`
- `get_task_start_hotspots(limit=10)`
- `get_task_target_hotspots(limit=10)`
- `get_task_route_hotspots(limit=10)`

這樣的分工比較符合目前 `M05 Persistence Layer` 的責任邊界：

- SQL 與聚合邏輯留在 DB manager。
- UI 只負責顯示與刷新。

### 7.3 績效頁刷新頻率

第一版不建議沿用主畫面 2 秒 refresh，也不需要接入 0.3 秒 MiR polling。

建議刷新策略：

- 開啟績效頁時先立即刷新一次。
- 視窗開啟後以 10 到 30 秒為週期刷新。
- 提供手動刷新按鈕。

推薦預設值：

- 15 秒。

原因如下：

- 任務統計不是秒級控制訊號，不需要高頻更新。
- 降低對 DB 的額外壓力。
- 降低和主畫面 polling 競爭資源的機會。

### 7.4 與主畫面高頻 MiR polling 解耦

績效頁第一版應只依賴 DB，不直接依賴 MiR API polling。

理由如下：

- 任務量與熱區本質上是任務紀錄統計，不是即時機器人控制畫面。
- 主畫面的 MiR status、battery、heartbeat、map position polling 已經夠多，不宜把績效頁再綁上去。
- 若直接綁 MiR polling，會讓績效頁與主控台的故障模式彼此牽連。

### 7.5 呈現元件策略

第一版建議先用：

- 數字卡片。
- 簡單表格。

不建議第一版就導入：

- 複雜圖表元件。
- 地圖熱圖。
- 外部 BI 元件。

### 7.6 與 `MainWindow` 的低耦合做法

若採獨立新視窗，建議結構如下：

- `MainWindow` 只負責提供入口按鈕與開啟視窗。
- 績效頁視窗自行持有刷新 timer。
- 績效頁只依賴 `TaskDBManager` 或一個更薄的 read-only service。
- 不讓績效頁直接存取主畫面的高頻旗標，例如 `is_AMR_idle`、`is_low_battery`、`polling_busy`。

若要再更保守一點，建議不要把績效頁完整實作再塞回 `main.py`，而是至少抽成單獨 class 或單獨檔案，減少 `main.py` 持續膨脹。

## 8. 分階段規劃

| Phase | 狀態 | 目標 | 主要變更 | 驗收重點 | 建議文件類型 |
|---|---|---|---|---|---|
| P1 | [x] 已完成 | 統計查詢與資料模型整理 | 定義任務量、熱區、路線 Top N 的聚合查詢與回傳格式。 | R06 | `documents/implements/R06-task-statistics-queries-for-performance-dashboard.md` |
| P2 | [ ] | GUI 入口按鈕與績效頁骨架 | 主畫面新增入口按鈕；建立獨立績效視窗骨架；規劃 refresh 流程 | 主畫面版面不重排；可開啟/關閉績效視窗；刷新不干擾主畫面 | `FXX` |
| P3 | [ ] | 任務量卡片與熱區表格 | 接入查詢結果，完成數字卡片、起點/目的地 Top N、可選路線 Top N | 畫面可讀、數字可驗算、空資料狀態明確 | `FXX` + `RXX` |
| P4 | [ ] | 驗收與擴充預留 | 確認命名、欄位定義、刷新策略、未來 KPI 擴充點 | 第一版範圍收斂，小而穩；後續 KPI 不需回頭重做入口設計 | `FXX` 或後續 `PXX` |

### P1. 統計查詢與資料模型整理

目標：

- 先把「統計口徑」說清楚，再做 UI。

主要變更：

- 在 `TaskDBManager.py` 規劃聚合查詢 methods。
- 明確定義任務量 summary 與 Top N 資料結構。
- 釐清第一版統計是否以「全保留資料」為口徑。
- 將 `created_at`、資料保留週期等不確定項標成待確認。

驗收重點：

- 每個統計項目都能對應到具體欄位。
- 不需要額外依賴 MiR API 即可產生資料。
- 對「累積值」與「即時值」的口徑有清楚區分。

建議文件類型：

- `RXX`: 績效統計查詢與讀模型。

### P2. GUI 入口按鈕與績效頁骨架

目標：

- 在不動主畫面主區塊的前提下，提供可進入的績效頁入口。

主要變更：

- 主畫面新增「績效分析」入口按鈕。
- 建立獨立績效視窗。
- 建立初始版面骨架、標題區、手動刷新按鈕與空狀態。
- 規劃視窗生命週期與 refresh timer。

驗收重點：

- 主畫面原有操作區不重新排版。
- 績效視窗可獨立開關，不阻斷主畫面操作。
- 視窗刷新時不影響主畫面原有 polling。

建議文件類型：

- `FXX`: 績效頁 GUI 入口與視窗骨架。

### P3. 任務量卡片與熱區表格

目標：

- 把第一版有價值的統計完整接到畫面上。

主要變更：

- 顯示任務量卡片。
- 顯示起點 Top N 表格。
- 顯示目的地 Top N 表格。
- 若資料量足夠，顯示路線組合 Top N 表格。
- 可選顯示 `mission_content` 分組表格。

驗收重點：

- 畫面一打開就能回答「任務量如何」與「熱區在哪裡」。
- 每個數字都可回推到 SQL 口徑。
- 空資料、少量資料、不足 Top N 時有合理顯示。

建議文件類型：

- `FXX`: 績效頁第一版 UI 呈現。
- `RXX`: 任務量與熱區聚合查詢擴充。

### P4. 驗收與擴充預留

目標：

- 在不超出第一版範圍的前提下，為第二版 KPI 擴充留接口。

主要變更：

- 整理欄位命名與口徑說明。
- 確認 refresh 頻率與查詢成本。
- 確認後續若要加入其他 KPI，是否可沿用相同視窗結構與查詢分層。

驗收重點：

- 第一版沒有為了未來擴充而過度設計。
- 但未來要加 KPI 時，也不需要推翻「入口按鈕 + 獨立績效頁」的方向。

建議文件類型：

- 若只是實作與驗收，延續 `FXX` 即可。
- 若要規劃第二版 KPI，再新開一份 `PXX`。

## 9. 風險與權衡

### 9.1 `main.py` 已經很大，新增績效頁是否會讓耦合更重

風險：

- 若把績效頁 UI、查詢、refresh timer、格式轉換全部塞進 `main.py`，主畫面會更難維護。

建議權衡：

- `MainWindow` 只保留入口按鈕與開窗責任。
- 統計查詢放在 `TaskDBManager.py`。
- 績效頁視窗至少獨立成單一 class。

### 9.2 如果 `tasks` table 沒有足夠歷史欄位，這版統計要如何保守設計

風險：

- 若沒有可確認的時間欄位與完整保留策略，就不適合承諾期間報表與時間型 KPI。

建議權衡：

- 第一版只做狀態數量與文字欄位聚合。
- 明確標示目前是「依保留中的任務資料統計」。
- 日期區間、趨勢圖、等待時間、執行時間全部延後。

### 9.3 熱區是否先用表格取代地圖熱圖

風險：

- 若第一版就做地圖熱圖，會把專案帶往另一組 UI 與視覺化複雜度。

建議權衡：

- 先用 Top N 表格取代熱圖。
- 等到欄位口徑穩定、使用者確認有價值，再考慮第二版視覺化。

### 9.4 現在只做任務量與熱區，如何保留之後擴充 KPI 的空間

風險：

- 若第一版把頁面寫死成單一表格，之後要加 KPI 會再重構一次。

建議權衡：

- 規劃為「摘要區 + 明細區」的基本骨架。
- 查詢 methods 以單一統計項目拆分，而不是一支大而全 method。
- 讓後續 KPI 可以追加新的區塊，不必回頭改主畫面入口模式。

### 9.5 採用獨立新頁面 / 新視窗後，如何避免和現有主畫面互相干擾

風險：

- 若共用過多 timer 或共享過多主畫面狀態，仍可能互相影響。

建議權衡：

- 績效頁使用自己的 refresh timer。
- 不依賴主畫面的高頻 MiR polling。
- 不把績效頁做成會修改任務資料的管理介面。
- 第一版保持唯讀。

## 10. 建議後續文件

本份 P04 之後，最可能接續的文件如下：

- `FXX`: 績效頁 GUI 與入口按鈕。
- `RXX`: 統計查詢與 `TaskDBManager` 擴充。
- `FXX`: 任務量卡片與熱區表格整合。
- `PXX`: 績效頁第二版 KPI 規劃。

可考慮的文件主題範例：

- `documents/implements/FXX-performance-dashboard-entry-and-window.md`
- `documents/implements/RXX-task-statistics-queries-for-performance-dashboard.md`
- `documents/implements/FXX-performance-dashboard-v1-task-volume-and-hotspots.md`
- `documents/planning/P05-mir-performance-dashboard-phase-2-kpis.md`

## 11. 待確認事項

以下事項建議在進入 FXX / RXX 前先確認：

- `tasks` 實際 schema 是否確實存在 `created_at`，且歷史資料品質可用。
- `tasks` 是否有 DB 層級的清理、歸檔或保留週期機制。
- 歷史資料中是否只存在 `Pending`、`Executing`、`Completed`、`Aborted` 四種狀態，或還有 legacy 狀態值。
- 第一版熱區統計是否要以「全部保留任務」為預設口徑，還是要先限定某些狀態。
- 路線組合 Top N 是否預設納入第一版主畫面，或先列為可選區塊。

## 12. 結論

本次方案的核心原則是：

- 不修改現行主控台主區域版面。
- 只新增入口按鈕，導向獨立績效頁。
- 第一版先小而穩，只做最容易從現況資料落地的任務量與起點/目的地熱區。

在目前專案基礎下，最務實的方向是：

- 以 `tasks` table 的既有欄位做聚合查詢。
- 以 `TaskDBManager.py` 承接統計 SQL。
- 以獨立子視窗承接績效頁 UI。
- 以數字卡片與 Top N 表格完成第一版。

這樣可以先把營運績效頁做出來，同時避免把主控台變成另一輪大規模 UI 重構。
