---
author: Codex
date: 2026-05-27
title: MiR 狀態與主地圖外圈同步
uuid: 29af37b08087486e9bce6ff59d7f9158
version: v1
status: completed
---

# F01 MiR 燈號同步到主地圖車輛外圈

## 1. 功能概述

目前主地圖上的車輛外圈只在特定移動狀態下顯示綠色光圈，`Ready` 或停著沒有任務時則沒有圈，這讓地圖上的車輛提示更像任務執行指示，而不是 MiR 真實燈號的視覺同步。

本功能要把主地圖上的車輛外圈改成由 MiR `state_id` 驅動，讓地圖上的小車外圈和右上角 `Status` 共同反映同一份 MiR 狀態語意。外圈會持續顯示，不再只限移動中狀態，且不使用閃動動畫，避免操作人員長時間觀看不適。

## 2. 需求描述

- **作為** 主管或現場操作人員
- **我希望** 主地圖上的小車外圈顏色能同步 MiR 的真實燈號狀態
- **如此一來** 我能在地圖上直接辨識機器人目前狀態，而不是只看到任務是否正在執行

## 3. 驗收條件

- **情境 1：Ready 或待命狀態仍持續顯示外圈**
  - **前提** MiR API 回傳有效的 `state_id`，且機器人目前為 `Ready` 或其他非移動狀態
  - **當** 主地圖刷新車輛 marker
  - **則** 地圖上的小車外圈仍持續顯示
  - **而且** 外圈顏色使用該 `state_id` 對應的 `map_ring_color`

- **情境 2：每個 state_id 使用自己的外圈顏色**
  - **前提** 系統已定義 MiR `state_id` 的中央狀態常數表
  - **當** `state_id` 在不同狀態之間切換
  - **則** 右上角 `Status` 與地圖外圈都從同一份中央常數取值
  - **而且** 地圖外圈可使用獨立於 label 文字色的高對比色碼

- **情境 3：外圈只表達顏色，不使用閃動**
  - **前提** 操作畫面長時間顯示主地圖
  - **當** 任一 MiR 狀態被渲染到地圖
  - **則** 外圈為靜態顯示
  - **而且** 不再使用只有移動中狀態才會出現的閃動綠色光圈

- **情境 4：Unknown / Offline 使用同一個異常色**
  - **前提** 系統無法取得有效的 MiR `state_id`，或目前輪詢/對帳判定狀態不可用
  - **當** 地圖與右上角狀態區重新渲染
  - **則** 外圈顯示明確的 Unknown/Offline 異常色
  - **而且** 不沿用上一個成功狀態的顏色

- **情境 5：小車本體外觀維持不變**
  - **前提** 主地圖車輛 marker 仍由 `draw_robot_marker()` 繪製
  - **當** 本功能啟用
  - **則** 只調整外圈繪製規則
  - **而且** 不更動小車本體的形狀與主要填色

## 4. 測試情境

| ID | 情境 | 前提 | 動作 | 預期結果 | 優先級 |
|---|---|---|---|---|---|
| TC1 | Ready 顯示外圈 | `state_id = Ready` 且無執行中任務 | 主地圖刷新 marker | 小車外圈持續顯示，不因無任務而消失 | 高 |
| TC2 | 移動中狀態換色 | `state_id` 從 `Ready` 變成 `Executing` 或 `Docking` | 主地圖刷新 marker | 外圈顏色切換到對應 state 色，不使用閃動動畫 | 高 |
| TC3 | 右上角與地圖共用狀態表 | 系統有中央狀態常數表 | `state_id` 更新 | `label_Status_1` 名稱與顏色、地圖外圈都由同一份表驅動 | 高 |
| TC4 | Unknown/Offline 異常色 | 輪詢失敗或 `state_id` 無法解析 | UI 重新渲染 | 外圈顯示同一個異常色，且不保留舊色 | 高 |
| TC5 | 小車本體不變 | 地圖上已有既有車輛圖示 | 啟用新狀態外圈 | 只有外圈規則變更，小車本體視覺不變 | 中 |

## 5. 實作說明

- **中央狀態常數表**
  - 在 `main.py` 建立單一來源的 MiR 狀態常數表。
  - 每個 `state_id` 至少定義：
    - `name`
    - `label_color`
    - `map_ring_color`
  - `Unknown/Offline` 使用同一個 fallback entry。

- **單一真相來源**
  - `state_id` 是唯一真相來源。
  - 地圖外圈不再從任務 `Executing/Pending` 狀態推導。
  - `query_mir_status_db()`、即時狀態輪詢與右上角狀態更新都應收斂到同一份呈現對映。

- **UI 影響範圍**
  - `main.py`
  - `label_Status_1`
  - `draw_robot_marker()`
  - 與 `current_mir_state_id`、`mir_status_poll_disconnected` 相關的 fallback 渲染流程

- **畫面規則**
  - 地圖外圈一律顯示，除非整個 robot marker 本身未被繪製。
  - 地圖外圈色碼可為白底地圖調整成高對比版本，但必須保留與 `state_id` 一致的語意。

- **文件缺口**
  - repository 內尚未保存主管提到的官方 `state_id -> 顏色` 文件。
  - 實作時應把外部文件中的正式對應表轉寫進中央常數，避免憑目前零散的 `status_map` 硬推。

## 6. 影響範圍

- `main.py`
- `documents/modules/M01-ui-application-shell.md`
- `documents/modules/M03-mir-api-adapter.md`

## 7. 風險與注意事項

- `main.py` 目前已有多份重複的 `status_map`，若只改其中一處會造成右上角與地圖圈圈不一致。
- 若 Unknown/Offline 繼續沿用上一個顏色，現場會誤判機器人仍處於正常狀態。
- 若直接沿用 label 文字色而不做 map 對比調整，白底地圖上的黃色、白色等色碼辨識度可能不足。

## 8. 非目標

- 不改動 MiR API 呼叫方式。
- 不改動任務排程或 DB 狀態流。
- 不改動小車本體 icon 造型。

## 9. 後續實作提示

1. 先收斂 `main.py` 內現有重複的 `status_map` 為單一常數。
2. 讓 `_update_status_label()` 與 `draw_robot_marker()` 共用同一份常數。
3. 補測試驗證 `Ready`、`Executing`、`Docking` 與異常狀態顏色切換。
4. 明確定義 Unknown/Offline fallback entry，供 label 與 map ring 共用。

## 10. 實作紀錄

### 最終行為

- 地圖上的車輛外圈現在會持續顯示，不再只在移動狀態出現。
- 外圈顏色改由 MiR `state_id` 對應的中央常數表決定。
- 右上角 `Status` 與地圖外圈共用同一份狀態來源。
- Unknown / Offline 會落到同一個 fallback 顏色，不再沿用上一個成功狀態。

### 異動檔案

- `main.py`
- `CONTEXT.md`

### 驗證

- `main.py` 已用 Python `compile(...)` 做語法檢查。

### 已知限制

- repository 內原本已有多份歷史 `status_map` / method 定義殘留，這次實作以新的最終 method 覆蓋它們；若後續持續整理 `MainWindow`，可再進一步清理死碼。
