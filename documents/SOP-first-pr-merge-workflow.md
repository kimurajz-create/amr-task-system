---
author: Codex
date: 2026-05-28
title: 第一次 PR 合併流程標準作業
uuid: 4e397c2d8ec54e55a317e570c2f7b6b1
version: v1
status: completed
---

# 第一次學習 PR 合併的標準作業

## 1. 目的

這份文件整理一次完整的 Git 合併流程，從功能分支開發完成後開始，到最後合併進 `main`、更新本地、刪除分支為止。

這份標準作業特別適用於這次實際情境：

- 本地功能分支還沒有 upstream
- 需要先 `push` 分支到 GitHub
- 透過 Pull Request 合併到 `main`
- PR 遇到 merge conflict
- 衝突處理策略是保留自己目前分支的版本

## 2. 名詞先懂

- `branch`：分支，拿來隔離功能開發
- `main`：主分支，正式整合後的版本
- `push`：把本地分支上傳到 GitHub
- `Pull Request` 或 `PR`：提交一個「我要把這條分支合進另一條分支」的申請
- `merge`：把兩條分支的變更合在一起
- `upstream`：本地分支對應的遠端分支
- `merge conflict`：Git 無法自動判斷要保留哪一邊的內容，需要人工決定

## 3. 適用前提

- 目前功能已經 commit 完成
- 知道自己要合進的目標分支是 `main`

先確認目前狀態：

```bash
git status -sb
git branch --show-current
```

## 4. 完整流程

### 步驟 1. 確認目前在哪個功能分支

```bash
git branch --show-current
```

例如會看到：

```text
spike/fullscreen-map-overlay
```

### 步驟 2. 第一次 push 功能分支

如果直接 `git push` 出現下面訊息：

```text
fatal: The current branch <branch-name> has no upstream branch.
```

代表：

- 本地分支存在
- 遠端還沒有對應分支
- 第一次 push 要明確指定 upstream

做法：

```bash
git push --set-upstream origin spike/fullscreen-map-overlay
```

之後同一條分支就可以直接：

```bash
git push
```

### 步驟 3. 在 GitHub 開 Pull Request

`push` 成功後，GitHub 通常會提示一條 PR 連結。打開後：

- `base` 選 `main`
- `compare` 選自己的功能分支
- 按 `Create pull request`

這一步不是直接把 `main` 蓋掉，而是提出「把我的分支合進 `main`」。

### 步驟 4. 檢查 PR 能不能直接合併

如果 PR 顯示可以直接 merge，就可以往下走。

若看到：

```text
Can't automatically merge
```

或 GitHub 顯示：

```text
This branch has conflicts that must be resolved
```

代表 `main` 和你的分支改到同一塊內容，Git 無法自動選擇。

### 步驟 5. 本地處理衝突

先抓最新遠端資訊：

```bash
git fetch origin
git branch --show-current
```

把最新 `main` 合進目前分支：

```bash
git merge origin/main
```

若某個檔案衝突，例如：

```text
task_thread.py
```

### 步驟 6. 衝突策略：保留自己分支的版本

如果這次策略是：

- 不保留 `main` 的衝突版本
- 保留自己目前功能分支的版本

可以使用：

```bash
git checkout --ours -- task_thread.py
```

注意：在 merge 過程中，`--ours` 指的是你目前所在分支，也就是你正在整理的功能分支版本。

做完後把檔案加入 staging：

```bash
git add task_thread.py
```

如果 merge 同時帶來其他正常變更，也一起 `add`。

### 步驟 7. 建立 merge commit

```bash
git commit -m "Merge origin/main into spike/fullscreen-map-overlay"
```

這個 commit 的意思不是功能修改，而是記錄：

- 我已把最新 `main` 合進我的功能分支

### 步驟 8. 把解完衝突的分支 push 回 GitHub

```bash
git push
```

push 成功後，GitHub 上那個 PR 會自動更新。

如果衝突真的解乾淨了，PR 頁面就會從不能 merge 變成可以 merge。

### 步驟 9. 在 GitHub 確認合併 PR

回到 PR 頁面後：

- 按 `Merge pull request`
- 再按 `Confirm merge`

看到 `Merged` 就代表這條功能分支已經正式進入 `main`。

### 步驟 10. 更新本地 main

PR merge 完，不代表你本地 `main` 自動更新，所以還要做：

```bash
git checkout main
git pull origin main
```

這一步是讓你本機的 `main` 和 GitHub 上最新的 `main` 同步。

### 步驟 11. 確認功能分支是否已安全可刪

```bash
git branch --merged main
```

如果看到自己的分支名稱出現在清單裡，代表它已經被合進 `main`，可以刪除。

### 步驟 12. 刪除本地與遠端分支

```bash
git branch -d spike/fullscreen-map-overlay
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
處理：把 `main` 合進自己的分支，解完衝突再 push。

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

## 8. 下次可以直接照這份做

1. 從最新 `main` 開新分支
2. 在新分支上開發與 commit
3. `git push --set-upstream origin <new-branch>`
4. 開 PR 合進 `main`
5. 若有衝突，先把 `origin/main` merge 進自己的分支再解
6. merge 完回本地更新 `main`
