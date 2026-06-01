# 場域設定與執行期對映

## 範圍

主要涉及的資產與程式：

- `main.py`
- `site/company.json`
- `site/hospital.json`
- `app_settings.json`

## 模組職責

這個模組透過外部化以下資訊，讓同一套應用程式可以在不同實體場域或 demo 環境下運作：

- 地圖圖片與 logo 資產
- 座標校正資料
- marker 幾何定義
- 地點顯示名稱
- MiR 地點識別名稱
- 任務顯示名稱
- marker 綁定關係
- room identifier
- 充電站標記

## 主要行為

### 設定解析順序

目前啟用的 site profile 依照以下順序決定：

1. `AMR_SITE_PROFILE` environment variable
2. `app_settings.json`
3. 內建預設值

### 場域設定載入

`load_site_config()` 會載入 `site/<profile>.json`，將缺漏欄位與預設值合併；若指定 profile 不存在或格式不合法，則回退到 `company`。

### Runtime Map 建立

`build_site_runtime_maps()` 會把場域設定資料轉成 runtime 可直接使用的字典結構，供以下用途使用：

- UI combo boxes and labels
- task scheduler mission/location translation
- map marker highlighting
- runtime marker widget placement
- room heartbeat mapping
- charging-station behavior

## 輸入

- selected site profile
- site JSON files
- default asset and calibration values

## 輸出

- `site_assets`
- `site_calibration`
- `USER_LOCATION_MAP` / `MIR_LOCATION_MAP` style mappings
- mission display-to-MiR mappings
- marker and room lookup tables
- marker geometry specifications
- required mission-code set for scheduler-related logic

## 邊界

- 這個模組負責定義不同 site 的變異，不負責應用程式流程本身。
- 它應提供 mapping data 與 marker 幾何資料，不應直接操作 widget 或 DB state。
- 它雖然已經朝 configuration-driven 方向設計，但目前仍部分耦合於 `main.py` 內的硬編碼 fallback 字典。

## 已知風險

- `main.py` 中的硬編碼預設值，長期可能與 site JSON schema 產生偏差。
- Runtime map 的慣例很重要，但目前仍偏向隱性規則。
- 如果 validation 太輕量，location 參照的 marker id 可能與實際 marker 幾何定義逐漸脫節。
- `site/*.json` 的驗證目前看起來偏輕量，因此格式錯誤可能只會靜默地讓行為退化。

## 文件缺口

後續應該補一份 schema 文件，明確定義以下結構的預期格式：

- `assets`
- `calibration`
- `markers`
- `locations`
- `missions`

## Marker Schema Contract

- `markers[*].marker_id` must be unique within a site profile.
- `markers[*].x_px` and `markers[*].y_px` are top-left map pixel coordinates for the marker widget.
- `markers[*].width_px` and `markers[*].height_px` are original marker widget dimensions.
- `markers[*].world_x_m` and `markers[*].world_y_m` are optional MiR world coordinates for the marker center.
- When `x_px/y_px` are omitted but `world_x_m/world_y_m` are present, runtime derives top-left pixel geometry through the site calibration.
- `locations[*].marker_id` may be omitted, but when `markers` are defined every referenced marker id must exist in `markers`.
- Runtime mapping exposes `location_to_marker`, `marker_locations_by_id`, and `marker_specs_by_id`.

有了這份 schema，新增新場域時會更安全，也更容易維護。
