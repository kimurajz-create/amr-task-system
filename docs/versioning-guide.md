# Versioning Guide

## Recommended Naming For This Project

這個專案建議分三層命名，避免只靠檔名管理版本。

### 1. Git tag

用來標記「哪個 commit 是一個正式可回頭找的版本」。

建議格式：

- `v1.0.0-hospital-initial`
- `v1.1.0-hospital-revision-1`
- `v1.1.1-hotfix-login`

原則：

- `v1.0.0` = 給院方的第一個正式版本
- `v1.1.0` = 同一主線下的第二版、第三版這類可感知修正版
- `v1.1.1` = 第二版之後的小修正

### 2. Branch name

如果要開分支，建議描述「改什麼」，不要把分支當正式版本號。

建議格式：

- `feature/performance-dashboard`
- `fix/hospital-feedback-round-1`
- `refactor/site-runtime-maps`

### 3. Delivery package filename

交給院方的壓縮檔或安裝包，檔名直接帶版本與用途。

建議格式：

- `AMR_Task_System_v1.0.0_院方初版.zip`
- `AMR_Task_System_v1.1.0_院方修正版.zip`
- `AMR_Task_System_v1.1.1_院方修正版_hotfix.zip`

## Practical Workflow

每次對外交付時：

1. 先確認這次是 `MAJOR`、`MINOR` 還是 `PATCH`
2. 更新 [CHANGELOG.md](../CHANGELOG.md)
3. 在對應 commit 打 Git tag
4. 匯出交付包時把版本寫進檔名
5. 若院方會直接操作 GUI，之後可再把版本號顯示在畫面角落或「關於」頁

## Current Project Recommendation

- 院方初版：`v1.0.0`
- 本次修正版：`v1.1.0`
- 下次若只是小修：`v1.1.1`
- 下次若又是一輪院方確認版：`v1.2.0`
- 若未來流程或畫面大改：`v2.0.0`

## Git Commands

建立 tag：

```bash
git tag v1.1.0-hospital-revision-1
```

查看 tag：

```bash
git tag
```

推送 tag：

```bash
git push origin v1.1.0-hospital-revision-1
```
