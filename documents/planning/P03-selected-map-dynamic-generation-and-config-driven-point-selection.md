---
author: Codex
date: 2026-06-04
title: SelectedMap 選圖視窗完全動態生成與 config-driven 點位選取
status: draft
version: v1
uuid: 5d77d6b2d6f24a8ab0ed6d0f62d1f731
---

# P03 SelectedMap 選圖視窗完全動態生成與 config-driven 點位選取

## 1. 背景

目前專案已完成主地圖 marker 的 config-driven 化：

- `site/*.json` 已有 `markers`
- `locations[*].marker_id` 已能把 location 綁定到主地圖 marker
- 主地圖 marker layer 已可依 site config 動態生成

但 `SelectedMap` 選圖視窗仍停留在舊做法：

- `selected_map.ui` / `ui_selected_map.py` 內固定存在 `btn_sm_rp1 ~ btn_sm_rp7`
- `SelectedMap._connect_location_buttons()` 直接把這 7 顆按鈕綁死
- `company.json` 仍用 `map_button_id` 暗示哪些點可在 selected map 點選
- `hospital.json` 的 `map_button_id` 幾乎全是 `null`，表示 schema 與 UI 已經脫節

這個設計已不適合目前與未來需求：

- company 場域未來可能從 7 個點擴增到 9 個以上
- hospital 場域可選點數量本來就不同
- 新增 site 時不應再手改 `.ui` 內的固定按鈕數量
- 點位新增、刪除、改名時，應盡量只調整 `site/*.json`

## 2. 目標

本規劃要把 `SelectedMap` 重構為真正的 config-driven 選點視窗，達成以下目標：

- `SelectedMap` 不再依賴固定數量的 Designer button
- 改成依據 site config 動態生成可點選元件
- 有幾個可選 location，就產生幾個 selectable widget
- 點下後維持既有行為：回填到主畫面的搜尋框 / dropdown
- 維持「讓使用者直接點位置」的簡單互動，不把 selected map 做成主地圖那種任務狀態 overlay 系統
- 維護方便優先，允許 selected map 與 main map 在技術細節上不同，但必須有清楚契約

## 3. 範圍

### In Scope

- 為 selected map 定義正式 schema 與 runtime model
- 移除 `SelectedMap` 對固定 `btn_sm_rp*` 的依賴
- 動態建立、定位、縮放 selectable widget
- 明確定義 selected map 的文字來源、排序、可見條件、幾何座標
- 整合既有 `open_map_selector()`、`location_selected`、dropdown 回填流程
- 規劃 company / hospital site config migration
- 補上 selected map 的測試策略與共享文件更新

### Out of Scope

- 不把 `SelectedMap` 改造成主地圖等級的任務監控層
- 不在這一輪引入地圖編輯器、拖拉式點位編輯器或 admin 座標校正工具
- 不變更 MiR API、task scheduling、DB schema
- 不要求 selected map 與 main map 共用完全相同的 widget 類型或 rendering pipeline

## 4. 現況與限制

### 現況觀察

- `MainWindow` 的 combo box 位置清單目前來自 `build_site_runtime_maps()` 產生的 `USER_LOCATION_MAP`
- `open_map_selector()` 只負責打開 `SelectedMap`，並在 `location_selected` signal 回來後回填指定 dropdown
- `SelectedMap` 目前只送出 `str` 型別的 location name，這個 contract 很簡單且值得保留
- `company.json` 的 `map_button_id` 其實不是 domain schema，而是舊 `.ui` 實作細節
- `hospital.json` 已經證明 `map_button_id` 無法描述「不同 site 有不同 selectable points」這件事

### 設計限制

- selected map 的底圖可能與 main map 相同，也可能未來不同
- selected map 的 clickable area 不能直接假設等於主地圖 marker 的小圖示範圍
- location 改名時，selected map 文案應能自動跟著更新，除非 site 明確指定 override label
- 若 site 有 marker 但不想出現在 selected map，需要有明確表達方式
- 若 config 缺漏或錯誤，應降級顯示並回報 warning，而不是讓視窗直接壞掉

## 5. 方案取捨與建議

### 方案 1

`selected map` 完全沿用 `markers` 資料並動態生成可點 widget

優點：

- 資料來源最少
- 不需要新增太多 schema
- 與主地圖 marker 關聯最直接

缺點：

- `markers` 的職責是主地圖 marker 幾何，不等於 selected map 的互動點需求
- 很難表達「marker 存在，但 selected map 不可點」
- 很難表達 selected map 專用的排序、文字 override、按鈕尺寸
- 若 clickable area 直接沿用 marker 幾何，醫院與未來高密度場域的點擊體驗會很差
- 一旦 selected map 底圖與 main map 不完全相同，marker 幾何就不再可靠

### 方案 2

為 `selected map` 建立專用的 selectable-point schema，但仍可引用 `location` / `marker`

優點：

- schema 職責清楚：main map marker 與 selected map clickable point 分離
- 能清楚定義哪些 location 可點、用什麼文字、什麼順序、什麼位置
- 容易支援不同 site 的不同點數，不再受固定 7 顆按鈕限制
- 可以保留與 `location` / `marker` 的引用，避免重複維護名稱與關聯
- 更符合「維護方便優先，但不要求 selected map 與 main map 技術一致」的偏好

缺點：

- 需要新增 schema 與 runtime builder
- 每個 site 都要補 selected map 專用資料
- 需要規劃 migration 與相容期

### 建議結論

建議採用方案 2，但不是完全切斷與 `location` / `marker` 的關係，而是採用「selected-map 專用 schema + location/marker 引用」的混合式設計。

結論理由：

- 這是最符合維護性、擴充性與 UX 需求的方案
- `map_button_id` 屬於舊 UI 實作細節，應逐步淘汰
- selected map 與 main map 的責任不同，不應被迫共用同一份幾何語意
- 仍然可以透過 reference/fallback 降低重複資料，保留 config-driven 的便利性

## 6. 建議資料模型

### 6.1 新增 top-level `selected_map` schema

建議每個 `site/*.json` 新增：

```json
{
  "selected_map": {
    "design_width_px": 3216,
    "design_height_px": 1824,
    "empty_state_text": "目前此場域沒有可選位置",
    "selectable_points": [
      {
        "point_id": "or01_robot",
        "location_mir_name": "LbV2_Robot position Hua",
        "marker_id": "label_rp_1",
        "label": "華陀會議室",
        "x_px": 230,
        "y_px": 370,
        "width_px": 100,
        "height_px": 25,
        "order": 10,
        "visible": true
      }
    ]
  }
}
```

### 6.2 欄位定義

- `design_width_px` / `design_height_px`
  - selected map 底圖的設計基準尺寸
  - 所有 selectable point 幾何都以這個座標系為準
  - 建議在 migration 時明確寫入，避免 runtime 只能依賴載入中的 pixmap 猜測

- `selectable_points[*].point_id`
  - selected map 內部穩定識別碼
  - 只用於 config、runtime warning、測試與 debug

- `selectable_points[*].location_mir_name`
  - 參照 `locations[*].mir_name`
  - 這一版建議用 `mir_name` 當 reference key，因為它在現有 schema 中最接近穩定 ID
  - 若未來 site schema 引入真正的 `location_id`，可再升級 reference contract

- `selectable_points[*].marker_id`
  - optional
  - 若未填，runtime 先從引用的 location 取 `marker_id`
  - 保留這個欄位可讓 selected map 在少數例外情境下直接覆寫

- `selectable_points[*].label`
  - optional
  - 若未填，預設使用引用 location 的 `display_name`
  - 這可確保一般改名只改 `locations[*].display_name` 即可同步反映

- `selectable_points[*].x_px` / `y_px` / `width_px` / `height_px`
  - selected map clickable widget 的幾何資料
  - 基準為 `selected_map.design_*`
  - 建議語意採 top-left + size，與現有 marker geometry 風格一致，降低認知成本

- `selectable_points[*].order`
  - 明確排序欄位
  - runtime 以數值小到大排序
  - 若缺漏，runtime 應 warning，並 fallback 到 `label` + `location_mir_name` 做穩定排序

- `selectable_points[*].visible`
  - optional，預設 `true`
  - `false` 時代表保留資料但不顯示

### 6.3 可見條件定義

selected map 的可見規則建議明確定義為：

- 只有存在於 `selected_map.selectable_points` 且 `visible != false` 的點會顯示
- `markers` 的存在不代表 selected map 必須顯示
- `locations` 有 `marker_id` 也不代表 selected map 必須顯示

這樣就能明確表達：

- 主地圖有 marker，但 selected map 不可點
- location 暫時保留，但 selected map 先不顯示

### 6.4 文字來源定義

建議文字決策順序如下：

1. `selectable_points[*].label`
2. 引用 location 的 `display_name`
3. 若兩者都缺，該點不顯示並回報 warning

### 6.5 排序定義

建議排序規則如下：

1. `order` 升冪
2. 若 `order` 相同或缺漏，fallback `label`
3. 再 fallback `location_mir_name`

### 6.6 `map_button_id` 的處理建議

建議把 `map_button_id` 視為 legacy migration 欄位，而不是長期保留的正式 schema。

規劃方向：

- 相容期：可先讀取但不再作為新設計核心
- 切換完成後：從 company / hospital config 移除
- 文件層面：在 `M02` 與後續 `RXX` 註明 deprecated -> removed 的時點

## 7. 建議 runtime contract

`build_site_runtime_maps()` 或其拆分後的 helper 應新增 selected map 相關輸出，例如：

- `selected_map_asset_path`
- `selected_map_design_size`
- `selected_map_points`
- `selected_map_points_by_id`
- `selected_map_location_names`
- `selected_map_config_warnings`

每個 runtime point 至少應解成：

- `point_id`
- `location_mir_name`
- `location_display_name`
- `selected_label`
- `marker_id`
- `x_px`
- `y_px`
- `width_px`
- `height_px`
- `order`
- `visible`

建議 builder 行為：

- 缺少 reference location 的 point：warning + 跳過
- reference location 存在但沒有 `marker_id`：允許存在，只要 selected map 幾何完整即可
- 幾何欄位不完整：warning + 跳過該點
- 無任何可用點：runtime 回傳空陣列，UI 顯示空狀態

## 8. UI 重構方向

`SelectedMap` 建議從「固定 7 顆按鈕」改成「底圖 + 動態 overlay 容器」：

- `selected_map.ui` 保留底圖、已選文字、確認/取消等靜態元素
- 移除 `btn_sm_rp1 ~ btn_sm_rp7`
- 新增或保留一個覆蓋在地圖上的容器，專門承載 runtime 建出的 selectable widget

建議 `SelectedMap` 新增簡單且單一職責的方法：

- `_clear_selectable_widgets()`
- `_build_selectable_widgets()`
- `_position_selectable_widgets()`
- `_show_empty_state_if_needed()`
- `set_selected_map_runtime(...)`

### 縮放策略

selected map 的 clickable widget 定位建議採用：

- config 座標以 `design_width_px` / `design_height_px` 為基準
- runtime 依 `label_sm_map_1` 當前顯示尺寸計算 `scale_x` / `scale_y`
- 每次 `resizeEvent()` 或底圖載入完成後重新定位所有 selectable widget

這樣可確保：

- company 與 hospital 兩種不同底圖尺寸都可共用機制
- 視窗縮放後點位仍維持相對位置正確
- 不必把 selected map 做成和 main map 完全相同的 marker overlay 系統

## 9. 與既有流程的整合

現有流程值得保留：

- `open_map_selector(target_dropdown)`
- `SelectedMap.location_selected.emit(str)`
- `_set_current_dropdown_value(location_name, target_dropdown)`

建議整合方式：

- `SelectedMap` 繼續只送出最終 `location_display_name`
- `open_map_selector()` 改成在 show 之前把「目前 site 的 selected-map runtime data」灌入 dialog
- dialog 不需要知道 start/destination 的業務差異，只負責回傳被點到的 location name
- 若 runtime 無可選點，dialog 仍可開啟，但 confirm 應 disabled，並顯示空狀態訊息

## 10. Migration 策略

### 10.1 原則

- 先引入新 schema 與 runtime，再切 UI
- 在相容期容忍 legacy `map_button_id`
- 最後再清理 legacy 欄位與 `.ui` 遺留元件

### 10.2 Company migration

第一階段：

- 依目前 `btn_sm_rp1 ~ btn_sm_rp7` 的實際位置，建立 `selected_map.selectable_points`
- 每個 point 參照既有 robot position location
- 先維持目前文字與順序，避免 UX 突變

第二階段：

- UI 切到新 runtime 後，驗證 company 不再依賴 `map_button_id`
- 驗證通過後移除 `map_button_id`

### 10.3 Hospital migration

第一階段：

- 補上 `selected_map` 區塊
- 只將需要在 selected map 顯示的 robot position 納入 `selectable_points`
- charging station、shelf position 是否可點，應由 site config 明確決定，不再用 `null map_button_id` 模糊表示

建議初始策略：

- 預設納入主要 robot position
- 預設不納入 charging station 與 shelf position，除非產品需求明確要求可點

### 10.4 相容期策略

建議保留短期 compatibility window：

- 若 site 有 `selected_map.selectable_points`，完全走新流程
- 若沒有新 schema，但有 legacy `map_button_id`，可用 transitional adapter 生成 runtime points
- transitional adapter 只作為 migration 緩衝，不作長期能力承諾

### 10.5 清理完成條件

以下條件全部成立後，可移除 legacy：

- company / hospital 都已補齊 `selected_map` schema
- `SelectedMap` 不再引用任何 `btn_sm_rp*`
- 測試已覆蓋無 legacy 的執行路徑
- `site/*.json` 不再需要 `map_button_id`

## 11. 風險與應對

### 11.1 reference key 穩定性

風險：

- 目前若以 `location_mir_name` 作 reference，MiR location rename 會影響 selected map

應對：

- 本階段先用 `mir_name`
- 在 shared docs 中註記未來可引入穩定 `location_id`

### 11.2 高密度點位的按鈕重疊

風險：

- hospital 或未來 site 的點位更多時，文字較長的按鈕可能互相覆蓋

應對：

- Phase 1 先允許 config 明確設定 `width_px` / `height_px`
- 若仍有 UX 問題，再開後續 phase 評估 label 精簡、tooltip、icon+text 組合或 callout 樣式

### 11.3 底圖更換導致座標漂移

風險：

- site 若更換 `assets.selected_map` 但沒同步更新 `design_*` 與 point geometry，位置會錯

應對：

- builder 對設計尺寸與 pixmap 尺寸差異給 warning
- 文件明確要求 selected map asset 更換時必須同步校正 point geometry

### 11.4 config 錯誤導致 dropdown 回填失敗

風險：

- selected map point 送出的 location name 若不在 combo box 中，點擊成功但回填失敗

應對：

- runtime builder 僅允許引用現有 location
- UI / tests 明確驗證 emitted location 是否可被目標 dropdown 找到

## 12. 依賴

- 既有 `site/*.json` location / marker schema
- `build_site_runtime_maps()` 及其後續可抽出的 helper
- `SelectedMap` 的 PySide6 widget 生命週期與 `resizeEvent()`
- `open_map_selector()` / `location_selected` / dropdown 回填流程
- 現有 offscreen UI 測試基礎

## 13. 多階段實作規劃

| Phase | 狀態 | 主題 | 主要產出 | 建議後續文件 |
|---|---|---|---|---|
| P1 | [ ] | SelectedMap schema 與 runtime contract | 正式定義 `selected_map` schema、fallback 規則、warning 規則、shared docs 更新 | `RXX` |
| P2 | [ ] | SelectedMap 動態 widget layer | 移除固定 `btn_sm_rp*`，改成 runtime 建立與定位 selectable widget | `RXX` |
| P3 | [ ] | Integration 與 migration 切換 | `open_map_selector()` 與 dropdown 回填整合，company/hospital config 補資料，完成相容切換 | `RXX` |
| P4 | [ ] | Cleanup 與驗證封板 | 移除 legacy `map_button_id` / fixed buttons 依賴，補齊測試與共享文件 | `RXX` 或必要時 `BXX` |

## 14. Phase 詳述與驗收

### P1. SelectedMap schema 與 runtime contract

目標：

- 為 selected map 建立正式 schema 與 builder contract
- 讓 selected map 的可選點從 UI 實作細節提升為 site config 能描述的資料

主要工作：

- 定義 `selected_map` top-level schema
- 定義 `selectable_points` 的 reference、label、geometry、order、visible 規則
- 在 `build_site_runtime_maps()` 或 helper 新增 selected map runtime 輸出
- 定義 config warning 行為與空狀態行為
- 更新 `CONTEXT.md`、`M01`、`M02` 的 shared language

可驗收結果：

- [ ] 文件已明確區分 `marker` 與 `selected-map selectable point`
- [ ] runtime builder 可輸出 selected map points，且不依賴 `.ui` button id
- [ ] config 缺漏時是 warning + skip，不是 crash
- [ ] shared docs 已補上 selected map 的責任與 schema 說明

建議後續文件：

- `RXX`: `SelectedMap schema and runtime contract`

### P2. SelectedMap 動態 widget layer

目標：

- 把 `SelectedMap` 從固定 7 顆按鈕重構為動態 overlay widget layer

主要工作：

- 清理 `selected_map.ui` / `ui_selected_map.py` 的固定 `btn_sm_rp*`
- 建立 overlay 容器與動態 widget lifecycle
- 實作 point geometry scaling 與 resize 後重定位
- 保留簡單的 `location_selected.emit(str)` contract

可驗收結果：

- [ ] `SelectedMap` 不再列舉固定 `btn_sm_rp1 ~ btn_sm_rp7`
- [ ] company / hospital 可依各自 point 數量動態生成不同數量 widget
- [ ] 視窗縮放後 selectable widget 仍維持正確位置
- [ ] 無可選點時可顯示空狀態，不會產生壞掉的按鈕

建議後續文件：

- `RXX`: `Dynamic SelectedMap widget layer`

### P3. Integration 與 migration 切換

目標：

- 把新 selected map runtime 接入主流程，完成 site config 遷移

主要工作：

- `open_map_selector()` 改為灌入目前 active site 的 selected-map runtime
- 驗證 `location_selected` 到 dropdown 回填仍沿用既有流程
- company config 補齊 selected map points
- hospital config 補齊 selected map points
- 短期保留 compatibility adapter，避免一次切換造成中斷

可驗收結果：

- [ ] company 不再依賴固定 7 顆 `.ui` button
- [ ] hospital 可顯示與 company 不同數量的 selectable points
- [ ] 點擊後可正確回填 start / destination dropdown
- [ ] location 改名後，未 override label 的 selected map 文案會自動同步

建議後續文件：

- `RXX`: `SelectedMap integration and site migration`

### P4. Cleanup 與驗證封板

目標：

- 移除 legacy 依賴，讓 selected map fully config-driven

主要工作：

- 移除 `map_button_id` 的正式依賴
- 清理 legacy fallback 與文件
- 補齊 unit / UI tests
- 對 config 錯誤情境加上 regression coverage

可驗收結果：

- [ ] `site/*.json` 不再需要 `map_button_id`
- [ ] 程式碼與 `.ui` 檔中不再依賴固定 `btn_sm_rp*`
- [ ] tests 覆蓋不同 site 點位數量、空資料、排序、名稱更新、錯誤 config、縮放、回填
- [ ] shared docs 已反映新 contract，沒有遺留舊語意

建議後續文件：

- `RXX`: `Legacy cleanup and verification`
- `BXX`: 只在 migration 過程中發現既有 site config 缺陷時另開

## 15. 測試策略

至少應覆蓋以下情境：

- 不同 site 點位數量不同
  - company 與 hospital runtime 產出的 selectable point 數量不同，UI 可正確建立

- 無可選點
  - `selected_map.selectable_points` 為空時，dialog 顯示空狀態且無法誤送出

- 點位名稱更新
  - location `display_name` 改變後，未指定 `label` override 的 selectable point 會自動反映

- 點位排序
  - `order` 不同時，widget 建立順序與鍵盤 focus 順序保持可預期

- config 缺漏或錯誤
  - 找不到 `location_mir_name`
  - 幾何欄位缺漏
  - `order` 缺漏
  - 重複 `point_id`
  - `visible: false`

- 視窗縮放後位置仍正確
  - 動態 widget 在不同顯示尺寸下仍落在預期相對位置

- 點擊後能正確回填 dropdown
  - emitted location name 能被 target dropdown 找到並設為 current index

建議測試層次：

- unit
  - selected map runtime builder
  - geometry scaling helper

- UI / offscreen
  - dynamic widget 建立數量
  - resize 後位置
  - click -> signal -> dropdown 回填

- config regression
  - company / hospital site profile 的 selected map schema 完整性檢查

## 16. 建議共享文件更新

若依此規劃啟動實作，建議同步更新：

- `CONTEXT.md`
  - 新增 `marker`、`selected-map selectable point`、`location reference` 等術語

- `documents/modules/M01-ui-application-shell.md`
  - 補 `SelectedMap` 從固定按鈕視窗轉為 runtime-driven dialog 的責任說明

- `documents/modules/M02-site-configuration-and-runtime-mapping.md`
  - 納入 `selected_map` schema、runtime outputs、warning contract

若後續發現 selected map contract 已足夠獨立，也可考慮新增：

- `documents/modules/M06-selected-map-runtime.md`

這不是本階段必做，但若 `M01` / `M02` 開始變得太擁擠，值得作為後續整理方向。

## 17. 實作順序建議

建議執行順序：

1. 先做 P1，把 schema、warning、shared language 固定下來
2. 再做 P2，讓 UI 真正脫離固定按鈕
3. 再做 P3，把 company / hospital config 補齊並接回主流程
4. 最後做 P4，移除 legacy 並封板測試

## 18. 完成定義

本規劃完成後，代表後續 F/R/B 文件與實作應以以下結果為準：

- 新 site 不必再修改 `.ui` 固定按鈕數量
- selected map 顯示幾個點，完全由 `site/*.json` 決定
- selected map 可清楚表達哪些 location 可點、顯示什麼文字、排什麼順序、擺在哪裡
- 點擊後仍沿用既有 dropdown 回填流程
- `map_button_id` 被視為過渡期 legacy，而非長期設計核心
