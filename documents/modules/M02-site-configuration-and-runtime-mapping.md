# 場域設定與執行期對映

## 範圍

目前主要由下列檔案共同構成：

- `main.py`
- `site/company.json`
- `site/hospital.json`
- `app_settings.json`

## 模組職責

這個模組負責把場域差異整理成可由執行期直接使用的設定資料，讓同一套程式可以在不同 demo 場域或現場環境中切換，而不必反覆改寫硬編碼。

主要職責包括：

- 場域地圖與 logo 資產設定
- 地圖校正點設定
- marker 幾何資訊
- UI 顯示地點名稱
- MiR 地點名稱映射
- 任務顯示名稱映射
- marker 對應關係
- room identifier 對應
- 充電站規則

## 主要行為

### 設定解析順序

系統目前依照下列順序決定要載入哪個場域 profile：

1. `AMR_SITE_PROFILE` 環境變數
2. `app_settings.json`
3. 內建預設值

### 場域設定載入

`load_site_config()` 會讀取 `site/<profile>.json`。若指定的 profile 不存在或載入失敗，會先回退到 `company` 設定，再退回內建的保底地圖與校正資料。

### 執行期對映建立

`build_site_runtime_maps()` 會把場域設定轉換成執行期可直接使用的對映結構，供現有 UI 與排程流程使用，例如：

- UI 下拉選單與標籤名稱
- 任務排程的 mission/location 翻譯
- 地圖 marker 高亮
- 執行期 marker widget 定位
- room heartbeat 對映
- 充電站相關規則

## 輸入

- 選定的 site profile
- 場域 JSON 檔案
- 預設資產與預設校正值

## 輸出

- `site_assets`
- `site_calibration`
- 類似 `USER_LOCATION_MAP` / `MIR_LOCATION_MAP` 的名稱對映
- 任務顯示名稱與 MiR 名稱之間的對映
- marker 與 room 的查找表
- marker 幾何規格表
- 與排程規則相關的必要 mission code 集合

## 邊界

- 本模組應該只描述場域差異，不應直接承擔 widget 行為或 DB state。
- 本模組提供 mapping data 與 marker 幾何資訊，但不應直接擁有畫面 widget 實體。
- 本模組是把系統往 configuration-driven 推進的基礎，但目前仍有部分 fallback 硬編碼留在 `main.py` 中。

## 已知風險

- `main.py` 仍同時承擔場域載入、fallback、schema 處理與 runtime 對映建立。
- runtime map 的型別邊界不夠明確，較容易在後續重構時被誤用。
- 如果 validation 不夠完整，location 指到不存在的 marker id 或 marker 幾何格式錯誤，可能只在執行期才暴露問題。
- `site/*.json` 目前仍缺少更正式的 schema 文件與維護流程說明。

## 文件缺口

目前已知應該補足的 schema 區塊包括：

- `assets`
- `calibration`
- `markers`
- `locations`
- `missions`

## Marker 結構契約

- `markers[*].marker_id` 在同一個 site profile 內必須唯一。
- `markers[*].x_px` 與 `markers[*].y_px` 代表 marker widget 左上角的地圖像素座標。
- `markers[*].width_px` 與 `markers[*].height_px` 代表 marker widget 的原始尺寸。
- `markers[*].world_x_m` 與 `markers[*].world_y_m` 是可選的 MiR 世界座標，代表 marker 中心點。
- 當 `x_px/y_px` 缺席、但 `world_x_m/world_y_m` 存在時，執行期會透過場域校正資料回推出左上角像素座標。
- `locations[*].marker_id` 可以省略；但一旦定義了 `markers`，所有被引用的 marker id 都必須存在。
- 執行期對映會暴露 `location_to_marker`、`marker_locations_by_id` 與 `marker_specs_by_id`。

後續若要再擴充 schema，應優先更新這份文件，避免場域設定一半屬於 UI、一半屬於 config 的語意再次分裂。
