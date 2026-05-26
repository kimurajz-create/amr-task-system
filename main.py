import sys
import os
import json
import ipaddress
import numpy as np
import requests
import random
import time
import functions
from pathlib import Path
from task_thread import TaskThread
from ui_login_window import Ui_Form_LoginWindow
from ui_admin_panel import Ui_Form_AdminPanel
from ui_selected_map import Ui_Form_SelectedMap
from utils import hash_password
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QWidget,QLabel,QLineEdit,QListWidget,
    QPushButton, QVBoxLayout, QMessageBox, QCompleter,QInputDialog,QComboBox,
    QLabel, QScrollArea, QFrame, QTableWidgetItem,QHeaderView,QHBoxLayout,QSizePolicy,
    QListWidgetItem,QGraphicsView, QGraphicsScene, QGraphicsProxyWidget,QToolBar,QMenu,
    QWidgetAction,QToolButton,
)
from PySide6.QtGui import (
    QPixmap, QPainter, QPen, QIcon, QPalette, 
    QColor, QMouseEvent,QBrush,QWheelEvent
)
from PySide6.QtCore import (
    QTimer, QDateTime, Qt,QSize,Signal,QEvent,QPoint,QRect
)
# 引入我們寫好的資料庫管理器
from TaskDBManager import TaskDBManager
from UserDBManager import UserDBManager
from ui_main import Ui_MainWindow

# 從轉換後的檔案中引入 UI 類別
# 注意：這裡假設您的轉換檔案名是 ui_login_window.py 和 ui_admin_panel.py
from ui_login_window import Ui_Form_LoginWindow
from ui_admin_panel import Ui_Form_AdminPanel

# 引入 PySide6 的 QThread 和 Signal
from PySide6.QtCore import QThread, Signal


def _get_runtime_search_dirs():
    # 同時搜尋 PyInstaller 解包資料夾與 exe 所在資料夾，
    # 讓同一份程式在開發環境與打包後都能找到資源檔。
    search_dirs = []

    if getattr(sys, "frozen", False):
        meipass_dir = getattr(sys, "_MEIPASS", None)
        if meipass_dir:
            search_dirs.append(Path(meipass_dir))
        search_dirs.append(Path(sys.executable).resolve().parent)
    else:
        search_dirs.append(Path(__file__).resolve().parent)

    return search_dirs


# 設定檔與圖片路徑共用的搜尋根目錄。
# 開發時會指向專案目錄；打包後則會額外檢查解包目錄與 exe 目錄。
RUNTIME_SEARCH_DIRS = _get_runtime_search_dirs()

# 提供給一般使用者的啟動預設值。
# 正常情況下應修改 app_settings.json，而不是直接改 main.py。
DEFAULT_APP_SETTINGS = {
    "site_profile": "company",
}

# 保底用的資源路徑。
# 只有當 site 設定檔缺欄位，或完全找不到設定檔時才會用到。
DEFAULT_SITE_ASSETS = {
    "main_map": "picture/pure_dilated_map.png",
    "selected_map": "picture/pure_dilated_map.png",
    "logo": "picture/aceicon1.png",
}

# 保底用的地圖校正點。
# 只有當 site 設定檔尚未提供 image_pts / world_pts 時才會使用。
DEFAULT_SITE_CALIBRATION = {
    "image_pts": [[933, 552], [567, 1381], [2635, 950]],
    "world_pts": [[1.465, 28.374], [-5.091, 9.006], [34.138, 17.249]],
}


def resolve_runtime_path(relative_path):
    # 把像 picture/xxx.png 這種相對路徑轉成實際可讀取的路徑，
    # 讓執行前與打包後都能共用同一種寫法。
    if not relative_path:
        return None

    if isinstance(relative_path, str) and relative_path.startswith(":/"):
        return relative_path

    relative_path = Path(relative_path)
    for base_dir in RUNTIME_SEARCH_DIRS:
        candidate = base_dir / relative_path
        if candidate.exists():
            return str(candidate)

    return str(RUNTIME_SEARCH_DIRS[0] / relative_path)


def load_app_settings():
    # app_settings.json 是一般使用者切換場域的入口；
    # 環境變數則保留給開發與測試時臨時覆蓋用。
    settings_relative_path = Path("app_settings.json")

    for base_dir in RUNTIME_SEARCH_DIRS:
        candidate = base_dir / settings_relative_path
        if not candidate.exists():
            continue

        try:
            with candidate.open("r", encoding="utf-8") as settings_file:
                app_settings = json.load(settings_file)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"app_settings.json 讀取失敗，改用預設值: {exc}")
            return DEFAULT_APP_SETTINGS.copy()

        merged_settings = DEFAULT_APP_SETTINGS.copy()
        merged_settings.update(app_settings)
        return merged_settings

    return DEFAULT_APP_SETTINGS.copy()


# 啟動時的場域決策優先順序：
# 1. AMR_SITE_PROFILE 環境變數（開發 / 測試臨時覆蓋）
# 2. app_settings.json（一般使用者設定）
# 3. DEFAULT_APP_SETTINGS 內建保底值
APP_SETTINGS = load_app_settings()
DEFAULT_SITE_PROFILE = os.environ.get(
    "AMR_SITE_PROFILE",
    APP_SETTINGS.get("site_profile", "company"),
)


def load_site_config(site_profile=None):
    # site_profile 只負責決定「要載入哪一個場域」；
    # 真正的地圖與 Logo 路徑都放在 site/<profile>.json 裡。
    # 從這一步開始，location / mission / quick action 也逐漸往 site config 集中。
    site_profile = site_profile or DEFAULT_SITE_PROFILE
    site_config_relative_path = Path("site") / f"{site_profile}.json"
    site_config_path = Path(resolve_runtime_path(site_config_relative_path))

    if not site_config_path.exists():
        # 如果指定場域不存在，先退回 company，至少保有可用的基準設定。
        if site_profile != "company":
            print(f"找不到 site profile: {site_profile}，改用 company 設定。")
            return load_site_config("company")
        # 如果連 company.json 都不存在，就退回程式內建的保底圖片路徑。
        print("找不到 company site config，改用內建預設地圖資源。")
        return {
            "site_id": "company",
            "assets": DEFAULT_SITE_ASSETS.copy(),
            "calibration": DEFAULT_SITE_CALIBRATION.copy(),
            "locations": [],
            "missions": [],
        }

    try:
        with site_config_path.open("r", encoding="utf-8") as config_file:
            site_config = json.load(config_file)
    except (json.JSONDecodeError, OSError) as exc:
        if site_profile != "company":
            print(f"site profile 讀取失敗: {site_profile}，改用 company 設定。原因: {exc}")
            return load_site_config("company")
        print(f"company site config 讀取失敗，改用內建預設設定。原因: {exc}")
        return {
            "site_id": "company",
            "assets": DEFAULT_SITE_ASSETS.copy(),
            "calibration": DEFAULT_SITE_CALIBRATION.copy(),
            "locations": [],
            "missions": [],
        }

    assets = DEFAULT_SITE_ASSETS.copy()
    assets.update(site_config.get("assets", {}))
    site_config["assets"] = assets

    calibration = DEFAULT_SITE_CALIBRATION.copy()
    calibration.update(site_config.get("calibration", {}))
    site_config["calibration"] = calibration

    # 這三個欄位是新 schema。
    # 就算 hospital 還沒補資料，也先保證程式拿得到空陣列，不會直接噴錯。
    site_config.setdefault("locations", [])
    site_config.setdefault("missions", [])
    site_config.setdefault("site_id", site_profile)
    return site_config

# ----------------------------------------------------------------------
# 1. 數據層：定義 MiR 英文代碼與中文名稱的對應關係
# 這是你的「翻譯字典」英翻中，工程語言轉user語言
# ----------------------------------------------------------------------
USER_LOCATION_MAP = {
    "LbV2_Robot position Hua": "華陀會議室",
    "LbV2_Robot position lecture hall 02": "演講廳_02",
    "LbV2_Robot position lecture hall 01": "演講廳_01",
    "LbV2_Robot position Sofa3": "沙發3",
    "LbV2_Robot position Sofa2": "沙發2",
    "LbV2_Robot position Sofa1": "沙發1",
    "LbV2_Robot position Reception V2": "櫃台",

    "LbV2_MiR Charge 48V V2": "充電樁",
    "LbV2_Robot position Elv  Bridge Map": "電梯橋",
    
    "LbV2_Shelf position Hua" : "車架位置(華陀)",
    "LbV2_Shelf position lecture hall 02" : "車架位置(演講廳_02)",
    "LbV2_Shelf position lecture hall 01": "車架位置(演講廳_01)",
    "LbV2_Shelf position Sofa3": "車架位置(沙發3)",
    "LbV2_Shelf position Sofa2": "車架位置(沙發2)",
    "LbV2_Shelf position Sofa1": "車架位置(沙發1)",
    "LbV2_Shelf position Reception V2": "車架位置(櫃台)",

}

USER_MISSION_GROUP_MAP ={
    "ACE_Elv_0625": "電梯",
    "Lobby Demo Reception to lecture hall 01": "Demo_櫃台到演講廳_01並返回櫃台",
    "Lobby Demo Reception to lecture hall 02": "Demo_櫃台到演講廳_02並返回櫃台",
    "Lobby Demo Reception to Sofa1": "Demo_櫃台到沙發1並返回櫃台",
    "Lobby Demo Reception to Sofa2": "Demo_櫃台到沙發2並返回櫃台",
    "Lobby Demo Reception to Sofa3": "Demo_櫃台到沙發3並返回櫃台",
    "Lobby Demo Seminar Presentation Jordan": "Demo_櫃台出發大廳繞一圈",
    
    "Lobby Demo Cart Transport": "Demo_載貨運輸",
    "Lobby Demo Empty Cart Transport": "Demo_空車運輸",
}

REQUIRED_MISSION_CODES = {
    "Lobby Demo Cart Transport",    # 載貨運輸
    "Lobby Demo Empty Cart Transport", # 空車運輸
}

LOCATION_TO_MARKER = {
    "華陀會議室": "label_rp_1",
    "演講廳_02": "label_rp_2",
    "演講廳_01": "label_rp_3",
    "沙發1": "label_rp_4",
    "沙發2": "label_rp_5",
    "沙發3": "label_rp_6",
    "櫃台": "label_rp_7",
    "車架位置(華陀)": "label_rp_1",
    "車架位置(演講廳_02)": "label_rp_2",
    "車架位置(演講廳_01)": "label_rp_3",
    "車架位置(沙發1)": "label_rp_4",
    "車架位置(沙發2)": "label_rp_5",
    "車架位置(沙發3)": "label_rp_6",
    "車架位置(櫃台)": "label_rp_7",
}


# 暫時定義:公司的marker想像成醫院手術室marker賦予其room_id
ROOM_ID_MAP = {
    "華陀會議室": "OR01",
    "演講廳_02": "OR02",
    "演講廳_01": "OR03",
    "沙發3": "OR05",
    "沙發2": "OR06",
    "沙發1": "OR07",
    "櫃台": "OR08",

    "充電樁": "OR09",
    "電梯橋": "OR10",

    "車架位置(華陀)": "OR01",
    "車架位置(演講廳_02)": "OR02",
    "車架位置(演講廳_01)": "OR03",
    "車架位置(沙發3)": "OR05",
    "車架位置(沙發2)": "OR06",
    "車架位置(沙發1)": "OR07",
    "車架位置(櫃台)": "OR08",
}



# 圖上停車格：定義顏色樣式
STYLE_DEFAULT = "border: none; background-color: #33B1FF;" # 預設樣式
STYLE_EXECUTING = "border: none; background-color: green;"
STYLE_PENDING = "border: none; background-color: orange; color: white; "

# # 定義 ToolTip 的樣式 暫時沒用到
# tooltip_reset_style = """
#     QToolTip {
#         /* 強制設定黑色背景和白色文字，符合您的 UX/UI */
#         background-color: black !important; /* 強制黑色背景 */
#         border: 1px solid #767676; 
#         border-radius: 4px;
#         padding: 3px;
#     }
#     """

# 反轉字典：方便載入 ComboBox 時，以中文為 Key，中翻英
MIR_LOCATION_MAP = {v: k for k, v in USER_LOCATION_MAP.items()}
MIR_MISSION_GROUP_MAP = {v: k for k, v in USER_MISSION_GROUP_MAP.items()}

CHARGING_STATION_NAME = "充電樁"


def build_site_runtime_maps(site_config):
    """
    將 site/<profile>.json 的新結構，轉回目前程式既有邏輯可直接使用的 map。

    目的：
    1. 讓資料來源改成 site config
    2. 但暫時不要一次重寫所有舊流程
    3. 缺資料時仍保留舊 hardcode 當 fallback
    """
    runtime_maps = {
        # 先以舊 hardcode 當保底值，避免某個場域尚未補完整時整段功能失效。
        "user_location_map": USER_LOCATION_MAP.copy(),
        "mir_location_map": MIR_LOCATION_MAP.copy(),
        "user_mission_group_map": USER_MISSION_GROUP_MAP.copy(),
        "mir_mission_group_map": MIR_MISSION_GROUP_MAP.copy(),
        "room_id_map": ROOM_ID_MAP.copy(),
        "location_to_marker": LOCATION_TO_MARKER.copy(),
        "required_mission_codes": set(REQUIRED_MISSION_CODES),
        "charging_station_name": CHARGING_STATION_NAME,
    }

    location_records = site_config.get("locations") or []
    mission_records = site_config.get("missions") or []

    user_location_map = {}
    location_to_marker = {}
    room_id_map = {}
    charging_station_name = None

    for location in location_records:
        # 每一筆 location 同時承載：
        # MiR 名稱、UI 顯示名稱、marker 對應、room_id、以及是否為充電站。
        mir_name = location.get("mir_name")
        display_name = location.get("display_name")
        if not mir_name or not display_name:
            continue

        user_location_map[mir_name] = display_name

        marker_id = location.get("marker_id")
        if marker_id:
            location_to_marker[display_name] = marker_id

        room_id = location.get("room_id")
        if room_id:
            room_id_map[display_name] = room_id

        # 這裡不是用 display_name == "充電樁" 判斷，
        # 而是明確看 is_charging_station，之後不同場域可自由換名字。
        if location.get("is_charging_station"):
            charging_station_name = display_name

    if user_location_map:
        # 由 locations 陣列組回舊程式常用的兩張表：
        # 1. MiR name -> UI name
        # 2. UI name -> MiR name
        runtime_maps["user_location_map"] = user_location_map
        runtime_maps["mir_location_map"] = {v: k for k, v in user_location_map.items()}
    if location_to_marker:
        runtime_maps["location_to_marker"] = location_to_marker
    if room_id_map:
        runtime_maps["room_id_map"] = room_id_map
    if charging_station_name:
        runtime_maps["charging_station_name"] = charging_station_name

    user_mission_group_map = {}
    required_mission_codes = set()

    for mission in mission_records:
        # 每一筆 mission 目前先保留兩種角色：
        # 1. 下拉選單顯示名稱
        # 2. 是否納入 scheduler 任務清單
        mir_name = mission.get("mir_name")
        display_name = mission.get("display_name")
        if not mir_name or not display_name:
            continue

        user_mission_group_map[mir_name] = display_name
        if mission.get("scheduler_enabled"):
            required_mission_codes.add(mir_name)

    if user_mission_group_map:
        runtime_maps["user_mission_group_map"] = user_mission_group_map
        runtime_maps["mir_mission_group_map"] = {v: k for k, v in user_mission_group_map.items()}
    if required_mission_codes:
        runtime_maps["required_mission_codes"] = required_mission_codes

    return runtime_maps

# ------------將「耗時操作」丟到背景 thread 執行----------
class DBWorker(QThread):
    """
    通用 Worker（背景執行緒）

    用途：
    - 將「耗時操作」丟到背景 thread 執行
    - 避免 UI 卡死

    參數：
    - func：要執行的函式（API / DB）
    - args：函式參數

    回傳：
    - finished.emit(result)
    - error.emit(error_message)
    """

    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args
        
    def run(self):
        try:
            result = self.func(*self.args)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# -----------------登入管理系統class----------------------------------
# ------------------ 設定 ------------------ #
USER_FILE = Path("users.json")
DEV_BACKDOOR_HASH = hash_password("Jordan@2025")

# ------------------ 登入視窗 ------------------ #
class LoginWindow(QWidget, Ui_Form_LoginWindow): 
    def __init__(self, user_db_manager, task_db_manager, parents = None):
        super().__init__(parents)
        
        # 1. 呼叫 setupUi 來載入 Designer 中設計的所有元件
        self.setupUi(self) 
        self.apply_login_dark_theme()

        self.user_db_manager = user_db_manager
        self.task_db_manager = task_db_manager  

        # 確保密碼輸入框是密文模式 (也可以在 Designer 中設定)
        self.lineEdit_password_input.setEchoMode(QLineEdit.Password)
        self.resize(350, 260)
        self.label_title.setGeometry(QRect(100, 22, 141, 18))
        self.lineEdit_username_input.setFixedHeight(34)
        self.lineEdit_password_input.setFixedHeight(34)
        self.label_username.setGeometry(QRect(20, 58, 70, 18))
        self.lineEdit_username_input.setGeometry(QRect(20, 88, 301, 34))
        self.label_password.setGeometry(QRect(20, 134, 70, 18))
        self.lineEdit_password_input.setGeometry(QRect(20, 164, 301, 34))
        self.btn_login.setGeometry(QRect(125, 210, 103, 30))

        self.btn_login.clicked.connect(self.login)
        # 假設註冊說明按鈕名稱是 self.btn_register_info
        # 如果您的 UI 中沒有此按鈕，請註解或刪除下面這行
        # self.btn_register_info.clicked.connect(self.show_register_info)

    def apply_login_dark_theme(self):
        self.setStyleSheet("""
        QWidget {
            background-color: #1E1E1E;
            color: #F2F2F2;
        }
        QLabel {
            color: #F4F4F4;
            background: transparent;
        }
        QLineEdit {
            background-color: #2C2C2C;
            color: #F2F2F2;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 0 10px;
            font-size: 13px;
            selection-background-color: #3A7BD5;
            selection-color: #FFFFFF;
        }
        QLineEdit::placeholder {
            color: #A9A9A9;
        }
        QPushButton {
            background-color: #3A3A3A;
            color: #F5F5F5;
            border: 1px solid #5C5C5C;
            border-radius: 6px;
            padding: 6px 14px;
        }
        QPushButton:hover {
            background-color: #4A4A4A;
        }
        QPushButton:pressed {
            background-color: #2E2E2E;
        }
        """)

    def login(self):
        username = self.lineEdit_username_input.text().strip()
        password = self.lineEdit_password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "錯誤", "請輸入帳號與密碼!")
            return
        
        input_hash = hash_password(password) # 將輸入密碼雜湊化

        # --- 1. 檢查開發者後門 ---
        if username == "admin" and input_hash == DEV_BACKDOOR_HASH:
            QMessageBox.information(self, "維護登入", "使用開發者後門登入成功。")
            self.close()
            # 🚨 傳遞 db_manager 給下一個視窗
            self.open_admin_panel("admin", self.user_db_manager) 
            return
        
        # --- 2. 從資料庫取得密碼 ---
        # 🚨 DB 邏輯替換了原本的 if username in self.users
        stored_hash = self.user_db_manager.get_user_password_hash(username) 

        # --- 3. 檢查一般登入 ---
        # 檢查是否有找到帳號 (stored_hash 非 None)，且 Hash 值匹配
        if stored_hash and stored_hash == input_hash:
            QMessageBox.information(self, "成功", f"歡迎回來，{username}！")
            self.close()
            
            # 🚨 傳遞 db_manager 給下一個視窗
            if username == "admin":
                self.open_admin_panel(username, self.user_db_manager)
            else:
                self.open_main_window(username, self.user_db_manager)
        else:
            QMessageBox.critical(self, "登入失敗", "帳號或密碼錯誤！")
    
    def show_register_info(self):
        """按下『使用者申請說明』時顯示提示"""
        QMessageBox.information(
            self,
            "使用者申請說明",
            "本系統僅限管理者（admin）建立帳號。\n\n"
            "若您需要新帳號，請聯絡系統管理員協助新增。"
        )

    def open_main_window(self, username, user_db_manager):
        self.main = MainWindow(username, user_db_manager,task_db_manager)
        self.main.show()

    def open_admin_panel(self, username, user_db_manager):
        self.admin_panel = AdminPanel(username, user_db_manager)
        self.admin_panel.show()

# ------------------ Admin 管理畫面 ------------------ #
# AdminPanel 繼承 QWidget 和 Ui_Form_AdminPanel
class AdminPanel(QWidget, Ui_Form_AdminPanel):
    def __init__(self, username, user_db_manager):
        super().__init__()  # <--- 呼叫 setupUi
        self.setupUi(self)

       # 🚨 修正點 2: 儲存 DB Manager，並移除 load_users() 和 self.users
        self.user_db_manager = user_db_manager 
        self.username = username

        self.user_list = self.listWidget_user
        self.label_cur_user.setText(f"👑 管理者：{username}")
        # 確保密碼輸入框是密文模式
        self.lineEdit_new_pass_input.setEchoMode(QLineEdit.Password)

        # --- 綁定事件 ---
        self.btn_add.clicked.connect(self.add_user)
        self.btn_del.clicked.connect(self.delete_user)
        self.btn_change_my_pw.clicked.connect(self.change_my_password)
            
        # 初始化使用者列表
        self.refresh_user_list()
    
    def refresh_user_list(self):
        self.user_list.clear()
        user_list = self.user_db_manager.get_all_usernames()
        for u in user_list:
            self.user_list.addItem(u)

    def add_user(self):
        username = self.lineEdit_new_user_input.text().strip()
        password = self.lineEdit_new_pass_input.text().strip()
        hashed_password = hash_password(password)
        if not username or not password:
            QMessageBox.warning(self, "錯誤", "請輸入帳號與密碼！")
            return
        
        # 🚨 修正點 4: 使用 DB Manager 新增使用者
        success = self.user_db_manager.add_new_user(username, hashed_password)

        if not success:
            QMessageBox.warning(self, "重複", "該帳號已存在或資料庫錯誤！")
            return
    
        self.refresh_user_list()
        QMessageBox.information(self, "成功", f"已新增使用者：{username}")
        self.lineEdit_new_user_input.clear()
        self.lineEdit_new_pass_input.clear()

    def delete_user(self):
        selected =self.user_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "錯誤", "請選擇要刪除的使用者！")
            return
        
        username = selected[0].text()
        
        if username == "admin":
            QMessageBox.warning(self, "禁止", "不能刪除 admin!")
            return
        
        self.user_db_manager.delete_user(username)
      
        self.refresh_user_list()
        QMessageBox.information(self, "成功", f"已刪除使用者：{username}")

    def change_my_password(self):
        """讓 admin 修改自己的密碼"""
        
        # 彈出輸入框時設定密文模式 QLineEdit.Password
        old_pw, ok = QInputDialog.getText(self, "舊密碼驗證", "請輸入舊密碼：", QLineEdit.Password)
 
        if not ok or not old_pw:
            return
        
        stored_admin_hash = self.user_db_manager.get_user_password_hash("admin")

        if hash_password(old_pw) != stored_admin_hash:
            QMessageBox.warning(self, "錯誤", "舊密碼錯誤！")
            return

        new_pw, ok = QInputDialog.getText(self, "新密碼", "請輸入新密碼：", QLineEdit.Password)
        if not ok or not new_pw:
            return

        new_hashed_password = hash_password(new_pw)
        self.user_db_manager.update_user_password("admin", new_hashed_password)

        QMessageBox.information(self, "成功", "密碼已更新！")


# ------------------選擇地圖位置--------------------- #
class SelectedMap(QWidget,Ui_Form_SelectedMap):
    # 訊號與槽的自動參數傳遞機制說明，信號定義、信號發射、信號連接、槽函數定義
    # 定義一個自定義 Signal，用於傳遞一個字串 (str) 參數
    location_selected = Signal(str)


    def __init__(self, map_image_path=None):
        super().__init__()
        self.setupUi(self)

        # 小地圖不再固定寫死公司版圖片，而是改由目前場域設定決定。
        self.set_map_image(map_image_path)

        # 連接地圖上的地點按鈕
        self._connect_location_buttons()
        # 連接「確定」按鈕到發送信號的方法
        self.btn_sm_enter.clicked.connect(self._confirm_selection)
        self.btn_sm_cancel.clicked.connect(self.close)

    def set_map_image(self, map_image_path):
        if not map_image_path:
            return

        # 保留 Qt Designer 裡的預設圖當 fallback，
        # 但實際執行時會改成目前場域設定的小地圖。
        map_pixmap = QPixmap(map_image_path)
        if map_pixmap.isNull():
            print(f"小地圖載入失敗: {map_image_path}")
            return

        self.label_sm_map_1.setPixmap(map_pixmap)
        self.label_sm_map_1.setScaledContents(True)

    def _update_selected_point(self, location_name):
        """
        槽函數：接收地點名稱，並更新結果顯示框
        """
        # 將按鈕文字設定到 QLineEdit 中
        self.lineEdit_sm_selectedpoint.setText(location_name)
        
        # 同時儲存選擇結果，供「確定」按鈕使用
        self.selected_location = location_name

    def _connect_location_buttons(self):
        """
        連接地圖上的地點按鈕(selected_map.ui)
        """
        # 將您所有按鈕儲存在一個列表或元組中，方便管理
        location_buttons = [
            self.btn_sm_rp1, self.btn_sm_rp2, self.btn_sm_rp3,
            self.btn_sm_rp4, self.btn_sm_rp5, self.btn_sm_rp6,
            self.btn_sm_rp7
        ]
        
        for btn in location_buttons:
            # 🚨 關鍵點：使用 lambda 傳遞按鈕的文字 🚨
            # lambda 忽略了 clicked 訊號自帶的 checked 狀態參數
            # name=btn.text() 確保傳遞的是按鈕當前的文字內容
            btn.clicked.connect(lambda checked, name=btn.text(): self._update_selected_point(name))
            
        # 額外建議：確保 LineEdit 清空以開始選擇
        self.lineEdit_sm_selectedpoint.setText("")
        self.selected_location = ""

    def _confirm_selection(self):
        #「確定」按鈕的槽函數，發射信號並關閉視窗 selected_map.ui
        selected_text = self.lineEdit_sm_selectedpoint.text()
        if selected_text:
            self.location_selected.emit(selected_text)
        self.close()





# ----------------------------------------------------------------------
# 界面層：定義通知項目的視覺外觀
class NotificationItem(QWidget):
    """
    客製化單一通知項目的視覺外觀
    """
    def __init__(self, type, message, parent=None):
        super().__init__(parent)

        # 根據類型定義樣式
        if type == "完成":
            bg_color = "#D4EDDA"  # 淺綠色
            icon_text = "✅ 成功"
        elif type == "警告":
            bg_color = "#FFF3CD"  # 黃色
            icon_text = "⚠️ 警告"
        else: # 錯誤或一般
            bg_color = "#F8D7DA"  # 紅色系
            icon_text = "❌ 錯誤"
        
        # 如果你希望所有東西都緊密貼合，請按照以下順序檢查並設置：
        # QListWidget CSS：確保 QListWidget::item 的 margin 和 padding 為 0px。
        # NotificationItem CSS：確保 NotificationItem 的 margin 為 0px 0。
        # NotificationItem Layout：確保 main_layout.setContentsMargins(0, 0, 0, 0)。

        # 設置 Widget 的背景顏色和圓角
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 5px;
                color: #000000;
                margin: 0px 0; /* 在項目上下留點空間 */
            }}
        """)
        
        # 設定主佈局 (水平排列：圖標 - 訊息 - 伸縮空間 - 按鈕)
        main_layout = QHBoxLayout(self)
        # 將 layout 的上下左右內邊界都設為 0
        main_layout.setContentsMargins(0, 0, 0, 0) #10,8,10,8 = 上,下,左,右
        main_layout.setSpacing(10)

        # 1. 圖標標籤
        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(icon_label)

        # 2. 訊息內容 (自動換行)
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        main_layout.addWidget(message_label)

        # # 1. 訊息內容 (圖標、類型和詳細訊息合併在同一個 QLabel 內) 暫時沒用到
        # full_message = f'<span style="font-weight: bold;">{icon_text}</span> {message}'
        # message_label = QLabel(full_message)
        # message_label.setWordWrap(True)
        # message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 這裡使用富文本 (Rich Text) 來讓 "✅ 成功：" 部分粗體，而訊息保持常規
        message_label.setTextFormat(Qt.RichText)
        main_layout.addWidget(message_label)

        # # 3. 讓訊息內容自動伸展
        # main_layout.addStretch() 

        # 4. 關閉按鈕 (X)
        close_btn = QPushButton("X")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("QPushButton { border: none; font-size: 18px; color: #555; background-color: transparent; }")
        main_layout.addWidget(close_btn)
        
        # 將關閉按鈕存為屬性，供外部連接訊號
        self.close_button = close_btn

class CompactNotificationItem(QWidget):
    def __init__(self, notification_type, message, parent=None):
        super().__init__(parent)

        palette_map = {
            "完成": {
                "bg": "#DFF3E5",
                "border": "#79CEA0",
                "text": "#183926",
                "icon_bg": "#EFFAF2",
                "icon_fg": "#1E8E52",
                "close": "#4B6B56",
                "icon": "✓",
            },
            "警告": {
                "bg": "#FFF4D6",
                "border": "#F1C96A",
                "text": "#5D4513",
                "icon_bg": "#FFF9EB",
                "icon_fg": "#B7791F",
                "close": "#7A622B",
                "icon": "!",
            },
            "取消": {
                "bg": "#F9E1E6",
                "border": "#E59AA9",
                "text": "#5B2732",
                "icon_bg": "#FDF1F4",
                "icon_fg": "#B54863",
                "close": "#7B4552",
                "icon": "×",
            },
            "錯誤": {
                "bg": "#F9E1E6",
                "border": "#E59AA9",
                "text": "#5B2732",
                "icon_bg": "#FDF1F4",
                "icon_fg": "#B54863",
                "close": "#7B4552",
                "icon": "×",
            },
        }
        palette = palette_map.get(notification_type, palette_map["錯誤"])

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {palette["bg"]};
                border: 1px solid {palette["border"]};
                border-radius: 10px;
                color: {palette["text"]};
            }}
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 6, 10, 6)
        main_layout.setSpacing(10)

        icon_label = QLabel(palette["icon"])
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(20, 20)
        icon_label.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {palette['icon_fg']}; "
            f"background-color: {palette['icon_bg']}; border: 1px solid {palette['border']}; "
            "border-radius: 10px;"
        )
        main_layout.addWidget(icon_label)

        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.RichText)
        message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        message_label.setStyleSheet(
            "font-size: 12px; color: #F4F7FB; background: transparent; border: none;"
        )
        main_layout.addWidget(message_label)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(18, 18)
        close_btn.setStyleSheet(
            f"QPushButton {{ border: none; font-size: 13px; font-weight: 700; "
            f"color: {palette['close']}; background-color: transparent; }}"
            f"QPushButton:hover {{ color: {palette['text']}; }}"
        )
        main_layout.addWidget(close_btn)

        self.close_button = close_btn

class MainWindow(QMainWindow, Ui_MainWindow):
    # 主函式
    def __init__(self, username, user_db_manager, task_db_manager):
        super().__init__()

        # *** 新增：儲存使用者資訊給漢堡選單 ***
        self.current_username_id = username
        # *** 新增這兩行：必須在 __init__ 裡設定初始值避免滑鼠事件報錯 ***
        
        self._drag_position = QPoint()
        self.dragging = False
        # 隱藏標題列
        self.setWindowFlag(Qt.FramelessWindowHint)

        self.setupUi(self) #這會設定 self.centralWidget 為您的原有內容容器。
        # 啟動時先決定本次執行要使用哪個場域，
        # 之後主地圖、小地圖、Logo 都從同一份設定讀取。
        # self.site_profile = 最終決定目前跑 company 還是 hospital 的值
        # self.site_config = 對應的 site/<profile>.json 內容
        # self.site_assets = 本次先抽出的地圖/Logo 資源包
        # self.site_calibration = 本次抽出的 image_pts / world_pts 校正資料
        self.site_profile = DEFAULT_SITE_PROFILE
        self.site_config = load_site_config(self.site_profile)
        self.site_assets = self.site_config["assets"]
        self.site_calibration = self.site_config["calibration"]
        # site_runtime_maps = 新舊架構之間的過渡層。
        # UI / TaskThread 仍吃熟悉的 map，但來源已經優先改成 site config。
        self.site_runtime_maps = build_site_runtime_maps(self.site_config)
        #########################################客製化title：穩健 ToolBar 方案########################################
        # 1. 創建客製化標題列的 QFrame
        #    這個 QFrame 包含了您設計的標題文字和最小化/最大化/關閉按鈕。
        self.titleBarFrame = self._create_title_bar_frame()
        self.titleBarFrame.setObjectName("CustomTitleFrame")
        self.titleBarFrame.setFixedHeight(40)
        
        # 2. 創建 QToolBar 作為客製化標題列的容器
        #    QToolBar 是 QMainWindow 專門用於功能區的標準元件，不會干擾 centralWidget。
        self.titleBarToolBar = QToolBar("CustomTitleBar")
        self.titleBarToolBar.setObjectName("CustomTitleBar")
        
        # 3. 設置 ToolBar 屬性 (關鍵設定，使其固定不動)
        self.titleBarToolBar.setMovable(False)          # 不允許使用者拖動 ToolBar
        self.titleBarToolBar.setFloatable(False)        # 不允許 ToolBar 浮動
        self.titleBarToolBar.setAllowedAreas(Qt.TopToolBarArea) # 只能在頂部
        
        # 4. 將客製化 QFrame 包裝成 QWidget 並加入 ToolBar
        #    我們需要這個 QWidget 來將整個 QFrame 放入 ToolBar 中。
        title_bar_widget = QWidget()
        title_bar_layout = QHBoxLayout(title_bar_widget)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.addWidget(self.titleBarFrame)
        
        self.titleBarToolBar.addWidget(title_bar_widget)
        
        # 5. 將 ToolBar 添加到 QMainWindow 的頂部
        #    這一步是將標題列疊加在 centralWidget 上方，但又不影響其內容。
        self.addToolBar(Qt.TopToolBarArea, self.titleBarToolBar)
        
        # 6. 應用 QSS 樣式
        self.apply_qss_styles()

        # ===== thread check api 狀態控制 =====
        self.api_error = False     # ⭐ 是否目前是 API 錯誤狀態（避免重複寫 DB）
        self.workers = []          # ⭐ 存所有 thread（避免被 Python 回收 → crash）
        self.polling_busy = False  # ⭐ 防止 polling 還沒結束又啟動
        self.active_workers = 0    # ⭐ 記錄目前有幾個 thread 在跑（這版是1但保險留著）
        self.last_mission_text = None
        self.current_mission_text = ""
        # Make room for a two-line status area: Status + Mission.
        self.label_Status_1.setMinimumWidth(520)
        self.label_Status_1.setMaximumWidth(900)
        self.label_Status_1.setMinimumHeight(68)
        self.label_Status_1.setMaximumHeight(80)
        self.label_Status_1.setWordWrap(True)
        self.label_Status_1.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._adjust_status_area_layout()

        ########################################儲存 Manager 實例，以便後續的方法可以使用################################
        self.user_db_manager = user_db_manager
        self.task_db_manager = task_db_manager # <-- 這是您需要的！
        
        ########################################QTableWidget右下待執行任務表格########################################
        #右邊待執行任務表格 
        self.tableWidget_pending_mission_list.setHorizontalHeaderLabels([" ","序", "流水號", "起始點", "目的地", "任務", "狀態","操作"])
        # 隱藏左側的垂直表頭
        self.tableWidget_pending_mission_list.verticalHeader().setVisible(False)
        # 禁用右上角的角落區塊
        self.tableWidget_pending_mission_list.setCornerButtonEnabled(False)
        # 在表格中添加一行
        self.tableWidget_pending_mission_list.setItem(0, 1, QTableWidgetItem("1"))
        self.tableWidget_pending_mission_list.setItem(0, 2, QTableWidgetItem("7123"))
        self.tableWidget_pending_mission_list.setItem(0, 3, QTableWidgetItem("減菌室-1"))
        self.tableWidget_pending_mission_list.setItem(0, 4, QTableWidgetItem("手術室04-A"))
        self.tableWidget_pending_mission_list.setItem(0, 5, QTableWidgetItem("拉車至指定定點"))
        self.tableWidget_pending_mission_list.setItem(0, 6, QTableWidgetItem("執行中"))
        self.tableWidget_pending_mission_list.setItem(0, 7, QTableWidgetItem(" "))
        # 呼叫我們剛剛建立的函式來置中所有文字
        self.set_table_items_center(self.tableWidget_pending_mission_list)

        # 設定列寬度的自適應策略
        self.header = self.tableWidget_pending_mission_list.horizontalHeader()
        self._configure_pending_mission_table()
        
        # 設置表格行高
        self.tableWidget_pending_mission_list.setWordWrap(True)
        self.tableWidget_pending_mission_list.resizeRowsToContents()

        ###########################################初始化所有狀態旗標#################################################
        #is_running，is_no_mission是TaskThread使用自己的
        #是否按下開始載運 1010
        # self.is_running=True
        #是否已無任務 1010
        # self.is_no_mission=False

        #是否AMR idle等待 1010
        self.is_AMR_idle=True
        #是否低電輛需充電 1010
        self.is_low_battery=False
        #是否已經通知低電量 1010
        self.is_low_battery_notified = False
        self.notified_task_results = set()
        self.mir_status_poll_disconnected = False
        #是否連線
        self.is_online = True
        self.is_test_mode = True
        

        # 將場域設定轉出的 runtime map 掛到 self。
        # 後面如果還看到 self.MIR_LOCATION_MAP / self.ROOM_ID_MAP，
        # 代表那段舊流程已經開始吃 site config 了。
        self.MIR_LOCATION_MAP = self.site_runtime_maps["mir_location_map"]
        self.MIR_MISSION_GROUP_MAP = self.site_runtime_maps["mir_mission_group_map"]
        self.CHARGING_STATION_NAME = self.site_runtime_maps["charging_station_name"]
        self.USER_LOCATION_MAP = self.site_runtime_maps["user_location_map"]
        self.USER_MISSION_GROUP_MAP = self.site_runtime_maps["user_mission_group_map"]
        self.ROOM_ID_MAP = self.site_runtime_maps["room_id_map"]
        self.LOCATION_TO_MARKER = self.site_runtime_maps["location_to_marker"]
        self.REQUIRED_MISSION_CODES = self.site_runtime_maps["required_mission_codes"]

        # 初始化 MiR 函數
        # 將您已經導入的 functions 模組，作為一個屬性(attribute)賦值給 MainWindow 實例 (self)
        self.functions = functions

        # 初始化任務執行緒
        self.task_thread = TaskThread(self)
        self.task_thread.log_message.connect(self.update_log_ui)
        self.task_thread.finished_task.connect(self.handle_task_completion)


        # 在主窗口 (通常是 MainWindow 類別) 中，找到並取得由 Qt Designer 創建的特定元件的物件實例
        self.comboBox_start = self.findChild(QComboBox, 'cmb_location2')
        self.comboBox_destination = self.findChild(QComboBox, 'cmb_location')

        # 🥇 僅創建一次 SelectedMap 實例
        # 右上 MAP 彈窗使用目前場域的小地圖資源，
        # 之後只要切 site_profile 就能換圖，不必再改程式。
        selected_map_path = resolve_runtime_path(self.site_assets.get("selected_map"))
        self.map_dialog = SelectedMap(selected_map_path) 
        # 隱藏地圖選擇對話框
        self.map_dialog.hide()

        # 連接按鈕到開啟函數，並傳遞目標
        self.btn_SelectStart.clicked.connect(lambda: self.open_map_selector(self.comboBox_start))
        self.btn_SelectDestination.clicked.connect(lambda: self.open_map_selector(self.comboBox_destination))
      

        # 載入已儲存的IP，並在初始化時顯示此IP
        functions.MIR_IP = functions.load_ip()
        IP = functions.MIR_IP
        if IP.startswith("http://"):
            IP=IP[7:]
        self.lineEdit_IP.setText(IP)
        self.heartbeat_display_count = functions.load_heartbeat_display_count()
        self.apply_heartbeat_label_visibility()

        # 暫時隱藏frame 0923
        self.frame_temp.hide()

        # polling timer
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_room_status)
        self.poll_timer.start(5000)  # ⭐ 建議 3~5 秒（避免打爆 API）

        if self.is_online:
            # ----------------------------------------
            # 1. 快速定時器 (Fast Polling) - 例如 300ms
            # 用於即時性要求高的資訊：位置、即時狀態
            # ----------------------------------------
            self.fast_timer = QTimer(self)
            # 連接需要快速更新的函式
            self.fast_timer.timeout.connect(self.query_mir_info)
            self.fast_timer.timeout.connect(self.poll_mir_position)
            # 啟動快速定時器
            self.fast_timer.start(0.3 * 1000) # 秒

            # ----------------------------------------
            # 2. 慢速定時器 (Slow Polling) - 例如 10 秒
            # 用於即時性要求低的資訊：電量、歷史資料、房間心跳
            # ----------------------------------------
            self.slow_timer = QTimer(self)
            # 連接需要慢速更新的函式
            self.slow_timer.timeout.connect(self.query_battery_status)
            self.slow_timer.timeout.connect(self.update_room_heartbeat_status)  # 房間心跳監控
            
            # self.slow_timer.timeout.connect(self.monitor_or_mir_api_status)
            # 啟動慢速定時器
            self.slow_timer.start(10 * 1000) # 10 秒

            # ----------------------------------------
            # 3. 設置 QTimer 自動刷新清單 (核心功能) ---
            # ----------------------------------------
            self.refresh_timer = QTimer(self)
            # 定時觸發 refresh_task_list 函式
            self.refresh_timer.timeout.connect(self.refresh_task_list)
            self.refresh_timer.timeout.connect(self.query_mir_status_db)
            # 每 2000 毫秒 (2 秒) 刷新一次
            self.refresh_timer.start(2000) 

            #----------------------------------------
            # 4. 設置 QTimer 自動新增循環任務 for test ---
            #----------------------------------------   
            self.loop_test_timer = QTimer(self) 
            # 定時觸發 loop_test 函式
            self.loop_test_timer.timeout.connect(self.add_test_batch_missions)
            # 每 210000 毫秒 (4 min) 刷新一次
            # self.loop_test_timer.start(240*1000) 
            
            # 第一次手動載入清單
            self.refresh_task_list()
            # ⭐ 主控啟動時載入地圖，同步一次 DB（單次初始化同步）
            self.load_map_positions()
            #cmb載入任務名字
            # self.load_mission_positions()
            self.load_mission_groups_positions()


        
        # 讀圖
        # 左側主地圖與小地圖共用同一組場域資源設定。
        # 這裡就是主畫面「依設定換地圖」的主要入口。
        main_map_path = resolve_runtime_path(self.site_assets.get("main_map"))
        self.original_pixmap = QPixmap(main_map_path)
        if self.original_pixmap.isNull():
            print(f"主地圖載入失敗: {main_map_path}")
        else:
            self.label_map_1.setPixmap(self.original_pixmap)
            self.label_map_1.resize(self.original_pixmap.size())
            print(self.label_map_1.width())
            print(self.label_map_1.height())
            # 印出原始圖片尺寸（寬 x 高）
            width = self.original_pixmap.width()
            height = self.original_pixmap.height()
            print(f"原始圖片大小：{width} x {height}")
        
        # 假設 self.label_map_1 是地圖
        # 新增一個用於繪圖的 Label，大小和位置與地圖相同
        self.label_car_overlay = QLabel(self.label_map_1.parent()) # 讓它與地圖有相同的父容器
        self.label_car_overlay.setGeometry(self.label_map_1.geometry())
        self.label_car_overlay.setStyleSheet("background-color: transparent;") # 設置背景透明
        self.label_car_overlay.raise_()

        # 【關鍵修正】設置窗口標誌，使其忽略滑鼠事件
        # Qt.WA_TransparentForMouseEvents 是用於 QWidget 的屬性，但 QLabel 繼承自 QWidget
        self.label_car_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.current_mir_state_id = None
        self.map_overlay_frames = {}
        self.map_overlay_content_widgets = {}
        self.map_overlay_collapsed = {
            "map_overlay_top_right": True,
            "map_overlay_bottom_right": True,
            "map_overlay_bottom_left": True,
        }
        self.map_overlay_summary_widgets = {}
        self.map_overlay_toggle_buttons = {}
        self._setup_main_map_overlay_containers()
        self._apply_main_map_overlay_theme()
        self._setup_overlay_edge_cards()
        self._refresh_overlay_card_summaries()
                
        # # 讀logo 暫時沒用到
        # self.icon_pixmap = QPixmap("./picture/aceicon1.png")
        # if self.icon_pixmap.isNull():
        #     print("圖片讀取失敗！")
        # else:
        #     self.label_logo.setPixmap(self.icon_pixmap)

        # Flag
        self.clicked_enabled = False
        self.sent_robot_to_in_progress = False
        self.last_click_overlay_pos = None
        self.last_robot_world_pos = None
        self.robot_glow_phase = 0
        self._apply_main_map_shell_layout()

        # image_pts / world_pts 已從 main.py 硬編碼抽離到 site config。
        # 這裡只負責讀取目前場域的校正點，不改動後續 affine 計算邏輯。
        self.image_pts = np.array(
            self.site_calibration["image_pts"],
            dtype=np.float32,
        )
        self.world_pts = np.array(
            self.site_calibration["world_pts"],
            dtype=np.float32,
        )

        # 建立仿射轉換矩陣
        self.affine_matrix = self.compute_affine_transform()
        # self.draw_car_position(-5.397, 7.455) 
        # self.poll_mir_position()

        #點擊按鈕觸發任務
        self.btn_StartMission.clicked.connect(self.on_map_location_clicked)
        self.btn_StartMission2.clicked.connect(self.on_start_mission_clicked)
        self.btn_StartRelativeMove.clicked.connect(self.on_relative_move_clicked)
        self.btn_UpdateInfo.clicked.connect(self.on_update_info_clicked)
        self.btn_ChargeMission.clicked.connect(self.on_start_chargestation_clicked)
        # self.btn_GetPM.clicked.connect(self.on_get_pending_mssion_clicked) 取得等待中任務 暫時停用
        self.btn_GetPM.hide() # 暫時隱藏
        self.btn_StopMission1.clicked.connect(self.on_stop_mission_clicked)
        self.btn_StopMission2.clicked.connect(self.on_stop_mission_clicked)
        self.btn_Reset.clicked.connect(self.on_reset_status_clicked)
        self.btn_save_ip.clicked.connect(self.on_save_ip_clicked)
        self.btn_IO_Up.clicked.connect(self.on_up_io_clicked)
        self.btn_IO_down.clicked.connect(self.on_down_io_clicked)
        self.btn_SentRobotTo.setEnabled(False)
        self.btn_SentRobotTo.clicked.connect(self.on_sent_robot_to_clicked)
        self.btn_Add_New_Mission.clicked.connect(self.on_add_new_mission_clicked)
        self.btn_Emergency_Cut_Line.clicked.connect(self.on_emergency_cut_line_clicked) #btn_Emergency_Cut_Line
        # self.setFixedSize(1440,768)
        self.setFixedSize(1920,1080)

        #勾選觸發任務
        self.chb_map.stateChanged.connect(self.toggle_click_mode_map)

        # 設置 QListWidget 的樣式表
        self.listWidget_msg.setStyleSheet("""
            QListWidget {
                border: 2px solid #2C3E50;
                padding: 0px; 
                background-color: #ffffff; /* 如果表格背景是深色，這裡也設為深色或透明 */
            }
            QListWidget::item {
                margin: 1px; /* 移除項目之間的預設邊距 */
                padding: 0px; /* 移除項目本身的內邊距 */
            }
        """)
        self._apply_main_map_overlay_theme()
        self._refresh_overlay_card_summaries()

        # self.setStyleSheet(tooltip_reset_style)
        # self.add_notification_item("錯誤", "9999 任務失敗：目標點座標錯誤。")
    
    # ----------------------------------------------------
    # ⭐ 客製化titlebar-標題列輔助方法 ⭐
    # ----------------------------------------------------
    def _raise_map_foreground_widgets(self):
        if not hasattr(self, "frame_map") or not hasattr(self, "label_car_overlay"):
            return

        for child in self.frame_map.children():
            if not isinstance(child, QWidget):
                continue
            if child in {self.label_map_1, self.label_car_overlay}:
                continue
            child.raise_()

    def _create_map_overlay_frame(self, object_name):
        overlay = QFrame(self.frame_map)
        overlay.setObjectName(object_name)
        overlay.setFrameShape(QFrame.StyledPanel)
        overlay.setFrameShadow(QFrame.Raised)
        overlay.setAttribute(Qt.WA_StyledBackground, True)
        overlay.setStyleSheet(self._build_overlay_frame_qss(object_name))
        overlay.show()
        return overlay

    def _build_overlay_button_qss(self, variant="secondary", icon_only=False):
        if variant == "primary":
            bg_color = "#1790FF"
            hover_color = "#36A1FF"
            border_color = "#1790FF"
            text_color = "#FFFFFF"
        elif variant == "danger":
            bg_color = "rgba(184, 49, 75, 0.18)"
            hover_color = "rgba(208, 68, 96, 0.28)"
            border_color = "rgba(255, 132, 157, 0.56)"
            text_color = "#FFD8DE"
        elif variant == "ghost":
            bg_color = "rgba(255, 255, 255, 0.06)"
            hover_color = "rgba(255, 255, 255, 0.12)"
            border_color = "rgba(149, 190, 225, 0.28)"
            text_color = "#EAF2FD"
        else:
            bg_color = "rgba(23, 144, 255, 0.12)"
            hover_color = "rgba(23, 144, 255, 0.22)"
            border_color = "rgba(95, 178, 255, 0.42)"
            text_color = "#EAF4FF"

        radius = 11 if not icon_only else 10
        padding = "0px" if icon_only else "0 12px"
        font_size = "13px" if not icon_only else "12px"

        return f"""
        QPushButton {{
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: {radius}px;
            padding: {padding};
            font-size: {font_size};
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:disabled {{
            background-color: rgba(255, 255, 255, 0.05);
            color: rgba(234, 244, 255, 0.36);
            border: 1px solid rgba(149, 190, 225, 0.16);
        }}
        """

    def _build_overlay_input_qss(self, title=False):
        if title:
            return """
            QLineEdit {
                color: #F2F7FF;
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: 700;
                padding: 0px;
            }
            """

        return """
        QLineEdit {
            color: #EAF4FF;
            background-color: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(150, 190, 225, 0.22);
            border-radius: 10px;
            font-size: 13px;
            padding: 0 12px;
        }
        """

    def _build_overlay_combo_qss(self):
        return """
        QComboBox {
            color: #EAF4FF;
            background-color: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(150, 190, 225, 0.22);
            border-radius: 10px;
            font-size: 13px;
            padding: 0 12px;
        }
        QComboBox::drop-down {
            border: none;
            width: 24px;
            background: transparent;
        }
        QComboBox QAbstractItemView {
            background-color: #0B1828;
            color: #EAF4FF;
            border: 1px solid rgba(95, 178, 255, 0.30);
            selection-background-color: rgba(23, 144, 255, 0.28);
        }
        """

    def _build_compact_status_label_qss(self, color):
        return (
            f"color: {color}; font-size: 18px; font-weight: 700; "
            "background-color: transparent;"
        )

    def _heartbeat_label_qss(self, text_color, border_color):
        return (
            "color: {text_color}; font-size: 11px; font-weight: 700; "
            "background-color: rgba(255, 255, 255, 0.92); "
            "border: 1px solid {border_color}; border-radius: 8px; padding: 2px 4px;"
        ).format(text_color=text_color, border_color=border_color)

    def _set_battery_progress_style(self, color):
        self.progressBar_battery.setStyleSheet(f"""
        QProgressBar {{
            color: #EAF4FF;
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(150, 190, 225, 0.24);
            border-radius: 9px;
            text-align: center;
            font-size: 11px;
            font-weight: 700;
        }}
        QProgressBar::chunk {{
            background-color: {color};
            border-radius: 8px;
        }}
        """)

    def _apply_main_map_overlay_theme(self):
        self.label_Status_1.setMinimumWidth(280)
        self.label_Status_1.setMaximumWidth(320)
        self.label_Status_1.setMinimumHeight(44)
        self.label_Status_1.setMaximumHeight(56)
        self.label_Status_1.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_Status_1.setStyleSheet(self._build_compact_status_label_qss("#7CFFB2"))

        self.lineEdit_MiR250_A.setStyleSheet(
            "color: #F2F7FF; font-size: 24px; font-weight: 700; background: transparent;"
        )
        self.lineEdit_MiR250_A.setMinimumSize(QSize(128, 40))
        self.lineEdit_MiR250_A.setMaximumSize(QSize(140, 40))

        self.progressBar_battery.setMinimumSize(QSize(88, 20))
        self.progressBar_battery.setMaximumSize(QSize(96, 20))
        self._set_battery_progress_style("#3DDC97")

        for button in (self.btn_ChargeMission, self.btn_Reset):
            button.setMinimumSize(QSize(88, 32))
            button.setMaximumSize(QSize(96, 32))
            button.setStyleSheet(self._build_overlay_button_qss("danger"))

        self.lineEdit_IP.setMinimumSize(QSize(126, 34))
        self.lineEdit_IP.setMaximumSize(QSize(150, 34))
        self.lineEdit_IP.setStyleSheet(self._build_overlay_input_qss())
        self.btn_save_ip.setMinimumSize(QSize(34, 34))
        self.btn_save_ip.setMaximumSize(QSize(34, 34))
        self.btn_save_ip.setStyleSheet(self._build_overlay_button_qss("ghost", icon_only=True))

        for label in (self.label_6, self.label, self.label_3):
            label.setMinimumSize(QSize(90, 20))
            label.setMaximumSize(QSize(110, 20))
            label.setStyleSheet("color: rgba(226, 236, 248, 0.78); font-size: 13px; font-weight: 600;")

        for combo in (self.cmb_location2, self.cmb_location, self.cmb_mission):
            combo.setMinimumHeight(38)
            combo.setMaximumHeight(38)
            combo.setMinimumWidth(0)
            combo.setMaximumWidth(16777215)
            combo.setStyleSheet(self._build_overlay_combo_qss())

        for button in (self.btn_SelectStart, self.btn_SelectDestination):
            button.setMinimumSize(QSize(64, 32))
            button.setMaximumSize(QSize(64, 32))
            button.setStyleSheet(self._build_overlay_button_qss("ghost"))

        self.btn_Emergency_Cut_Line.setStyleSheet(self._build_overlay_button_qss("danger"))
        self.btn_Add_New_Mission.setStyleSheet(self._build_overlay_button_qss("primary"))

        self.lineEdit_PendingMission.setStyleSheet(self._build_overlay_input_qss(title=True))
        self.lineEdit_PendingMission.setMinimumSize(QSize(180, 32))
        self.lineEdit_PendingMission.setMaximumSize(QSize(220, 32))

        for button in (self.btn_StartMission, self.btn_StopMission1):
            button.setMinimumSize(QSize(34, 34))
            button.setMaximumSize(QSize(34, 34))
        self.btn_StartMission.setStyleSheet(self._build_overlay_button_qss("primary", icon_only=True))
        self.btn_StopMission1.setStyleSheet(self._build_overlay_button_qss("danger", icon_only=True))

        self.frame_pending_mission_list.setStyleSheet("border: none; background: transparent;")
        self.tableWidget_pending_mission_list.setStyleSheet("""
        QTableWidget {
            background-color: rgba(7, 16, 27, 0.76);
            alternate-background-color: rgba(255, 255, 255, 0.03);
            color: #EAF4FF;
            border: 1px solid rgba(150, 190, 225, 0.18);
            border-radius: 12px;
            gridline-color: rgba(150, 190, 225, 0.10);
            font-size: 11px;
        }
        QTableWidget::item {
            padding: 4px;
            border-bottom: 1px solid rgba(150, 190, 225, 0.08);
        }
        QHeaderView::section {
            background-color: rgba(255, 255, 255, 0.06);
            color: rgba(234, 244, 255, 0.82);
            padding: 4px;
            border: none;
            border-bottom: 1px solid rgba(150, 190, 225, 0.16);
            font-size: 11px;
            font-weight: 700;
        }
        """)
        self.tableWidget_pending_mission_list.setAlternatingRowColors(True)
        self.tableWidget_pending_mission_list.verticalHeader().setDefaultSectionSize(42)
        self.tableWidget_pending_mission_list.horizontalHeader().setDefaultSectionSize(68)
        self.tableWidget_pending_mission_list.horizontalHeader().setMinimumSectionSize(22)

        self.lineEdit_MessageAnnounce.setStyleSheet(
            "color: rgba(226, 236, 248, 0.78); font-size: 12px; font-weight: 700; background: transparent;"
        )
        self.lineEdit_MessageAnnounce.setMinimumSize(QSize(100, 20))
        self.lineEdit_MessageAnnounce.setMaximumSize(QSize(120, 20))

        for layout in (self.horizontalLayout_4, self.horizontalLayout_8):
            layout.setSpacing(6)

        for dot, color in (
            (self.lineEdit_MessageAnnounce_6, "#42BE57"),
            (self.lineEdit_MessageAnnounce_7, "#FF9D2F"),
        ):
            dot.setMinimumSize(QSize(10, 10))
            dot.setMaximumSize(QSize(10, 10))
            dot.setAlignment(Qt.AlignCenter)
            dot.setStyleSheet(
                f"background-color: {color}; color: transparent; border-radius: 5px; border: none;"
            )

        for label in (self.lineEdit_current_tasks, self.lineEdit_pending_tasks):
            label.setMinimumHeight(20)
            label.setMaximumHeight(20)
            label.setStyleSheet(
                "color: rgba(226, 236, 248, 0.78); font-size: 12px; font-weight: 600; background: transparent;"
            )

        self.chb_map.setMinimumSize(QSize(120, 30))
        self.chb_map.setMaximumSize(QSize(126, 30))
        self.chb_map.setStyleSheet("""
        QCheckBox {
            color: #EAF4FF;
            background-color: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(150, 190, 225, 0.22);
            border-radius: 10px;
            padding: 0 10px;
            font-size: 12px;
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 14px;
            height: 14px;
            background-color: transparent;
            border: 1px solid rgba(234, 244, 255, 0.72);
            border-radius: 4px;
        }
        QCheckBox::indicator:checked {
            background-color: #1790FF;
            image: url(:/icons/icons/check.svg);
        }
        """)

        self.btn_SentRobotTo.setMinimumSize(QSize(34, 30))
        self.btn_SentRobotTo.setMaximumSize(QSize(34, 30))
        self.btn_SentRobotTo.setStyleSheet(self._build_overlay_button_qss("primary", icon_only=True))

        for index in range(1, 14):
            label = getattr(self, f"lbl_OR_Heartbeat_{index}")
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignCenter)
            label.setMinimumSize(QSize(56, 34))
            label.setMaximumSize(QSize(60, 34))
            label.setStyleSheet(self._heartbeat_label_qss("#5A6573", "#B7C7D9"))

        self.listWidget_msg.setStyleSheet("""
        QListWidget {
            border: 1px solid rgba(150, 190, 225, 0.20);
            border-radius: 12px;
            padding: 0px;
            background-color: rgba(7, 16, 27, 0.86);
        }
        QListWidget::item {
            margin: 2px;
            padding: 0px;
        }
        """)
        self.listWidget_msg.setSpacing(2)

    def _build_overlay_summary_title_qss(self):
        return (
            "color: #F3F8FF; background: transparent; "
            "font-size: 15px; font-weight: 700;"
        )

    def _build_overlay_summary_chip_qss(self, variant="neutral"):
        if variant == "success":
            background = "rgba(61, 220, 151, 0.20)"
            border = "rgba(124, 255, 178, 0.48)"
            color = "#D8FFE7"
        elif variant == "warning":
            background = "rgba(255, 157, 47, 0.18)"
            border = "rgba(255, 191, 116, 0.42)"
            color = "#FFEBD2"
        elif variant == "danger":
            background = "rgba(184, 49, 75, 0.18)"
            border = "rgba(255, 132, 157, 0.42)"
            color = "#FFD8DE"
        else:
            background = "rgba(23, 144, 255, 0.18)"
            border = "rgba(95, 178, 255, 0.42)"
            color = "#EAF4FF"

        return (
            "background-color: {background}; color: {color}; "
            "border: 1px solid {border}; border-radius: 11px; "
            "padding: 0 10px; font-size: 12px; font-weight: 700;"
        ).format(background=background, color=color, border=border)

    def _create_overlay_summary_label(self, parent, object_name, chip=False, variant="neutral"):
        label = QLabel(parent)
        label.setObjectName(object_name)
        label.setAlignment((Qt.AlignCenter if chip else Qt.AlignLeft) | Qt.AlignVCenter)
        label.setStyleSheet(
            self._build_overlay_summary_chip_qss(variant)
            if chip
            else self._build_overlay_summary_title_qss()
        )
        label.hide()
        return label

    def _build_overlay_frame_qss(self, object_name, collapsed=False):
        background_alpha = 232 if collapsed else 218
        border_alpha = 138 if collapsed else 118
        radius = 18 if collapsed else 16
        return f"""
            QFrame#{object_name} {{
                background-color: rgba(7, 15, 26, {background_alpha});
                border: 1px solid rgba(138, 182, 219, {border_alpha});
                border-radius: {radius}px;
            }}
        """

    def _set_overlay_frame_style(self, object_name):
        overlay = self.map_overlay_frames.get(object_name)
        if overlay is None:
            return
        overlay.setStyleSheet(
            self._build_overlay_frame_qss(
                object_name,
                self.map_overlay_collapsed.get(object_name, False),
            )
        )

    def _setup_overlay_edge_cards(self):
        if not self.map_overlay_frames:
            return

        for object_name, overlay in self.map_overlay_frames.items():
            toggle_button = QPushButton(overlay)
            toggle_button.setObjectName(f"{object_name}_toggle")
            toggle_button.setCursor(Qt.PointingHandCursor)
            toggle_button.clicked.connect(
                lambda _checked=False, key=object_name: self._toggle_map_overlay_collapsed(key)
            )
            toggle_button.show()
            self.map_overlay_toggle_buttons[object_name] = toggle_button

            summary_widgets = {}
            if object_name == "map_overlay_top_right":
                summary_widgets["title"] = self._create_overlay_summary_label(overlay, f"{object_name}_title")
                summary_widgets["status"] = self._create_overlay_summary_label(
                    overlay, f"{object_name}_status", chip=True, variant="success"
                )
                summary_widgets["battery"] = self._create_overlay_summary_label(
                    overlay, f"{object_name}_battery", chip=True
                )
                summary_widgets["tasks"] = self._create_overlay_summary_label(
                    overlay, f"{object_name}_tasks", chip=True
                )
            elif object_name == "map_overlay_bottom_right":
                summary_widgets["title"] = self._create_overlay_summary_label(overlay, f"{object_name}_title")
                summary_widgets["count"] = self._create_overlay_summary_label(
                    overlay, f"{object_name}_count", chip=True, variant="warning"
                )
                summary_widgets["active"] = self._create_overlay_summary_label(
                    overlay, f"{object_name}_active", chip=True
                )
            elif object_name == "map_overlay_bottom_left":
                summary_widgets["current"] = self._create_overlay_summary_label(
                    overlay, f"{object_name}_current", chip=True, variant="success"
                )
                summary_widgets["pending"] = self._create_overlay_summary_label(
                    overlay, f"{object_name}_pending", chip=True, variant="warning"
                )
                summary_widgets["notice"] = self._create_overlay_summary_label(
                    overlay, f"{object_name}_notice", chip=True
                )

            self.map_overlay_summary_widgets[object_name] = summary_widgets
            self._set_overlay_frame_style(object_name)
            self._apply_overlay_card_state(object_name)

    def _toggle_map_overlay_collapsed(self, object_name):
        self.map_overlay_collapsed[object_name] = not self.map_overlay_collapsed.get(object_name, False)
        self._apply_overlay_card_state(object_name)
        self._apply_main_map_overlay_panel_layouts()
        self._refresh_overlay_card_summaries()

    def _raise_overlay_card_chrome(self, object_name):
        for widget in self.map_overlay_summary_widgets.get(object_name, {}).values():
            widget.raise_()

        toggle_button = self.map_overlay_toggle_buttons.get(object_name)
        if toggle_button is not None:
            toggle_button.raise_()

    def _apply_overlay_card_state(self, object_name):
        overlay = self.map_overlay_frames.get(object_name)
        if overlay is None:
            return

        collapsed = self.map_overlay_collapsed.get(object_name, False)

        for widget in self.map_overlay_content_widgets.get(object_name, []):
            widget.setVisible(not collapsed)

        for widget in self.map_overlay_summary_widgets.get(object_name, {}).values():
            widget.setVisible(collapsed)

        toggle_button = self.map_overlay_toggle_buttons.get(object_name)
        if toggle_button is not None:
            toggle_button.setText("+" if collapsed else "-")
            toggle_button.setToolTip("Expand" if collapsed else "Collapse")
            toggle_button.setStyleSheet(self._build_overlay_button_qss("ghost", icon_only=True))

        self._set_overlay_frame_style(object_name)
        self._raise_overlay_card_chrome(object_name)

    def _get_task_status_counts(self):
        if not hasattr(self, "tableWidget_pending_mission_list"):
            return {"total": 0, "pending": 0, "executing": 0}

        total = self.tableWidget_pending_mission_list.rowCount()
        pending = 0
        executing = 0
        for row in range(total):
            item = self.tableWidget_pending_mission_list.item(row, 6)
            status_text = item.text().strip() if item else ""
            if status_text == "Executing":
                executing += 1
            elif status_text == "Pending":
                pending += 1

        return {"total": total, "pending": pending, "executing": executing}

    def _get_robot_state_summary(self):
        status_map = {
            1: ("Starting", "warning"),
            2: ("ShuttingDown", "danger"),
            3: ("Ready", "success"),
            4: ("Pause", "warning"),
            5: ("Executing", "success"),
            6: ("Aborted", "warning"),
            7: ("GoalReached", "success"),
            8: ("Docked", "success"),
            9: ("Docking", "success"),
            10: ("EmergencyStop", "danger"),
            11: ("ManualControl", "danger"),
            12: ("Error", "danger"),
        }
        return status_map.get(getattr(self, "current_mir_state_id", None), ("Unknown", "neutral"))

    def _refresh_overlay_card_summaries(self):
        if not getattr(self, "map_overlay_summary_widgets", None):
            return

        task_counts = self._get_task_status_counts()
        notification_count = self.listWidget_msg.count() if hasattr(self, "listWidget_msg") else 0

        top_right = self.map_overlay_summary_widgets.get("map_overlay_top_right", {})
        if top_right:
            robot_name = self.lineEdit_MiR250_A.text().strip() if hasattr(self, "lineEdit_MiR250_A") else ""
            status_text, status_variant = self._get_robot_state_summary()
            battery_value = self.progressBar_battery.value() if hasattr(self, "progressBar_battery") else 0

            top_right["title"].setText(robot_name or "MiR250-A")
            top_right["status"].setText(status_text)
            top_right["status"].setStyleSheet(self._build_overlay_summary_chip_qss(status_variant))
            top_right["battery"].setText(f"{battery_value}%")
            top_right["tasks"].setText(f"Pending {task_counts['pending']}")

        bottom_right = self.map_overlay_summary_widgets.get("map_overlay_bottom_right", {})
        if bottom_right:
            bottom_right["title"].setText("Tasks")
            bottom_right["count"].setText(f"List {task_counts['total']}")
            bottom_right["active"].setText(f"Run {task_counts['executing']}")

        bottom_left = self.map_overlay_summary_widgets.get("map_overlay_bottom_left", {})
        if bottom_left:
            bottom_left["current"].setText(f"Now {task_counts['executing']}")
            bottom_left["pending"].setText(f"Wait {task_counts['pending']}")
            bottom_left["notice"].setText(f"Notice {notification_count}")

    def _build_main_map_overlay_specs(self):
        top_right_widgets = [
            self.horizontalLayoutWidget_6,
            self.horizontalLayoutWidget_5,
            self.horizontalLayoutWidget_4,
            self.btn_SelectStart,
            self.horizontalLayoutWidget_2,
            self.btn_SelectDestination,
            self.horizontalLayoutWidget,
            self.btn_Emergency_Cut_Line,
            self.btn_Add_New_Mission,
        ]
        bottom_right_widgets = [
            self.lineEdit_PendingMission,
            self.btn_StartMission,
            self.btn_StopMission1,
            self.frame_pending_mission_list,
        ]
        bottom_left_widgets = [
            self.horizontalLayoutWidget_7,
            self.horizontalLayoutWidget_8,
            self.chb_map,
            self.btn_SentRobotTo,
            *(getattr(self, f"lbl_OR_Heartbeat_{index}") for index in range(1, 14)),
            self.lineEdit_MessageAnnounce,
            self.verticalLayoutWidget,
        ]

        return [
            ("map_overlay_top_right", top_right_widgets, (20, 18, 20, 24)),
            ("map_overlay_bottom_right", bottom_right_widgets, (20, 18, 20, 20)),
            ("map_overlay_bottom_left", bottom_left_widgets, (20, 18, 20, 20)),
        ]

    def _get_widgets_bounds_in_frame_map(self, widgets):
        bounds = None
        for widget in widgets:
            if widget is None:
                continue
            top_left = widget.mapTo(self.frame_map, QPoint(0, 0))
            widget_rect = QRect(top_left, widget.size())
            bounds = widget_rect if bounds is None else bounds.united(widget_rect)

        return bounds if bounds is not None else QRect()

    def _rehost_widget_into_overlay(self, widget, overlay):
        top_left = widget.mapTo(self.frame_map, QPoint(0, 0))
        local_top_left = top_left - overlay.pos()
        widget.setParent(overlay)
        widget.move(local_top_left)
        widget.show()
        widget.raise_()

    def _set_frame_map_relative_geometry(self, widget, rect):
        parent_widget = widget.parentWidget()
        if parent_widget is None or parent_widget is self.centralwidget:
            widget.setGeometry(rect)
            return

        if parent_widget is self.frame_map:
            widget.setGeometry(rect)
            return

        local_top_left = parent_widget.mapFrom(self.frame_map, rect.topLeft())
        widget.setGeometry(QRect(local_top_left, rect.size()))

    def _get_main_map_overlay_panel_rects(self):
        if not hasattr(self, "frame_map"):
            return {}

        frame_width = self.frame_map.width()
        frame_height = self.frame_map.height()
        if frame_width <= 0 or frame_height <= 0:
            return {}

        margin = 16
        panel_gap = 14

        top_right_collapsed = self.map_overlay_collapsed.get("map_overlay_top_right", False)
        bottom_right_collapsed = self.map_overlay_collapsed.get("map_overlay_bottom_right", False)
        bottom_left_collapsed = self.map_overlay_collapsed.get("map_overlay_bottom_left", False)

        top_right_width = (
            min(440, max(420, frame_width // 5 + 60))
            if top_right_collapsed
            else min(560, max(520, frame_width // 4 + 72))
        )
        bottom_right_width = 260 if bottom_right_collapsed else min(560, max(520, frame_width // 4 + 72))

        top_right_height = 68 if top_right_collapsed else 346
        bottom_right_height = 64 if bottom_right_collapsed else 314
        top_right_rect = QRect(frame_width - top_right_width - margin, margin, top_right_width, top_right_height)
        bottom_right_rect = QRect(
            frame_width - bottom_right_width - margin,
            frame_height - bottom_right_height - margin,
            bottom_right_width,
            bottom_right_height,
        )

        available_left_width = (
            360
            if bottom_left_collapsed
            else max(520, min(760, bottom_right_rect.left() - margin - panel_gap))
        )
        bottom_left_height = 64 if bottom_left_collapsed else 198
        bottom_left_rect = QRect(
            margin,
            frame_height - bottom_left_height - margin,
            available_left_width,
            bottom_left_height,
        )

        return {
            "map_overlay_top_right": top_right_rect,
            "map_overlay_bottom_right": bottom_right_rect,
            "map_overlay_bottom_left": bottom_left_rect,
        }

    def _apply_top_right_overlay_layout(self, overlay_rect):
        overlay_name = "map_overlay_top_right"
        collapsed = self.map_overlay_collapsed.get(overlay_name, False)
        toggle_button = self.map_overlay_toggle_buttons.get(overlay_name)
        summary_widgets = self.map_overlay_summary_widgets.get(overlay_name, {})
        panel_padding = 16

        if collapsed:
            if toggle_button is not None:
                self._set_frame_map_relative_geometry(
                    toggle_button,
                    QRect(overlay_rect.right() - 42, overlay_rect.top() + 18, 26, 26),
                )

            title_width = min(120, max(108, overlay_rect.width() - 292))
            start_x = overlay_rect.left() + panel_padding + title_width + 8
            chip_y = overlay_rect.top() + 17
            self._set_frame_map_relative_geometry(
                summary_widgets["title"],
                QRect(overlay_rect.left() + panel_padding, overlay_rect.top() + 14, title_width, 38),
            )
            self._set_frame_map_relative_geometry(
                summary_widgets["status"],
                QRect(start_x, chip_y, 84, 30),
            )
            self._set_frame_map_relative_geometry(
                summary_widgets["battery"],
                QRect(start_x + 92, chip_y, 52, 30),
            )
            self._set_frame_map_relative_geometry(
                summary_widgets["tasks"],
                QRect(start_x + 152, chip_y, 64, 30),
            )
            return

        panel_padding = 16
        row_gap = 8
        button_gap = 10
        map_button_width = 64
        row_height = 40
        header_height = 42
        status_height = 52
        content_width = overlay_rect.width() - panel_padding * 2
        control_width = content_width - map_button_width - 10
        button_x = overlay_rect.right() - panel_padding - map_button_width + 1
        primary_button_width = (content_width - button_gap) // 2
        secondary_button_width = content_width - primary_button_width - button_gap
        top_y = overlay_rect.top() + panel_padding
        row_2_y = top_y + header_height + row_gap
        row_3_y = row_2_y + status_height + row_gap
        row_4_y = row_3_y + row_height + row_gap
        row_5_y = row_4_y + row_height + row_gap
        button_y = overlay_rect.bottom() - panel_padding - 40 + 1
        if toggle_button is not None:
            self._set_frame_map_relative_geometry(
                toggle_button,
                QRect(overlay_rect.right() - 38, overlay_rect.top() + 14, 22, 22),
            )

        self._set_frame_map_relative_geometry(
            self.horizontalLayoutWidget_6,
            QRect(overlay_rect.left() + panel_padding, top_y, content_width - 28, header_height),
        )
        self._set_frame_map_relative_geometry(
            self.horizontalLayoutWidget_5,
            QRect(overlay_rect.left() + panel_padding, row_2_y, content_width, status_height),
        )
        self._set_frame_map_relative_geometry(
            self.horizontalLayoutWidget_4,
            QRect(overlay_rect.left() + panel_padding, row_3_y, control_width, row_height),
        )
        self._set_frame_map_relative_geometry(
            self.btn_SelectStart,
            QRect(button_x, row_3_y + 4, map_button_width, 32),
        )
        self._set_frame_map_relative_geometry(
            self.horizontalLayoutWidget_2,
            QRect(overlay_rect.left() + panel_padding, row_4_y, control_width, row_height),
        )
        self._set_frame_map_relative_geometry(
            self.btn_SelectDestination,
            QRect(button_x, row_4_y + 4, map_button_width, 32),
        )
        self._set_frame_map_relative_geometry(
            self.horizontalLayoutWidget,
            QRect(overlay_rect.left() + panel_padding, row_5_y, content_width, row_height),
        )
        self._set_frame_map_relative_geometry(
            self.btn_Emergency_Cut_Line,
            QRect(overlay_rect.left() + panel_padding, button_y, primary_button_width, 40),
        )
        self._set_frame_map_relative_geometry(
            self.btn_Add_New_Mission,
            QRect(
                overlay_rect.left() + panel_padding + primary_button_width + button_gap,
                button_y,
                secondary_button_width,
                40,
            ),
        )

    def _apply_bottom_right_overlay_layout(self, overlay_rect):
        overlay_name = "map_overlay_bottom_right"
        collapsed = self.map_overlay_collapsed.get(overlay_name, False)
        toggle_button = self.map_overlay_toggle_buttons.get(overlay_name)
        summary_widgets = self.map_overlay_summary_widgets.get(overlay_name, {})
        panel_padding = 16

        if collapsed:
            if toggle_button is not None:
                self._set_frame_map_relative_geometry(
                    toggle_button,
                    QRect(overlay_rect.right() - 38, overlay_rect.top() + 17, 22, 22),
                )
            self._set_frame_map_relative_geometry(
                summary_widgets["title"],
                QRect(overlay_rect.left() + panel_padding, overlay_rect.top() + 14, 64, 34),
            )
            self._set_frame_map_relative_geometry(
                summary_widgets["count"],
                QRect(overlay_rect.left() + 88, overlay_rect.top() + 17, 58, 30),
            )
            self._set_frame_map_relative_geometry(
                summary_widgets["active"],
                QRect(overlay_rect.left() + 154, overlay_rect.top() + 17, 54, 30),
            )
            return

        title_y = overlay_rect.top() + panel_padding
        list_y = overlay_rect.top() + 58
        list_height = overlay_rect.height() - 74

        self._set_frame_map_relative_geometry(
            self.lineEdit_PendingMission,
            QRect(overlay_rect.left() + panel_padding, title_y, 220, 32),
        )
        if toggle_button is not None:
            self._set_frame_map_relative_geometry(
                toggle_button,
                QRect(overlay_rect.right() - 124, title_y, 34, 34),
            )
        self._set_frame_map_relative_geometry(
            self.btn_StartMission,
            QRect(overlay_rect.right() - 84, title_y, 34, 34),
        )
        self._set_frame_map_relative_geometry(
            self.btn_StopMission1,
            QRect(overlay_rect.right() - 44, title_y, 34, 34),
        )
        self._set_frame_map_relative_geometry(
            self.frame_pending_mission_list,
            QRect(overlay_rect.left() + panel_padding, list_y, overlay_rect.width() - panel_padding * 2, list_height),
        )
        self._sync_pending_mission_table_geometry()

    def _sync_pending_mission_table_geometry(self):
        if not hasattr(self, "frame_pending_mission_list") or not hasattr(self, "tableWidget_pending_mission_list"):
            return

        self.tableWidget_pending_mission_list.setGeometry(self.frame_pending_mission_list.rect())

    def _configure_pending_mission_table(self):
        header = self.tableWidget_pending_mission_list.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        header.setSectionResizeMode(7, QHeaderView.Fixed)

        self.tableWidget_pending_mission_list.setColumnWidth(1, 42)
        self.tableWidget_pending_mission_list.setColumnWidth(2, 62)
        self.tableWidget_pending_mission_list.setColumnWidth(3, 76)
        self.tableWidget_pending_mission_list.setColumnWidth(4, 76)
        self.tableWidget_pending_mission_list.setColumnWidth(6, 62)
        self.tableWidget_pending_mission_list.setColumnWidth(7, 54)
        self._sync_pending_mission_table_geometry()

    def _apply_bottom_left_overlay_layout(self, overlay_rect):
        overlay_name = "map_overlay_bottom_left"
        collapsed = self.map_overlay_collapsed.get(overlay_name, False)
        toggle_button = self.map_overlay_toggle_buttons.get(overlay_name)
        summary_widgets = self.map_overlay_summary_widgets.get(overlay_name, {})

        if collapsed:
            if toggle_button is not None:
                self._set_frame_map_relative_geometry(
                    toggle_button,
                    QRect(overlay_rect.right() - 38, overlay_rect.top() + 17, 22, 22),
                )
            chip_y = overlay_rect.top() + 17
            self._set_frame_map_relative_geometry(
                summary_widgets["current"],
                QRect(overlay_rect.left() + 16, chip_y, 88, 30),
            )
            self._set_frame_map_relative_geometry(
                summary_widgets["pending"],
                QRect(overlay_rect.left() + 112, chip_y, 88, 30),
            )
            self._set_frame_map_relative_geometry(
                summary_widgets["notice"],
                QRect(overlay_rect.left() + 208, chip_y, 108, 30),
            )
            return

        self._set_frame_map_relative_geometry(
            self.horizontalLayoutWidget_7,
            QRect(overlay_rect.left() + 58, overlay_rect.top() + 16, 92, 24),
        )
        self._set_frame_map_relative_geometry(
            self.horizontalLayoutWidget_8,
            QRect(overlay_rect.left() + 156, overlay_rect.top() + 16, 92, 24),
        )
        self._set_frame_map_relative_geometry(
            self.chb_map,
            QRect(overlay_rect.right() - 178, overlay_rect.top() + 14, 126, 30),
        )
        if toggle_button is not None:
            self._set_frame_map_relative_geometry(
                toggle_button,
                QRect(overlay_rect.left() + 16, overlay_rect.top() + 14, 34, 30),
            )
        self._set_frame_map_relative_geometry(
            self.btn_SentRobotTo,
            QRect(overlay_rect.right() - 42, overlay_rect.top() + 14, 34, 30),
        )

        heartbeat_top_y = overlay_rect.top() + 12
        heartbeat_bottom_y = overlay_rect.top() + 52
        heartbeat_start_x = overlay_rect.left() + 262
        heartbeat_step = 62
        for index in range(6):
            widget = getattr(self, f"lbl_OR_Heartbeat_{index + 1}")
            self._set_frame_map_relative_geometry(
                widget,
                QRect(heartbeat_start_x + index * heartbeat_step, heartbeat_top_y, 56, 34),
            )
        for index in range(7):
            widget = getattr(self, f"lbl_OR_Heartbeat_{index + 7}")
            self._set_frame_map_relative_geometry(
                widget,
                QRect(heartbeat_start_x + index * heartbeat_step, heartbeat_bottom_y, 56, 34),
            )

        self._set_frame_map_relative_geometry(
            self.lineEdit_MessageAnnounce,
            QRect(overlay_rect.left() + 16, overlay_rect.top() + 96, 120, 20),
        )
        self._set_frame_map_relative_geometry(
            self.verticalLayoutWidget,
            QRect(
                overlay_rect.left() + 16,
                overlay_rect.top() + 120,
                overlay_rect.width() - 32,
                overlay_rect.height() - 136,
            ),
        )

        self.listWidget_msg.setMinimumSize(QSize(0, 0))
        self.listWidget_msg.setMaximumSize(QSize(16777215, 16777215))

    def _apply_main_map_overlay_panel_layouts(self):
        if not hasattr(self, "map_overlay_frames"):
            return

        overlay_rects = self._get_main_map_overlay_panel_rects()
        if not overlay_rects:
            return

        top_right_overlay = self.map_overlay_frames.get("map_overlay_top_right")
        if top_right_overlay is not None:
            top_right_rect = overlay_rects["map_overlay_top_right"]
            top_right_overlay.setGeometry(top_right_rect)
            self._apply_top_right_overlay_layout(top_right_rect)
            self._raise_overlay_card_chrome("map_overlay_top_right")

        bottom_right_overlay = self.map_overlay_frames.get("map_overlay_bottom_right")
        if bottom_right_overlay is not None:
            bottom_right_rect = overlay_rects["map_overlay_bottom_right"]
            bottom_right_overlay.setGeometry(bottom_right_rect)
            self._apply_bottom_right_overlay_layout(bottom_right_rect)
            self._raise_overlay_card_chrome("map_overlay_bottom_right")

        bottom_left_overlay = self.map_overlay_frames.get("map_overlay_bottom_left")
        if bottom_left_overlay is not None:
            bottom_left_rect = overlay_rects["map_overlay_bottom_left"]
            bottom_left_overlay.setGeometry(bottom_left_rect)
            self._apply_bottom_left_overlay_layout(bottom_left_rect)
            self._raise_overlay_card_chrome("map_overlay_bottom_left")

    def _setup_main_map_overlay_containers(self):
        if self.map_overlay_frames:
            return

        for object_name, widgets, padding in self._build_main_map_overlay_specs():
            overlay_bounds = self._get_widgets_bounds_in_frame_map(widgets)
            if overlay_bounds.isNull():
                continue

            left_pad, top_pad, right_pad, bottom_pad = padding
            overlay_rect = overlay_bounds.adjusted(
                -left_pad,
                -top_pad,
                right_pad,
                bottom_pad,
            )
            overlay = self._create_map_overlay_frame(object_name)
            overlay.setGeometry(overlay_rect)

            for widget in widgets:
                self._rehost_widget_into_overlay(widget, overlay)

            overlay.raise_()
            self.map_overlay_frames[object_name] = overlay
            self.map_overlay_content_widgets[object_name] = list(widgets)
            setattr(self, object_name, overlay)

    def _get_main_map_scale(self):
        if not hasattr(self, "original_pixmap") or self.original_pixmap.isNull():
            return 1.0, 1.0

        pixmap_width = max(1, self.original_pixmap.width())
        pixmap_height = max(1, self.original_pixmap.height())
        return (
            self.label_map_1.width() / pixmap_width,
            self.label_map_1.height() / pixmap_height,
        )

    def _apply_main_map_shell_layout(self):
        if not hasattr(self, "centralwidget") or not hasattr(self, "frame_map"):
            return

        shell_rect = self.centralwidget.rect()
        if shell_rect.isNull():
            return

        self.frame_map.setMinimumSize(QSize(0, 0))
        self.frame_map.setMaximumSize(QSize(16777215, 16777215))
        self.frame_map.setGeometry(shell_rect)
        self.frame_map.setStyleSheet("background-color: transparent;")

        self.label_map_1.setMinimumSize(QSize(0, 0))
        self.label_map_1.setMaximumSize(QSize(16777215, 16777215))
        self.label_map_1.setGeometry(self.frame_map.rect())
        self.label_map_1.setStyleSheet("border: none; background-color: #050B12;")
        self.label_map_1.lower()

        if hasattr(self, "label_car_overlay"):
            self.label_car_overlay.setGeometry(self.label_map_1.geometry())
            self.label_car_overlay.raise_()
            if hasattr(self, "map_overlay_frames"):
                self._apply_main_map_overlay_panel_layouts()
            self._raise_map_foreground_widgets()

            if self.last_robot_world_pos is not None:
                self.draw_car_position(*self.last_robot_world_pos)
            elif self.last_click_overlay_pos is not None:
                marker_pixmap = QPixmap(self.label_car_overlay.size())
                marker_pixmap.fill(Qt.transparent)
                marker_painter = QPainter(marker_pixmap)
                self.draw_click_marker(marker_painter, *self.last_click_overlay_pos)
                marker_painter.end()
                self.label_car_overlay.setPixmap(marker_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_main_map_shell_layout()

    def _create_control_button(self, name, text):
        """創建視窗控制按鈕 (最小化, 最大化, 關閉)"""

        # 針對選單按鈕使用 QToolButton
        if name == "menuToggleButton":
            btn = QToolButton(self) # 使用 QToolButton
        else:
            btn = QPushButton(text) # 其他使用 QPushButton

        # 如果是 QPushButton (控制按鈕)，設置文字
        if isinstance(btn, QPushButton):
             btn.setText(text)
       
        btn.setObjectName(name)
        # 固定尺寸
        btn.setFixedSize(40, 40) 
        return btn

    def _create_title_bar_frame(self):
        """創建並佈局客製化標題列的框架和元件"""
        frame = QFrame()
        frame.setObjectName("CustomTitleFrame") # 名字很重要，用於 QSS 和事件判斷
        frame.setFixedHeight(40) 
        
        title_layout = QHBoxLayout(frame)
        title_layout.setContentsMargins(10, 0, 0, 0) 
        title_layout.setSpacing(0)
        
        # 菜單按鈕 (如果有需要，可以保留)
        self.menuToggleButton = self._create_control_button("menuToggleButton", "")
        
        # 應用程式名稱標籤
        self.appLogoLabel = QLabel()
        self.appLogoLabel.setObjectName("appLogoLabel")
        self.appLogoLabel.setFixedSize(24, 24)

        # Logo 也放進同一份資源設定，避免場域路徑分散在不同地方。
        # 之後若某個場域要換 Logo，只需要修改 site/<profile>.json。
        logo_path = resolve_runtime_path(self.site_assets.get("logo"))
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            self.appLogoLabel.setPixmap(
                logo_pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        self.appNameLabel = QLabel("ACE Solution - MiR")
        self.appNameLabel.setObjectName("appNameLabel")
        
        # 視窗控制按鈕
        self.minimizeButton = self._create_control_button("minimizeButton", "—") 
        # 確保 self.maximizeButton 存在，供 _toggle_maximize 呼叫
        self.maximizeButton = self._create_control_button("maximizeButton", "☐") 
        self.closeButton = self._create_control_button("closeButton", "✕") 

        # 連接訊號 (Signal)
        self.minimizeButton.clicked.connect(self.showMinimized)
        self.maximizeButton.clicked.connect(self._toggle_maximize)
        self.closeButton.clicked.connect(self.close)

        # 佈局元件
        title_layout.addWidget(self.menuToggleButton) # 如果不需要菜單鈕就註解掉
        title_layout.addSpacing(6)
        title_layout.addWidget(self.appLogoLabel)
        title_layout.addSpacing(8)
        title_layout.addWidget(self.appNameLabel)
        title_layout.addStretch() # 伸展空間，將控制按鈕推到最右邊
        title_layout.addWidget(self.minimizeButton)
        title_layout.addWidget(self.maximizeButton)
        title_layout.addWidget(self.closeButton)

        # **新增呼叫菜單創建**
        self._create_menu()
        
        return frame
        
    def _toggle_maximize(self):
        """切換視窗最大化/還原狀態並更新按鈕圖示"""
        # 請確保這個方法也被加回您的 MainWindow 類別中
        if self.isMaximized():
            self.showNormal()
            self.maximizeButton.setText("☐") # 方框圖示 (還原)
        else:
            self.showMaximized()
            self.maximizeButton.setText("❐") # 雙方框圖示 (最大化)

    def apply_qss_styles(self):
        """應用深色主題樣式表"""
        qss = r"""
        /* ==================== 標題列相關樣式 ==================== */
        調整mainwindow 深色背景
        /* 1. 設定 QMainWindow 本身和所有 QWidget 的基礎顏色 */
        QMainWindow, QWidget {
            background-color: #1e1e1e; /* 使用你選擇的深色 */
            color: #FFFFFF;           /* 預設文字顏色 */
        }
        
        /* 2. 確保 QFrame 也是這個顏色 (通常你的內容區會被 QFrame 包裹) */
        QFrame {
            background-color: #1e1e1e;
        }
        
        /* 1. QToolBar 容器樣式 (確保背景顏色一致，並移除預設邊框) */
        QToolBar#CustomTitleBar {
            background-color: #393939; 
            border: none; 
            padding: 0px;
            margin: 0px;
        }
        /* 2. 解決 ToolBar 內部間距問題，確保 QFrame 緊貼邊緣 */
        QToolBar#CustomTitleBar QWidget {
            background-color: transparent; 
            padding: 0px;
            margin: 0px;
            border: none;
        }

        /* 3. 客製化標題列 QFrame 樣式 */
        #CustomTitleFrame {
            background-color: #3C3C3C; 
            border-bottom: 1px solid #555;
        }

        /* 應用程式名稱文字 */
        #appNameLabel {
            color: white;
            font-size: 14pt;
            font-weight: 500;
            margin-left: 10px;
        }
        
        /* 4. 視窗控制按鈕通用樣式 */
        #minimizeButton, #maximizeButton, #closeButton {
            /* ... (保持您原有的按鈕樣式) ... */
            color: white;
            border: none;
            margin: 0px; 
            padding: 0px 8px;
            font-weight: bold;
            font-size: 14pt;
            background-color: transparent;
        }

        #minimizeButton:hover, #maximizeButton:hover {
            background-color: #555555;
        }

        #closeButton:hover {
            background-color: #E81123; 
        }

        /* ==================== 菜單/漢堡包按鈕 QToolButton 樣式 ==================== */
        QToolButton#menuToggleButton {
            border: none;
            background-color: #2D2D30; 
            color: white;
            font-size: 18pt; 
            padding: 0px 5px;
            /* 關鍵修正 1: 透過 QSS 的 qproperty-text 設定按鈕文字為 "☰" (Unicode U+2630) */
            qproperty-text: "≡"; 
            text-align: center;
        }

        /* 關鍵修正 2: 強制隱藏 QToolButton 的菜單指示器 (三角錐) */
        QToolButton#menuToggleButton::menu-indicator {
            image: none; /* 移除任何指示圖案 */
            width: 0px;  /* 強制寬度為 0 */
            margin: 0px; /* 移除任何可能的邊距佔位 */
        }

        /* ==================== 內容區樣式 (保持不變) ==================== */
        /* 假設您的 centralWidget (Designer 創建的) 是直接子元件 */
        QStackedWidget, QWidget#DesignerCentralWidget { 
            background-color: #1E1E1E; 
            color: #ccc;
        }
        """
        self.setStyleSheet(qss)
    

    # ----------------------------------------------------
    # ⭐ 菜單按鈕 ⭐
    # ----------------------------------------------------
    def _create_menu(self):
        """創建並設定菜單內容，這個菜單將由 menuToggleButton 觸發"""

        # 創建菜單主體
        self.userMenu = QMenu(self)
        self.userMenu.setObjectName("UserMenu")

        # --- 1. 使用者資訊 (標題或不可點擊的 Action) ---
        # 創建一個 QWidgetAction 來容納使用者名稱和角色 QLabel
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        # 稍微調整邊距，讓它看起來更像菜單標題
        info_layout.setContentsMargins(15, 10, 15, 10) 
        info_layout.setSpacing(1)
        
        # 假設這是使用者名稱和 ID (這裡可以放入您實際的 username 變數)
        user_label = QLabel(self.current_username_id) 
        user_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: #E0E0E0;")
        
        # 假設這是角色
        role_label = QLabel("管理者")
        role_label.setStyleSheet("font-size: 9pt; color: #A0A0A0;")
        
        info_layout.addWidget(user_label)
        info_layout.addWidget(role_label)
        info_layout.setAlignment(user_label, Qt.AlignLeft)
        info_layout.setAlignment(role_label, Qt.AlignLeft)

        # 創建 QWidgetAction 並設定 widget
        info_action = QWidgetAction(self.userMenu)
        info_action.setDefaultWidget(info_widget)
        info_action.setEnabled(False) # 不可點擊
        
        # 將使用者資訊加入菜單
        self.userMenu.addAction(info_action)
        self.userMenu.addSeparator() # 分隔線

        # --- 2. 登出 ---
        self.actionLogout = self.userMenu.addAction("登出")
        # 這裡使用一個通用的圖示路徑，如果沒有，請用您自己的
        # 確保您已經引入 QIcon
        # self.actionLogout.setIcon(QIcon(":/icons/logout.svg")) 
        self.actionLogout.triggered.connect(self.handle_logout) # 連接到登出槽函式

        # 將 QMenu 實例指派給按鈕
        self.menuToggleButton.setMenu(self.userMenu)
        self.menuToggleButton.setPopupMode(QToolButton.InstantPopup)

        # QToolButton 預設會顯示箭頭，我們將其關閉。
        # self.menuToggleButton.setArrowType(Qt.NoArrow) 
        self.menuToggleButton.setToolTip("使用者設定")
    
    def handle_logout(self):
        self.close()
        # 在這裡實現登出的邏輯
        print("使用者已登出")


    # ====== 每 n 秒查一次 API 狀態記錄下來給手術室桌機軟體確認用======
    def poll_room_status(self):
        # ⭐ 如果上一輪還沒跑完 → 直接跳過（避免 thread 疊加）
        if self.polling_busy:
            return

        self.polling_busy = True
        self.active_workers = 0  # ⭐ 每輪 reset

         # ===== API 健康檢查（丟到背景 thread）=====
        worker_api = DBWorker(self.check_api_status_worker)

         # ⭐ 設定 thread 行為（成功 / 失敗 / 清理）
        self._setup_worker(worker_api, self.api_ok, self.api_error_handler)

    # API 呼叫（背景執行，不碰 UI）
    def check_api_status_worker(self):
        return functions.check_api_status_v3()

    
    def api_ok(self, status=None):
        # print("✅ API 正常")

        # ⭐ 不管狀態，直接嘗試清（DB 自己判斷有沒有）
        self.task_db_manager.clear_room_error("MASTER")

        self.api_error = False
        self._print_mission_text(status)

        # API 成功後，把最新 mission_text 同步到 console 與狀態列。
        self._print_mission_text(status)

    def _print_mission_text(self, status):
        # 只處理 MiR /status 回來的 dict。
        if not isinstance(status, dict):
            return

        mission_text = status.get("mission_text")
        # 若內容沒變，避免重複刷新 UI 與 console。
        if mission_text is None or mission_text == self.last_mission_text:
            return

        self.last_mission_text = mission_text
        self.current_mission_text = mission_text
        # mission_text 改變時，重新組合狀態列文字。
        self._update_status_label(self.current_mir_state_id)
        print(f"mission_text: {mission_text}")

    def _update_status_label(self, state_id):
        # 將 MiR state_id 轉成人看得懂的狀態文字與顏色。
        status_map = {
            1: ("Starting", "yellow"),
            2: ("ShuttingDown", "red"),
            3: ("Ready", "green"),
            4: ("Pause", "yellow"),
            5: ("Executing", "green"),
            6: ("Aborted", "yellow"),
            7: ("GoalReached", "green"),
            8: ("Docked", "green"),
            9: ("Docking", "green"),
            10: ("EmergencyStop", "red"),
            11: ("ManualControl", "red"),
            12: ("Error", "purple"),
        }

        status_name, color = status_map.get(state_id, ("Unknown", "white"))
        # First line shows robot state; mission text is appended on line two.
        label_text = f"Status: {status_name}"
        """
        label_text = f"Status：{status_name}"

        """
        # 統一組合狀態列格式；若有 mission_text 就顯示在後面。
        label_text = f"Status: {status_name}"
        label_text = f"Status: {status_name}"
        label_text = f"Status: {status_name}"
        if self.current_mission_text:
            label_text = f"{label_text}\nMission: {self.current_mission_text}"

        self.label_Status_1.setText(label_text)
        self.label_Status_1.setStyleSheet(self._build_compact_status_label_qss(color))


    def _update_status_label(self, state_id):
        # 將 MiR state_id 轉成人看得懂的狀態文字與顏色。
        status_map = {
            1: ("Starting", "yellow"),
            2: ("ShuttingDown", "red"),
            3: ("Ready", "green"),
            4: ("Pause", "yellow"),
            5: ("Executing", "green"),
            6: ("Aborted", "yellow"),
            7: ("GoalReached", "green"),
            8: ("Docked", "green"),
            9: ("Docking", "green"),
            10: ("EmergencyStop", "red"),
            11: ("ManualControl", "red"),
            12: ("Error", "purple"),
        }

        status_name, color = status_map.get(state_id, ("Unknown", "white"))
        # 統一組合狀態列格式；若有 mission_text 就顯示在後面。
        label_text = f"Status: {status_name}"

        if self.current_mission_text:
            label_text = f"{label_text}\nMission: {self.current_mission_text}"

        self.label_Status_1.setText(label_text)
        self.label_Status_1.setStyleSheet(self._build_compact_status_label_qss(color))

    def _update_status_label(self, state_id):
        # Final status renderer used by the UI: line 1 = robot state, line 2 = mission text.
        status_map = {
            1: ("Starting", "yellow"),
            2: ("ShuttingDown", "red"),
            3: ("Ready", "green"),
            4: ("Pause", "yellow"),
            5: ("Executing", "green"),
            6: ("Aborted", "yellow"),
            7: ("GoalReached", "green"),
            8: ("Docked", "green"),
            9: ("Docking", "green"),
            10: ("EmergencyStop", "red"),
            11: ("ManualControl", "red"),
            12: ("Error", "purple"),
        }

        status_name, color = status_map.get(state_id, ("Unknown", "white"))
        mission_line = self.current_mission_text or "-"
        label_text = f"Status: {status_name}\nMission: {mission_line}"

        self.label_Status_1.setText(label_text)
        self.label_Status_1.setStyleSheet(self._build_compact_status_label_qss(color))
        self.label_Status_1.setToolTip(f"Mission: {mission_line}")
        self._refresh_overlay_card_summaries()

    def _adjust_status_area_layout(self):
        self._apply_main_map_overlay_panel_layouts()

    def api_error_handler(self):
        print("❌ API 異常")

        # ⭐ 只有「第一次錯誤」才寫 DB（避免狂寫）gi
        if not self.api_error:
            self.task_db_manager.mark_room_error("MASTER", "API_ERROR")
            self.api_error = True

    def _setup_worker(self, worker, success_cb, error_cb):
        self.active_workers += 1 # ⭐ 記錄目前有幾個 worker 在跑

        # ===== 成功 / 失敗 callback =====
        worker.finished.connect(success_cb)
        worker.error.connect(error_cb)

        # ⭐ 防止 thread 被 Python 回收（超重要）
        self.workers.append(worker)

        # ===== 收尾（不論成功或失敗都會清理）=====
        worker.finished.connect(lambda: self._cleanup_poll_worker(worker))
        worker.error.connect(lambda: self._cleanup_poll_worker(worker))

        worker.start() # ⭐ 啟動 thread
    
    def _cleanup_poll_worker(self, worker):
        # ⭐ 從列表移除（避免記憶體累積）
        if worker in self.workers:
            self.workers.remove(worker)

        self.active_workers -= 1

        # ⭐ 所有 worker 都結束 → 才允許下一輪 polling
        if self.active_workers == 0:
            self.polling_busy = False
        




    # ----------------------------------------------------
    # ⭐ 處理 TaskThread 訊號的 Slot (最小功能版) ⭐
    # ----------------------------------------------------
    def update_log_ui(self, message: str):
        """
        [槽] 接收來自 TaskThread 的日誌訊息。
        
        Args:
            message (str): 來自執行緒的日誌或狀態文字。
        """
        # ⚠️ 這裡只會將訊息打印到你的 PyCharm/VS Code/終端機的控制台
        print(f"[{time.strftime('%H:%M:%S')}][TASK THREAD LOG] {message}")
        
        # TODO: 未來請在這裡加入程式碼，將訊息寫入到 UI 上的日誌顯示區。

    def _notify_task_result(self, result_status: str, task_id: int, start_point: str, target_point: str):
        notification_key = (result_status, task_id)
        if notification_key in self.notified_task_results:
            return

        self.notified_task_results.add(notification_key)

        if result_status == "Completed":
            self.add_notification_item("完成", f"{task_id} 任務完成: 從 {start_point} 前往 {target_point}")
        elif result_status == "Aborted":
            self.add_notification_item("取消", f"{task_id} 任務被取消/中止: 從 {start_point} 前往 {target_point}")

    def _finalize_task_result(self, task_id: int, result_status: str, start_point: str, target_point: str):
        transitioned = self.task_db_manager.transition_task_status(
            task_id,
            from_status="Executing",
            to_status=result_status,
        )

        if not transitioned:
            return False

        self.is_AMR_idle = True
        self._notify_task_result(result_status, task_id, start_point, target_point)
        self.refresh_task_list()
        return True

    def handle_task_completion(self, task_id: int, result_status: str, start_point: str, target_point: str):
        print(f"[TASK RESULT] task_id={task_id}, status={result_status}")
        finalized = self._finalize_task_result(task_id, result_status, start_point, target_point)
        if not finalized:
            self.is_AMR_idle = True
        return
        """
        [槽] 接收 TaskThread 發出的任務完成訊號 (task_id)。
        
        Args:
            task_id (int): 已完成任務的資料庫 ID。
        """
        # ⚠️ 這裡只會將訊息打印到控制台
        # if hasattr(self, 'task_thread') and self.task_thread and self.task_thread.isRunning():  
            # TaskThread.stop() 內部會將 self.is_running 設為 False
            # self.task_thread.stop() 
            # self.task_thread.wait()
            # self.task_thread.deleteLater()
            # self.task_thread = None 
            # self.log_message.emit("🛑 收到中斷指令，排程執行緒正在停止...")
        # self.db_manager._resequence_pending_tasks()
        print(f"[TASK COMPLETED] 任務 ID {task_id} 已完成，等待 UI 刷新。")
        
        
        # TODO: 未來請在這裡加入程式碼，刷新 QTableWidget 或更新任務狀態顯示。

    #######################UXUI_tablewidget#######################
   
    # 將 QTableWidget 中所有單元格的文字設定為置中
    def set_table_items_center(self, table_widget):
        for row in range(table_widget.rowCount()):
            for col in range(table_widget.columnCount()):
                item = table_widget.item(row, col)
                if item is not None:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    #  添加刪除按鈕
    #  self.add_delete_button(row_count)
        
    # 建立一個刪除按鈕
    # 建立一個刪除按鈕
    def add_delete_button(self, row):
        """建立一個帶有刪除圖示的按鈕，並加入表格"""

        # 建立一個中央對齊的 Widget (容器)
        container_widget = QWidget()
        layout = QHBoxLayout(container_widget)

        # 設置佈局的間距和邊界為 0，讓按鈕可以置中 (這是對的)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
     
        # 建立一個 QPushButton
        delete_btn = QPushButton("")
        delete_btn.setFixedSize(30, 30) # 強制設定按鈕的固定大小
        
        # 載入垃圾桶圖示
        delete_icon = QIcon(":/icons/icons/trash-2.svg") 
        delete_btn.setIcon(delete_icon)
        delete_btn.setIconSize(QSize(20, 20)) 
        
        # 設置按鈕的樣式 (省略部分樣式程式碼)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5252;
                border: none;
                border-radius: 12px;
                padding: 2px;
            }
        """)
        
        # 將按鈕加入佈局 (現在按鈕在容器內置中了)
        layout.addWidget(delete_btn)
        
        # 連接按鈕的點擊事件到一個刪除函式
        delete_btn.clicked.connect(lambda: self.handle_delete_action(row))
        
        # 將這個中央對齊的 Widget (包含按鈕) 放入表格單元格
        self.tableWidget_pending_mission_list.setCellWidget(row, 7, container_widget)
        
    # 刪除表格中的行
    def handle_delete_action(self, row):
        """根據行號刪除表格中的行"""
        # 這邊col是隱藏的，也就是db第一行
        task_id_item = self.tableWidget_pending_mission_list.item(row, 0)
        if task_id_item is None:
            return
        try:
            task_id = task_id_item.text()
            self.task_db_manager.delete_task(task_id)
            self.task_db_manager._resequence_pending_tasks()
        except ValueError:
            print("錯誤：無法取得有效的任務 ID。")
        except Exception as e:
            print(f"資料庫刪除錯誤: {e}")
      

    # 新增一條通知到清單
    def add_notification_item(self, type, message):
        """
        將客製化的 NotificationItem 加入到 self.listWidget_msg 中
        """
        # 1. 創建客製化 Widget
        notification_widget = CompactNotificationItem(type, message)
        
        # 2. 創建 QListWidgetItem 作為容器
        list_item = QListWidgetItem(self.listWidget_msg)
        
        # 3. 設定 QListWidgetItem 的高度以容納 widget
        list_item.setSizeHint(notification_widget.sizeHint())
        
        # 4. 將客製化 Widget 設定給 QListWidgetItem
        self.listWidget_msg.setItemWidget(list_item, notification_widget)
        
        # 5. 將新項目放到最上方 (實現最新的通知在最上面)
        self.listWidget_msg.insertItem(0, list_item)

        # 6. 連接關閉按鈕的事件：點擊時刪除該項目
        close_btn = notification_widget.close_button
        
        # 這是關鍵步驟：點擊按鈕時，取得 list_item 的行號並刪除
        close_btn.clicked.connect(
            lambda: (
                self.listWidget_msg.takeItem(self.listWidget_msg.row(list_item)),
                self._refresh_overlay_card_summaries(),
            )
        )
        self._refresh_overlay_card_summaries()

    def closeEvent(self, event):
        """
        程式關閉時，安全關閉資料庫連線。
        """
        if self.task_db_manager:
            self.task_db_manager.close()
        super().closeEvent(event)

    #######################postgresql資料庫#######################
    # 新增任務按鈕
    def on_add_new_mission_clicked(self):
        start_place = self.cmb_location2.currentText()
        destination = self.cmb_location.currentText()
        mission_content = self.cmb_mission.currentText()

        new_id = self.create_new_db_task(start_place, destination, mission_content)
        print("new_id", new_id)

        if new_id:
            print(f"✅ 新增任務成功，DB ID: {new_id}")
            self.cmb_location2.setCurrentIndex(0)
            self.cmb_location.setCurrentIndex(0)
            self.cmb_mission.setCurrentIndex(0)
            # 刷新表格，顯示新任務
            self.refresh_task_list()
        else:
            print("❌ 寫入資料庫失敗。") 


    # 新增一個共用function
    def create_new_db_task(self, start_place, destination, mission_content):
        """
        共用的新增任務邏輯：
        依 destination 對應 room_id，並寫入 DB
        """
        room_id = self.ROOM_ID_MAP.get(destination)

        if not start_place or not destination or not mission_content:
            print("請填寫所有欄位！")
            return None

        # 呼叫 TaskDBManager 寫入 DB
        # DB 會自動處理 sequence (排隊順序) 和 id (流水號)
        # room_id=room_id keyword argument（關鍵字參數）
        new_id = self.task_db_manager.add_new_task(
            start_place,
            destination,
            mission_content,
            room_id=room_id
        )
        return new_id

    # 新增loop任務
    def add_test_batch_missions(self):
        if self.is_test_mode:
            points=["華陀會議室","演講廳_02","演講廳_01","櫃台"]
            mission_content = "Demo_空車運輸"
            missions_list = []
            # 建立一個任務 Tuple 列表 [(start, target, content), ...]
            for i in range(len(points)):
                start_point = points[i]
                #意思是模數運算，循環隊列
                target_point = points[(i + 1) % len(points)]
                missions_list.append((start_point, target_point, mission_content))
            
            # --- 關鍵：呼叫新的批次方法 ---
            success = self.task_db_manager.add_batch_tasks(missions_list) 
            
            if success:
                print(f"✅ 成功新增 {len(missions_list)} 筆循環任務。")
                self.refresh_task_list()
            else:
                print("❌ 批次寫入資料庫失敗。")
        else:
            print("❌ 無法在非測試模式下新增循環任務。")



    # 在DB新增任務
    def on_emergency_cut_line_clicked(self):

        start_place = self.cmb_location2.currentText()
        destination = self.cmb_location.currentText()
        mission_content = self.cmb_mission.currentText()
        
        # 檢查欄位是否為空
        if not start_place or not destination or not  mission_content :
            print("請填寫所有欄位！")
            return
        
        # 呼叫 TaskDBManager 寫入 DB
        # DB 會自動處理 sequence (排隊順序) 和 id (流水號)
        new_id = self.task_db_manager.emergency_insert_task(start_place, destination, mission_content)
        print("new_id", new_id)

        if new_id:
            print(f"🚨 緊急插單成功，DB ID: {new_id}")
            self.cmb_location2.setCurrentIndex(0)
            self.cmb_location.setCurrentIndex(0)
            self.cmb_mission.setCurrentIndex(0)
        
            # 刷新表格，顯示新任務
            self.refresh_task_list()
        else:
            print("❌ 寫入資料庫失敗。")

   
   # 讀DB然後刷新GUI表格
    def refresh_task_list(self):
        """
        [QTimer 連接的函式]
        從 DB 查詢 'Pending' 或 'Executing' 任務，並刷新 QTableWidget。
        """
        # 呼叫 TaskDBManager 取得待執行任務 (已依 sequence 排序)
        tasks = self.task_db_manager.get_pending_tasks()
    

        # 確保表格總欄數為 8 欄 (1個隱藏DB_ID + 7個顯示欄位)
        if self.tableWidget_pending_mission_list.columnCount() != 8:
            print(self.tableWidget_pending_mission_list.columnCount())
            # 如果你的初始化沒設定，在這裡設定一次
            self.tableWidget_pending_mission_list.setColumnCount(8)
            self.tableWidget_pending_mission_list.setColumnHidden(0, True)
        else:
            self.tableWidget_pending_mission_list.setColumnHidden(0, True)

        # 1. 清空表格設定行數為 0
        self.tableWidget_pending_mission_list.setRowCount(0)

        # 呼叫 ToolTip 更新函式
        self.refresh_label_tooltip(tasks) 

        if not tasks:
            self._refresh_overlay_card_summaries()
            return
        
        self.tableWidget_pending_mission_list.setRowCount(len(tasks))

        # 2. 遍歷任務並填充表格
        for row_idx, task in enumerate(tasks):
            # 任務物件 (task) 是一個字典，Key 對應 DB 欄位名稱
            # A. 隱藏欄位 (索引 0)
            self.tableWidget_pending_mission_list.setItem(row_idx, 0, QTableWidgetItem(str(task['id']))) 
            
            # B. 顯示欄位 (索引 1 開始) - **注意索引偏移**
            
            # 索引 1: 序
            self.tableWidget_pending_mission_list.setItem(row_idx, 1, QTableWidgetItem(str(task['sequence'])))
            
            # 索引 2: 流水號 (使用 DB 的 mission_content 或其他欄位)
            # 註: 如果你的 DB 任務資訊中沒有獨立的「流水號」欄位，可能需要調整 DB 設計
            self.tableWidget_pending_mission_list.setItem(row_idx, 2, QTableWidgetItem(str(task['id']))) 
            
            # 索引 3: 起點
            self.tableWidget_pending_mission_list.setItem(row_idx, 3, QTableWidgetItem(task['start_point']))
            
            # 索引 4: 目的地
            self.tableWidget_pending_mission_list.setItem(row_idx, 4, QTableWidgetItem(task['target_point']))

            # 索引 5: 任務 (這裡對應你 UI 標題的「任務」，可能是 mission_content 的完整描述)
            self.tableWidget_pending_mission_list.setItem(row_idx, 5, QTableWidgetItem(task['mission_content']))
            
            # 索引 6: 狀態
            item_status = QTableWidgetItem(task['status'])
            
            # 根據狀態給予顏色提示 (可選)
            if task['status'] == 'Executing':
                item_status.setForeground(QColor('green'))
            elif task['status'] == 'Pending':
                item_status.setForeground(QColor('#FFA500'))
            self.tableWidget_pending_mission_list.setItem(row_idx, 6, item_status)
            
            # 索引 7: 空白/操作按鈕欄位
            # self.tableWidget_pending_mission_list.setItem(row_idx, 7, ) 
            self.add_delete_button(row_idx) # add_delete_button
            

            # 重新呼叫你的置中函式和列寬調整 (這不會被前面的 setRowCount(0) 影響)
            self.set_table_items_center(self.tableWidget_pending_mission_list)
            self.tableWidget_pending_mission_list.resizeRowsToContents()

        self._refresh_overlay_card_summaries()

    #######################刷新label&tooltip#######################
    def create_tooltip_html(self, task, role):
        """
        格式化單個任務資訊 (與之前相同，但為類別方法)
        """
        # 確保您的 ToolTip 內容符合 UX 需求
        html_content = f"""
        <div style="margin-top: 5px;">
            <span style="font-weight: bold;">
            任務狀態: {task.get('status', 'N/A')} ({role})<br>
            流水號: {task.get('id', 'N/A')}<br>
            任務排序: {task.get('sequence', 'N/A')}<br>
            任務內容: {task.get('mission_content', 'N/A')}</span>
        </div>
        """
        return html_content

    def refresh_label_tooltip(self, tasks):
        # ----------------------------------------------------
        # 步驟 1: 清空所有可能的標記狀態 (重置)
        # ----------------------------------------------------
        # 遍歷所有已知地點標記的名稱
        for marker_name in self.LOCATION_TO_MARKER.values():
            # 這一行程式碼讓您能夠用一個簡單的迴圈，遍歷地圖上所有名稱有規律的標記
            marker_label = getattr(self, marker_name, None)
            if marker_label:
                marker_label.setToolTip("")
                marker_label.setStyleSheet(STYLE_DEFAULT) 
                marker_label.setText("")
                # marker_label.hide()
        # ----------------------------------------------------
        # **新增步驟**：對任務進行排序
        # 讓 'Executing' 狀態的任務排在後面，這樣它們的設定會覆蓋 'Pending' 
        # ----------------------------------------------------
        def sort_key(task):
            status = task.get('status')
            sequence_text = task.get('sequence', 0)

            status_weight = 1
            if status == 'Executing':
                status_weight = 2
            inverted_sequence = -sequence_text
            return (status_weight, inverted_sequence)

        sorted_tasks = sorted(tasks, key=sort_key)
                
        # ----------------------------------------------------
        # 步驟 2: 遍歷任務，直接更新起點和目的地的標記
        # ----------------------------------------------------
        for task in sorted_tasks:
            start_point = task.get('start_point')
            target_point = task.get('target_point')
            status = task.get('status')
            sequence_text = str(task.get('sequence', ''))
            
            # 決定顏色樣式
            style = STYLE_PENDING
            if status == 'Executing':
                style = STYLE_EXECUTING
                
            # ----------------------------------
            # 更新起點標記
            # ----------------------------------
            start_marker_name = self.LOCATION_TO_MARKER.get(start_point)
            if start_marker_name:
                marker_label = getattr(self, start_marker_name, None)
                if marker_label:
                    # 建立 ToolTip 資訊，標註為「起點」
                    tooltip_html = self.create_tooltip_html(task, "起點")
                    marker_label.setText(sequence_text)
                    marker_label.setToolTip(tooltip_html)
                    marker_label.setStyleSheet(style)
                    marker_label.show()
            
            # ----------------------------------
            # 更新目的地標記
            # ----------------------------------
            target_marker_name = self.LOCATION_TO_MARKER.get(target_point)
            if target_marker_name and target_marker_name != start_marker_name:
                marker_label = getattr(self, target_marker_name, None)
                if marker_label:
                    # 建立 ToolTip 資訊，標註為「目的地」
                    tooltip_html = self.create_tooltip_html(task, "目的地")
                    marker_label.setText(sequence_text)
                    marker_label.setToolTip(tooltip_html)
                    marker_label.setStyleSheet(style)
                    marker_label.show()
        
    #######################自動詢問#################################

    # 自動詢問當前任務狀態與等待中任務
    def query_mir_info(self):
        try:
            status_info = functions.check_MiR_status()
            #轉換成「格式化的 JSON 字串」，用來方便顯示（indent=4 表示用四個空格縮排）
            status_info_str = json.dumps(status_info, indent = 4) 
            self.current_mission_text = status_info.get("mission_text", self.current_mission_text)
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
            full_message = f"[{timestamp}] 狀態：\n{status_info_str}\n{'-'*40}"
            self.plntxtEdit_Info.appendPlainText(full_message)
            #取得等待任務名字
            pm_names = functions.get_pending_mission_names()
            if pm_names:
                pm_names_with_index = [f"任務{index+1} {name}" for index, name in enumerate(pm_names)]
                self.txtEdit_GetPM.setPlainText("\n".join(pm_names_with_index))
                #self.txtEdit_GetPM.setPlainText("\n".join(pm_names))
            else:
                self.txtEdit_GetPM.setPlainText("No pending missions")
                
            state_ID = functions.check_MiR_status_state_ID()
            self.current_mir_state_id = state_ID
            self.robot_glow_phase = (self.robot_glow_phase + 1) % 3
            if self.last_robot_world_pos is not None:
                self.draw_car_position(*self.last_robot_world_pos)
            self._update_status_label(state_ID)
        except Exception as e:
            self.label_Status_1.setText("錯誤")
            self.label_Status_1.setToolTip("")

    # 詢問車子資料庫是否有執行的任務，並用MiR API確認底層車子任務是否完成
    def query_mir_status_db(self):
       
        executing_task_data = self.task_db_manager.get_currently_executing_task()
        # 檢查是否有正在執行的任務
        if not executing_task_data:
            self.mir_status_poll_disconnected = False
            # 沒有任務在執行，直接退出
            return
        
        task_id = executing_task_data['id']
        start_point = executing_task_data['start_point']
        target_point = executing_task_data['target_point']
        mq_id = executing_task_data.get('mq_id')  # ✅ 取出你綁定的 mq_id

        if not mq_id:
            # 補綁 mq_id：如果 mission_queue 有新 id，就補回 DB
            latest_mq_id = functions.get_mission_queue_max_id()
            if latest_mq_id:
                self.task_db_manager.update_task_mq_id(task_id, latest_mq_id)
                mq_id = latest_mq_id
            else:
                return

        state = functions.get_mission_queue_id_state(mq_id)  # ✅ 查指定 mq_id 的 state

        # mission_queue 的 id 以及 state
        # max_id_state = functions.get_mission_queue_max_id_state()
        # max_mission_id  = functions.get_mission_queue_max_id()
        # print(f"max_id_state: {max_id_state}, max_mission_id: {max_mission_id}") 

        if state is None:
            if not self.mir_status_poll_disconnected:
                print(f"[MIR RECONCILE] mission queue state unavailable for mq_id={mq_id}")
            self.mir_status_poll_disconnected = True
            return

        if self.mir_status_poll_disconnected:
            print(f"[MIR RECONCILE] mission queue connection restored for mq_id={mq_id}")
            self.mir_status_poll_disconnected = False

        if  state == "Done":
            self._finalize_task_result(task_id, "Completed", start_point, target_point)
            return
            self.add_notification_item("完成", f"{task_id} 任務完成: 從 {start_point} 前往 {target_point}")

        elif state == "Aborted":
            self._finalize_task_result(task_id, "Aborted", start_point, target_point)
            return
            self.is_AMR_idle = True
            self.add_notification_item("取消", f"{task_id} 任務被取消/中止: 從 {start_point} 前往 {target_point}")

        # 刷新 UI 任務列表
        self.refresh_task_list() 

    # 自動詢問Sent robot to車子狀態
    def query_mir_status(self):
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.query_mir_status_ready)
        self.status_timer.start(5000)

    def _update_sent_robot_to_button_state(self):
        self.btn_SentRobotTo.setEnabled(
            self.clicked_enabled and not self.sent_robot_to_in_progress
        )
        
    # 自動詢問到了沒
    def query_mir_status_ready(self):
        state_id = functions.check_MiR_status_state_ID()
        if state_id == 3:
            print("導航完成，刪除位置")
            self.status_timer.stop()
            functions.delete_srt_position()
            self.sent_robot_to_in_progress = False
            self._update_sent_robot_to_button_state()
        self.load_map_positions()


    # 自動詢問電池狀態
    def query_battery_status(self):
        battery_level = functions.get_battery_level()
        # 根據電量設定顏色
        if battery_level <=20:
            color = "red"
            self.is_low_battery = True
            if not self.is_low_battery_notified:
                self.add_notification_item("警告", f"電量低於 {battery_level}%，任務暫停，暫回充電樁充電。")
                self.is_low_battery_notified = True

        # 如果電量已經達到 100%， 並且 AMR 之前確實因為電量低於 20% 而被標記為低電量，狀態 (正在充電)， 那麼就發送「充電完成」的通知，並重置低電量狀態旗標。」
        elif battery_level == 100 and self.is_low_battery_notified:
            color = "#085508"
            self.add_notification_item("完成", f"電量已恢復到 {battery_level}%，接續執行。")
            self.is_low_battery=False  #低電量旗標設定 1010
            self.is_low_battery_notified = False
        else:
            color = "orange" if battery_level <= 50 else "#085508"
            self.is_low_battery=False  #低電量旗標設定 1010
             


        # 設定進度條顏色。沒有設定 ::chunk 樣式時，Qt 有時會不渲染 chunk 或讓它預設尺寸極小
        self._set_battery_progress_style(color)
        self.progressBar_battery.setValue(battery_level)
        self._refresh_overlay_card_summaries()
        
    # 自動取得歷史錯誤資料
    def query_his_data(self):
        his_data = functions.get_error_history_data()
        if his_data:
            response = requests.post("http://localhost:3000/upload", json=his_data)
            print("伺服器回應：", response.json())
        else:
            # print("沒有錯誤，不需要送出資料") 0923
            pass

    def get_heartbeat_label(self, index):
        return getattr(self, f"lbl_OR_Heartbeat_{index}", None)

    def get_heartbeat_room_label_map(self):
        room_label_map = {}
        for index in range(1, self.heartbeat_display_count + 1):
            room_label_map[f"OR{index:02d}"] = f"lbl_OR_Heartbeat_{index}"
        return room_label_map

    def apply_heartbeat_label_visibility(self):
        for index in range(1, 14):
            label = self.get_heartbeat_label(index)
            if not label:
                continue

            if index <= self.heartbeat_display_count:
                label.show()
            else:
                label.clear()
                label.hide()

    # ================================房間心跳監控================================
    def update_room_heartbeat_status(self):
        """
        定期查詢房間心跳狀態，並更新 GUI 標籤的顏色
        綠色 (線上): 距離最後心跳 < 10 秒
        灰色 (離線): 距離最後心跳 >= 10 秒
        """
        try:
            # 查詢所有房間的在線狀態
            all_rooms = self.task_db_manager.get_all_rooms_online_status()
            
            # 依照設定檔決定要顯示哪些 heartbeat 標籤
            room_label_map = self.get_heartbeat_room_label_map()
            
            # 更新 GUI 標籤
            for room in all_rooms:
                room_id = room['room_id']
                is_online = room['is_online']
                error_status = room.get('error_status')  # 獲取異常狀態
                
                # 如果房間 ID 存在於標籤映射中，更新對應的標籤
                if room_id in room_label_map:
                    label_name = room_label_map[room_id]
                    
                    # 嘗試取得標籤物件
                    # 使用 getattr 來動態取得屬性（UI 標籤）
                    try:
                        label = getattr(self, label_name, None)
                        if label:
                            # 從房間 ID 提取房間號 (例如 'OR01' → '01')
                            room_number = room_id[2:] if room_id.startswith('OR') else room_id

                            if error_status:
                                label.setStyleSheet(self._heartbeat_label_qss("#C06A00", "#FD7E14"))
                                label.setText(f"{room_number}\n異常")
                                continue
                            if is_online:
                                label.setStyleSheet(self._heartbeat_label_qss("#1F8A4D", "#28A745"))
                                label.setText(f"{room_number}\n線上")
                                continue
                            label.setStyleSheet(self._heartbeat_label_qss("#5A6573", "#6C757D"))
                            label.setText(f"{room_number}\n離線")
                            continue
                            
                            # 設定標籤的樣式（背景白色，用文字和邊框顏色表示狀態）
                            # 優先級: 異常 > 離線 > 在線
                            if error_status:  # 異常 - 橙色
                                label.setStyleSheet(
                                    "color: #fd7e14; "  # 橙色文字
                                    "font-size: 16px; "
                                    "background-color: white; "  # 白色背景
                                    "border: 2px solid #fd7e14; "
                                    "border-radius: 5px; "
                                    "padding: 4px;"
                                )
                                # label.setText(f"{room_number} 🟠 {error_status}")
                                label.setText(f"{room_number} 🟠 異常")
                            elif is_online:  # 在線 - 綠色
                                label.setStyleSheet(
                                    "color: #28a745; "  # 綠色文字
                                    "font-size: 16px; "
                                    "background-color: white; "  # 白色背景
                                    "border: 2px solid #28a745; "
                                    "border-radius: 5px; "
                                    "padding: 4px;"
                                )
                                label.setText(f"{room_number} 🟢 線上")
                            else:  # 離線 - 灰色
                                label.setStyleSheet(
                                    "color: #6c757d; "  # 灰色文字
                                    "font-size: 16px; "
                                    "background-color: white; "  # 白色背景
                                    "border: 2px solid #6c757d; "
                                    "border-radius: 5px; "
                                    "padding: 4px;"
                                )
                                label.setText(f"{room_number} 離線")
                        else:
                            # 標籤不存在，可能是還沒有添加到 UI 中
                            pass
                    except AttributeError:
                        # 標籤還未在 UI 中定義，跳過
                        pass
                        
        except Exception as e:
            print(f"❌ 更新房間心跳狀態失敗: {e}")


    # ================================ API 狀態監視 =================
    def monitor_or_mir_api_status(self):
        try:
            status = functions.check_api_status_v3()
            self._print_mission_text(status)
            # 如果之前有 API 錯誤狀態，現在恢復了，就清除 DB 中的錯誤標記
            if self.api_error:
                self.task_db_manager.clear_room_error("MASTER")
                self.api_error = False
        except Exception:
            # 如果 API 錯誤狀態，就在 DB 中標記
            if not self.api_error:
                self.task_db_manager.mark_room_error("MASTER", "API_ERROR")
                self.api_error = True


    
    
    ##################################按鈕############################################
    # 按鈕(取得等待任務名字) #暫時停用
    def on_get_pending_mssion_clicked(self):
        pm_names = functions.get_pending_mission_names()
        if pm_names:
            self.txtEdit_GetPM.setPlainText("\n".join(pm_names))
        else:
            self.txtEdit_GetPM.setPlainText("No pending missions")


    # 按鈕(取得當前任務狀態)
    def on_update_info_clicked(self):
        status_info = functions.check_MiR_status()
        #轉換成「格式化的 JSON 字串」，用來方便顯示（indent=4 表示用四個空格縮排）
        status_info_str = json.dumps(status_info, indent = 4) 
        self.plntxtEdit_Info.setPlainText(status_info_str)
        state_ID = status_info.get("state_id")
        self.current_mir_state_id = state_ID
        self.current_mission_text = status_info.get("mission_text", self.current_mission_text)
        self._update_status_label(state_ID)
        
        
    # 按鈕(回去充電站)
    def on_start_chargestation_clicked(self):
        # 先拿到「本場域定義的充電站顯示名稱」，
        # 再反查對應的 MiR position name 後送出。
        charge_code = self.MIR_LOCATION_MAP.get(self.CHARGING_STATION_NAME)
        if charge_code:
            functions.run_combo_location(charge_code)
            print(f"✅ 已送出任務到充電站代碼: {charge_code}")
        else:
            QMessageBox.critical(
                self,
                "錯誤！",
                f"🚨 請檢查場域設定是否有定義充電站: {self.CHARGING_STATION_NAME}",
            )
            
            
            

    # 按鈕(重製任務狀態)
    def on_reset_status_clicked(self):
        functions.clear_MiR_error()

    
    # 按鈕(前往地圖位置) 
    def on_map_location_clicked(self):
        """
        這個函式現在只負責啟動任務排程執行緒。
        原來的 while 迴圈邏輯已經移到 self.task_thread.run() 中了。
        """
        self.btn_StartMission.setDisabled(True)
        self.btn_StopMission1.setDisabled(False)
        self.btn_SentRobotTo.setEnabled(False)
        
        # 判斷執行緒是否已經在運行
        if not self.task_thread.isRunning():
            # 確保旗標為 True，以啟動執行緒中的 while 迴圈
            self.task_thread.is_running = True 
            
            # ⭐ 關鍵：啟動執行緒，這會執行 TaskThread 類別中的 run() 函式
            self.task_thread.start() 
            
            # 可以在 UI 上顯示一個訊息，告訴使用者排程器已啟動
            print("任務排程已開始執行...")
            # 或是 self.update_log_ui("任務排程已開始執行...")
        else:
            print("任務排程已在運行中，請勿重複啟動。")

        # 原版while迴圈執行任務暫時沒用到
        '''
        self.is_running=True
        while self.is_running:
            # 呼叫 TaskDBManager 取得最高優先權任務
            # priority_tasks = [{'id': 7, 'sequence': 7, 'start_point': '櫃台', 'target_point': '實驗室C', 'mission_content': '運送文件', 'status': 'Pending'}]
            priority_tasks = self.task_db_manager.get_highest_priority_task()
            if priority_tasks is None:
                self.is_no_mission=True
                while self.is_no_mission:
                    # 命令AMR去充電站(需coding) 1010
                    self.on_start_chargestation_clicked()
                    time.sleep(0.1)
                    QApplication.processEvents()  # ✅ 強制刷新 UI   
                    if self.is_running==False:
                        # 命令AMR去充電站(需coding) 1010
                        self.on_start_chargestation_clicked()
                        break
                    priority_tasks = self.task_db_manager.get_highest_priority_task()
                    if priority_tasks is not None:
                        self.is_no_mission=False
                        break
            
            mir_code_id = priority_tasks[0]['id']
            mir_code_s = priority_tasks[0]['start_point']
            mir_code_d = priority_tasks[0]['target_point']      
            mir_code = priority_tasks[0]['mission_content']

            mir_code_s = MIR_LOCATION_MAP.get(mir_code_s)
            mir_code_d = MIR_LOCATION_MAP.get(mir_code_d)
            mir_code = MIR_MISSION_GROUP_MAP.get(mir_code)

            # mir_code_s = self.cmb_location2.currentData()
            # mir_code_d = self.cmb_location.currentData()
            # mir_code = self.cmb_mission.currentData()
            charge_code = MIR_LOCATION_MAP.get(CHARGING_STATION_NAME)

            if "Charge" in mir_code_d:
                if mir_code and mir_code_s and mir_code_d:
                    # functions.run_combo_location(mir_code)
                    functions.run_combo_location_multi_var(mir_code_s,mir_code_d,mir_code)
                    self.task_db_manager.update_task_status(mir_code_id, new_status="Executing", command_sent=True)

                    # ⭐ 關鍵修正點 1：發送任務後，AMR 狀態應為忙碌 (False)
                    self.is_AMR_idle = False 

                    functions.run_combo_location(charge_code)
                    print(f"✅ 已送出前往任務到 MiR 代碼: {mir_code}")
                else:
                    # 處理沒有選中任何選項的情況
                    print("❌ 地點或對應代碼無效。")
            else:
                if mir_code and mir_code_s and mir_code_d:
                    # functions.run_combo_location(mir_code)
                    print(mir_code_s,mir_code_d,mir_code)
                    functions.run_combo_location_multi_var(mir_code_s,mir_code_d,mir_code)
                    self.task_db_manager.update_task_status(mir_code_id, new_status="Executing", command_sent=True)

                    # ⭐ 關鍵修正點 2：發送任務後，AMR 狀態應為忙碌 (False)
                    self.is_AMR_idle = False 

                    print(f"✅ 已送出前往任務到 MiR 代碼: {mir_code}")
                else:
                    # 處理沒有選中任何選項的情況
                    print("❌ 地點或對應代碼無效。")
            QApplication.processEvents()  # ✅ 強制刷新 UI

            # 等待前一任務完成 1010
            print("等待任務完成....")
            while not self.is_AMR_idle:
                time.sleep(0.1)
                QApplication.processEvents()  # ✅ 強制刷新 UI   

            if self.is_running==False:
                # 命令AMR去充電站(需coding) 1010
                self.on_start_chargestation_clicked()
                break       

            if self.is_low_battery:
                time.sleep(0.1)
                # 命令AMR去充電站(需coding) 1010
                self.on_start_chargestation_clicked()
                while self.is_low_battery:
                    time.sleep(0.1)
                    QApplication.processEvents()  # ✅ 強制刷新 UI     
        '''  
        
    # 按鈕(中斷執行中與等待任務)
    def on_stop_mission_clicked(self):
        self.btn_StartMission.setDisabled(False)
        self.btn_StopMission1.setDisabled(True)
        self._update_sent_robot_to_button_state()
        # 不要馬上停止
        # functions.stop_the_mission()
        # 2. 停止排程執行緒
        # 這裡必須呼叫 TaskThread 實例的 stop() 方法，讓它安全退出 run() 迴圈。
        # 程式碼是在執行動作前，對您的執行緒實例進行三次連續的安全檢查，這是專業的 Python 程式設計中，處理執行緒和類別實例時的標準做法
        if hasattr(self, 'task_thread') and self.task_thread and self.task_thread.isRunning():  
            # TaskThread.stop() 內部會將 self.is_running 設為 False
            self.task_thread.stop() 
            # self.log_message.emit("🛑 收到中斷指令，排程執行緒正在停止...")
        self.task_db_manager._resequence_pending_tasks()
            
        
     # 按鈕(執行特定任務) 
    def on_start_mission_clicked(self):
        # 取得任務ID(GUID)
        mission_guid = functions.get_mission_id(self.cmb_mission.currentText())
        functions.start_the_mission(mission_guid)
    
    # 按鈕(執行相對移動任務)
    def on_relative_move_clicked(self):
        x = self.dsb_x.value()
        y = self.dsb_y.value()
        ori = self.dsb_ori.value()
        mission_guid = functions.get_mission_id(self.cmb_mission.currentText())
        functions.run_relative_move(mission_guid,x,y,ori)

    # 按鈕(輸入ip)
    def on_save_ip_clicked(self):
        """
        處理儲存 IP 按鈕的點擊事件。
        負責：清理輸入、驗證 IP 格式、測試 API 連線，並在成功時儲存 IP 設定。
        """
        # 1. 取得與清理輸入
        # 去除輸入字串開頭與結尾的空白字元
        IP = self.lineEdit_IP.text().strip()
        try:
            # 2. 移除協議頭 (若存在)
            # 如果使用者輸入了完整的 "http://" 協議頭，將其移除，只保留 IP 或域名
            if IP.startswith("http://"):
                IP = IP[7:]
            # 3. IP 格式驗證
            # 嘗試將字串解析為有效的 IP 位址 (IPv4 或 IPv6)。
            # 如果格式錯誤，會拋出 ValueError。
            ipaddress.ip_address(IP)
            # 4. 建立全域 IP 變數 (純 IP 和完整 URL)
            functions.MIR_IP = IP                # 儲存純 IP/域名 到全域變數
            full_ip = f"http://{IP}"             # 建立帶有 http:// 的完整 URL
            functions.Full_IP = full_ip          # 儲存完整 URL 到全域變數
            # 5. 連線狀態測試
            # 呼叫外部函式，檢查此 IP 的 API 是否可連線 (例如 MiR 機器人)
            test_url = functions.check_api_status_v2()
            # 6. 處理測試結果
            if test_url == 0:
                # 連線成功
                functions.save_ip(full_ip)       # ✅ 寫入檔案，作為下次啟動的預設 IP
                functions.MIR_IP = full_ip       # ✅ 即時更新全域變數，使程式立即使用新 IP
                print("成功儲存 IP:", full_ip)
            elif test_url == 1:
                # 連線失敗
                self.show_error(f"無法連線到車子") # 顯示錯誤訊息給使用者
        except ValueError:
            # 格式錯誤處理
            # 如果 ipaddress.ip_address(IP) 失敗，表示格式無效
            print("無效的 IP 格式")
            # 這裡可以加上 self.show_error("無效的 IP 格式") 提醒使用者

    # 按鈕(IO_Module UP)
    def on_up_io_clicked(self):
        functions.set_lift_position(True)

    # 按鈕(IO_Module Down) 
    def on_down_io_clicked(self):
        functions.set_lift_position(False)

    # 按鈕(Sent robot to go)
    def on_sent_robot_to_clicked(self):
        if self.sent_robot_to_in_progress:
            print("Sent robot to 導航尚未完成，暫不接受第二次送車。")
            return

        X=self.dsb_x_m.value()
        Y=self.dsb_y_m.value()
        Z=self.dsb_ori_m.value()
        print(f"派送車子到:{X},{Y},{Z}")
        self.sent_robot_to_in_progress = True
        self._update_sent_robot_to_button_state()
        functions.post_position(X,Y,Z)
        self.load_map_positions()
        functions.run_combo_location("Sent robot to")
        self.query_mir_status()

    def open_map_selector(self, target_dropdown):
        """
        開啟地圖選擇視窗，並動態連接到目標下拉式選單。
        """
        # 確保解除舊的連接
        try:
            self.map_dialog.location_selected.disconnect()
        except TypeError:
            pass

        # 建立一個臨時的 lambda 槽函數，lambda 在這裡的作用就是一個轉接頭，接收訊號自動傳遞的 location_name，將收到的 location_name和我們在外部已經知道的 target_dropdown 一起傳遞進去。
        self.map_dialog.location_selected.connect(
            lambda location_name: self._set_current_dropdown_value(location_name, target_dropdown)
        )

        # 顯示重用的單一實例
        self.map_dialog.show()
        # 激活隱藏的視窗
        self.map_dialog.activateWindow()

    def _set_current_dropdown_value(self, location_name, target_dropdown):
        """
        通用的槽函數：將 SelectedMap 傳回的值設定到指定的 target_dropdown。
        """

        # 尋找該地點名稱在下拉式選單中的索引位置
        index = target_dropdown.findText(location_name)

        if index != -1:
            # ✅ 如果地點存在 (index 不是 -1)，則設定為當前選項
            target_dropdown.setCurrentIndex(index)
            print(f"下拉式選單 ({target_dropdown.objectName()}) 已成功設定為: {location_name}")
        else:
            print(f"錯誤：'{location_name}' 不存在於目標選單中。")




    ##################################勾選框############################################
    
    # 地圖點擊啟用勾選
    def toggle_click_mode_map(self,state):
        print("state =", state)
        self.clicked_enabled = (state == 2)
        if state == 2:
            self._update_sent_robot_to_button_state()
        else:
            self.clear_click_marker()
            self.btn_SentRobotTo.setEnabled(False)
        print(self.clicked_enabled)
        print("點擊模式已", "啟用" if self.clicked_enabled else "關閉")


    ##################################下拉式選單############################################

   

    # # 取得地圖名字
    # def load_map_positions(self):
    #     self.cmb_location.clear()
    #     self.cmb_location2.clear()

    #     # 獲取 MiR 系統回傳的所有英文代碼列表
    #     mir_codes_list = functions.get_curmaps_positions_cmb() 

    #     user_names_list = []
    #     # print("--- 字典 Key 對應診斷 ---")
    #     # print("MiR 傳回的代碼列表:", mir_codes_list)

    #     if mir_codes_list:
    #         for mir_code in mir_codes_list:

    #             # 查找中文名稱，如果找不到，就顯示原始的英文代碼
    #             # 字典名稱.get(Key,Default Value)。A (第一個參數)，Python 會嘗試將這個值作為 Key 去字典裡查找。B (第二個參數)，如果找不到 Key 的值，則返回這個預設值
    #             user_name = USER_LOCATION_MAP.get(mir_code, mir_code)

    #             # 關鍵步驟：addItem(顯示中文, 隱藏英文代碼)
    #             self.cmb_location.addItem(user_name, mir_code)
    #             self.cmb_location2.addItem(user_name, mir_code)

    #             user_names_list.append(user_name)
    #             # 自動補完器
    #             completer = QCompleter(user_names_list)
    #             # ✅ 不分大小寫
    #             completer.setCaseSensitivity(Qt.CaseInsensitive)
    #             self.cmb_location.setCompleter(completer) 
    #             self.cmb_location2.setCompleter(completer) 

    # 改英文、中文、數字排序
    def load_map_positions(self):
        # 1. 初始化下拉式選單
        self.cmb_location.clear()
        self.cmb_location2.clear()

        # 獲取 MiR 系統回傳的所有英文代碼列表
        mir_codes_list = functions.get_curmaps_positions_cmb() 
        # 用於儲存最終要加入選單的 (中文名稱, 英文代碼) 數據
        combo_data_list = []
        # 用於檢查重複的中文名稱，以確保每個地理位置只出現一次
        unique_user_names = set() 
        
        if mir_codes_list:
            for mir_code in mir_codes_list:
                # 名稱轉換，查找中文名稱，如果找不到，就顯示原始的英文代碼
                user_name = self.USER_LOCATION_MAP.get(mir_code, mir_code)
                # --- 關鍵去重邏輯 ---
                if user_name not in unique_user_names:
                    unique_user_names.add(user_name)
                    # 將 (中文名稱, 原始英文代碼) 組合成元組，加入列表準備排序
                    combo_data_list.append((user_name, mir_code))

            # --- 2. 排序邏輯 ---
            # 依據元組的第一個元素 (中文名稱/user_name) 進行排序
            # Python 預設的字串排序適用於中文/英文/數字的字典序
            sorted_combo_data = sorted(combo_data_list, key=lambda x: x[0])

            # --- 3. 重新建立下拉式選單和自動補完器 ---
            
            user_names_list = [] # 用於自動補完器的列表
            for user_name, mir_code in sorted_combo_data:
                # 關鍵步驟：addItem(顯示中文, 隱藏英文代碼)
                self.cmb_location.addItem(user_name, mir_code)
                self.cmb_location2.addItem(user_name, mir_code)

                user_names_list.append(user_name)

            # --- 4. 設置自動補完器 ---
            if user_names_list: # 確保列表非空
                # 創建第一個 Completer 實例
                completer1 = QCompleter(user_names_list)
                completer1.setCaseSensitivity(Qt.CaseInsensitive)
                
                # 創建第二個 Completer 實例
                completer2 = QCompleter(user_names_list)
                completer2.setCaseSensitivity(Qt.CaseInsensitive)
                
                # 將獨立的 Completer 設置給各自的 ComboBox
                self.cmb_location.setCompleter(completer1) 
                self.cmb_location2.setCompleter(completer2)
            # ⭐ 同步到資料庫
            self.task_db_manager.sync_ui_locations(sorted_combo_data)
                
    # 取得全部任務名字
    def load_mission_positions(self):
        self.cmb_mission.clear()
        names = functions.get_mission_id_cmb()
        if names:
            self.cmb_mission.addItems(names)
            completer = QCompleter(names)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.cmb_mission.setCompleter(completer)

    # 取得分類後的每個任務名稱by Mission_groups
    def load_mission_groups_positions(self):
        self.cmb_mission.clear()

        user_names_list = []
        combo_data_list = []   # ⭐ 新增：準備給 DB 的資料

        # 獲取 MiR 系統回傳的所有英文代碼列表
        mir_codes_list = functions.get_mission_groups_id_cmb()

        # print("--- 字典 Key 對應診斷 ---")
        # print("MiR 傳回的代碼列表:", mir_codes_list)

        if mir_codes_list:
            for mir_code in mir_codes_list:

                # 【篩選步驟】：只處理你想要的兩種任務代碼
                if mir_code in self.REQUIRED_MISSION_CODES:

                    # 1. 翻譯：使用你的字典來獲取中文名稱 (Value)
                    # 字典名稱.get(Key,Default Value)。
                    # A (第一個參數)，Python 會嘗試將這個值作為 Key 去字典裡查找；B (第二個參數)，如果找不到 Key 的值，則返回這個預設值
                    user_name = self.USER_MISSION_GROUP_MAP.get(mir_code, mir_code)
                    
                    # 2. 載入 ComboBox (加蓋)
                    # 顯示給使用者看中文 (user_name)，隱藏 MiR 英文代碼 (mir_code)
                    self.cmb_mission.addItem(user_name, mir_code)

                    user_names_list.append(user_name)

                    # ⭐ 關鍵：收集資料（跟 map 一樣格式）
                    combo_data_list.append((user_name, mir_code))

            
            # 自動補完器
            completer = QCompleter(user_names_list)
            # ✅ 不分大小寫
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.cmb_mission.setCompleter(completer) 

            # ⭐⭐ 核心：同步到 DB（照抄 map）
            self.task_db_manager.sync_ui_missions(combo_data_list)

       
 

    ##################################仿射矩陣演算法&畫車位置############################################

    '''根據三個點建立仿射矩陣'''
    def compute_affine_transform(self):
        # A 是 3 個世界座標點，加上一列常數 1，組成 3x3 矩陣
        # 每列為一個點：[x, y, 1]，準備進行仿射轉換
        A = np.hstack([self.world_pts, np.ones((3, 1))])  # world_pts 是 (3x2)，加上 (3x1) → 得到 (3x3)
        # B 是對應的 3 個圖片座標點，每列為一個點：[pixel_x, pixel_y]，共 (3x2)
        B = self.image_pts                                
        # 解 A @ X ≈ B 的最小平方法問題，找出最符合的仿射轉換矩陣 X（3x2）
        # lstsq：least squares 最小平方法 → 會自動幫我們找出誤差最小的解 X
        X, _, _, _ = np.linalg.lstsq(A, B, rcond=None)
        # 回傳 X，就是我們算出來的仿射轉換矩陣（shape 是 3x2）
        return X  # 3x2 矩陣
    
    '''將 MiR 世界座標轉換成圖片像素座標'''
    def world_to_image(self, world_x, world_y):
        # 將輸入的世界座標(x, y) 組成一個向量 [x, y, 1]，shape 是 (1x3)
        input_vec = np.array([world_x, world_y, 1.0])  # 1x3
        # 用仿射矩陣做矩陣乘法，把世界座標轉換成對應的圖片座標 (1x2)
        pixel = input_vec @ self.affine_matrix         # 等同於 np.dot(input_vec, affine_matrix)
        # 回傳轉換後的圖片座標（四捨五入為整數像素位置）
        return int(pixel[0]), int(pixel[1])
    

    '''將 MiR 圖片像素座標轉換成世界座標'''
    def image_to_world(self,pixel_x,pixel_y):
        # 將原本 3x2 的 affine_matrix 補成 3x3，加入 [0, 0, 1] 這一列
        affine_3x3 = np.vstack([self.affine_matrix.T, [0, 0, 1]])  # shape = (3, 3)
        # 計算反矩陣
        inv_affine = np.linalg.inv(affine_3x3)  # shape = (3, 3)
        # 點擊的像素位置向量 [x, y, 1]
        pixel_vec = np.array([pixel_x, pixel_y, 1.0])
        # 做反轉換，取得世界座標
        world_coord = inv_affine @ pixel_vec
        return float(world_coord[0]), float(world_coord[1])
    
    # 畫出車子位置
    def draw_car_position_backup(self,x,y):
        x, y = self.world_to_image(x,y)

        pixmap = self.original_pixmap.copy()
        painter = QPainter(pixmap)

        # ... 設置畫筆 (pen) ...
        pen = QPen(QColor("red"))
        pen.setWidth(6)
        painter.setPen(pen)

        # ... 繪製圓點 ...
        radius = 3
        painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
        painter.end()
        self.label_map_1.setPixmap(pixmap)

    def draw_click_marker(self, painter, x, y):
        marker_color = QColor(0, 220, 255)
        marker_pen = QPen(marker_color)
        marker_pen.setWidth(3)
        painter.setPen(marker_pen)

        radius = 8
        painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
        painter.drawLine(x - 12, y, x + 12, y)
        painter.drawLine(x, y - 12, x, y + 12)

    def is_robot_in_motion_state(self):
        return self.current_mir_state_id in {5, 9}

    def draw_robot_marker(self, painter, x, y):
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self.is_robot_in_motion_state():
            glow_alpha = 120 + (self.robot_glow_phase % 3) * 35
            glow_pen = QPen(QColor(57, 255, 20, glow_alpha))
            glow_pen.setWidth(6)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(x - 18, y - 18, 36, 36)

        body_rect = QRect(x - 11, y - 9, 22, 18)
        painter.setPen(QPen(QColor("#0B1F33"), 2))
        painter.setBrush(QColor("#E84C3D"))
        painter.drawRoundedRect(body_rect, 5, 5)

        painter.setBrush(QColor("#DFF6FF"))
        painter.drawRoundedRect(QRect(x - 6, y - 6, 12, 7), 2, 2)

        painter.setBrush(QColor("#2F3B45"))
        painter.drawEllipse(x - 9, y + 6, 5, 5)
        painter.drawEllipse(x + 4, y + 6, 5, 5)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FFD166"))
        painter.drawEllipse(x - 13, y - 2, 4, 4)
        painter.drawEllipse(x + 9, y - 2, 4, 4)

    def draw_car_position(self, world_x, world_y):
        # 確保兩個 QLabel 的位置和尺寸對齊 (雖然尺寸不同，但它們必須重疊)
        # self.label_car_overlay.setGeometry(self.label_map_1.geometry())
        # self.label_car_overlay.raise_() 
        
        # 1. 轉換到原始地圖影像 (706x469) 的像素座標
        x_orig, y_orig = self.world_to_image(world_x, world_y) 
        
        # --- 縮放校準開始 ---
        
        # 2. 原始地圖尺寸 (仿射矩陣的座標系)
        # orig_width = 706  
        # orig_height = 469 

        orig_width = max(1, self.original_pixmap.width())
        orig_height = max(1, self.original_pixmap.height())

        # 3. 繪圖畫布的當前尺寸 (self.label_car_overlay 的尺寸)
        current_width = self.label_car_overlay.width() # 應該是 1072
        current_height = self.label_car_overlay.height() # 應該是 608

        # 4. 計算縮放比例
        scale_x = current_width / orig_width  # 1072 / 706 ≈ 1.518
        scale_y = current_height / orig_height # 608 / 469 ≈ 1.296

        # 5. 校準座標 (將原始像素座標映射到實際顯示區域)
        # 注意：這裡假設地圖是被拉伸來填滿 1072x608 的 QLabel
        x_final = int(x_orig * scale_x)
        y_final = int(y_orig * scale_y)
        
        # --- 縮放校準結束 ---
        
        # 6. 繪圖
        # 繪圖畫布的尺寸必須和疊圖層的尺寸一致！
        pixmap = QPixmap(self.label_car_overlay.size()) # 尺寸為 1072x608
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        self.draw_robot_marker(painter, x_final, y_final)
        if self.last_click_overlay_pos is not None:
            click_x, click_y = self.last_click_overlay_pos
            self.draw_click_marker(painter, click_x, click_y)

        painter.end()
        
        self.label_car_overlay.setPixmap(pixmap)

    def clear_click_marker(self):
        self.last_click_overlay_pos = None
        if self.last_robot_world_pos is not None:
            self.draw_car_position(*self.last_robot_world_pos)
        else:
            self.label_car_overlay.clear()

    # 更新MiR位置
    def update_robot_position(self,world_x,world_y):
        # 畫在地圖上
        self.last_robot_world_pos = (world_x, world_y)
        self.draw_car_position(world_x,world_y)

    # 自動取得當前MiR車子位置
    def poll_mir_position(self):
        world_x,world_y= functions.check_MiR_status_position()
        # print(f"目前位置：{world_x,world_y}")
        self.update_robot_position(world_x,world_y)

    ##################################跳出錯誤訊息############################################
    def show_error(self,msg):
        #print("我是 QWidget 嗎？", isinstance(self, QWidget))
        QMessageBox.critical(None,"連線錯誤",msg)
    
    
    '''
    # 偵測滑鼠點擊圖片位置       
    def mousePressEvent(self, event: QMouseEvent): 
            widget = self.childAt(event.pos())  # 取得點擊位置的元件
            if not self.clicked_enabled and widget is self.label_map_1:
                print("尚未啟用點擊模式")
                return
            if widget is self.label_map_1:  # 檢查是否是 QLabel
                relative_pos = self.label_map_1.mapFrom(self, event.pos())
                x = relative_pos.x()/1.48
                y = relative_pos.y()/1.26
                world_x, world_y = self.image_to_world(x, y)
                self.dsb_x_m.setValue(world_x)
                self.dsb_y_m.setValue(world_y)
                print(world_x,world_y)
                # -5.397, 7.455
                # world_x8, world_y8 = self.image_to_world(219, 651)
                # world_x9, world_y9 = self.world_to_image(world_x8,world_y8)
                # print(world_x8, world_y8)
                # print(world_x9, world_y9)
                print(f"你點了圖片座標 ({x:.1f}, {y:.1f})，對應世界座標為 ({world_x:.2f}, {world_y:.2f})")
            super().mousePressEvent(event)
    '''

    def mousePressEvent(self, event: QMouseEvent):
        """
        處理滑鼠按下事件。
        優先序： 1. 標題列拖曳 > 2. 地圖圖片點擊 > 3. 預設處理
        """

        # 取得點擊位置的元件
        widget = self.childAt(event.pos())
        
        # 1. 處理客製化標題列拖曳邏輯 (優先處理)
        
        # 檢查點擊是否在 CustomTitleFrame 本身，或其子元件上 (例如 QLabel 或按鈕)
        if widget and (widget.objectName() == "CustomTitleFrame" or widget.parentWidget() is self.titleBarFrame):
            
            # 確保點擊的不是控制按鈕 (如果有加入 check_button_clicked 邏輯，可以在這裡過濾)
            # 為了簡化，我們先假設點擊 titleBarFrame 區域就開始拖曳
            if event.button() == Qt.LeftButton and not self.isMaximized():
                # 計算拖曳起始點
                self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return # 拖曳事件已處理
        
        # 2. 處理原有的 地圖圖片點擊 邏輯 (只在點擊 self.label_map_1 時觸發)
        # 假設 self.clicked_enabled, self.label_map_1, self.image_to_world, self.dsb_x_m, self.dsb_y_m 都已存在
        if widget is self.label_map_1:
            
            # 檢查點擊模式是否啟用
            if not self.clicked_enabled:
                print("尚未啟用點擊模式")
                event.accept()
                return
                
            # 進行座標轉換和設定值
            relative_pos = self.label_map_1.mapFrom(self, event.pos())
            # 請保留您原有的縮放係數 (1.48 和 1.26)
            scale_x, scale_y = self._get_main_map_scale()
            x = relative_pos.x() / scale_x
            y = relative_pos.y() / scale_y
            world_x, world_y = self.image_to_world(x, y)
            
            self.dsb_x_m.setValue(world_x)
            self.dsb_y_m.setValue(world_y)

            self.last_click_overlay_pos = (relative_pos.x(), relative_pos.y())
            if self.last_robot_world_pos is not None:
                self.draw_car_position(*self.last_robot_world_pos)
            else:
                marker_pixmap = QPixmap(self.label_car_overlay.size())
                marker_pixmap.fill(Qt.transparent)
                marker_painter = QPainter(marker_pixmap)
                self.draw_click_marker(marker_painter, relative_pos.x(), relative_pos.y())
                marker_painter.end()
                self.label_car_overlay.setPixmap(marker_pixmap)
            
            print(f"{world_x}, {world_y}")
            print(f"你點了圖片座標 ({x:.1f}, {y:.1f})，對應世界座標為 ({world_x:.2f}, {world_y:.2f})")
            
            event.accept()
            return # 地圖點擊事件已處理

        # 3. 呼叫父類別方法
        # 如果以上所有客製化邏輯都沒有處理該事件，則交給 QMainWindow 預設處理
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """處理滑鼠移動事件：實際移動視窗。"""
        # 檢查是否按著左鍵 並且 已經有拖曳起點 並且 不是最大化狀態
        if event.buttons() == Qt.LeftButton and not self._drag_position.isNull() and not self.isMaximized():
            # 移動視窗到新的位置: 全域滑鼠位置 - 拖曳起點
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """處理滑鼠釋放事件：清除拖曳起點。"""
        if event.button() == Qt.LeftButton and not self._drag_position.isNull():
            self._drag_position = QPoint()
            event.accept()
        else:
            super().mouseReleaseEvent(event)




# main.py (程式進入點)

DB_CONFIG = {
        'user': 'postgres',
        'host': 'localhost',
        'database': 'military_mir250_project',
        'password': '123456',
        'port': 5432
    }

if __name__ == "__main__":
    
    # 假設 DB_CONFIG 已經定義好
    # DB_CONFIG = {...} 

    # 1. 🚨 初始化 UserDBManager 實例
    user_db_manager = UserDBManager(DB_CONFIG)
    if not user_db_manager.connect():
        QMessageBox.critical(None, "錯誤", "無法連線到使用者資料庫，應用程式將關閉。")
        sys.exit(1)
    user_db_manager.initialize_user_table() # 只初始化一次 admin 帳號 
    
    # 2. 初始化任務資料庫管理器 (用於 MainWindow 的表格)
    task_db_manager = TaskDBManager(DB_CONFIG)
    if not task_db_manager.connect():
        QMessageBox.critical(None, "錯誤", "無法連線到任務資料庫，應用程式將關閉。")
        # 這裡可以選擇 sys.exit(1) 或繼續，看任務資料庫是否為核心功能
        sys.exit(1)
    
    # 3. 啟動應用程式
    
    app = QApplication(sys.argv)

    # 4. 🚨 將所有需要的 Manager 傳遞給 LoginWindow
    # LoginWindow 必須調整為接收 user_db_manager 和 task_db_manager
    login_win = LoginWindow(user_db_manager, task_db_manager) 
    login_win.show()
    
    # 5. 確保在程式關閉前關閉資料庫連線 (可選但推薦)
    app.aboutToQuit.connect(user_db_manager.close)
    app.aboutToQuit.connect(task_db_manager.close)
    
    sys.exit(app.exec())
 
   
