---
author: Codex
date: 2026-06-23
title: MainWindow 拖曳、下拉式選單與地圖互動卡頓問題
uuid: 2f0f6c7f6d1e4c0f93b8f4d8b6d2a101
version: v1
status: proposed
---

# B01 - MainWindow 拖曳、下拉式選單與地圖互動卡頓問題

## 1. Bug 概述

操作人員反映桌面 UI 在以下情境會出現明顯的「卡住」或「不順」：

- 拖曳主視窗
- 點擊或展開下拉式選單
- 操作主地圖區域

這個症狀不是單一 widget 的局部問題，而是以 `MainWindow` 為中心的整體互動反應變慢，並且在定時輪詢啟用時最明顯。

## 2. 修正目標

在不改變以下業務行為的前提下，降低主操作畫面的可見卡頓：

- MiR 狀態監控
- 任務清單顯示
- 地圖 marker 顯示
- 任務狀態對帳與同步

這次修正應保留現有操作流程，但要把昂貴的 polling、重繪與表格更新工作移出 UI event loop，或至少降低它們在 UI thread 上執行的頻率與成本。

## 3. 目前發現

### F1. 高頻輪詢直接跑在 UI thread

`MainWindow` 目前直接在 UI thread 啟動多個 timer：

- `poll_timer` 每 `5000ms`
- `fast_timer` 每 `300ms`
- `slow_timer` 每 `10000ms`
- `refresh_timer` 每 `2000ms`

相關程式位置：

- `main.py:1522-1559`

其中最關鍵的是 `fast_timer`，因為它每 `300ms` 呼叫：

- `query_mir_info()`
- `poll_mir_position()`

而這兩條路徑目前仍包含同步工作。

### F2. 同步 MiR HTTP 呼叫仍會阻塞 event loop

以下由 UI 觸發的 polling 路徑，會直接同步呼叫 `requests.get()`：

- `functions.check_MiR_status()`
- `functions.check_MiR_status_state_ID()`
- `functions.get_battery_level()`
- `functions.check_MiR_status_position()`
- `functions.get_pending_mission_names()`

相關程式位置：

- `functions.py:133-185`
- `functions.py:495-522`

其中多個 request 沒有設定 timeout。一旦 MiR API 回應變慢，UI thread 就會持續阻塞到 request 完成為止。

### F3. `query_mir_info()` 每 300ms 做的事情太多

`query_mir_info()` 目前會：

- 取得完整 MiR status
- 把格式化 JSON 持續 append 到 `plntxtEdit_Info`
- 取得 pending mission names
- 取得目前 MiR `state_id`
- 刷新狀態顯示

相關程式位置：

- `main.py:2729-2753`

這代表一次 `300ms` timer tick 可能同時觸發多次 HTTP 呼叫，加上文字元件持續增長與 repaint 成本。

### F4. Pending mission 名稱查詢成本會隨佇列成長

`functions.get_pending_mission_names()` 會先抓 mission queue 清單，再針對每一筆 pending mission 額外呼叫 API 解析 mission 名稱。

相關程式位置：

- `functions.py:495-522`

當 pending queue 變多時，這段成本會跟著提高，而且它目前仍跑在 UI thread 上，直接影響拖曳與下拉互動。

### F5. 任務表格更新過於頻繁，且每次都整張重建

`refresh_task_list()` 目前會：

- 查詢 pending 與 executing tasks
- 清空整張表
- 重建所有 `QTableWidgetItem`
- 每列重新建立刪除按鈕 widget
- 重新做整表置中
- 呼叫 `resizeRowsToContents()`

相關程式位置：

- `main.py:2566-2636`

這段每 `2000ms` 會跑一次，而 `query_mir_status_db()` 在自己的流程結尾也會再次呼叫 `refresh_task_list()`。

相關程式位置：

- `main.py:2758-2815`

因此操作人員互動畫面時，可能會遇到連續兩次整表重建。

### F6. 專案已經有 worker pattern，但最熱的 polling 路徑沒有使用

`DBWorker` 已存在，而且目前 `poll_room_status()` 已經用它把部分工作移出 UI thread，代表這個專案已經接受這種寫法。

相關程式位置：

- `main.py:805-826`
- `main.py:1947-1970`

因此這次卡頓修正應優先延伸既有 worker pattern，而不是再引入另一套新的並行模型。

## 4. 範圍

### In Scope

- `main.py`
- `functions.py`
- 可行時補上聚焦於 UI responsiveness 或 polling 行為的測試
- 重構 `MainWindow` 的 polling 流程以降低 UI thread 阻塞

### Out Of Scope

- 修改 mission 業務規則
- 重設整個 `MainWindow` 架構
- 把 UI 從 `QTableWidget` 全面改寫成其他 widget 架構
- 修改 task DB schema
- 修改 site config schema

## 5. 根因陳述

這次卡頓的主要原因是 `MainWindow` 將高頻 MiR 輪詢、任務表格重建、overlay 重繪與狀態刷新工作直接放在 UI thread 執行。當同步 HTTP 請求或大量表格重建耗時變長時，Qt 無法順暢處理滑鼠與 widget 互動事件，因此拖曳、展開下拉選單與地圖點擊都會出現延遲與卡頓。

## 6. 驗收條件

- **情境 1：視窗拖曳維持順暢**
  - **Given** 主操作視窗已開啟，且 online polling 啟用
  - **When** 操作人員連續拖曳自訂 title bar 數秒
  - **Then** 視窗移動應保持順暢，不應因 polling 出現明顯停頓

- **情境 2：下拉式選單互動維持順暢**
  - **Given** 主操作視窗已開啟，且 online polling 啟用
  - **When** 操作人員點擊 `cmb_location`、`cmb_location2` 或 `cmb_mission`
  - **Then** 下拉選單應能即時展開，不應在 popup 出現前出現明顯 freeze

- **情境 3：地圖互動維持順暢**
  - **Given** 地圖點擊模式已啟用
  - **When** 操作人員點擊或操作主地圖 overlay
  - **Then** 點擊回饋與座標更新應正常顯示，不應被無關 polling 造成明顯卡頓

- **情境 4：MiR 狀態更新仍然正常**
  - **Given** 系統在線且 MiR 狀態發生變化
  - **When** 修正後的 polling 持續運作
  - **Then** 狀態標籤、robot marker 與電量顯示仍應正確刷新

- **情境 5：任務清單仍正確反映 DB 狀態**
  - **Given** PostgreSQL 中的 task 記錄發生變化
  - **When** 修正後的 refresh cycle 執行
  - **Then** 任務表格仍應正確顯示目前 pending / executing tasks，且不應出現重複列或失效的刪除按鈕

- **情境 6：API 變慢時整個視窗不應被凍結**
  - **Given** MiR API 暫時回應緩慢
  - **When** polling 發生
  - **Then** UI 應仍可互動，即使狀態資料延遲或暫時不可用也不應拖垮整個視窗

## 7. 建議修正策略

### Phase 1. 先拿掉最重的 UI thread 壓力

先做低風險且預期會立刻改善的調整：

- 減少 `query_mir_info()` 內的工作量
- 停止每 `300ms` 持續 append 大段 status JSON
- 不要在 `300ms` 路徑上解析 pending mission names
- 避免同一輪 refresh 中重複呼叫 `refresh_task_list()`
- 把 `set_table_items_center()` 與 `resizeRowsToContents()` 移出 per-row loop

這一階段應該在 worker 化之前就能先讓互動變順。

### Phase 2. 將高熱 polling 路徑移到 worker thread

延用既有 `DBWorker` pattern 處理最熱的 polling 工作：

- MiR status fetch
- MiR position fetch
- 若仍昂貴，則包含 mission queue state reconciliation

原則：

- worker thread 只負責抓資料
- UI widget 更新只能回到 main thread 透過 signal / callback 執行
- 必須避免 timer 疊出大量重複 worker

### Phase 3. 穩定 refresh cadence

重新整理 timer 職責，讓每個 timer 只做一類工作：

- fast timer：只保留動畫等級或輕量狀態更新
- slow timer：電量與 heartbeat
- refresh timer：task table 對帳與刷新

目標不是取消 polling，而是讓高頻 timer 只做便宜或已背景化的工作。

## 8. 實作備註

- 優先延伸 `DBWorker` 用法，不要額外引入第二套並行抽象。
- `functions.py` 的 API helper 盡量維持現有 caller 相容，但缺少 timeout 的地方要補齊。
- 不可從 worker thread 直接更新 Qt widget。
- 若修正過程引入共享 polling state，需保持狀態集中、清楚，不要散落在無關 flag。
- 若完整 diff-based task-table renderer 對這次 bugfix 來說過大，可以暫時保留整表 refresh，但必須移除明顯重複與高成本的重建步驟，並讓 UI 不再明顯卡頓。

## 9. 驗證計畫

### 手動驗證

以下檢查需在 online polling 開啟的情況下進行：

1. 開啟主操作視窗，連續拖曳 10-15 秒。
2. 在 polling 持續運作時，重複開關 `cmb_location`、`cmb_location2`、`cmb_mission`。
3. 在 robot position 持續更新時，重複點擊主地圖。
4. 確認 battery、status label、robot marker 仍正常更新。
5. 確認 pending / executing task rows 顯示正確，且 delete button 仍正常運作。

### 技術驗證重點

- 確認沒有引入跨 thread 直接更新 Qt widget
- 確認 worker 會正確 cleanup，不會累積
- 確認 repeated polling 不會造成重複 signal 綁定
- 確認 task table refresh 後 row count 與狀態顯示仍正確

## 10. 風險

### R1. 跨 thread 更新 UI 的錯誤

把 polling 移出 UI thread 是正確方向，但也會帶來從 worker thread 直接動到 Qt widget 的風險。實作時必須保證 worker 只回傳資料，UI 更新回到 main-thread callback。

### R2. Worker 疊加執行

如果每次 timer tick 都不加防護地啟動新 worker，應用程式可能只是把 UI 卡頓換成 polling backlog。因此每條高頻 polling 路徑都需要 active-job guard。

### R3. 刷新正確性回歸風險

降低 refresh 頻率或移除重複 refresh 後，可能暴露原本隱藏的狀態顯示或任務對帳假設。驗證時必須同時檢查互動順暢度與功能正確性。

## 11. 升級規則

若修正過程中需要做以下任一項，應升級為 `ddd-plan`：

- 將 `QTableWidget` 換成全新的展示元件
- 在多個視窗之間導入共享 polling coordinator
- 把 `functions.py` 重構成完整非同步 API client layer
- 將整體 polling 模型從 timer-driven 改成 event-driven

若本次工作仍落在 timer 整理、worker 抽離、timeout 補強與 task-table refresh 優化，則應維持為 `BXX` bugfix。

## 12. 下一個聊天室的建議執行順序

1. 先做 Phase 1 的低風險減壓調整。
2. 觀察拖曳與下拉互動是否已有明顯改善。
3. 再把 `query_mir_info()` 與 `poll_mir_position()` 改成 worker 化。
4. 重新執行手動 responsiveness 驗證。
5. 若仍有卡頓，再往更深的 task-table refresh 優化收斂。

## 13. 交接提示詞

下一個聊天室可直接使用：

`請依照 documents/implements/B01-main-window-ui-stutter-during-drag-and-dropdown.md 修正 MainWindow 拖曳、下拉式選單、地圖互動卡頓問題，先做低風險改善，再做 worker 化，完成後回報驗證結果。`
