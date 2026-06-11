---
author: Codex
date: 2026-06-11
title: MiR 狀態驅動的 Status label 與地圖車子外圈顏色同步規劃
status: draft
version: v1
---

# P06 MiR 狀態驅動的 Status label 與地圖車子外圈顏色同步規劃

## 1. 背景

目前 `refactor/main-site-profile` 分支已完成 `site_profile`、main map overlay、dynamic marker layer 等重構，但 MiR 狀態呈現仍分散在多個 UI 更新點：

- `Status label` 內部自行維護 `state_id -> 顏色/名稱` 對照
- 地圖上的 robot marker 外圈尚未使用同一套狀態規則
- API 斷線與 mission queue 狀態不可用時，沒有統一切換到 `Unknown/Offline`
- MiR 狀態刷新後，label 與 marker 沒有保證由同一條 presentation 流程一起更新

主幹已經有一套較完整的做法，核心是將 MiR 狀態 UI 收斂為共用 mapping，並以單一 refresh 入口同步 `Status label` 與地圖 robot marker。本規劃的目標是把這套能力移植到 `refactor/main-site-profile`，同時維持既有 `site_profile` 架構與其他 UI 行為不變。

## 2. 目標

本次只處理下列行為：

- 右上角 `Status label` 依 MiR `state_id` 顯示對應狀態名稱與顏色
- 地圖 robot marker 外圈顏色依同一套 `state_id` 規則變化
- API 斷線或 mission queue 狀態不可用時，呈現 `Unknown/Offline` fallback
- 每次 MiR 狀態更新後，統一刷新 status label 與地圖 marker，避免兩邊不同步
- 保持邏輯可相容 `site_profile` 架構，不寫死 `company` / `hospital`
- 儘量沿用主幹命名與結構，例如 `MIR_STATE_UI`、`UNKNOWN_MIR_STATE_UI`、`_get_mir_state_ui()`、`_refresh_robot_status_presentation()`

## 3. 範圍

### In Scope

- `main.py` 內的 MiR 狀態 UI mapping 整理
- `Status label` 的狀態名稱與顏色同步
- main map robot marker 外圈顏色同步
- API / mission queue unavailable 的 fallback 狀態處理
- MiR 狀態 presentation refresh 流程收斂

### Out of Scope

- `selected_map` 的可點選區塊與顯示邏輯
- main map marker tooltip / task badge / pending mission marker 行為
- 任務調度、DB schema、MiR API 存取方式
- 現有 robot body 圖樣、地圖縮放邏輯、site config schema
- overlay summary card 或 performance dashboard 相關 UI

## 4. 目前觀察

### 主幹已存在的關鍵能力

- 模組層共用常數
  - `MIR_STATE_UI`
  - `UNKNOWN_MIR_STATE_UI`
- 共用 helper
  - `_has_mir_state_connection_issue()`
  - `_get_mir_state_ui(state_id)`
  - `_refresh_robot_status_presentation()`
- 呈現流程
  - `_update_status_label()` 不再自己維護 `status_map`，改由 `_get_mir_state_ui()` 提供名稱與顏色
  - `draw_robot_marker()` 直接使用 `state_ui["map_ring_color"]`
  - `query_mir_info()` 與 `query_mir_status_db()` 在狀態改變後呼叫同一個 refresh 入口

### `refactor/main-site-profile` 的缺口

- 尚未定義 `MIR_STATE_UI`
- 尚未定義 `UNKNOWN_MIR_STATE_UI`
- 尚未實作 `_get_mir_state_ui()`
- 尚未實作 `_refresh_robot_status_presentation()`
- `Status label` 仍在 `_update_status_label()` 內嵌 `status_map`
- `draw_robot_marker()` 目前只在移動狀態畫 glow，沒有 state-based 外圈
- `query_mir_info()` 更新完狀態後只刷新 label，沒有保證同步刷新 marker
- `query_mir_status_db()` 已有 `mir_status_poll_disconnected` 旗標，但未在 unavailable / restored 時統一刷新到 fallback UI

## 5. 設計方向

### 設計原則

- 一份 mapping，兩個 UI 使用
- 一個 refresh 入口，兩個視覺結果同步更新
- fallback 狀態由 connection issue 判定，不在多處散落 if/else
- 不碰 `site_profile` runtime map 與 selected map schema
- 不新增 company / hospital 分支判斷

### 建議結構

- 模組層常數
  - `MIR_STATE_UI`
  - `UNKNOWN_MIR_STATE_UI`
- `MainWindow` helper
  - `_has_mir_state_connection_issue()`
  - `_get_mir_state_ui(state_id)`
  - `_refresh_robot_status_presentation()`
- 呈現函式
  - `_update_status_label(state_id)`
  - `draw_robot_marker(painter, x, y)`
- 輪詢整合點
  - `query_mir_info()`
  - `query_mir_status_db()`
  - 視需要補上 `api_error_handler()`

## 6. 分階段規劃

| 階段 | 狀態 | 目標 | 內容 | 預計文檔 |
|---|---|---|---|---|
| P1 | [ ] 待開始 | 收斂 MiR state UI mapping | 將主幹的狀態名稱/顏色/外圈顏色 mapping 併入分支，補齊 fallback helper | F03 |
| P2 | [x] 已完成 | 同步 status label 與 robot ring | 讓 `_update_status_label()` 與 `draw_robot_marker()` 都使用同一份 state UI 資料 | F03 |
| P3 | [ ] 待開始 | 收斂 presentation refresh 流程 | 將 `query_mir_info()` / `query_mir_status_db()` 改為透過統一 refresh 入口更新 UI | F03 |
| P4 | [ ] 待開始 | 驗證 site_profile 相容性與 fallback | 驗證 company / hospital / 其他 site profile 不需特判，且 offline/unavailable 有一致呈現 | F03 |

## 7. 各階段詳述

## P1 收斂 MiR state UI mapping

### 目標

在 `main.py` 建立單一 MiR 狀態 UI 資料來源，提供名稱、label 顏色、map ring 顏色與 fallback 狀態。

### 內容

- 新增 `MIR_STATE_UI`
- 新增 `UNKNOWN_MIR_STATE_UI`
- 新增 `_has_mir_state_connection_issue()`
- 新增 `_get_mir_state_ui(state_id)`

### 完成條件

- [ ] `state_id` 對應名稱與顏色不再散落在多個函式
- [ ] connection issue 時可統一回傳 `Unknown/Offline`
- [ ] helper 不依賴特定 `site_profile`

### 風險

- 分支內有多個重複定義的 `_update_status_label()`，若沒有明確只保留最後有效邏輯，容易把舊實作混進來

## P2 同步 status label 與 robot ring

### 目標

讓 `Status label` 與 robot marker 外圈都使用同一份 state UI mapping。

### 內容

- 改寫最後生效的 `_update_status_label()`，改由 `_get_mir_state_ui()` 取 `name` / `label_color`
- 改寫 `draw_robot_marker()`，以 `state_ui["map_ring_color"]` 畫固定外圈
- 保留既有 robot body 與 overlay 幾何流程

### 完成條件

- [ ] label 顯示名稱與顏色來自共用 mapping
- [ ] robot ring 顏色來自同一份共用 mapping
- [ ] 不改動 map overlay 尺寸與機器人主體造型

### 風險

- 現行 marker 仍有 motion glow 邏輯，需決定是完全改成 state ring，或保留 glow 但讓 glow 與 state ring 並存
- 若兩者並存，需明確規範 ring 與 glow 的視覺優先順序

## P3 收斂 presentation refresh 流程

### 目標

每次 MiR 狀態更新後，label 與 marker 由同一個入口一起刷新。

### 內容

- 新增 `_refresh_robot_status_presentation()`
- `query_mir_info()` 更新 `current_mir_state_id` / `current_mission_text` / `api_error` 後，統一呼叫 refresh
- `query_mir_status_db()` 在 mission queue unavailable / restored / disconnect cleared 時統一呼叫 refresh
- 視需要讓 `api_error_handler()` 在首次 API error 時也刷新為 fallback 狀態

### 完成條件

- [ ] `query_mir_info()` 不再只更新 label
- [ ] `query_mir_status_db()` 在 fallback 切換點有明確 refresh
- [ ] label 與 marker 不再各自走獨立刷新路徑

### 風險

- 若 `last_robot_world_pos` 尚未建立，refresh 只會更新 label，不會重畫 marker；需確認這是可接受的初始行為

## P4 驗證 site_profile 相容性與 fallback

### 目標

確認這次變更只影響狀態呈現，不破壞 `site_profile` 與 main map overlay 既有架構。

### 內容

- 驗證 `company` / `hospital` / 其他 site profile 都不需額外分支
- 驗證 `Unknown/Offline` 在 API error 與 mission queue unavailable 兩條路徑都一致生效
- 驗證恢復連線後能回到對應 state 顏色與名稱

### 完成條件

- [ ] 無 `if self.site_profile == ...` 類型新邏輯
- [ ] offline/unavailable 顯示一致
- [ ] 恢復後 label 與 marker 一起回復

## 8. 建議實作順序

1. 先加入 `MIR_STATE_UI` 與 `UNKNOWN_MIR_STATE_UI`
2. 新增 `_has_mir_state_connection_issue()` 與 `_get_mir_state_ui()`
3. 改最後生效的 `_update_status_label()`
4. 改 `draw_robot_marker()`
5. 新增 `_refresh_robot_status_presentation()`
6. 改 `query_mir_info()`
7. 改 `query_mir_status_db()`
8. 視測試結果決定是否補 `api_error_handler()`

## 9. 驗證策略

- 手動切換常見 `state_id`
  - `Ready`
  - `Executing`
  - `Docking`
  - `Error`
- 模擬 API 失敗，確認 label 與 marker 都進入 `Unknown/Offline`
- 模擬 mission queue state `None`，確認 fallback 生效
- 恢復連線後確認 label 與 marker 同步恢復
- 驗證既有 map click、robot position redraw、site profile 載入流程不受影響

## 10. 非目標與不變項

- 不改 selected map UI
- 不改 task list / pending mission marker / tooltip 流程
- 不改 site config schema
- 不改 MiR API access method
- 不改 DB schema 與 task reconciliation 規則

## 11. 建議後續實作文檔

- `documents/implements/F03-mir-state-driven-status-label-and-robot-ring-sync.md`

這份 F03 建議聚焦在單檔 `main.py` 的行為收斂與驗證，不另拆 RXX，除非實作過程中發現 `_update_status_label()` 重複定義、polling callback 與 map overlay redraw 已經需要額外做結構性清理。
