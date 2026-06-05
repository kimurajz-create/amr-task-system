# 地圖維護快速手冊

## 適用範圍
這份文件是最短版的維護入口，主要給以下兩類調整使用：
- 主地圖 marker 維護
- selected-map 可點選點位維護

當你要修改 `site/company.json` 或 `site/hospital.json` 時，先看這份即可。

## 主地圖 Marker
主地圖 marker 定義在 `site/<profile>.json` 的 `markers`。

每一筆 marker 資料負責描述主地圖上的幾何資訊：
- `marker_id`
- `x_px`
- `y_px`
- `width_px`
- `height_px`

`locations[*].marker_id` 只負責引用 marker，不負責定義幾何座標。

### 什麼情況要改主地圖 Marker
- 新增主畫面上可見的 marker
- 移動既有 marker
- 因為地圖資產變更而調整 marker 尺寸
- 從主地圖移除某個 marker

### 主地圖 Marker 維護步驟
1. 打開目標場域檔案，例如 `site/company.json`。
2. 找到 `markers` 陣列。
3. 新增或更新 marker 幾何資料。
4. 確認對應的 `locations[*].marker_id` 指向相同的 `marker_id`。
5. 如果主地圖圖片有更換，請重新檢查所有受影響 marker 的座標。

### 主地圖 Marker 維護規則
- 同一個 site profile 內，`marker_id` 必須唯一。
- 多個 location 可以共用同一個 `marker_id`。
- 如果某個 location 不需要出現在主地圖上，`marker_id` 可以是 `null`。
- 主地圖 marker 的維護應在 JSON 中完成，不要去改 `main.ui` 或 Qt Designer。

## Selected Map 點位
selected-map 點位定義在 `site/<profile>.json` 的 `selected_map.selectable_points`。

每一筆 selected-map 點位資料負責描述彈出地圖中的一個可點擊區域：
- `point_id`
- `location_mir_name`
- `label`
- `order`
- `visible`
- `x_px`
- `y_px`
- `width_px`
- `height_px`
- `marker_id` 可選

### 什麼情況要改 Selected Map 點位
- 在 selected-map 視窗新增一個可點選點位
- 在 selected-map 視窗隱藏某個點位
- 修改 selected-map 顯示文字或排序
- 調整可點擊區域的位置或尺寸
- 更換 selected-map 底圖資產

### Selected Map 維護步驟
1. 打開目標場域檔案。
2. 找到頂層的 `selected_map` 區塊。
3. 如果 selected-map 圖片有更換，更新 `asset_path` 或 design size。
4. 在 `selectable_points` 中新增或更新點位資料。
5. 確認每個 `location_mir_name` 都對應到真實存在的 `locations[*].mir_name`。
6. 只要 selected-map 底圖換過，就重新檢查 clickable geometry。

### Selected Map 維護規則
- selected-map 點位和主地圖 marker 有關聯，但不是同一件事。
- 主地圖上有 marker，不代表 selected-map 一定要有對應點位。
- location 有 `marker_id`，也不代表 selected-map 一定要顯示。
- `selectable_points[*].marker_id` 是可選欄位；沒填時，runtime 可回退使用對應 location 的 `marker_id`。
- 如果 `visible` 是 `false`，該點位不應出現在 runtime 中。

## 要改哪個區塊
- 想移動主畫面上的 marker：改 `markers`
- 想改彈出地圖的可點擊區域：改 `selected_map.selectable_points`
- 想改業務 location 綁到哪個主地圖 marker：改 `locations[*].marker_id`
- 想改 selected-map 的文字來源或顯示順序：改 `selected_map.selectable_points`

## 常見錯誤
- 應該改 `site/*.json`，卻跑去改 `main.ui`
- 改了 `locations[*].marker_id`，卻忘了在 `markers` 補對應定義
- 換了地圖圖片，卻沒有重新校正座標
- 使用了不存在於 `locations` 的 `location_mir_name`
- 直接把主地圖 marker 幾何複製給 selected-map 使用，卻忽略兩者座標語意不同

## 相關文件
- `documents/planning/P02-map-marker-externalization-and-scaled-positioning.md`
- `documents/planning/P03-selected-map-dynamic-generation-and-config-driven-point-selection.md`
- `documents/implements/R03-site-marker-schema-and-runtime-maps.md`
- `documents/implements/R04-dynamic-map-marker-layer.md`
- `documents/implements/R05-map-marker-maintenance-cleanup.md`
- `documents/modules/M02-site-configuration-and-runtime-mapping.md`
