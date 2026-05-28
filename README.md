# AMR Task System

## 啟動方式

一般啟動：

```powershell
python main.py
```

## Site Profile 切換

程式啟動時會依照下列優先順序決定要載入哪個場域設定：

1. `AMR_SITE_PROFILE` 環境變數
2. `app_settings.json` 內的 `site_profile`

目前可用值：

- `company`
- `hospital`

### 方式 1: 固定使用 `hospital.json`

修改 [app_settings.json](./app_settings.json)：

```json
{
  "site_profile": "hospital"
}
```

然後照原本方式啟動：

```powershell
python main.py
```

### 方式 2: 單次啟動臨時切換到 hospital

```powershell
$env:AMR_SITE_PROFILE="hospital"
python main.py
```

如果有設定 `AMR_SITE_PROFILE`，它會覆蓋 `app_settings.json` 的值。

## 設定檔

- [app_settings.json](./app_settings.json): 場域切換設定
- [config.json](./config.json): MiR IP 與其他執行期設定
- [site/hospital.json](./site/hospital.json): hospital 場域設定
- [site/company.json](./site/company.json): company 場域設定

## Linux / Wayland 備註

如果在 Linux 的 Wayland 環境遇到 Qt 視窗問題，可以先用 X11 相容模式啟動：

```bash
export QT_QPA_PLATFORM=xcb
python main.py
```
