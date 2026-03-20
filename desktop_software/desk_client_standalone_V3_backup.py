import functions
from desktop_TaskDBManager import TaskDBManager ,create_new_db_task
from ui_desk_client import Ui_MainWindow
from PySide6.QtWidgets import QApplication, QWidget
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

from desktop_config import (
    DB_CONFIG,
    USER_LOCATION_MAP,
    USER_MISSION_GROUP_MAP,
    REQUIRED_MISSION_CODES,
    ROOM_ID_MAP,
    POLL_INTERVAL,
    room_id,
    ENV,
    EXPECTED_DB_HOST
)

import ui_desk_client
print(ui_desk_client.__file__)

class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()

        self.env = ENV  # ⭐ 這就是你的環境
        self.check_env_safety()

        self.db_error = False   # ⭐ 加這行
        self.setupUi(self)
        self.setWindowTitle("台中國軍醫 MiR")

        # ===== 通知區 =====
        self.frame_notify.hide()
        self.btn_close_notify.clicked.connect(self.hide_notify)

        # ===== 任務監看 polling =====

        # 記錄狀態變化
        self.last_task_id = None
        self.last_status = None
        self.last_notified_task_id = None

        # 設定 MiR IP
        functions.MIR_IP = functions.load_ip()

        # 初始化 DB
        self.db_manager = TaskDBManager(DB_CONFIG)
        if not self.db_manager.connect():
            QMessageBox.critical(self, "錯誤", "無法連線到 PostgreSQL，請檢查 DB_CONFIG。")

        # 啟動時先顯示等待畫面
        self.hide_notify()

        # 初始化下拉式選單(撈取api)  
        self.load_map_positions()
        self.load_mission_groups_positions()

        # polling timer
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_room_status)
        self.poll_timer.start(POLL_INTERVAL)  # 每 2 秒查一次

        # ===== 下達任務區 =====

        # signals
        self.btn_add_task_db.clicked.connect(self.on_create_task_db_clicked)
        self.btn_delete_task_db.clicked.connect(self.on_delete_task_db_clicked)


    # ===== 通知區 =====
    def show_notify(self, title, message):

        self.lbl_notify_title.setText(title)
        self.lbl_notify_msg.setText(message)

        # 讓通知置中
        parent = self.frame_notify.parent()
        x = (parent.width() - self.frame_notify.width()) // 2
        y = (parent.height() - self.frame_notify.height()) // 2
        self.frame_notify.move(x, y)

        self.frame_notify.raise_()
        self.frame_notify.show()

        # QApplication.beep()


    def hide_notify(self):

        self.lbl_notify_title.setText("🚗 等待車輛")
        self.lbl_notify_msg.setText("等候通知....")

        self.frame_notify.show()



    # ===== 下拉式選單 =====
    def load_map_positions(self):
        # 1. 初始化下拉式選單
        self.cmb_start_point.clear()
        self.cmb_end_point.clear()

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_room_status)
        self.poll_timer.start(5000)  # 每2秒

        # 獲取 MiR 系統回傳的所有英文代碼列表
        mir_codes_list = functions.get_curmaps_positions_cmb() 
        # 用於儲存最終要加入選單的 (中文名稱, 英文代碼) 數據
        combo_data_list = []
        # 用於檢查重複的中文名稱，以確保每個地理位置只出現一次
        unique_user_names = set() 
        
        if mir_codes_list:
            for mir_code in mir_codes_list:
                # 名稱轉換，查找中文名稱，如果找不到，就顯示原始的英文代碼
                user_name = USER_LOCATION_MAP.get(mir_code, mir_code)
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
                self.cmb_start_point.addItem(user_name, mir_code)
                self.cmb_end_point.addItem(user_name, mir_code)

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
                self.cmb_start_point.setCompleter(completer1) 
                self.cmb_end_point.setCompleter(completer2)


     # 取得分類後的每個任務名稱by Mission_groups
    def load_mission_groups_positions(self):
        self.cmb_mission.clear()

        user_names_list = []

        # 獲取 MiR 系統回傳的所有英文代碼列表
        mir_codes_list = functions.get_mission_groups_id_cmb()

        # print("--- 字典 Key 對應診斷 ---")
        # print("MiR 傳回的代碼列表:", mir_codes_list)

        if mir_codes_list:
            for mir_code in mir_codes_list:

                # 【篩選步驟】：只處理你想要的兩種任務代碼
                if mir_code in REQUIRED_MISSION_CODES:

                    # 1. 翻譯：使用你的字典來獲取中文名稱 (Value)
                    # 字典名稱.get(Key,Default Value)。
                    # A (第一個參數)，Python 會嘗試將這個值作為 Key 去字典裡查找；B (第二個參數)，如果找不到 Key 的值，則返回這個預設值
                    user_name = USER_MISSION_GROUP_MAP.get(mir_code, mir_code)
                    
                    # 2. 載入 ComboBox (加蓋)
                    # 顯示給使用者看中文 (user_name)，隱藏 MiR 英文代碼 (mir_code)
                    self.cmb_mission.addItem(user_name, mir_code)

                    user_names_list.append(user_name)
            
            # 自動補完器
            completer = QCompleter(user_names_list)
            # ✅ 不分大小寫
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.cmb_mission.setCompleter(completer) 

    # ====== 開始任務 ======
    def on_create_task_db_clicked(self):
        start_place = self.cmb_start_point.currentText()
        destination = self.cmb_end_point.currentText()
        mission_content = self.cmb_mission.currentText()

        new_id = create_new_db_task(
            self.db_manager,
            start_place,
            destination,
            mission_content
        )

        if new_id:
            self.log(f"✅ 新增任務成功，DB ID: {new_id}")
            QMessageBox.information(self, "成功", f"新增任務成功，DB ID: {new_id}")
        else:
            self.log("❌ 新增任務失敗")
            QMessageBox.warning(self, "失敗", "新增任務失敗")

    # ===== 刪除任務 ======
    def on_delete_task_db_clicked(self):
       
        task_id = self.txt_delete_task_id.text()

        if not task_id:
            QMessageBox.warning(self, "錯誤", "請輸入 task id")
            return

        self.db_manager.delete_task(int(task_id))

        self.log(f"🗑 任務 {task_id} 已刪除")

    # ====== log ======
    def log(self, text):
        from datetime import datetime

        now = datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"[{now}] {text}")
    

    # ====== 每 n 秒查一次 ======
    def poll_room_status(self):

        try:
            task = self.db_manager.get_latest_task_for_room(room_id)

            if self.db_error:
                self.log("✅ 資料庫連線已恢復")
                self.db_error = False

        except Exception as e:

            if not self.db_error:
                self.log("⚠️ 資料庫連線異常，請確認網路")
                print("DB error:", e)
                self.db_error = True
            return
        
        # 1️⃣ 無任務控制
        # 若 DB 沒有任務，只在「從有任務 → 沒任務」時提示一次
        if not task:

            if self.last_task_id is not None or self.last_status is not None:
                self.log(f"ℹ️ {room_id} 目前沒有任務")

                self.last_task_id = None
                self.last_status = None

            return

        current_task_id = task["id"]
        current_status = task["status"]

        # 2️⃣ 狀態變化控制
        # 只有當 task_id 或 status 改變時才輸出 log，避免 polling 一直重複印
        if current_task_id != self.last_task_id or current_status != self.last_status:

            # print(current_task_id, current_status,self.last_task_id, self.last_status)

            self.log(
                f"🔄 room_id={task['room_id']} | "
                f"id={task['id']} | "
                f"mq_id={task['mq_id']} | "
                f"status={task['status']} | "
                f"{task['start_point']} -> {task['target_point']} | "
                f"{task['mission_content']}"
            )

            self.last_task_id = current_task_id
            self.last_status = current_status

        # 任務完成通知
        if current_status == "Completed" and current_task_id != self.last_notified_task_id:

            self.show_notify(
                "🚗 車輛到達",
                f"手術室 {room_id} 請卸貨"
            )
            
            self.log(f"🔔 車已到達 / 任務完成：{room_id}（task_id={current_task_id}）")

            self.last_notified_task_id = current_task_id

        # 任務中止通知
        if current_status == "Aborted" and current_task_id != self.last_notified_task_id:

            self.show_notify(
                "⚠️ 任務中止",
                f"手術室 {room_id} 請聯絡控制室"
            )

            self.log(f"⚠️ 任務中止：{room_id}（task_id={current_task_id}）")

            self.last_notified_task_id = current_task_id

    # 寫內外環防呆 function 
    def check_env_safety(self):
        db_host = DB_CONFIG["host"]

        if db_host in ["localhost"]:
            print("⚠️ Local DB，跳過環境檢查")
            return

        expected_host = EXPECTED_DB_HOST.get(self.env)

        if expected_host and db_host != expected_host:
            QMessageBox.critical(
                None,
                "錯誤",
                f"❌ {self.env} 環境 DB 設定錯誤\n目前: {db_host}\n應該: {expected_host}"
            )
            sys.exit()

if __name__ == "__main__":

    import sys

    app = QApplication(sys.argv)
    # message box title 也能是深色
    app.setStyle("Fusion")
    
    app.setStyleSheet("""
    QWidget {
        background-color: rgb(0,0,0);
        color: white;
    }

    QMessageBox {
        color: white;
    }
    """)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())