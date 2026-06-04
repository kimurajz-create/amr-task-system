---
author: Codex
date: 2026-06-04
title: 任務統計查詢與資料模型整理
uuid: 837ca4fc41ac4e359f77a155e0a80c30
version: v1
planning: documents/planning/P04-mir-performance-dashboard-task-volume-and-route-hotspots.md
status: completed
---

# R06 任務統計查詢與資料模型整理

## 1. Scope

P04 P1 先把績效 dashboard 需要的統計入口收斂到 `TaskDBManager.py`，讓後續 UI 階段只負責顯示 summary 與 Top N 結果，不再各自拼 SQL。

## 2. Goals

- 在 `TaskDBManager.py` 提供可直接給 dashboard 使用的任務量 summary 查詢。
- 在同一層提供 `mission_content`、`start_point`、`target_point`、`start_point -> target_point` 的 Top N 聚合查詢。
- 明確定義第一版統計口徑：以目前 `tasks` table 保留資料為準，不先引入日期區間或趨勢線。
- 對空白文字欄位與 legacy status 保留可預期的回傳格式。

## 3. Changes

### R1. 新增任務量 summary 查詢

- 新增 `get_task_status_summary()`。
- 回傳固定欄位：
  - `pending_count`
  - `executing_count`
  - `completed_count`
  - `aborted_count`
  - `active_count`
  - `finished_count`
  - `other_status_count`
  - `total_count`
  - `status_breakdown`
- `status_breakdown` 保留原始狀態名稱與筆數，讓未來若 DB 中仍有 legacy status，不會被靜默吞掉。

### R2. 新增 Top N 統計查詢

- 新增 `get_task_volume_by_mission(limit=None)`。
- 新增 `get_task_start_hotspots(limit=10)`。
- 新增 `get_task_target_hotspots(limit=10)`。
- 新增 `get_task_route_hotspots(limit=10)`。
- Top N 查詢都由 DB 層完成 `GROUP BY`、排序與 `LIMIT`，UI 只接結果。

### R3. 定義第一版欄位與回傳口徑

- 第一版統計全部以 `tasks` 目前保留資料計算。
- `Pending` / `Executing` 屬於較接近即時佇列的數字。
- `Completed` / `Aborted` / `Total` 屬於保留中歷史資料的累積值。
- `route` 結果會額外提供 `route_label`，格式固定為 `<start_point> -> <target_point>`。

### R4. 補上輸入保護與空白值正規化

- Top N `limit` 僅接受正整數或 `None`，非法值會拋出 `ValueError`。
- `mission_content`、`start_point`、`target_point` 的空字串 / 空白 / `NULL` 會統一呈現為 `(未填寫)`。
- 這份正規化同時寫在 SQL 聚合與 Python 回傳層，避免 UI 看到空標籤。

## 4. Test Coverage

| Test ID | Type | Coverage |
|---|---|---|
| R06-T1 | unit | `get_task_status_summary()` 會回傳固定 summary 欄位並保留 legacy status breakdown |
| R06-T2 | unit | `get_task_volume_by_mission()` 會使用 blank-safe grouping 並帶入指定 limit |
| R06-T3 | unit | 起點 / 目的地 / 路線 hotspot 查詢會回傳固定欄位，路線結果會帶 `route_label` |
| R06-T4 | unit | 非法 Top N limit 會被拒絕，避免不合理查詢設定流入 DB 層 |

## 5. Verification

```bash
python -m unittest tests.test_task_statistics_queries
```

## 6. Notes

- 這一版沒有把 `created_at` 納入條件，因為 `P04` 已標記該欄位存在性、資料品質與保留週期仍待確認。
- 若後續要加入「今日任務量」或「近 7 日趨勢」，應先確認 `tasks` schema 與歷史資料可信度，再擴充同一組查詢入口。
- 目前 methods 都是 read-only 聚合查詢，沒有引入任何新的 MiR API 依賴。
