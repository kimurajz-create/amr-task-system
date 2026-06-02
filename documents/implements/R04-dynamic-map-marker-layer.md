---
author: Codex
date: 2026-06-02
title: MainWindow 動態 Map Marker Layer
uuid: 7e39ff0f8d0d45df91c4aa3b6d42c2a1
version: v1
planning: documents/planning/P02-map-marker-externalization-and-scaled-positioning.md
status: completed
---

# R04 MainWindow 動態 Map Marker Layer

## 1. 背景

P02 的 P1 已把 marker schema 與 runtime maps 收斂到 `site/*.json` 與 `build_site_runtime_maps()`。  
但主畫面仍然依賴 `ui_main.py` 內建的 `label_rp_*` widget 與 Designer 幾何座標，造成兩個問題：

- `hospital` 站點有 `label_rp_8` 到 `label_rp_13`，Designer 並沒有對應 widget，runtime data 雖然完整，UI 卻無法真正顯示。
- `company` / `hospital` 的 marker 幾何已經來自 site config，但 widget 生命週期仍綁在 Qt Designer，P2 想要的 configuration-driven marker layer 尚未完成。

## 2. 重構目標

- **領域收斂**：把 map marker widget 的建立、清理、重新定位全部收回 `MainWindow` runtime layer。
- **變更方向**：初始化時清掉 Designer 產生的 `label_rp_*`，再依 `MARKER_SPECS_BY_ID` 動態建立同名 marker widget。
- **風險控制**：保留 `marker_id == widget objectName == self.<marker_id>` 契約，避免影響 `refresh_label_tooltip()`、task layer、resize overlay 流程。

## 3. 重構需求

| ID | 需求 | 說明 | 驗收重點 |
|---|---|---|---|
| R1 | 動態 marker widget lifecycle | `MainWindow` 必須能在 runtime 清掉既有 `label_rp_*` 並依 marker specs 重建 | 主畫面不再依賴 `ui_main.py` 內固定 marker 幾何 |
| R2 | 保留 marker attribute contract | runtime 建立後仍要能用 `getattr(self, marker_id)` 取回 widget | 現有 tooltip / task 樣式流程不需改 API |
| R3 | 支援超過 Designer 既有數量的 marker | `hospital` 的 `label_rp_8` 到 `label_rp_13` 也必須能建立 | site config 新增 marker 時不需先改 `.ui` |
| R4 | 延續既有縮放定位路徑 | `resizeEvent()` 與 `_apply_main_map_shell_layout()` 仍透過 `_position_map_marker_widgets()` 套用 scaled geometry | P1/R03/B01 已完成的 geometry contract 不回退 |

## 4. 測試矩陣

| 測試案例 | 說明 | 結果 |
|---|---|---|
| Runtime marker rebuild | 驗證 runtime 會清掉既有 `label_rp_*`，並能建立 `label_rp_13` 這種 Designer 沒有的 id | 通過 |
| Company marker world-to-pixel parity | 驗證 `company` 仍由 `world_x_m/world_y_m` 推導 marker top-left pixel | 通過 |
| Company marker legacy UI scaling | 驗證 `company` marker 經縮放後仍落在既有 UI 尺寸對齊位置 | 通過 |
| Hospital explicit pixel geometry | 驗證 `hospital` marker 維持 `x_px/y_px` 與 `1.0x` legacy UI 對齊 | 通過 |
| Company sofa marker mapping | 驗證 `Sofa3/2/1` 對應 `label_rp_4/5/6` 的 runtime contract 未回退 | 通過 |

## 5. 實作說明

- 新增 `_is_map_marker_widget_name()`、`_clear_runtime_map_marker_widgets()`、`_build_runtime_map_marker_widgets()`、`_rebuild_runtime_map_marker_widgets()`。
- `MainWindow` 新增 `_clear_map_marker_widgets()` / `_build_map_marker_widgets()`，在初始化時以 runtime marker specs 重新建立 marker layer。
- runtime 建立出的 widget 使用與 marker id 相同的 `objectName`，並同步掛回 `self.label_rp_*` attribute，讓既有 `refresh_label_tooltip()` 與任務標記流程維持不變。
- `ui_main.py` 保留原始 Designer marker 定義，但它們只作為啟動時的 legacy 產物；進入 `MainWindow` 後會被清掉，不再作為執行期依賴。
- `_position_map_marker_widgets()`、`resizeEvent()`、`_apply_main_map_shell_layout()` 保持原 contract，延續 R03 與 B01 已完成的 scaled geometry。

## 6. 非目標

- 不處理 `selected_map.ui` 的 marker cleanup，這屬於 P3。
- 不加入 marker 編輯模式或點選後直接改寫 JSON，這屬於 P4。
- 不修改 MiR API polling、task scheduler、DB schema。

## 7. 後續建議

- P3 可以正式移除 `ui_main.py` 內的 Designer marker 定義，讓 `.ui` 檔只保留地圖底圖與功能區塊。
- 若後續 site profile 需要不同 marker 外觀，可把 runtime marker style 再抽成 site-level visual schema，而不是回到 Designer 固定 widget。
