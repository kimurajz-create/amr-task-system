# Outer Ring Changelog

本檔記錄 `refactor/main-site-profile-outer-ring` 外環分支的對外交付版本。
版本號以 Git 歷史推定，不把純文件 commit 視為交付版。

## Branch

- 分支：`refactor/main-site-profile-outer-ring`
- 版本推定基準：以實際功能變更 commit 為主

## Released

### v1.3.0 - 2026-10-21

- 狀態：目前外環第四版（重置與 Dashboard 匯出）
- 用途：一鍵重置改為 `James_Reset_All` 流程，並補上績效 Dashboard 時間篩選與 PDF／Excel 匯出
- 主要變更：
  - 重置：clear_error → 清空佇列 → I/O 降下頂升柱 → 派送 `James_Reset_All`（急停時可 Pending，任務內含回充）
  - Dashboard：時間區間篩選、PDF 與文字版 Excel 匯出
  - 醫院任務選單維持只開「載運」
- 參考 commit：`f54dcb3` - `Harden reset around e-stop and drop the extra charge step.`
- 相關 commit：`7d4a77b` `06ee5e5` `63c1497` `1ab44e9` `3e256c3`
- 建議 Git tag：`v1.3.0-outer-ring-reset-dashboard`
- 建議交付包檔名：`AMR_Task_System_OuterRing_v1.3.0_重置與Dashboard_20261021`
- 備註：交付資料夾名稱含版本號、主題、日期，方便辨識

### v1.2.0 - 2026-09-22

- 狀態：外環第三版（UI 優化交付）
- 用途：醫院端操作流程與介面預設優化（略過登入、目的地預設洗滌室、載運、自動 play、充電樁不進選單、中文警報、Executing 不可刪）
- 參考 commit：`3f22d45` - `Fix delete-task unit tests for Windows console encoding.`
- 相關 commit：`5467cca` `b6886e0` `422bb89` `5c5c86f` `babff40` `bb30d9d`
- 建議 Git tag：`v1.2.0-outer-ring-ui-optimize`
- 建議交付包檔名：`AMR_Task_System_OuterRing_v1.2.0_UI優化_20260922`
- 備註：已被 v1.3.0 取代為目前最新交付版

### v1.1.0 - 2026-08-25

- 狀態：外環第二版
- 用途：院方初版之後，依回饋修正的版本
- 參考 commit：`af3742d` - `Fix emergency task room_id persistence`
- 建議 Git tag：`v1.1.0-outer-ring-revision-1`
- 建議交付包檔名：`AMR_Task_System_OuterRing_v1.1.0_院方修正版.zip`
- 備註：已被 v1.2.0 取代為目前最新交付版

### v1.0.0 - 2026-08-20

- 狀態：外環院方初版
- 用途：以外環場域設定完成作為第一個交付給院方確認的版本
- 參考 commit：`e4947b2` - `Add CF01 outer-ring shelf location config`
- 相關 commit：`09a6d81` - `Adjust selected-map positions for CF1 and charge station`
- 建議 Git tag：`v1.0.0-outer-ring-initial`
- 建議交付包檔名：`AMR_Task_System_OuterRing_v1.0.0_院方初版.zip`
- 備註：`v1.0.0` 以 2026-08-20 當天外環功能成形的一組 commit 推定，若你有實際交付時間可再微調日期
