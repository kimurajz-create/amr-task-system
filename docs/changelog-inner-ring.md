# Inner Ring Changelog

本檔記錄 `refactor/main-site-profile-inner-ring` 內環分支的對外交付版本。
版本號以 Git 歷史推定，不把純文件 commit 視為交付版。

## Branch

- 分支：`refactor/main-site-profile-inner-ring`
- 版本推定基準：以實際功能變更 commit 為主
- 不列入版本：`a3f512d` `docs: add release changelog and versioning guide`
- 不列入版本：`fe45ff9` `docs: clarify inner-ring release changelog`

## Released

### v1.3.0 - 2026-10-21

- 狀態：目前內環第四版（重置與 Dashboard 匯出）
- 用途：一鍵重置改為 `James_Reset_All` 流程，並補上績效 Dashboard 時間篩選與 PDF／Excel 匯出（與外環對齊）
- 主要變更：
  - 重置：clear_error → 清空佇列 → I/O 降下頂升柱 → 派送 `James_Reset_All`（急停時可 Pending，任務內含回充）
  - Dashboard：時間區間篩選、PDF 與文字版 Excel 匯出
  - 醫院任務選單維持只開「載運」
- 參考 commit：`6146c73` - `Sync performance dashboard PDF and Excel export from outer-ring.`
- 相關 commit：`2921778` `87c3977` `045483b`
- 建議 Git tag：`v1.3.0-inner-ring-reset-dashboard`
- 建議交付包檔名：`AMR_Task_System_InnerRing_v1.3.0_重置與Dashboard_20261021`
- 備註：交付資料夾名稱含版本號、主題、日期，方便辨識

### v1.2.0 - 2026-09-22

- 狀態：內環第三版（UI 優化交付）
- 用途：醫院端操作流程與介面預設優化（略過登入、起始點預設滅菌室、載運、自動 play、充電樁不進選單、中文警報、Executing 不可刪）
- 參考 commit：`e38ea17` - `Fix delete-task unit tests for Windows console encoding.`
- 相關 commit：`01d6fd1` `94cae82` `57920e4` `ec1d50d` `029e6eb`
- 建議 Git tag：`v1.2.0-inner-ring-ui-optimize`
- 建議交付包檔名：`AMR_Task_System_InnerRing_v1.2.0_UI優化_20260922`
- 備註：已被 v1.3.0 取代為目前最新交付版

### v1.1.0 - 2026-08-25

- 狀態：內環第二版
- 用途：院方初版之後，依回饋修正的版本
- 參考 commit：`22ba4dc` - `Fix emergency task room_id persistence`
- 建議 Git tag：`v1.1.0-inner-ring-revision-1`
- 建議交付包檔名：`AMR_Task_System_v1.1.0_院方修正版.zip`
- 備註：已被 v1.2.0 取代為目前最新交付版

### v1.0.0 - 2026-08-20

- 狀態：內環院方初版
- 用途：對應上一個 commit，作為第一個交付給院方確認的版本
- 參考 commit：`82bd775` - `Add sterilization room selected-map point for hospital profile`
- 建議 Git tag：`v1.0.0-inner-ring-initial`
- 建議交付包檔名：`AMR_Task_System_v1.0.0_院方初版.zip`
- 備註：若院方實際收到檔案的日期不同，可再把此日期改成實際交付日
