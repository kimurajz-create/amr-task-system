# 🛠 Linux GUI 拖曳失效修復紀錄

### 🚩 問題狀況

* **現象**：打包到 Linux 後，自定義標題列無法拖動。
* **原因**：Linux **Wayland** 協定基於安全機制，封鎖了應用程式直接控制視窗座標的權限。

---

### 🚀 解決方案

#### 1. 外部修正：使用 `.sh` 啟動腳本 (不需重改程式碼)

此方法強制程式在 X11 相容模式下執行，繞過 Wayland 限制。

**步驟：**

1. 在終端機輸入： `nano start.sh`
2. 貼上以下內容：
```bash
#!/bin/bash
export QT_QPA_PLATFORM=xcb
./main

```


3. 存檔離開： `Ctrl+O` -> `Enter` -> `Ctrl+X`
4. 賦予執行權限：
```bash
chmod +x start.sh

```


5. 執行方法： ` ./start.sh`

#### 2. 內部修正：程式碼內嵌 (推薦，使用者可直接點擊 main)

在 `main.py` 最頂端（必須在 import Qt 套件之前）加入：

```python
import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

```

#### 3. 最佳實作：改用系統原生拖曳 API

若不想依賴相容模式，應修改 `mouseMoveEvent` 邏輯：

```python
# 讓系統接管拖曳，不手動計算座標
self.windowHandle().startSystemMove()

```

---