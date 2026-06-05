---
author: Codex
date: 2026-06-05
title: 績效 dashboard v1 任務量與熱點統計
uuid: 83b84f4f4a4d41b0b58d9c43411d3f2d
version: v1
planning: documents/planning/P04-mir-performance-dashboard-task-volume-and-route-hotspots.md
status: completed
---

# F02 績效 dashboard v1 任務量與熱點統計

## 1. Scope

本次實作對應 `P04` 的 `P3`，把 `R06` 已完成的統計查詢正式接進 dashboard 視窗，讓使用者在同一個畫面看到任務總量摘要、任務類型分組、起點 Top N、目的地 Top N、路線 Top N。

這一版只處理既有 `tasks` table 已可直接支援的聚合資料，不新增時間區間、SLA、等待時間、MiR heartbeat 或 API 成功率等 KPI。

## 2. Requirement / User Story

- **As a** 需要快速理解 MiR 任務分布的管理者
- **I want** 在 dashboard 視窗直接看到任務量與熱門路線統計
- **So that** 我不用另外查資料庫，也能快速判斷目前任務集中在哪些任務類型、起點、目的地與搬運路線

## 3. Acceptance Criteria

- **Scenario 1: dashboard 顯示任務量摘要與分組**
  - **Given** `TaskDBManager` 可以回傳任務摘要與 `mission_content` 分組結果
  - **When** 使用者開啟或刷新 dashboard
  - **Then** 視窗會顯示 Pending / Executing / Completed / Aborted / Total 卡片
  - **And** 顯示任務類型分組列表

- **Scenario 2: dashboard 顯示起點、目的地、路線 Top N**
  - **Given** `TaskDBManager` 可以回傳起點、目的地與路線聚合查詢
  - **When** 使用者開啟或刷新 dashboard
  - **Then** 視窗會顯示起點 Top N、目的地 Top N、路線 Top N 三個區塊
  - **And** 每列至少包含標籤與數量

- **Scenario 3: snapshot provider 發生錯誤時保留警示訊息**
  - **Given** dashboard 刷新過程任一統計查詢失敗
  - **When** 視窗執行刷新
  - **Then** 視窗狀態列顯示 warning 訊息
  - **And** 不會影響主畫面既有 polling 生命週期

## 4. Test Scenarios / Examples

| ID | Scenario | Given | When | Then | Priority |
|---|---|---|---|---|---|
| F02-T1 | snapshot builder 會把 mission / hotspot 資料映射成 section rows | 傳入摘要與四組 Top N 資料 | 建立 snapshot | 每個 section 都帶固定 rows 結構與標題 | High |
| F02-T2 | dashboard refresh 會把 section rows 套到視窗 | 視窗吃到完整 snapshot provider | 觸發 refresh | section 內容會更新成多列文字，不再停留在 placeholder | High |
| F02-T3 | `MainWindow` snapshot provider 會整合 `TaskDBManager` 的五個統計入口 | 有 fake db manager | 呼叫 `get_performance_dashboard_snapshot()` | 回傳 summary + 任務量 + 三組 hotspots + 路線 Top N | High |

## 5. Implementation Notes

- 延續 `performance_dashboard.py` 作為 dashboard UI 模組，不把統計顯示細節塞回 `main.py`
- `build_performance_dashboard_snapshot()` 擴充為接受：
  - `task_status_summary`
  - `task_volume_by_mission`
  - `start_hotspots`
  - `target_hotspots`
  - `route_hotspots`
- section 以固定 `rows` 格式描述，UI 端只負責 rendering，不在 widget 內重新拼資料
- `MainWindow.get_performance_dashboard_snapshot()` 改為一次整合 `R06` 提供的五個查詢方法
- 若任一查詢失敗，dashboard 維持 warning banner，避免把例外往主畫面 timer 擴散

## 6. Verification

```bash
python -m unittest tests.test_performance_dashboard_window
python -m unittest tests.test_task_statistics_queries
```

## 7. Notes

- 本次不新增新的 SQL 聚合方法；查詢邏輯沿用 `R06`
- 若後續要加入時間區間篩選、SLA 或等待時間 KPI，應在新的 `FXX` / `PXX` 文件內擴充，而不是把 `P3` 視為最終 dashboard 形態
