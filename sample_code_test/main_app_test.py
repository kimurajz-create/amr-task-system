import sys
import json
import hashlib
from pathlib import Path

# 引入 PySide6 核心元件
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QMessageBox, QListWidget, QInputDialog
)
from PySide6.QtCore import Qt

# 從轉換後的檔案中引入 UI 類別
# 注意：這裡假設您的轉換檔案名是 ui_login_window.py 和 ui_admin_panel.py
from ui_login_window import Ui_Form_LoginWindow
from ui_admin_panel import Ui_Form_AdminPanel

# ---------------- 編碼 ------------------- #
def hash_password(password: str) -> str:
    """將密碼進行 SHA256 編碼"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# ------------------ 設定 ------------------ #
USER_FILE = Path("users.json")
DEV_BACKDOOR_HASH = hash_password("Jordan@2025")

# ------------------ 資料存取 ------------------ #
def load_users():
    """讀取使用者資料"""
    if USER_FILE.exists():
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        users = {"admin": hash_password("admin123")}
        save_users(users)
        return users

def save_users(users):
    """儲存使用者資料"""
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

# ------------------ 登入視窗 ------------------ #
# LoginWindow 繼承 QWidget 和 Ui_Form_LoginWindow
class LoginWindow(QWidget, Ui_Form_LoginWindow): 
    def __init__(self):
        super().__init__()
        
        # 1. 呼叫 setupUi 來載入 Designer 中設計的所有元件
        self.setupUi(self) 
        
        # 2. 存取元件並綁定事件 (請務必確認 Designer 中的 objectName)
        
        # 根據您提供的截圖和慣例，元件名稱假設如下 (如果不同請自行修改)：
        # 帳號輸入框: self.lineEdit_username_input
        # 密碼輸入框: self.lineEdit_password_input
        # 登入按鈕: self.btn_login
        # 註冊說明按鈕: self.btn_register_info (此按鈕名稱需在 Designer 中確認)

        # 確保密碼輸入框是密文模式 (也可以在 Designer 中設定)
        self.lineEdit_password_input.setEchoMode(QLineEdit.Password)

        # --- 載入資料 & 綁定事件 ---
        self.users = load_users()
        self.btn_login.clicked.connect(self.login)
        # 假設註冊說明按鈕名稱是 self.btn_register_info
        # 如果您的 UI 中沒有此按鈕，請註解或刪除下面這行
        # self.btn_register_info.clicked.connect(self.show_register_info) 


    def login(self):
        """登入檢查"""
        username = self.lineEdit_username_input.text().strip()
        password = self.lineEdit_password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "錯誤", "請輸入帳號與密碼！")
            return

        hashed = hash_password(password)
        # 開發者後門檢查
        if username == "admin" and hashed == DEV_BACKDOOR_HASH:
            QMessageBox.information(self, "維護登入", "使用開發者後門登入成功。")
            self.close()
            self.open_admin_panel("admin")
            return

        # 一般使用者檢查
        if username in self.users and self.users[username] == hashed:
            QMessageBox.information(self, "成功", f"歡迎回來，{username}！")
            self.close()
            if username == "admin":
                self.open_admin_panel(username)
            else:
                self.open_main_app(username)
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

    def open_main_app(self, username):
        self.main = MainApp(username)
        self.main.show()

    def open_admin_panel(self, username):
        self.admin_panel = AdminPanel(username)
        self.admin_panel.show()


# ------------------ 使用者主畫面 (未轉換 UI，保持原樣) ------------------ #
class MainApp(QWidget):
    def __init__(self, username):
        super().__init__()
        self.setWindowTitle("主系統")
        self.resize(300, 150)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"👋 歡迎登入：{username}"))
        self.setLayout(layout)


# ------------------ Admin 管理畫面 ------------------ #
# AdminPanel 繼承 QWidget 和 Ui_Form_AdminPanel
class AdminPanel(QWidget, Ui_Form_AdminPanel): 
    def __init__(self, username):
        super().__init__()
        self.setupUi(self) # <--- 呼叫 setupUi

        self.users = load_users()
        self.username = username
        
        # 根據您的截圖，元件名稱假設如下 (如果不同請自行修改)：
        self.user_list = self.listWidget_user
        
        # 設置管理者名稱顯示 (假設您有一個 QLabel 叫 label_cur_user)
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
        for u in self.users.keys():
            self.user_list.addItem(u)

    def add_user(self):
        username = self.lineEdit_new_user_input.text().strip()
        password = self.lineEdit_new_pass_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "錯誤", "請輸入帳號與密碼！")
            return
        if username in self.users:
            QMessageBox.warning(self, "重複", "該帳號已存在！")
            return

        self.users[username] = hash_password(password)
        save_users(self.users)
        self.refresh_user_list()
        QMessageBox.information(self, "成功", f"已新增使用者：{username}")
        self.lineEdit_new_user_input.clear()
        self.lineEdit_new_pass_input.clear()

    def delete_user(self):
        selected = self.user_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "錯誤", "請選擇要刪除的使用者！")
            return

        username = selected.text()
        if username == "admin":
            QMessageBox.warning(self, "禁止", "不能刪除 admin！")
            return

        del self.users[username]
        save_users(self.users)
        self.refresh_user_list()
        QMessageBox.information(self, "成功", f"已刪除使用者：{username}")

    def change_my_password(self):
        """讓 admin 修改自己的密碼"""
        
        # 彈出輸入框時設定密文模式 QLineEdit.Password
        old_pw, ok = QInputDialog.getText(self, "舊密碼驗證", "請輸入舊密碼：", QLineEdit.Password)
        if not ok or not old_pw:
            return
        if hash_password(old_pw) != self.users.get("admin"):
            QMessageBox.warning(self, "錯誤", "舊密碼錯誤！")
            return

        new_pw, ok = QInputDialog.getText(self, "新密碼", "請輸入新密碼：", QLineEdit.Password)
        if not ok or not new_pw:
            return

        self.users["admin"] = hash_password(new_pw)
        save_users(self.users)
        QMessageBox.information(self, "成功", "密碼已更新！")


# ------------------ 主程式進入點 ------------------ #
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 檢查轉換後的 .py 檔案是否存在
    if 'Ui_Form_LoginWindow' not in globals() or 'Ui_Form_AdminPanel' not in globals():
        QMessageBox.critical(None, "錯誤", "找不到轉換後的 UI 類別。請確認 'ui_login_window.py' 和 'ui_admin_panel.py' 存在且成功引入！")
        sys.exit(1)
        
    win = LoginWindow()
    win.show()
    sys.exit(app.exec())