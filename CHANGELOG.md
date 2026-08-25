# Changelog

本檔用來記錄對外可辨識的交付版本，不取代 Git commit 歷史。

## Versioning Rule

- 對外版本使用 `vMAJOR.MINOR.PATCH`
- `MAJOR`：有明顯重構、流程大改、需重新教育訓練
- `MINOR`：同一主線下的功能調整、院方回饋修正、可辨識的第二版第三版
- `PATCH`：小幅 bug fix，不改主要操作流程

## Released

### v1.1.0 - 2026-08-25

- 狀態：目前第二版
- 用途：院方初版之後，依回饋修正的版本
- 建議 Git tag：`v1.1.0-hospital-revision-1`
- 建議交付包檔名：`AMR_Task_System_v1.1.0_院方修正版.zip`
- 備註：若後續只修小 bug，可延伸為 `v1.1.1`

### v1.0.0 - 2026-08-20

- 狀態：院方初版
- 用途：對應上一個 commit，作為第一個交付給院方確認的版本
- 參考 commit：`82bd775` - `Add sterilization room selected-map point for hospital profile`
- 建議補正式 Git tag：`v1.0.0-hospital-initial`
- 建議交付包檔名：`AMR_Task_System_v1.0.0_院方初版.zip`
- 備註：若院方實際收到檔案的日期不同，可再把此日期改成實際交付日

## Next Release Template

複製以下區塊後往上新增：

### vX.Y.Z - YYYY-MM-DD

- 狀態：
- 用途：
- 建議 Git tag：
- 建議交付包檔名：
- 主要變更：
