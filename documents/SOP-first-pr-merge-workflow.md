---
author: Codex
date: 2026-05-28
title: First PR Merge Workflow SOP
uuid: 4e397c2d8ec54e55a317e570c2f7b6b1
version: v1
status: completed
---

# 第一次學習 Merge 的 SOP

## 1. 目的

這份文件整理一次完整的 Git 合併流程，從功能分支開發完成後開始，到最後合併進 `main`、更新本地、刪除分支為止。

這份 SOP 特別適用於這次實際情境：

- 本地功能分支還沒有 upstream
- 需要先 `push` 分支到 GitHub
- 透過 Pull Request 合併到 `main`
- PR 遇到 merge conflict
- 衝突處理策略是保留自己目前 branch 的版本

## 2. 名詞先懂

- `branch`: 分支，拿來隔離功能開發
- `main`: 主分支，正式整合後的版本
- `push`: 把本地分支上傳到 GitHub
- `Pull Request` 或 `PR`: 提交一個「我要把這條 branch 合進另一條 branch」的申請
- `merge`: 把兩條 branch 的變更合在一起
- `upstream`: 本地 branch 對應的遠端 branch
- `merge conflict`: Git 無法自動判斷要保留哪一邊的內容，需要人工決定

## 3. 適用前提

開始前先確認：

- 目前功能已經 commit 完成
- 知道自己要合進的目標分支是 `main`
- 本地沒有不想一起帶進去的暫存修改

可先檢查：

```bash
git status -sb
git branch --show-current
```

## 4. 完整 SOP

### Step 1. 確認目前在哪個功能分支

```bash
git branch --show-current
```

這次實際分支是：

```bash
spike/fullscreen-map-overlay
```

如果你不是在自己的功能分支上，先切回去。

### Step 2. 第一次 push 功能分支

如果直接 `git push` 出現下面這種訊息：

```text
fatal: The current branch <branch-name> has no upstream branch.
```

意思是：

- 本地 branch 存在
- 遠端還沒有對應 branch
- 第一次 push 要明確指定

正確做法：

```bash
git push --set-upstream origin spike/fullscreen-map-overlay
```

成功後，以後這條分支就可以直接用：

```bash
git push
```

### Step 3. 在 GitHub 開 Pull Request

`push` 成功後，GitHub 通常會提示一條 PR 連結。打開後：

- `base` 選 `main`
- `compare` 選自己的功能分支
- 填寫標題與簡單描述
- 按 `Create pull request`

這一步不是直接把 `main` 蓋掉，而是提出「把我的 branch 合進 `main`」。

### Step 4. 檢查 PR 能不能直接 merge

如果 PR 顯示可以直接 merge，就可以往下走。

如果看到：

```text
Can't automatically merge
```

或 GitHub 顯示：

```text
This branch has conflicts that must be resolved
```

代表 `main` 和你的 branch 改到同一塊內容，Git 無法自動選擇。

### Step 5. 本地處理 merge conflict

這次實際採用的是本地解衝突，流程如下：

先抓最新遠端資料：

```bash
git fetch origin
```

確認自己還在功能分支：

```bash
git branch --show-current
```

把最新 `main` 合進目前 branch：

```bash
git merge origin/main
```

這次的衝突檔案是：

```bash
task_thread.py
```

### Step 6. 衝突策略：保留自己 branch 的版本

這次需求是「後蓋前」，也就是：

- 不保留 `main` 的衝突版本
- 保留目前功能分支自己的版本

如果只想保留自己 branch 的版本，可以用：

```bash
git checkout --ours -- task_thread.py
```

注意：在 merge 過程中，`--ours` 指的是你目前所在 branch，也就是你正在整理的功能分支版本。

做完後把檔案加入 staging：

```bash
git add task_thread.py
```

如果 merge 同時帶來其他正常變更，也一起 `add`。

### Step 7. 建立 merge commit

衝突解完後提交：

```bash
git commit -m "Merge origin/main into spike/fullscreen-map-overlay"
```

這個 commit 的意思不是功能修改，而是記錄：

- 我已把最新 `main` 合進我的功能分支
- 我已處理好衝突

### Step 8. 把解完衝突的 branch push 回 GitHub

```bash
git push
```

push 成功後，GitHub 上那個 PR 會自動更新。

如果衝突真的解乾淨了，PR 頁面就會從不能 merge 變成可以 merge。

### Step 9. 在 GitHub 確認 merge PR

回到 PR 頁面後：

- 確認狀態正常
- 按 `Merge pull request`
- 再按 `Confirm merge`

看到 `Merged` 就代表這條功能分支已經正式進入 `main`。

### Step 10. 更新本地 main

PR merge 完，不代表你本地 `main` 自動更新，所以還要做：

```bash
git checkout main
git pull origin main
```

這一步是讓你本機的 `main` 和 GitHub 上最新的 `main` 同步。

### Step 11. 確認功能分支是否已安全可刪

先檢查：

```bash
git branch --merged main
```

如果看到自己的分支名稱出現在清單裡，代表它已經被合進 `main`，可以刪除。

這次確認後，`spike/fullscreen-map-overlay` 已經在 merged 清單內。

刪分支前提醒：

- 先確認你要刪的是「這次 PR 的分支」，不是其他舊分支
- 先確認這條分支有出現在 `git branch --merged main` 清單裡
- 記住本機刪除和遠端刪除是兩件事，兩個指令都要分開確認分支名稱

### Step 12. 刪除本地與遠端 branch

刪本地：

```bash
git branch -d spike/fullscreen-map-overlay
```

刪遠端：

```bash
git push origin --delete spike/fullscreen-map-overlay
```

做到這一步，這次 merge 流程才算完整收尾。

## 5. 這次實際走過的完整指令順序

```bash
git push --set-upstream origin spike/fullscreen-map-overlay
git fetch origin
git merge origin/main
git checkout --ours -- task_thread.py
git add task_thread.py
git commit -m "Merge origin/main into spike/fullscreen-map-overlay"
git push
git checkout main
git pull origin main
git branch --merged main
git branch -d spike/fullscreen-map-overlay
git push origin --delete spike/fullscreen-map-overlay
```

## 6. 常見判斷句

### 看到「has no upstream branch」

意思：第一次 push，還沒綁遠端分支。  
處理：用 `git push --set-upstream origin <branch>`

### 看到「Can't automatically merge」

意思：PR 有衝突，GitHub 不能自動合併。  
處理：把 `main` 合進自己的 branch，解完衝突再 push。

### 同事說「合併到主分支」

通常意思是：

- 先把你的功能分支 push 上去
- 開 PR
- 再 merge 進 `main`

不是把 `main` 整條覆蓋掉。

## 7. 完成定義

符合以下條件，就算這次 merge 流程完成：

- 功能分支已 push 到遠端
- PR 已建立
- conflict 已處理
- PR 狀態顯示 `Merged`
- 本地 `main` 已 `git pull origin main`
- 本地功能分支已刪除
- 遠端功能分支已刪除

## 8. 下次可以直接照這份做

下次做新功能時，建議流程是：

1. 從最新 `main` 開新 branch
2. 在新 branch 上開發與 commit
3. `git push --set-upstream origin <new-branch>`
4. 開 PR 合進 `main`
5. 若有衝突，先把 `origin/main` merge 進自己的 branch 再解
6. merge 完回本地更新 `main`
7. 刪除已完成的功能分支

這樣就會是一個完整、乾淨、可重複的協作流程。
