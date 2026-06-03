---
author: Codex
date: 2026-06-03
title: 地圖標記維護清理
uuid: b6fd3260f4ae4526a8a1317f8a2f0bb5
version: v1
planning: documents/planning/P02-map-marker-externalization-and-scaled-positioning.md
status: completed
---

# R05 地圖標記維護清理

## 1. Scope

P02 P3 會從主地圖移除剩餘的 Qt Designer marker 相依，讓 marker 維護完全改由 `site/*.json` 設定驅動。

## 2. Goals

- 移除 `main.ui` / `ui_main.py` 中預先建立的 `label_rp_*` widget。
- 讓 `MainWindow._build_map_marker_widgets()` 成為主地圖 marker 唯一的執行期建立路徑。
- 保留既有執行期 marker 契約：
  - `marker_id == widget.objectName() == self.<marker_id>`
  - `refresh_label_tooltip()` 仍透過 `LOCATION_TO_MARKER` 與 `getattr()` 解析 marker
  - marker 幾何仍由 `MARKER_SPECS_BY_ID` 提供
- 明確將 `selected_map.ui` 排除在這次清理範圍之外。

## 3. Changes

### R1. 從主地圖 UI 移除舊有 Designer marker

- 刪除 `main.ui` 中的 `label_rp_*` widget 宣告。
- 刪除 `ui_main.py` 中對應產生的 widget 初始化與 tooltip 文字。
- 主地圖 UI 的其他結構維持不變。

### R2. 簡化 MainWindow 的 marker 生命週期

- 從 `MainWindow` 移除舊有 marker 蒐集 fallback 邏輯。
- 執行期 marker 現在一律直接由 `self.MARKER_SPECS_BY_ID` 建立。
- `_clear_map_marker_widgets()` 與 `_build_map_marker_widgets()` 現在只處理執行期建立的 marker instance。

### R3. 保持設定驅動的 marker 行為不變

- Marker id 仍會回掛到 `self.<marker_id>`，因此 tooltip 與 task-highlighting 流程維持相容。
- `refresh_label_tooltip()` 在沒有任何 Designer placeholder widget 的情況下仍可正常運作。
- P1 既有的執行期 marker warning 與 location 綁定行為維持不變。

## 4. Test Coverage

| Test ID | Type | Coverage |
|---|---|---|
| R05-T1 | unit | `Ui_MainWindow` 在 setup 後不再宣告 `label_rp_*` widget |
| R05-T2 | unit | `main.ui` 原始檔不再包含舊有 `label_rp_*` widget 宣告 |
| R05-T3 | unit | 既有的執行期 marker map 測試在清理後仍然通過 |

## 5. Verification

```bash
python -m unittest tests.test_site_runtime_marker_maps tests.test_map_marker_ui_cleanup
```

## 6. Notes

- `selected_map.ui` 仍是 `P02` 所描述的固定按鈕式選擇介面；這次清理只適用於主地圖 overlay。
- `main.ui` 原本就無法穩定透過 `pyside6-uic` 重新產生，因此 P3 更新是直接套用到 `main.ui` 與 `ui_main.py`，以保持執行期程式與預期清理結果一致。
