---
author: Codex
date: 2026-06-01
title: 場域標記結構與執行期對映
uuid: 4f0bd7b39c3f4c3ca29a0fa41bc2ea3b
version: v1
planning: documents/planning/P02-map-marker-externalization-and-scaled-positioning.md
status: completed
---

# R03 場域標記結構與執行期對映

## 1. 目標

P02 的 P1 階段要把地圖 marker 幾何資訊從只存在於 Qt Designer 的狀態，移到 `site/*.json` 內管理，同時維持現有 location-to-marker 行為在目前 UI 下仍可正常運作。

## 2. 使用者故事

- **作為** 維護多個場域 profile 的維護者
- **我希望** marker id 與 marker 幾何資訊都保存於場域設定，並透過穩定的執行期對映暴露出來
- **如此一來** 後續 UI 工作就能從設定資料建立與定位 marker widget，而不是繼續依賴硬編碼的 `label_rp_*` 幾何

## 3. 範圍與影響

| 區域 | 調整前 | R03 變更 |
|---|---|---|
| `site/company.json` | marker id 只存在於 locations | 新增 `markers[*]` 紀錄，並把既有像素幾何與真實 MiR 世界座標一起保存 |
| `site/hospital.json` | marker id 只存在於 locations | 新增 `markers[*]` 幾何紀錄，來源為 MiR 世界座標加上場域校正換算 |
| `main.py` / `load_site_config()` | 沒有明確的 `markers` 預設值 | 對每個 site profile 一律正規化出 `markers` 空陣列 |
| `main.py` / `build_site_runtime_maps()` | 只建立 location / mission / room maps | 新增 `marker_specs_by_id` 與 `marker_locations_by_id`，並驗證 marker schema |
| `MainWindow` 執行期狀態 | 沒有直接的 marker 幾何執行期契約 | 保存 `MARKER_SPECS_BY_ID` 與 `MARKER_LOCATIONS_BY_ID`，供後續 P2 使用 |

## 4. 驗收說明

- `company` 場域 profile 現在包含 `label_rp_1` 到 `label_rp_7` 的 marker 幾何設定，以及對應的真實 MiR 世界座標。
- 執行期對映現在會暴露：
  - `location_to_marker`
  - `marker_locations_by_id`
  - `marker_specs_by_id`
- 一旦某個場域定義了 `markers`，所有被 `locations[*].marker_id` 引用的 marker id 都必須存在。
- marker 可直接提供 `x_px/y_px`，也可改由 `world_x_m/world_y_m` 讓執行期透過校正資料回推出像素位置。
- hospital 的 marker 幾何已由 MiR 世界座標與場域校正資料推導完成，且 OR 4 依照現場命名規則刻意缺席。

## 5. 風險

- company 在本迭代仍以目前 UI 像素幾何作為工作真相，因為它的畫面 marker 佈局尚未完全改成由世界座標資料重算。
- 一旦 site 開始定義 `markers`，validation 就會變嚴格；幾何錯誤或重複 id 會直接失敗。

## 6. 實作紀錄

### 本迭代的最終行為

- `load_site_config()` 一律回傳 `markers` 集合。
- `build_site_runtime_maps()` 會建立 marker 反查對映與經過驗證的 marker 幾何表。
- `company` marker 幾何仍對齊目前 `ui_main.py` 的 label 位置，同時在 config 中保留真實 MiR 世界座標。
- `hospital` 現在包含 OR 1-3 與 OR 5-13 的 marker 幾何，來源為 MiR 世界座標換算。
- `hospital` 移除了 OR 4 的 robot / shelf 對應，以符合現場實際命名。

### 異動檔案

- `main.py`
- `site/company.json`
- `site/hospital.json`
- `documents/modules/M02-site-configuration-and-runtime-mapping.md`

### 驗證目標

- JSON 檔仍可正確解析。
- `main.py` 仍保持語法正確。
- `company` 的 runtime maps 同時包含 marker 幾何與 marker-to-location 反查結構。

## 7. 下一步

在 P2 中把 marker widget 改成真正由執行期資料建立與定位，讓 UI 不再依賴 Designer 內固定的 `label_rp_*` 幾何。
