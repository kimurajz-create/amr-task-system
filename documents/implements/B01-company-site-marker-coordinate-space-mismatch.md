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

本 bug 需要先釐清一個前提：`site/company.json` 內目前保存的 `world_x_m/world_y_m` 應視為 company 場域的真實 MiR 世界座標來源，不應為了貼合目前小地圖 widget 幾何而被改寫。

真正的不一致發生在 `company` profile 的像素座標契約，而不是世界座標本身。現況同時存在兩種不同的像素空間：

- `x_px/y_px` 對得上 `ui_main.py` 內既有固定 Site Marker widget 幾何，也就是使用者現在在 company 畫面上實際看到的 `1072 x 608` 小地圖 UI 空間。
- `calibration.image_pts` 則對應 `picture/pure_dilated_map.png` 的原始大圖像素空間；該圖尺寸為 `3216 x 1824`，剛好是目前 UI 地圖顯示尺寸的 `3x`。

因此，若直接把 company 的 `world_x_m/world_y_m` 套進目前 `main.py` 的 affine transform，得到的會是原始大圖像素，而不是目前 UI 小地圖像素。代表數字如下：

- `label_rp_1`
  - 儲存的 UI 左上角像素：`(290, 230)`
  - 由世界座標直接回投影：`(842, 720)`，落在 `3216 x 1824` 大圖空間
  - 若縮回目前 UI 顯示尺度：`(281, 240)`，已接近現有 widget 位置
- `label_rp_7`
  - 儲存的 UI 左上角像素：`(870, 320)`
  - 由世界座標直接回投影：`(2548, 956)`，同樣落在大圖空間
  - 若縮回目前 UI 顯示尺度：`(850, 319)`，也接近現有 widget 位置

這說明 company 的第一個問題是「大圖 pixel 空間」與「UI pixel 空間」被混用，而不是 world 座標錯誤。

此外，company 還有第二個不一致：沙發區三個 Site Marker 的語意映射與左右幾何順序疑似相反。依目前世界座標回投影並縮回 UI 尺度後，三個 marker 的 X 位置約為：

- `label_rp_6`：`x ≈ 403`（左）
- `label_rp_5`：`x ≈ 505`（中）
- `label_rp_4`：`x ≈ 597`（右）

但目前 `ui_main.py` 內固定 widget 幾何是：

- `label_rp_4`：`x = 410`（左）
- `label_rp_5`：`x = 510`（中）
- `label_rp_6`：`x = 590`（右）

而 `site/company.json` locations 又將：

- `label_rp_6` 對應 `Sofa3`
- `label_rp_5` 對應 `Sofa2`
- `label_rp_4` 對應 `Sofa1`

也就是說，world 座標呈現出的左右順序比較像 `Sofa3 -> Sofa2 -> Sofa1`，但現有固定 widget 左右順序卻是 `Sofa1 -> Sofa2 -> Sofa3`。這代表 B01 不只要處理 pixel 空間契約，也要確認 company 的沙發 marker 對應關係是否反轉。

`hospital` 是對照組：其主地圖尺寸本身就是 `1072 x 608`，`x_px/y_px` 與校正回推結果落在同一個像素空間，因此不會出現上述落到另一張大圖座標系的問題。

## 2. 修正目標

把這件事定義成一個獨立 bug：在目前產品迭代下，company 的 marker 資料契約必須收斂為一致且可驗證的兩層語意。

- `world_x_m/world_y_m`：代表真實 MiR 世界座標，不因目前小地圖 widget 幾何而被強制改寫。
- `x_px/y_px`：代表本迭代中 `ui_main.py` 固定 Site Marker widget 的左上角 UI 像素位置。

本次修正的核心是讓這兩層語意之間的轉換規則清楚且一致，而不是把其中一層硬改成另一層。具體來說，B01 需要同時收斂兩個面向：

- company 的 `world -> pixel` 換算結果若要拿來比對目前 UI，必須先經過正確的顯示尺度轉換，不能直接拿大圖像素與小地圖 widget 像素相比。
- company 的 sofa marker 幾何與 location-to-marker 語意必須一致；若現有 `label_rp_4/5/6` 左右順序與 `Sofa1/2/3` 名稱定義不一致，需明確修正或明確文件化。

本次修正必須：

- 保留 `world_x_m/world_y_m` 作為 company 的真實世界座標來源
- 保留 `x_px/y_px`
- 保留 `ui_main.py` 既有固定 marker widgets
- 不把 P2 工作提前拉進來
- 不在本次迭代改成動態建立 marker widget
- 不在沒有獨立證據的情況下改寫 company 的世界座標

## 3. 驗收準則

- **情境 1：Company 世界座標必須保持為真實來源**
  - **前提** 已載入 `company` 場域 profile 與其 `site/company.json` marker 紀錄
  - **當** 修正 B01 後重新檢視 marker schema
  - **則** `world_x_m/world_y_m` 仍代表真實 MiR 世界座標，不會被直接覆寫成目前 UI widget 的像素對應值

- **情境 2：Company marker 的世界座標若用於比對 UI，必須先轉到正確像素空間**
  - **前提** 已載入 `company` 場域 profile 與其 `site/company.json` marker 紀錄
  - **當** 將每個帶有 `world_x_m/world_y_m` 的 marker 經過 company 校正資料轉成像素，再依 `width_px/height_px` 換算為 marker 左上角座標，並轉換到目前 UI 顯示尺度
  - **則** 回推後的左上角座標應與目前 company UI 期待的位置一致，每個軸向允許誤差 `+/- 1 px`，而不是落在 `3216 x 1824` 大圖空間

- **情境 3：Company 維持目前可見的 marker 佈局**
  - **前提** `ui_main.py` 內仍存在 `label_rp_1` 到 `label_rp_7` 固定 marker widgets
  - **當** 應用程式以 `site_profile = company` 載入
  - **則** 畫面上的 marker 位置仍應與目前 company 小地圖對齊，不應跳到另一個大圖座標空間

- **情境 4：Company sofa marker 的名稱語意與幾何順序一致**
  - **前提** 使用 `company` marker schema 與對應 locations
  - **當** 檢查 `label_rp_4/5/6` 與 `Sofa1/2/3` 的左右順序
  - **則** marker 幾何順序、location-to-marker 對映與實際場域名稱語意必須一致；若現況為刻意反向，需明確文件化

- **情境 5：像素幾何資料仍是本迭代契約的一部分**
  - **前提** 使用 `company` marker schema
  - **當** 這個 bug 被修正後
  - **則** `site/company.json` 內仍需保留 `x_px/y_px`，並持續代表本迭代中 UI marker 左上角像素位置

- **情境 6：Hospital 行為不可回歸**
  - **前提** 已載入 `hospital` 場域 profile
  - **當** 對 `hospital` 套用同樣的校正回推一致性檢查
  - **則** hospital markers 仍應維持對應其既有 `x_px/y_px` 的結果，不產生回歸

## 4. 測試情境

| ID | 情境 | 前提 | 動作 | 預期結果 | 優先級 |
|---|---|---|---|---|---|
| TC1 | 重現 company 的大圖 / UI 像素空間不一致 | 現行 `company` marker 與校正資料 | 將 `world_x_m/world_y_m` 直接回投影成左上角像素 | 至少一個 marker 會落在 `3216 x 1824` 大圖空間，且與儲存的 `x_px/y_px` 不一致，成功重現 bug | 高 |
| TC2 | 驗證 company 的 UI 像素對齊規則 | 更新後的 `company` marker / 校正資料 / 轉換規則 | 回投影所有 company markers 並轉到目前 UI 顯示尺度 | 每個 marker 的左上角像素都與預期 UI 幾何一致，誤差在 `+/- 1 px` 內 | 高 |
| TC3 | 驗證 company 世界座標未被錯誤覆寫 | 更新後的 `company` marker schema | 比對修正前後的 `world_x_m/world_y_m` | 原始 MiR 世界座標維持不變，沒有被強制改成小地圖 widget 對應值 | 高 |
| TC4 | 驗證 sofa marker 語意與幾何一致 | `company` 的 `label_rp_4/5/6` 與 `Sofa1/2/3` 對映 | 檢查左右順序與 location-to-marker 對照 | 幾何順序與名稱語意一致，或明確記錄為刻意設計 | 高 |
| TC5 | 保持目前 company UI 佈局 | `ui_main.py` 既有固定 `label_rp_*` widgets | 載入 company profile 並檢視 marker | 畫面上的 marker 仍停留在目前小地圖位置 | 高 |
| TC6 | 防止 hospital 回歸 | 現行 `hospital` 場域 profile | 執行同樣的一致性檢查 | hospital markers 仍通過，不改變既有顯示位置 | 中 |

## 5. 實作註記

- `ui_main.py` 仍透過固定的 `QLabel` widgets (`label_rp_1` 到 `label_rp_7`) 持有目前 company marker 的可見幾何位置。
- `refresh_label_tooltip()` 目前只裝飾既有 widget，不會根據 `MARKER_SPECS_BY_ID` 重新定位。
- `_build_marker_specs_by_id()` 只有在缺少 `x_px/y_px` 時，才會根據 `world_x_m/world_y_m` 回推出像素位置，因此這個不一致目前比較像潛伏中的資料債，而不是已經直接重排畫面的執行期 bug。
- `company` 的 `calibration.image_pts` 目前對應原始大圖，而 `x_px/y_px` 與固定 widget 幾何對應目前小地圖 UI，因此兩者不能直接互相比較。
- 目前 `company` 主地圖 `picture/pure_dilated_map.png` 尺寸為 `3216 x 1824`，`ui_main.py` 的地圖顯示區則是 `1072 x 608`，兩者比例為 `3:1`。
- 目前診斷結果顯示，若先把 world 座標回投影到大圖，再縮回 `1/3` UI 尺度，`label_rp_1`、`label_rp_2`、`label_rp_3`、`label_rp_5`、`label_rp_7` 已接近現有 widget 位置；`label_rp_4` 與 `label_rp_6` 則呈現左右反向的跡象，需回到 sofa 對映語意確認。
- 修正方向應讓 `company` 的資料內部一致，但不要把 P2 的動態 marker 圖層提早納入。
- 可接受的修正方向包括：
  - 在 world 回投影結果與目前 UI 幾何之間建立明確的顯示尺度轉換規則
  - 調整 company 校正資料，讓它直接對應目前實際顯示的小地圖空間
  - 修正 company 的 marker-to-location 配對方式，讓 sofa 名稱語意與實際左右位置一致
- 本 bug 的範圍外項目：
  - 動態建立 marker widgets
  - 移除 `x_px/y_px`
  - 更換目前 `ui_main.py` 的 marker 佈局系統
  - 在沒有獨立證據時重寫 company 的真實 MiR 世界座標

## 6. 補充說明

- 這個 bug 形式化了 `R03-site-marker-schema-and-runtime-maps.md` 已經提到的 company 風險：company 目前仍把 UI 像素幾何當成工作真相，但保留下來的世界座標資料與校正點實際落在另一個大圖渲染空間。
- B01 的價值在於先把「世界座標真相」、「大圖 pixel 空間」、「目前 UI pixel 空間」三者的契約講清楚，避免後續 marker layer 工作再次建立在混合語意上。
- 若 sofa marker 左右反向最終被證實為獨立資料問題，可在後續視複雜度拆成單獨 bug；但在目前診斷下，仍建議將其作為 B01 的同批觀察一併收斂。
