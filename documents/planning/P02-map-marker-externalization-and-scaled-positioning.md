---
author: Codex
date: 2026-06-01
title: 地圖標記外部化與縮放定位規劃
status: draft
version: v1
---

# P02 地圖 Marker 外部化與縮放定位

## 目標

將目前透過 Qt Designer 固定擺放的停車格 marker，改成由場域設定驅動的 marker 圖層，並滿足以下需求：

- 主地圖縮放時仍能維持正確對齊
- 不需要重新打開 Qt Designer，就能新增、刪除或移動 marker
- 保留現有任務 tooltip 與高亮顯示行為

## 為什麼需要這份規劃

目前藍色停車格長方形的資料來源被拆成兩半：

- `main.ui` / `ui_main.py` 用固定的 `QRect` 幾何座標定義 `label_rp_1` 到 `label_rp_7`
- `site/*.json` 只透過 `marker_id` 把業務地點對應到這些 widget id

這樣的拆法會產生兩個實際問題：

1. `label_map_1` 現在已經會跟著新版全地圖版面伸縮，但靜態 marker widget 不會依照目前顯示比例重算位置。
2. 只要新增或刪除 marker，就得同時修改場域資料與 Qt Designer 裡的 widget 樹，這正好違背了 site config 原本想降低維護成本的目的。

## 現況發現

- `ui_main.py` 仍然在 `frame_map` 底下用固定 geometry 建立 `label_rp_1` 到 `label_rp_7`。
- `main.py` 已經在 `draw_car_position()` 裡，透過 `original_pixmap` 與目前地圖顯示尺寸的比值，正確縮放機器人 marker。
- `main.py` 也已經在 `refresh_label_tooltip()` 中，透過 `LOCATION_TO_MARKER` 與 `getattr(self, marker_name)` 集中處理 marker 查找。
- `build_site_runtime_maps()` 已經顯示專案正在朝向場域設定驅動的 runtime data 前進，但 marker 的幾何資訊還沒有被納入這個 runtime model。

## 使用者故事

- **身為** 場域維護者
- **我希望** 地圖 marker 來自 site data，而不是 Qt Designer 的固定幾何座標
- **如此一來** 我就能安全地縮放地圖、移動 marker、或增減停車格，而不會破壞現有的 runtime 高亮邏輯

## 範圍

| 區域 | 檔案 | 預計文件類型 | 需要變更的原因 |
|---|---|---|---|
| 場域設定與執行期對映 | `site/*.json`, `main.py`, `documents/modules/M02-site-configuration-and-runtime-mapping.md` | RXX | Marker 幾何資訊必須變成執行期設定，而不是只存在於 UI 幾何座標裡。 |
| 介面應用殼層 | `main.py`, `main.ui`, `ui_main.py` | RXX | Marker widget 必須改成從設定動態建立與定位。 |
| MiR API 介接層 | `functions.py` | 無 | 這次 marker 重構不需要更改 API 契約。 |
| 任務排程 / 持久化 | `task_thread.py`, `TaskDBManager.py`, `UserDBManager.py` | 無 | Marker 渲染應該仍屬於呈現層關注點。 |

## 設計方向

### 建議的單一資料來源

將 marker 幾何資料移到 `site/*.json`，以明確的 marker 定義方式保存。每個 site 應自行描述：

- `marker_id`
- 原始地圖的像素座標
- 原始地圖下的寬與高
- 如果未來有不同 marker 形狀，可額外保留可選的樣式 metadata

建議格式如下：

```json
{
  "markers": [
    {
      "marker_id": "label_rp_1",
      "x_px": 290,
      "y_px": 230,
      "width_px": 18,
      "height_px": 26
    }
  ]
}
```

### 座標策略

使用原始地圖的像素座標，不使用目前 widget 的畫面座標，也不使用百分比字串。

原因如下：

- 專案目前的地圖校正資料本來就是以原始地圖像素為基準
- `draw_car_position()` 已經有一套適合縮放安全渲染的比例換算模式
- 當 site 更換底圖時，校正與 marker 擷取都能在同一個座標系統中進行

### 執行期 Widget 策略

在地圖 pixmap 載入完成後，由程式動態建立 map marker widget，並在地圖顯示尺寸變更時重新定位。

相容性原則：

- 保留 `label_rp_1` 這類 `marker_id`
- 動態建立的 widget 仍使用相同的 object name
- 透過 `setattr(self, marker_id, widget)` 把它重新掛回 `self`

這樣就能讓像 `refresh_label_tooltip()` 這類既有程式，在底層資料來源切換後仍然繼續正常工作。

## 分階段規劃

| 階段 | 狀態 | 名稱 | 產出 | 後續文件類型 | 預期文件 |
|---|---|---|---|---|---|
| P1 | [x] 已完成 | 場域 marker 結構與執行期對映 | 由 site config 接管 marker 幾何資訊與 location-to-marker 綁定。 | R03 | `documents/implements/R03-site-marker-schema-and-runtime-maps.md` |
| P2 | [x] 已完成 | MainWindow 動態 marker 圖層 | Marker widget 改成由 site data 動態建立與重新定位，不再依賴 Designer 幾何座標。 | R04 | `documents/implements/R04-dynamic-map-marker-layer.md` |
| P3 | [x] 已完成 | Designer marker 清理與維護流程 | 專案可透過編輯 config 來增減 marker，並加入缺漏參照的保護機制。 | RXX | `documents/implements/R05-map-marker-maintenance-cleanup.md` |
| P4 | [ ] 可選 | Marker 座標擷取輔助 | 為新場域提供更快速的座標擷取工作流。 | FXX 或 RXX | P1-P3 落地後再定 |

---

## P1 場域 Marker 結構與執行期對映

### 目標

擴充 site profile schema，讓 marker 幾何資訊與其他地圖設定一起存放在同一份場域設定中。

### 關鍵決策

- 在每個 `site/*.json` 新增頂層 `markers` 陣列
- 保留 `locations[*].marker_id` 作為業務地點與畫面 marker 之間的連結
- 建立新的 runtime 結構，例如 `marker_specs_by_id`
- 檢查重複的 `marker_id`，並在 location 指向不存在的 marker 定義時提出警告

### 驗收期望

- [x] `site/company.json` 與 `site/hospital.json` 可以直接描述 marker 幾何資訊，不需要碰 Qt Designer。
- [x] `build_site_runtime_maps()` 能回傳適合 runtime 使用的 marker 幾何結構。
- [x] runtime layer 能分辨「這個 location 本來就沒有 marker」與「這個 location 指到了一個設定錯誤的 marker」。

### 風險

- 現有 location 會重複使用同一個 marker id，例如 robot position 與 shelf position 共用同一格，因此 validation 必須允許多個 location 指向同一個 marker。
- 遷移期間可能同時存在舊的 Designer marker 與新的 config marker，runtime 必須明確決定優先使用哪一種來源。

---

## P2 MainWindow 動態 Marker 圖層

### 目標

將靜態 `label_rp_*` widget 換成動態建立的 marker widget，並讓它跟著目前顯示中的地圖幾何資訊移動。

### 關鍵決策

- 在 `original_pixmap` 載入後再建立 marker
- marker widget 應掛在目前顯示中的地圖區域，而不是舊的固定矩形
- marker 幾何位置計算沿用 `draw_car_position()` 相同的縮放比例邏輯
- marker 的重新排版應掛在現有更新 map shell 的 resize 流程上

### 預期實作樣貌

- 新增輔助方法，例如：
  - `_build_map_marker_widgets()`
  - `_position_map_marker_widgets()`
  - `_clear_map_marker_widgets()`
- 更新 `resizeEvent()` 或 `_apply_main_map_shell_layout()`，讓地圖縮放後能重新定位 marker
- 保留目前 runtime attribute contract，確保 `getattr(self, marker_name)` 仍能正確取到對應 widget

### 驗收期望

- [x] 視窗縮放時，marker widget 仍能保持正確對齊。
- [x] `refresh_label_tooltip()` 不需要重訂 task-layer contract，也能持續更新 marker 文字、tooltip 與顏色狀態。
- [x] 機器人 marker overlay 與點擊 marker 的行為，仍能獨立於停車格 marker 正常運作。

### 風險

- 如果 marker 掛到錯誤的 parent widget，位置可能再次漂移，或被畫在地圖圖片下方。
- 如果遷移期間舊 widget 與新 widget 同時存在且名稱相同，tooltip 更新可能會打到錯誤的 instance。

---

## P3 Designer Marker 清理與維護流程

### 目標

讓 marker 維護工作變成修改 config，而不是修改 Qt Designer。

### 關鍵決策

- 當動態 marker 穩定後，將 `main.ui` 中硬編碼的 `label_rp_*` widget 移除或忽略
- 文件化一套支援的 add/remove/move 工作流：
  - 在 `site/*.json` 補上 marker 幾何資料
  - 讓 `locations[*].marker_id` 指向它
  - 重啟程式並驗證
- 為以下狀況加入 runtime 警告：
  - 未被使用的 marker 定義
  - 缺少的 marker 定義
  - 重複的 marker id

### 驗收期望

- [x] 刪除 marker 不再需要去刪 Qt Designer widget。
- [x] 新增 marker 不再需要在 `.ui` 檔裡複製並重新命名 `QLabel`。
- [x] 場域維護者只看一份 JSON，就能理解該 site 的 marker 佈局。

### 風險

- 如果 `selected_map.ui` 仍假設可點擊按鈕數量固定，那主地圖雖然會變成 config-driven，但選點視窗仍可能維持半靜態狀態。
- 如果新工作流沒有寫清楚，團隊仍可能沿用 Qt Designer 當成預設編輯方式。

---

## P4 可選的 Marker 座標擷取輔助

### 目標

降低新地圖擷取 marker 座標時的操作成本。

### 可能方向

- 僅開發者可用的 click mode，直接輸出原始地圖像素座標
- 可協助產生 JSON 片段模板的 admin dialog
- 將 marker spec 快速複製到剪貼簿的輔助功能

### 為什麼這是可選項

P1-P3 先解決正確性與可維護性問題。只有當 marker 編輯足夠頻繁時，P4 才值得投入成為專用的座標擷取流程。

## 不在本次範圍內

- 調整 MiR API polling
- 更改 task scheduling 或 DB schema
- 重設計機器人外圈或 click marker 的視覺效果
- 除非 P3 證明它是阻塞點，否則不重寫 selected-map button 架構

## 建議的下一步文件

1. 依照 P1 撰寫 `R03-site-marker-schema-and-runtime-maps.md`。
2. [x] 完成 `R04-dynamic-map-marker-layer.md`，並讓 `MainWindow` 以 runtime marker specs 動態建立 map marker layer。
3. 下一步判斷 `selected_map.ui` 是否也需要同步改成 config-driven 清理方案。

## 若本規劃啟動，需要同步更新的上下文文件

如果 P1 開始執行，應同步更新共享文件，避免後續工作繼續把 site marker 視為一半屬於 UI、一半屬於 config：

- `CONTEXT.md`
- `documents/modules/M02-site-configuration-and-runtime-mapping.md`
- 如果 runtime marker layer 後續成為一級 UI 子系統，也可一併更新 `documents/modules/M01-ui-application-shell.md`
