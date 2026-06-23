---
author: Codex
date: 2026-06-22
title: site location 單一真實來源與 ui_locations 發佈責任重整
uuid: 8c33fce2f4d648318afefc3e2b54d9a7
version: v1
status: in_progress
---

# R07 site location 單一真實來源與 ui_locations 發佈責任重整

## 1. Scope

本次重整只處理 location 主資料責任與 `ui_locations` 發佈流程，不改動 task queue、mission queue、heartbeat 流程本身。

主要涉及：

- `main.py`
- `TaskDBManager.py`
- `site/company.json`
- `site/hospital.json`
- `desktop_software` branch 內讀取 `ui_locations` 的桌機程式

本次目標是讓：

- `site/*.json` 成為 location 的單一真實來源
- 主程式不再把 MiR live 掃描出的不完整資料寫回 DB
- 桌機程式能持續從 DB 讀到穩定、乾淨、帶 `room_id` 的資料

## 2. Goals

- 明確定義 `site config`、`ui_locations`、MiR live locations 三者責任
- 將 `ui_locations` 從「混合主檔」收斂成「已整理發佈表」
- 消除目前因 `display_name` 歷史值、跨 site 混用、`room_id` 空值造成的桌機不穩定
- 以最小改動完成止血，避免先進入大型 schema redesign

## 3. Current Findings

### R1. site config 已具備正式 location 定義

`site/company.json` 與 `site/hospital.json` 的 `locations[]` 已完整描述：

- `mir_name`
- `display_name`
- `room_id`
- `marker_id`
- `is_charging_station`

`build_site_runtime_maps()` 也已經把這些資料轉成主程式 runtime lookup：

- `user_location_map`
- `mir_location_map`
- `room_id_map`
- `location_to_marker`

這代表 location 正式主資料其實已存在於 `site/*.json`，不是缺資料，而是責任尚未收斂。

### R2. 主程式目前同時做了兩種不同責任

主程式目前有兩條 location 資料路徑：

1. 建立任務時：
   - 使用 `site config -> room_id_map`
   - 這條路徑是正確且穩定的
2. 更新 `ui_locations` 時：
   - 從 MiR API 讀 map positions
   - 用 `USER_LOCATION_MAP` 把 MiR name 轉成 UI display name
   - 再把 `(display_name, mir_code)` 寫回 DB

第二條路徑的問題是：它輸出的是「MiR 當前掃到哪些點」的快照，不是完整 location 主資料。

### R3. desktop_software 實際上把 ui_locations 當正式資料來源

`desktop_software` 目前直接讀：

- `SELECT display_name, mir_code, room_id FROM ui_locations`

並且：

- `room_id` 為空就略過該筆
- 建立任務時直接使用該筆 `room_id`

因此桌機的期待其實是：

- `ui_locations` 是乾淨的
- `ui_locations` 是同一 site 的
- `ui_locations` 內每筆可選 location 都有 `room_id`

這與主程式目前把它當 live snapshot 寫入的方式相衝突。

## 4. Target Responsibility Model

### R4. 單一真實來源

`site/<profile>.json` 的 `locations[]` 是 location canonical source。

它應決定：

- 哪些 location 是正式存在的
- 每個 location 的正式 `display_name`
- 每個 location 的正式 `mir_name`
- 每個 location 的正式 `room_id`
- 哪些 location 屬於目前 site

### R5. DB 表責任

`ui_locations` 不再視為主檔，而視為 published cache / projection。

它的責任是：

- 提供桌機或其他外部 consumer 一份穩定查詢結果
- 僅承接來自 `site config` 整理後的資料
- 不自行承載歷史 display name 與不完整 live 掃描結果

### R6. 主程式責任

主程式應分開兩種來源：

1. `site config`
   - 用於 location 命名
   - 用於 `room_id` 對應
   - 用於 UI 正式清單發佈
2. MiR live locations
   - 只用於判斷當前 map 上是否存在
   - 只用於 warning、健康檢查、比對未配置點
   - 不直接定義 `ui_locations` 主內容

### R7. desktop_software branch 責任

桌機程式不負責修正 location 主資料，只負責消費乾淨資料。

也就是說，桌機可以繼續讀 DB，但 DB 內容必須已經是：

- 單一 site
- 正式命名
- 帶 `room_id`
- 不含不該顯示的歷史髒資料

## 5. Proposed Changes

### R8. 先止血：停止把 MiR 半成品同步成 ui_locations 主內容

主程式不應再用目前的 `(display_name, mir_code)` 組合直接 upsert `ui_locations`。

最小止血做法：

- 保留 MiR API 讀取 locations 的流程，因為 UI combo 與現場狀態仍需要
- 停止現有 `sync_ui_locations(sorted_combo_data)` 這種從 live data 反推 DB 的寫法
- 改為由 `site config` 產出正式 `ui_locations` 發佈資料，再寫 DB

### R9. 發佈資料的最小欄位集合

若沿用現有桌機讀法，`ui_locations` 至少應穩定提供：

- `display_name`
- `mir_code` 或 `mir_name`
- `room_id`

建議將本次發佈語意明確定義為：

- 一筆 row 代表一個「可供桌機使用的 site location」
- 該 row 必須已完成 site config 正規化

### R10. 發佈來源改為 site config

主程式應新增一條明確流程，例如概念上：

1. 讀取目前啟用的 site profile
2. 從 `site_config["locations"]` 篩出需要發佈到桌機的 location
3. 將正式的 `display_name / mir_name / room_id` 全量發佈到 `ui_locations`
4. 同 site 舊資料一併更新或替換

這條流程的資料來源只能是 site config，不可混用 live 掃描結果補欄位。

### R11. 桌機短期維持讀 DB，不強迫改讀 site json

為了最小改動，本次不要求 `desktop_software` 直接吃 `site/*.json`。

短期策略：

- 讓桌機維持讀 `ui_locations`
- 但把 `ui_locations` 定義成由主程式發佈的乾淨 projection

這樣能最小幅度改動使用端，同時先收斂資料責任。

## 6. Delivery Phases

### Phase 1. 先止血

- 停止主程式以 MiR live 掃描結果 upsert `ui_locations`
- 新增或改寫 `ui_locations` 發佈流程，使其只吃 `site config`
- 保證發佈到 `ui_locations` 的資料都帶正式 `room_id`
- 若 `site config` 中某些 location 不應出現在桌機清單，先在發佈層排除

完成後的驗收結果：

- 主程式重新啟動後，不會再把髒的歷史 `display_name` 寫回 DB
- 桌機讀到的資料集合與 site config 一致

### Phase 2. 再重構

- 將「MiR live locations 比對」與「UI location 發佈」拆成兩個明確函式
- 在 `TaskDBManager` 中把 `sync_ui_locations()` 語意改名或改責任，避免誤解成 live sync
- 若有需要，新增 site-aware 的 DB 寫入條件，避免不同 site 互相覆蓋

完成後的驗收結果：

- 程式碼層面看得出 canonical source 與 published projection 的差異
- `ui_locations` 不再由 UI combobox 組裝內容反推

### Phase 3. 最後清資料

- 清除 DB 內舊 site 殘留資料
- 清除歷史 `display_name`
- 補齊或重建 `room_id`
- 驗證桌機實際看到的項目數與 site config 發佈數一致

完成後的驗收結果：

- DB 中不再殘留與目前 site config 不一致的 location row
- 桌機下拉選單不需靠 `if not room_id: continue` 才能避開髒資料

## 7. Acceptance Criteria

| ID | Type | Criteria |
|---|---|---|
| R07-A1 | runtime | 啟動主程式後，`ui_locations` 僅包含目前 site config 定義並發佈的 location |
| R07-A2 | runtime | `ui_locations` 的桌機可見 location 均具備正式 `room_id` |
| R07-A3 | runtime | 主程式不再把 MiR live 掃描結果中的未知名稱或歷史名稱直接寫入 `ui_locations` |
| R07-A4 | runtime | 桌機建立任務時讀到的 `room_id` 與主程式 `ROOM_ID_MAP` 對同一 `display_name` 的結果一致 |
| R07-A5 | data | DB 清理後，不同 site 的 location 不會因 `display_name` 衝突互相覆蓋 |

## 8. Risks

### R12. `display_name` 作為 conflict key 風險偏高

若 `ui_locations` 仍以 `display_name` 為唯一鍵，則會有：

- 跨 site 同名衝突
- 改名歷史覆蓋問題
- 無法區分不同 profile 的 published rows

本次若先做最小改動，可以先不重做整個 schema，但至少要在實作時確認：

- DB 目前是否只會同時服務單一 site
- 或是否已有可用欄位能限制 site 範圍

若答案是否定的，就應升級成較大範圍的 schema refactor。

### R13. site config 內不一定所有 location 都該進桌機下拉

目前 `locations[]` 可能同時包含：

- 手術室
- 車架位置
- 充電樁
- 電梯
- demo 點位

若桌機真正只應顯示可派送目的地，本次可能需要最小補一個發佈篩選規則。

短期可以先沿用現有業務規則，例如：

- 只發佈有 `room_id` 且屬於桌機可操作類型的點

但長期較好做法是讓 site schema 顯式標示用途，例如：

- `location_type`
- `publish_to_desktop`
- `task_selectable`

### R14. 若要做多 site 並存，可能超出小型改動

如果需求已包含：

- 同一 DB 同時承接多個 site
- 桌機依 site 切換
- 保留歷史版本 location

那就不只是止血，而是正式資料模型重整，應升級成 `ddd-plan` 後再拆 phase。

## 9. Out Of Scope

本次不處理：

- task schema redesign
- mission schema redesign
- heartbeat 表責任調整
- `desktop_software` 全面改為直接讀 `site/*.json`
- location 欄位全面正規化為新資料表族群

## 10. Verification Plan

### V1. 啟動驗證

- 啟動主程式
- 確認 location UI 仍可顯示來自 MiR 現場 map 的可用點
- 確認 DB 發佈流程未再寫入未知 display name

### V2. DB 驗證

- 查詢 `ui_locations`
- 確認 row 集合與當前 site config 發佈集合一致
- 確認桌機使用的 row 均有 `room_id`

### V3. 桌機驗證

- 啟動 `desktop_software`
- 確認下拉資料乾淨、無歷史名稱
- 任選一筆建立 task，確認帶入的 `room_id` 與 site config 一致

## 11. Escalation Rule

本案目前可視為小型資料責任重整，不必先升級 `ddd-plan`。

只有在下列任一條件成立時，才升級為較大型規劃：

- 需要修改 `ui_locations` schema 才能安全承接多 site
- 需要同時改主程式與桌機的 location 模型
- 需要引入新 canonical table，而不只是把 `site config` 發佈到既有表
- 需要保留歷史版本或做資料遷移腳本治理

## 12. Implementation Hint

新聊天室若依本文件直接實作，建議順序：

1. 先找出 `main.py` 中所有 `ui_locations` 寫入點
2. 將 live-sync 寫入改成 site-config publish 寫入
3. 調整 `TaskDBManager` 命名與 SQL，使責任明確
4. 補一個最小 DB 清理策略
5. 最後才檢查 `desktop_software` 是否仍需微調過濾邏輯

## 13. 實作記錄

### 狀態
部分實作

### 實作摘要

- 新增 `build_ui_location_publish_rows(site_config)`，明確由 `site/*.json` 產生 `ui_locations` 發佈資料。
- 發佈規則先採最小假設：只發佈同一 active site 中具備 `display_name / mir_name / room_id` 的 location。
- `MainWindow` 啟動時改為先發佈 site projection 到 `ui_locations`，不再把 MiR live combo 結果直接回寫 DB。
- `TaskDBManager` 新增 `publish_ui_locations()`，以全量覆蓋方式清掉舊資料並重建當前 site projection。

### 測試覆蓋

- `tests/test_ui_locations_publishing.py`
  - 驗證 hospital site 只發佈具備 `room_id` 的 location，且排除 `充電樁`
  - 驗證 `publish_ui_locations()` 會先清空 `ui_locations`，再寫入 `(display_name, mir_code, room_id)` projection

### 變更的檔案

#### 生產代碼

- `main.py`
- `TaskDBManager.py`

#### 測試代碼

- `tests/test_ui_locations_publishing.py`

### 驗收標準驗證

| 驗收標準 | 狀態 | 依據 |
|---|---|---|
| R07-A1 | 部分 | 已改為由 site config 發佈 `ui_locations`；尚未做真 DB 內容人工核對 |
| R07-A2 | 通過 | `build_ui_location_publish_rows()` 只發佈具備 `room_id` 的 location |
| R07-A3 | 通過 | `load_map_positions()` 不再把 MiR live 掃描結果同步進 `ui_locations` |
| R07-A4 | 部分 | 發佈資料與 `ROOM_ID_MAP` 同源於 site config；尚未做桌機端端到端驗證 |
| R07-A5 | 部分 | 在「單一 active site」前提下改為全量覆蓋，可避免同庫殘留舊 site 髒資料；未處理多 site 並存 |

### 執行的命令

```bash
python -m unittest tests.test_ui_locations_publishing
python -m unittest tests.test_ui_locations_publishing tests.test_site_runtime_marker_maps tests.test_task_statistics_queries
```

### 假設與決策

- 採用使用者補充前提：同一時間只啟用一個 site，不做多 site 同庫並存設計。
- 目前最小發佈規則為「有 `room_id` 才發佈到桌機」，用來排除 `充電樁` 等非桌機目標點。
- `load_map_positions()` 在執行期間會被多次呼叫，因此發佈流程放在啟動階段，避免反覆 `DELETE + INSERT`。

### 延遲項目

- 尚未補真實 DB 驗證步驟，確認現場 `ui_locations` 內容與目前 site config 完全一致。
- 尚未驗證 `desktop_software` 實際下拉行為與任務建立流程。
- 若未來需要更細的桌機發佈規則，仍建議在 site schema 補 `publish_to_desktop` 或同類欄位。

### 備註

- 這次屬於 R07 Phase 1 止血實作，先把 canonical source 與 published projection 的責任切開。
- 若後續需求升級為多 site 並存或保留歷史版本，應改走 `ddd-plan` 拆成較大型資料模型重整。
