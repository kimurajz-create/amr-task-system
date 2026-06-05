---
author: Codex
date: 2026-06-04
title: 績效 dashboard 入口與視窗骨架
uuid: 9f8a7d8c7b5346c4b8a3a4c2f8d5e1b2
version: v1
planning: documents/planning/P04-mir-performance-dashboard-task-volume-and-route-hotspots.md
status: completed
---

# F01 績效 dashboard 入口與視窗骨架

## 1. Scope

本次實作對應 `P04` 的 `P2`，先把績效 dashboard 從主畫面導入可開啟、可重開、可定時刷新的獨立視窗骨架。

這一階段不直接完成任務量 / 熱區 Top N 呈現，而是先把後續 `P3` 要掛載的視窗容器、刷新節奏與主程式整合點固定下來。

## 2. Requirement / User Story

- **As a** 調度員或現場管理者
- **I want** 從主畫面快速打開績效 dashboard 視窗，看到目前統計頁面骨架與刷新狀態
- **So that** 後續任務量與熱區統計接入時，不需要再重做入口、視窗生命週期與刷新機制

## 3. Acceptance Criteria

- **Scenario 1: 主畫面可開啟 dashboard**
  - **Given** 使用者已進入 `MainWindow`
  - **When** 使用者從右上角使用者選單點擊 `績效看板`
  - **Then** 系統會開啟績效 dashboard 視窗

- **Scenario 2: dashboard 以單例方式重用**
  - **Given** dashboard 視窗已經建立過
  - **When** 使用者再次點擊 `績效看板`
  - **Then** 系統會聚焦既有視窗，而不是再開一個新的實例

- **Scenario 3: 視窗具備刷新骨架**
  - **Given** dashboard 視窗已開啟
  - **When** 視窗初始化或使用者點擊 `立即刷新`
  - **Then** 視窗會更新最後刷新時間，並顯示目前已接入/待接入的區塊狀態

- **Scenario 4: 主畫面 polling 不受影響**
  - **Given** 主畫面既有 MiR polling / DB refresh timer 正在運作
  - **When** 使用者開啟或關閉 dashboard 視窗
  - **Then** 主畫面既有 timer 與調度流程不需要為 dashboard 改變生命週期

## 4. Test Scenarios / Examples

| ID | Scenario | Given | When | Then | Priority |
|---|---|---|---|---|---|
| F01-T1 | dashboard 骨架會吃到 snapshot provider | 視窗使用假的 provider 建立 | 執行刷新 | 狀態文字、卡片值、最後刷新時間會更新 | High |
| F01-T2 | dashboard controller 會重用既有視窗 | 已透過 controller 開過一次視窗 | 再次呼叫 open | 回傳同一個視窗實例 | High |
| F01-T3 | 關閉視窗只會隱藏，不會銷毀 | dashboard 視窗已建立 | 使用者關閉視窗 | 視窗被隱藏，可再次 reopen | Medium |

## 5. Implementation Notes

- 新增 `performance_dashboard.py` 封裝 dashboard 視窗與單例 controller，避免把更多 UI 狀態塞回 `main.py`
- `MainWindow` 只負責提供入口與 snapshot provider
- 這一版先接入 `TaskDBManager.get_task_status_summary()` 作為摘要卡片資料來源，任務量 / 起點 / 目的地 / 路線 Top N 仍保留為 `P3` placeholder
- dashboard 自己管理 15 秒 refresh timer，不改動主畫面既有 fast / slow / refresh polling

## 6. Verification

```bash
python -m unittest tests.test_performance_dashboard_window
python -m unittest tests.test_task_statistics_queries
```

## 7. Notes

- `P2` 先完成入口與視窗骨架，讓 `P3` 可以專注在統計綁定與 Top N 呈現
- 若後續 dashboard 需要更多篩選、時間區間或 KPI，應在新的 `FXX` / `PXX` 文件中擴充，而不是把 `P2` 視窗骨架無限制膨脹
