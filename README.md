# AMR Task System Outer Ring

這份 README 對應的是外環版本。這個專案是給 MiR AMR 使用的桌面任務管理系統，使用 `PySide6` 製作 GUI，透過 `requests` 呼叫 MiR REST API，並用 `PostgreSQL` 保存任務佇列、使用者帳號、UI 位置對照與房間心跳資料。

目前程式的主要入口是 `main.py`。執行後會開啟登入視窗，登入成功後進入主畫面，提供下列能力：

- 建立、排序、刪除與執行任務佇列
- 從 MiR 讀取機器人狀態、電量、位置與 mission queue 狀態
- 在主地圖與 selected map 上顯示站點、marker 與機器人位置
- 依場域切換不同地圖、站點、marker、任務映射
- 將可用 UI 位置與任務映射同步到 PostgreSQL
- 顯示績效儀表板，統計任務量、起點/終點熱點與路線熱點
- 顯示房間 heartbeat 狀態

## 目前實際目錄結構

以下是目前專案內和啟動、維護最相關的結構：

```text
amr-task-system/
|- main.py                        # GUI 入口、場域設定載入、主流程
|- functions.py                   # MiR API 呼叫與 config.json 讀寫
|- TaskDBManager.py               # 任務/心跳/UI 對照等 PostgreSQL 操作
|- UserDBManager.py               # 使用者帳號初始化與管理
|- task_thread.py                 # 任務排程執行緒
|- performance_dashboard.py       # 績效儀表板視窗與統計組裝
|- app_settings.json              # 一般使用者的場域切換設定
|- site/
|  |- company.json                # company 場域設定
|  `- hospital.json               # hospital 場域設定
|- picture/                       # 地圖、logo 與相關圖片資源
|- icons/                         # 儀表板與 UI 圖示
|- tests/                         # 單元測試
|- docs/                          # 額外 changelog
|- documents/                     # 開發文件、規劃與簡報草稿
|- demo_test/                     # 歷史測試打包產物
|- AMR_Task_System_InnerRing_*/   # 已打包 Windows 執行檔產物
|- AMR_Task_System_OuterRing_*/   # 已打包 Windows 執行檔產物
|- main.spec                      # PyInstaller 打包設定
`- desk_client_standalone_V3.spec # 另一份 PyInstaller 設定
```

## 執行前置條件

目前專案沒有 `requirements.txt`、`pyproject.toml` 或資料庫 migration/sql 初始化腳本，所以需要先手動準備環境。

- 作業系統：建議 Windows
- Python：建議 `3.10` 以上
- PostgreSQL：需要可連線的資料庫
- MiR AMR：需要可連線的 MiR REST API
- 網路：執行機器需能連到 MiR IP 與 PostgreSQL

依照目前 import 與程式使用情況，至少需要安裝：

```bash
pip install PySide6 requests numpy psycopg2-binary pytz debugpy
```

`debugpy` 目前是 `task_thread.py` 直接 import，所以若未安裝，啟動就可能失敗。

## 安裝方式

1. 建立虛擬環境。

```bash
python -m venv .venv
```

2. 啟用虛擬環境。

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

3. 安裝依賴。

```bash
pip install PySide6 requests numpy psycopg2-binary pytz debugpy
```

4. 準備 PostgreSQL 資料庫與資料表。

目前程式碼直接依賴下列資料表存在：

- `users`
- `tasks`
- `room_heartbeat`
- `ui_locations`
- `ui_missions`

注意：程式只會自動補一筆 `admin` 使用者，不會自動建立 `users` 或其他資料表結構。

## 執行方式

### 從原始碼啟動

1. 依下方說明建立 `config.json`
2. 確認 `app_settings.json` 與 `site/*.json` 設定正確
3. 確認 `main.py` 內的 `DB_CONFIG` 已改成你的資料庫連線資訊
4. 執行：

```bash
python main.py
```

### 切換場域

目前場域載入順序如下：

1. 環境變數 `AMR_SITE_PROFILE`
2. `app_settings.json` 內的 `site_profile`
3. 程式內建預設值 `company`

PowerShell 範例：

```powershell
$env:AMR_SITE_PROFILE = "hospital"
python main.py
```

### 打包執行檔

專案中已有 PyInstaller spec：

```bash
pyinstaller main.spec
```

不過目前 README 主要以原始碼執行為主，因為現場設定、資料庫與 MiR IP 仍需個別調整。

## 設定方式

目前實際上會影響執行的設定分成 4 類。

### 1. `config.json`

`config.json` 已被 `.gitignore` 忽略，請手動建立，不要提交真實檔案。

目前程式實際讀取的欄位只有：

- `MIR_IP`：MiR REST API 根網址
- `heartbeat_display_count`：主畫面要顯示幾個 heartbeat label，程式會自動限制在 `0` 到 `13`

專案內目前沒有 `config.example.json`，可直接用下面這份安全範例手動建立：

```json
{
  "MIR_IP": "http://192.168.0.100",
  "heartbeat_display_count": 10
}
```

補充：

- `MIR_IP` 要填 MiR 主機的 base URL，例如 `http://10.11.202.251`
- `heartbeat_display_count` 若填超出範圍，程式會被夾到 `0~13`
- 目前 `config.json` 不包含 API 帳密

### 2. `app_settings.json`

這個檔案目前主要只控制預設場域：

```json
{
  "site_profile": "hospital"
}
```

可用值至少包含：

- `company`
- `hospital`

### 3. `site/<profile>.json`

這是目前場域設定的核心來源。`main.py` 會讀取 `site/company.json` 或 `site/hospital.json`，內容包含：

- `site_id`
- `display_name`
- `assets`
  - `main_map`
  - `selected_map`
  - `logo`
- `calibration`
  - `image_pts`
  - `world_pts`
- `markers`
- `locations`
- `missions`
- `selected_map`
- `target_3_rule`（部分場域有）

這些設定會決定：

- 主地圖與 selected map 用哪張圖
- world 座標如何轉成地圖像素
- 哪些 location 對應哪個 MiR 點位名稱
- 哪些 mission 允許被排程器使用
- 哪些點位要同步到 `ui_locations`
- 哪些 selected map 按鈕要顯示

### 4. PostgreSQL 連線

目前資料庫設定不是從 `config.json` 讀取，而是直接寫死在 `main.py`：

```python
DB_CONFIG = {
    "user": "postgres",
    "host": "localhost",
    "database": "military_mir250_project",
    "password": "123456",
    "port": 5432
}
```

新環境上線前，請先把這段改成實際資料庫資訊。

## 重要依賴與實際行為

### MiR API 認證

目前 `functions.py` 內直接使用：

- `API_USER = "Distributor"`
- `API_PASSWORD = "distributor"`

也就是說，目前只有 MiR IP 走 `config.json`，API 帳號密碼仍是程式碼常數；如果現場帳號不同，需要直接修改 `functions.py`。

### 預設管理者帳號

`UserDBManager.initialize_user_table()` 會在 `users` 資料表已存在的前提下，自動補一筆：

- 帳號：`admin`
- 密碼：`admin123`

建議第一次登入後立即更改。

### heartbeat label 數量

主畫面最多只支援 `13` 個 heartbeat label。即使 `config.json` 設更大，UI 仍只會顯示到 `13`。

### 本地上傳端點

主畫面在查詢錯誤歷史時，會把資料 POST 到：

```text
http://localhost:3000/upload
```

這不是啟動主程式的必要條件，但若你的流程依賴這個錯誤上傳接口，還需要另外準備本機服務。

## 已知限制與注意事項

- 目前沒有自動化安裝檔、`requirements.txt` 或 lock file，依賴需要手動安裝。
- 目前沒有資料庫 schema/migration 腳本，資料表需要手動建立。
- `DB_CONFIG` 仍寫死在 `main.py`，不是外部設定。
- MiR API 帳密仍寫死在 `functions.py`，不是外部設定。
- `config.json` 只負責 MiR IP 與 heartbeat 顯示數量，不包含所有系統設定。
- 場域切換高度依賴 `site/*.json` 中的 `locations`、`missions`、`markers` 與 `selected_map` 結構正確。
- 專案內含歷史打包產物與測試資料夾，真正的原始碼入口仍是 `main.py`，不要把 `demo_test/` 或已打包資料夾誤認成開發主線。
- README 所列資料表名稱是由目前程式查詢/更新邏輯反推，不代表資料庫結構已完整文件化。

## 建議的新接手流程

如果你是第一次接手，建議照這個順序確認：

1. 先安裝 Python 依賴
2. 建立 `config.json`
3. 設定 `app_settings.json` 或 `AMR_SITE_PROFILE`
4. 檢查 `site/<profile>.json` 的地圖、點位與 mission 映射
5. 修改 `main.py` 內的 `DB_CONFIG`
6. 確認 PostgreSQL 資料表已建立
7. 確認 MiR 可連線
8. 執行 `python main.py`

## 測試

專案目前有 `tests/`，包含場域設定、selected map runtime、dashboard 與 scheduler 相關測試。若環境已裝好依賴，可先從：

```bash
python -m unittest discover -s tests
```

開始驗證。
