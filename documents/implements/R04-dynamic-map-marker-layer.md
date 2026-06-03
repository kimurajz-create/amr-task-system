---
author: Codex
date: 2026-06-03
title: 動態地圖標記圖層
uuid: 4c8e508f7d4d4e5f9c8b0d8e4dbf5b5b
version: v1
planning: documents/planning/P02-map-marker-externalization-and-scaled-positioning.md
status: completed
---

# R04 動態地圖標記圖層

## 1. Scope

P02 P2 以 `MARKER_SPECS_BY_ID` 驅動的執行期 widget 取代主地圖上的 `label_rp_*` Designer marker，同時維持既有 tooltip 與任務高亮行為不變。

## 2. Goals

- 從 site 設定建立 marker widget，而不是依賴硬編碼在 `main.ui` 的 marker instance。
- 保留 `marker_id` 作為執行期 widget 屬性契約，讓既有程式仍可使用 `getattr(self, marker_id)`。
- 依照實際顯示的地圖尺寸縮放 marker 幾何，確保 robot overlay、task marker 與地圖點擊座標轉換保持對齊。
- 避免破壞既有用於 world-coordinate 選點的主地圖點擊流程。

## 3. Changes

### R1. MainWindow 接手執行期 marker 生命週期

- `MainWindow` 現在透過以下方法管理 marker widget：
  - `_build_map_marker_widgets()`
  - `_position_map_marker_widgets()`
  - `_clear_map_marker_widgets()`
  - `_sync_main_map_overlay_geometry()`
- 執行期 widget 會根據 `self.MARKER_SPECS_BY_ID` 建立。
- 舊的 Designer `label_rp_*` widget 會被隱藏，不再作為執行期的真實來源。

### R2. Marker 與 overlay 縮放共用同一套幾何契約

- 新增的 geometry helper 會在以下座標系之間縮放 marker 矩形與點座標：
  - original map image coordinates
  - displayed overlay coordinates
- `draw_car_position()` 與地圖點擊處理都改用同一套縮放規則，而不是硬編碼比例。
- 每當主地圖外框尺寸改變時，marker widget 都會跟著 overlay 幾何重新定位。

### R3. 保留既有 tooltip 與 task 行為

- 執行期 marker widget 會依照自己的 `marker_id` 指派回 `self`。
- `refresh_label_tooltip()` 仍可透過 `getattr(self, marker_id)` 解析 marker。
- Marker widget 會維持對滑鼠事件透明，讓地圖點擊仍能傳遞到主地圖互動流程。

## 4. Test Coverage

| Test ID | Type | Coverage |
|---|---|---|
| R04-T1 | unit | marker 幾何可從原始地圖像素正確縮放到顯示中的 overlay 幾何 |
| R04-T2 | unit | display-to-source 的點位轉換與 source-to-display 轉換維持對齊 |
| R04-T3 | unit | 很小的 marker 規格在縮放後仍會產生可見的執行期 widget 尺寸 |

## 5. Verification

```bash
python -m unittest tests.test_site_runtime_marker_maps
```

## 6. Notes

- P2 刻意先將實作維持在 `MainWindow` 內部，讓後續 P3 清理過時 Designer marker 時，不需要再次改動執行期行為。
- `CONTEXT.md` 目前實質上仍是空的，因此這次重構主要依據 `P02`、`R03` 與既有模組文件，而不是專案層級的領域術語。
