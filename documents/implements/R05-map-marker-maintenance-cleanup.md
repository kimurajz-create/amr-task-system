---
author: Codex
date: 2026-06-02
title: Map Marker Maintenance Cleanup
uuid: b6fd3260f4ae4526a8a1317f8a2f0bb5
version: v1
planning: documents/planning/P02-map-marker-externalization-and-scaled-positioning.md
status: completed
---

# R05 Map Marker Maintenance Cleanup

## 1. 背景

P02 的 P1 與 P2 已經把 marker schema 與主地圖 runtime marker layer 收斂到 `site/*.json`、`build_site_runtime_maps()`、`MainWindow._build_map_marker_widgets()`。

但主 UI 原始來源仍殘留一批 Qt Designer 時代的 `label_rp_*` widget，會帶來兩個維護風險：

- 新增或刪除 marker 時，維護者容易誤以為還需要同步修改 `main.ui` / `ui_main.py`
- 即使 runtime 已經完全接手 marker 建立流程，UI source 仍保留舊幾何與假資料 tooltip，增加後續誤用與回歸機率

P3 的目標是正式清掉這條舊維護路徑，並把 add/remove/move marker 的操作方式文件化。

## 2. 變更目標

- 主地圖 marker 只允許由 runtime layer 建立，不再依賴 Designer 預置的 `label_rp_*`
- `main.ui` / `ui_main.py` 不再實例化 legacy marker widget
- 維護 marker 的唯一資料來源為 `site/<profile>.json`
- 保留既有 runtime contract：
  - `marker_id == widget.objectName() == self.<marker_id>`
  - `refresh_label_tooltip()` 仍以 `LOCATION_TO_MARKER` / `getattr()` 驅動
  - `_position_map_marker_widgets()` 仍負責縮放後幾何

## 3. 實作結果

### R1. 移除主 UI 的 legacy marker 實例化

- [main.ui](/abs/path/d:/Jordan_Backup/2025_NonIQ_Project/MiR/ACE_MIR_803/mir-software/amr-task-system/main.ui) 的 `label_rp_1` 到 `label_rp_7` 區塊已停用，不再參與 UI 載入與後續 `ui_main.py` 生成。
- [ui_main.py](/abs/path/d:/Jordan_Backup/2025_NonIQ_Project/MiR/ACE_MIR_803/mir-software/amr-task-system/ui_main.py) 不再建立 `self.label_rp_*`，也移除了舊的預設 tooltip / text。

### R2. 保持 runtime marker layer 為唯一來源

- `MainWindow._build_map_marker_widgets()` 仍在初始化時清空 map marker layer，並依 `MARKER_SPECS_BY_ID` 重新建立 widget。
- `_clear_runtime_map_marker_widgets()` / `_build_runtime_map_marker_widgets()` 的 contract 不變，仍可支援超出舊 Designer 數量的 marker id。

### R3. 文件化 add/remove/move 工作流

- **新增 marker**
  - 在 `site/<profile>.json` 的 `markers` 新增一筆 `marker_id`
  - 讓對應 `locations[*].marker_id` 指到這個 id
  - 啟動後 runtime 會自動建立同名 widget

- **刪除 marker**
  - 從 `locations[*].marker_id` 移除引用
  - 再刪除 `markers[*]` 對應紀錄
  - 不需要修改 Qt Designer widget

- **移動 marker**
  - 若場域使用顯式像素幾何，調整 `x_px/y_px`
  - 若場域使用世界座標回投影，調整 `world_x_m/world_y_m`
  - 不需要在 `.ui` 內拖拉 `QLabel`

- **保護機制**
  - `build_site_runtime_maps()` 已驗證：只要 `locations[*].marker_id` 指向不存在的 marker，啟動時就直接失敗
  - marker id 重複、幾何欄位型別錯誤，也會在 runtime map 建立階段被擋下

### R4. 明確排除本階段範圍

- `selected_map.ui` 目前仍是固定按鈕式選點 UI，沒有納入這次 config-driven marker cleanup
- P3 只清理主地圖 marker layer 的 legacy Designer 依賴，不重寫 selected-map button 架構

## 4. 驗證

| 驗證項目 | 方式 | 結果 |
|---|---|---|
| Runtime marker lifecycle 仍可重建 `label_rp_13` 等新 id | `tests/test_site_marker_coordinate_parity.py` 既有測試 | 通過 |
| `Ui_MainWindow` 不再實例化 legacy `label_rp_*` | 新增 `MainWindowUiCleanupTests` | 通過 |
| marker world/pixel geometry 與縮放 contract 無回歸 | 既有座標 parity 測試 | 通過 |

## 5. 測試指令

```bash
python -m unittest tests.test_site_marker_coordinate_parity
```

## 6. 影響檔案

- [main.ui](/abs/path/d:/Jordan_Backup/2025_NonIQ_Project/MiR/ACE_MIR_803/mir-software/amr-task-system/main.ui)
- [ui_main.py](/abs/path/d:/Jordan_Backup/2025_NonIQ_Project/MiR/ACE_MIR_803/mir-software/amr-task-system/ui_main.py)
- [tests/test_site_marker_coordinate_parity.py](/abs/path/d:/Jordan_Backup/2025_NonIQ_Project/MiR/ACE_MIR_803/mir-software/amr-task-system/tests/test_site_marker_coordinate_parity.py)
- [documents/planning/P02-map-marker-externalization-and-scaled-positioning.md](/abs/path/d:/Jordan_Backup/2025_NonIQ_Project/MiR/ACE_MIR_803/mir-software/amr-task-system/documents/planning/P02-map-marker-externalization-and-scaled-positioning.md)

## 7. 後續觀察

- 若未來要讓場域維護者直接在 UI 上編輯 marker，可把 P4 收斂成 JSON 片段產生器或座標擷取輔助，而不是回到 Designer 複製 widget 的流程。
- 若 `selected_map.ui` 之後也要改成 config-driven，建議沿用同一份 `locations` / `markers` 資料來源，避免形成第二套位置真相。
