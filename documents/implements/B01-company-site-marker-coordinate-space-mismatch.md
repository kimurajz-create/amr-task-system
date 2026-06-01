---
author: Codex
date: 2026-06-01
title: Company 場域標記座標空間不一致
uuid: 653d2f94f0e3465cb8b69cf9b6fd2b98
version: v1
status: draft
---
# B01 Company 場域標記座標空間不一致

## 1. 問題概述

`site/company.json` 目前在同一批 marker 紀錄中混用了兩種不同的座標空間。

- `x_px/y_px` 對得上 `ui_main.py` 內既有固定 marker widget 幾何，也就是使用者現在在 company 畫面上實際看到的小地圖位置。
- 同一筆紀錄又保存了 `world_x_m/world_y_m`；但這組世界座標若透過目前 `main.py` 的 `company` 校正資料回投影，得到的像素位置會落在另一個較大的底圖空間，而不是目前小地圖 UI 空間。

目前資料中的觀察例子：

- `label_rp_1`：儲存的左上角像素是 `(290, 230)`，但由世界座標與校正回推後得到的是 `(842, 720)`
- `label_rp_7`：儲存的左上角像素是 `(870, 320)`，但由世界座標與校正回推後得到的是 `(2548, 956)`

這代表 `company` profile 內部是不一致的。雖然現在畫面看起來還正常，但那是因為執行期仍在顯示 `ui_main.py` 內舊的固定 widget。

`hospital` 是對照組：它的 `x_px/y_px` 與校正回推後的像素位置是一致的。

## 2. 修正目標

把這件事定義成一個獨立 bug：在目前產品迭代下，company 的 marker 紀錄必須能收斂到單一且一致的畫面座標空間。

這個 bug 所採用的正確座標空間是：

- `ui_main.py` 目前固定 marker widget 使用的左上角像素空間
- 相對於使用者現在真正看到的 company 小地圖畫面骨架
- 不是另一個未被目前 UI 採用的原始大圖像素空間

本次修正必須：

- 保留 `x_px/y_px`
- 保留 `ui_main.py` 既有固定 marker widgets
- 不把 P2 工作提前拉進來
- 不在本次迭代改成動態建立 marker widget

## 3. 驗收準則

- **情境 1：Company marker 的世界座標回投影後要落回目前 UI 空間**
  - **前提** 已載入 `company` 場域 profile 與其 `site/company.json` marker 紀錄
  - **當** 將每個帶有 `world_x_m/world_y_m` 的 marker 經過 company 校正資料轉成像素，再依 `width_px/height_px` 換算為 marker 左上角座標
  - **則** 回推後的左上角座標應與目前 company UI 期待的位置一致，每個軸向允許誤差 `+/- 1 px`

- **情境 2：Company 維持目前可見的 marker 佈局**
  - **前提** `ui_main.py` 內仍存在 `label_rp_1` 到 `label_rp_7` 固定 marker widgets
  - **當** 應用程式以 `site_profile = company` 載入
  - **則** 畫面上的 marker 位置仍應與目前 company 小地圖對齊，不應跳到另一個大圖座標空間

- **情境 3：像素幾何資料仍是本迭代契約的一部分**
  - **前提** 使用 `company` marker schema
  - **當** 這個 bug 被修正後
  - **則** `site/company.json` 內仍需保留 `x_px/y_px`，並持續代表本迭代中 UI marker 左上角像素位置

- **情境 4：Hospital 行為不可回歸**
  - **前提** 已載入 `hospital` 場域 profile
  - **當** 對 `hospital` 套用同樣的校正回推一致性檢查
  - **則** hospital markers 仍應維持對應其既有 `x_px/y_px` 的結果，不產生回歸

## 4. 測試情境

| ID | 情境 | 前提 | 動作 | 預期結果 | 優先級 |
|---|---|---|---|---|---|
| TC1 | 重現目前 company 不一致問題 | 現行 `company` marker 與校正資料 | 將 `world_x_m/world_y_m` 回投影成左上角像素 | 至少一個 marker 與儲存的 `x_px/y_px` 不一致，成功重現 bug | 高 |
| TC2 | 驗證修正後的 company 一致性 | 更新後的 `company` marker / 校正資料 | 回投影所有 company markers | 每個 marker 的左上角像素都與預期 UI 幾何一致，誤差在 `+/- 1 px` 內 | 高 |
| TC3 | 保持目前 company UI 佈局 | `ui_main.py` 既有固定 `label_rp_*` widgets | 載入 company profile 並檢視 marker | 畫面上的 marker 仍停留在目前小地圖位置 | 高 |
| TC4 | 防止 hospital 回歸 | 現行 `hospital` 場域 profile | 執行同樣的一致性檢查 | hospital markers 仍通過，不改變既有顯示位置 | 中 |

## 5. 實作註記

- `ui_main.py` 仍透過固定的 `QLabel` widgets (`label_rp_1` 到 `label_rp_7`) 持有目前 company marker 的可見幾何位置。
- `refresh_label_tooltip()` 目前只裝飾既有 widget，不會根據 `MARKER_SPECS_BY_ID` 重新定位。
- `_build_marker_specs_by_id()` 只有在缺少 `x_px/y_px` 時，才會根據 `world_x_m/world_y_m` 回推出像素位置，因此這個不一致目前比較像潛伏中的資料債，而不是已經直接重排畫面的執行期 bug。
- 修正方向應讓 `company` 的資料內部一致，但不要把 P2 的動態 marker 圖層提早納入。
- 可接受的修正方向包括：
  - 調整 company 校正資料，讓它對應目前實際顯示的小地圖空間
  - 修正 company 的世界座標與像素資料配對方式，讓世界座標回投影後真正落回目前 UI 位置
- 本 bug 的範圍外項目：
  - 動態建立 marker widgets
  - 移除 `x_px/y_px`
  - 更換目前 `ui_main.py` 的 marker 佈局系統

## 6. 補充說明

- 這個 bug 形式化了 `R03-site-marker-schema-and-runtime-maps.md` 已經提到的 company 風險：company 目前仍把 UI 像素幾何當成工作真相，但保留下來的世界座標資料並不屬於同一個渲染空間。
- B01 的價值在於先把座標空間契約講清楚，避免後續 marker layer 工作再次建立在混合語意上。
