# 任務排程器

## 範圍

主要檔案：`task_thread.py`

## 職責

本模組負責 UI 執行緒之外的背景任務派送流程。

主要職責包括：

- 從 PostgreSQL 輪詢最高優先序的待辦任務
- 將任務資料翻譯成 MiR 任務派送呼叫
- 等待 mission queue 完成
- 透過 DB manager 更新任務執行狀態
- 當沒有任務或電量過低時，把機器人送回充電站
- 把執行紀錄與完成訊號回傳給 UI

## 主要執行期物件

| 物件 | 用途 |
|---|---|
| `TaskThread` | 長時間運行的排程執行緒，負責派送並監看任務 |

## 依賴

- `main.py`：提供 runtime maps 與共用旗標
- `functions.py`：提供 MiR 任務派送與 mission queue 狀態查詢
- `TaskDBManager.py`：提供任務挑選與任務狀態持久化

## 執行流程

1. 從 DB 讀取最高優先序的待辦任務。
2. 若目前沒有任務，標記無任務狀態並將 MiR 送回充電站。
3. 透過 runtime maps 轉換 `start_point`、`target_point` 與 `mission_content`。
4. 向 MiR 送出整合後的任務。
5. 取得對應的 MiR mission queue id。
6. 在可取得 `mq_id` 的情況下，將任務標記為 `Executing` 並持久化。
7. 等待 mission queue 狀態變成 `Done` 或 `Aborted`。
8. 將完成事件回傳給 UI，然後繼續下一輪。

## 輸入

- 來自 PostgreSQL 的待辦任務資料列
- 來自 `MainWindow` 的 runtime mapping
- 由 UI 共用的電量與 idle 旗標

## 輸出

- 寫回 DB 的狀態更新，例如 `Executing`
- 傳回 UI 的 `finished_task` 訊號
- 描述排程狀態的紀錄訊息
- 派送到 MiR 的 mission 與回充 fallback 指令

## 目前內嵌於此的操作策略

- 沒有待辦任務時就把 MiR 送回充電站。
- 缺少 mission / location runtime mapping 時跳過本輪。
- 等待 queue 狀態時容忍暫時性的 MiR 斷線並重試。
- 低電量會在任務處理後觸發回充行為。

## 邊界

- 排程器擁有派送順序與 mission 完成等待邏輯。
- 它不應直接操作 widget，只應透過訊號回傳結果。
- 它目前依賴 `MainWindow` 狀態，實務上可行，但耦合偏高。

## 已知風險

- `TaskThread` 直接讀取 `MainWindow` 的共用旗標與 maps，降低獨立性。
- 對帳結果依賴外部 MiR queue 可用性，可能讓任務落在不明確的中間狀態。
- 「無任務回充」與「低電量回充」目前是 thread 行為，而不是清楚分離的領域規則。

## 可重構接縫

- 注入更窄的排程上下文，而不是整個 `MainWindow`。
- 將派送策略與執行緒生命週期拆開。
- 補上正式的任務狀態機文件與對應的實作守門機制。
