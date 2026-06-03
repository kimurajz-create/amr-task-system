---
author: Codex
date: 2026-06-03
title: 站點標記結構與執行期對應表
uuid: 1e32fbc57d1e4ba6ab6571f1bb1ba833
version: v1
planning: documents/planning/P02-map-marker-externalization-and-scaled-positioning.md
status: completed
---

# R03 站點標記結構與執行期對應表

## 1. Scope

P02 P1 聚焦於將主地圖標記幾何資料移入 `site/*.json`，並讓 `build_site_runtime_maps()` 提供以 marker 為中心的執行期資料結構，供後續 UI 工作使用。

## 2. Goals

- 將 marker 幾何資料外部化到 site 設定，不再依賴 Qt Designer 幾何作為唯一真實來源。
- 保留 `locations[*].marker_id` 作為業務位置與 marker 的綁定關係。
- 讓執行期對應表能區分：
  - 本來就不需要 marker 的 location
  - 參考了不存在 marker 定義的 location

## 3. Changes

### R1. Site schema 新增 `markers`

- `site/company.json` 現在包含一個 `markers` 陣列，初始資料來自 `ui_main.py` 目前的 `label_rp_1` 到 `label_rp_7` 幾何設定。
- `site/hospital.json` 現在包含 `label_rp_1` 到 `label_rp_13` 的 `markers` 陣列。
- 每個 marker 規格目前包含：
  - `marker_id`
  - `x_px`
  - `y_px`
  - `width_px`
  - `height_px`

### R2. 執行期對應表提供 marker 結構

- `build_marker_specs_by_id()` 會將 marker 紀錄正規化為以 `marker_id` 為 key 的 dictionary。
- `build_site_runtime_maps()` 現在回傳：
  - `marker_specs_by_id`
  - `marker_location_names_by_id`
  - `locations_without_markers`
  - `marker_config_warnings`

### R3. P1 階段的驗證維持非破壞式

- 重複的 marker 定義會被收集為 warning。
- 指向未定義 `marker_id` 的 location 仍會保留在執行期對應表中，並同時回報 warning。
- 沒有 `marker_id` 的 location 會被獨立追蹤，讓後續階段能區分「設計上沒有 marker」與「marker 參照損壞」。

## 4. Test Coverage

| Test ID | Type | Coverage |
|---|---|---|
| R03-T1 | unit | `company` 與 `hospital` 的 site profile 都能提供完整的 `marker_specs_by_id` 對應表，且所有執行期 marker 參照都能解析到已定義的 marker id |
| R03-T2 | unit | 共用 marker 與無 marker 的 location 會在執行期對應表中分開追蹤 |
| R03-T3 | unit | 重複 marker id 與遺失 marker 參照會產生 warning，但不會丟失執行期 location 綁定 |

## 5. Verification

```bash
python -m unittest tests.test_site_runtime_marker_maps
```

## 6. Notes

- hospital 的 marker 座標是從目前樓層平面資產取得的初始 config 基線，之後可在 P2/P3 微調，而不需要修改程式碼。
- P2 現在可以直接使用 `MARKER_SPECS_BY_ID`，將舊有的 Designer marker widget 替換為執行期建立的 widget。
