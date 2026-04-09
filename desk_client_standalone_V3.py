"""
======================== 系統架構說明 ========================

本程式已全面改為「非同步架構」，避免 UI freeze：

1️⃣ UI Thread（主執行緒）
   - 負責畫面更新（Qt 限制：只能在主執行緒操作 UI）

2️⃣ Worker Thread（QThread）
   - 負責所有「耗時操作」
     ✔ API 呼叫（MiR）
     ✔ DB 查詢 / 寫入

3️⃣ Signal 機制
   - Worker 執行完 → 回傳資料 → 主執行緒更新 UI

------------------------------------------------------------

⚠️ 重要原則：
👉 UI 不可在 thread 中操作
👉 DB / API 不可在 UI thread 執行

------------------------------------------------------------

目前已處理：
✔ API 非同步（dropdown）
✔ DB 非同步（新增任務）
✔ polling 非同步（避免 UI 卡住）
✔ thread lifecycle 管理（避免 QThread destroyed error）

============================================================
"""
import winsound
import os
import json
import re
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

from PySide6.QtCore import QThread, Signal

# from desktop_config import (
#     DB_CONFIG,
#     USER_LOCATION_MAP,
#     USER_MISSION_GROUP_MAP,
#     REQUIRED_MISSION_CODES,
#     POLL_INTERVAL,
#     room_id,
# )

import ui_desk_client
print(ui_desk_client.__file__)


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

class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()

        '''
        ===== 系統啟動流程 =====
        MainWindow init
            ↓
        on_env_changed() 被呼叫（初始化環境）
            ↓
        poll_timer.start(...) ← ⭐ 在這裡啟動
            ↓
        每 N 秒 → poll_room_status()
        '''

        # self.env = ENV  # ⭐ 這就是你的環境
        # self.check_env_safety()
        self.startup_check()

        self.CONFIG_MAP = {
            "內環": "inner.json",
            "外環": "outer.json"
        }
        self.is_first_load = True
        self.db_error = False   # ⭐ 加這行
        self.api_error = False  # ⭐ 加這行
        self.setupUi(self)
        self.setWindowTitle("台中國軍醫 MiR")

        self.workers = []          # ⭐ 管理所有 thread（避免被 Python GC 回收 → crash）
        self.polling_busy = False  # ⭐ 防止 polling 重疊（避免同時多個 DB 查詢）

        # ⚠️ 若沒有這兩個：
        # - 會出現 QThread destroyed while running
        # - 或 polling 疊加導致卡頓

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

        # 啟動時先顯示等待畫面
        self.hide_notify()

        
        
        # polling timer
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_room_status)

        # ===== 下達任務區 =====
        # signals
        self.btn_add_task_db.clicked.connect(self.on_create_task_db_clicked)
        self.btn_delete_task_db.clicked.connect(self.on_delete_task_db_clicked)
        # 延遲 50 毫秒後只執行一次 self.init_data（通常用在 UI 初始化完成後再跑邏輯），先把畫面抓出來，再去抓資料避免卡頓
        QTimer.singleShot(50, self.init_data)

        # ===== 環境切換 =====
        # 當使用者改變下拉選單時，自動呼叫 on_env_changed
        # 程式啟動時，先用目前選項手動執行一次（初始化環境）
        self.cmb_env.currentTextChanged.connect(self.on_env_changed)
        self.on_env_changed(self.cmb_env.currentText())

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

  
    def load_map_positions_from_db(self, rows):
        """
        UI 更新（從 DB 載入）

        這裡只做：
        ✔ DB 資料 → UI（ComboBox）
        ✔ 不做任何轉換（主控已經處理好）

        參數：
        rows: [(display_name, mir_code), ...]

        ⚠️ 注意：
        - UI 操作只能在主執行緒
        - 不要在這裡打 DB / API
        """

        # 1️⃣ 初始化下拉選單
        self.cmb_start_point.clear()
        self.cmb_end_point.clear()

        user_names_list = []  # 用於自動補完器
        # print("DEBUG rows:", rows[:2])
        # 2️⃣ 塞入 ComboBox（顯示中文，隱藏 mir_code）
        for row in rows:
            display_name = row["display_name"]
            mir_code = row["mir_code"]
            room_id = row.get("room_id")   # ⭐ 不會炸
            # print(f"DEBUG location row: display_name={display_name}, mir_code={mir_code}, room_id={room_id}")

            # ⭐ 核心：只顯示有效地點
            if not room_id:
                continue

            data = {
                "room_id": room_id,
                "mir_code": mir_code
            }

            self.cmb_start_point.addItem(display_name, data)
            self.cmb_end_point.addItem(display_name, data)

            user_names_list.append(display_name)

        # 3️⃣ 設置自動補完器
        if user_names_list:
            completer = QCompleter(user_names_list)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.cmb_start_point.setCompleter(completer)
            self.cmb_end_point.setCompleter(completer)
  

    def load_mission_groups_from_db(self, rows):
        """
        UI 更新（從 DB 載入 mission groups）

        這裡只做：
        ✔ DB 資料 → UI（ComboBox）
        ✔ 不做任何轉換（主控已經處理好）

        參數：
        rows: [(display_name, mir_code), ...]

        ⚠️ 注意：
        - UI 操作只能在主執行緒
        - 不要在這裡打 DB / API
        """

        self.cmb_mission.clear()

        user_names_list = []
        # print("DEBUG mission rows:", rows[:2])
        
        for row in rows:
            display_name = row["display_name"]
            mir_code = row["mir_code"]

            self.cmb_mission.addItem(display_name, mir_code)
            user_names_list.append(display_name)

        # 自動補完器
        if user_names_list:
            completer = QCompleter(user_names_list)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.cmb_mission.setCompleter(completer)

    def fetch_locations_from_db(self):
        """
        從 DB 取得 UI locations（背景執行）

        回傳：
        [(display_name, mir_code), ...]

        ⚠️ 這個 function 會丟給 Worker thread 執行
        """
        return self.db_manager.get_ui_locations()
    
    def fetch_missions_from_db(self):
        """
        從 DB 取得 mission groups（背景執行）

        回傳：
        [(display_name, mir_code), ...]

        ⚠️ 這個 function 會丟給 Worker thread 執行
        """
        return self.db_manager.get_ui_missions()


    def get_room_error_from_db(self):
        return self.db_manager.get_room_error("MASTER")

    # ====== 開始任務 ======
    def on_create_task_db_clicked(self):
        start_data = self.cmb_start_point.currentData()
        end_data = self.cmb_end_point.currentData()
        print("DEBUG start_data:", start_data)
        print("DEBUG end_data:", end_data)
        if not start_data or not end_data:
            print("❌ 選單資料錯誤")
            return

        start_place = self.cmb_start_point.currentText()
        destination = self.cmb_end_point.currentText()
        print("DEBUG start_place:", start_place)
        print("DEBUG destination:", destination)

        # ⭐ 正確拆 data
        room_id = end_data["room_id"]
        mission_content = self.cmb_mission.currentText()

        # ⭐ 丟進 DB
        worker = DBWorker(
            create_new_db_task,
            self.db_manager,
            start_place,
            destination,
            mission_content,
            room_id
        )

        self.workers.append(worker)
        worker.start()
   

    def on_task_success(self, result):
        self.log(f"✅ 新增任務成功，DB ID: {result}")
        QMessageBox.information(self, "成功", f"新增任務成功，DB ID: {result}")

    def on_task_error(self, err):
        self.log(f"❌ 新增任務錯誤: {err}")
        QMessageBox.warning(self, "錯誤", err)


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
        """
        定時查詢 DB（非同步）

        流程：
        Timer → Worker → DB 查詢 → 回傳 → UI 更新

        ⭐ polling_busy：
        防止上一個還沒結束又啟動（避免 thread 疊加）
        """
        if self.polling_busy:
            return
        
        self.polling_busy = True

        # ===== DB polling =====
        worker = DBWorker(self.get_task_data)
        worker.finished.connect(self.handle_task_result)
        worker.error.connect(self.handle_task_error)
        self.workers.append(worker)
        worker.finished.connect(lambda: self._cleanup_poll_worker(worker))
        worker.error.connect(lambda: self._cleanup_poll_worker(worker))
        worker.start()

        # ===== API polling（新增 ⭐）=====

        worker_api = DBWorker(self.get_room_error_from_db)
        worker_api.finished.connect(self.update_api_light)
        worker_api.error.connect(self.handle_api_error)

        self.workers.append(worker_api)

        worker_api.finished.connect(lambda: self._cleanup_poll_worker(worker_api))
        worker_api.error.connect(lambda: self._cleanup_poll_worker(worker_api))

        worker_api.start()

        # ===== 房間心跳更新（新增 ⭐）=====
        worker_heartbeat = DBWorker(self.update_heartbeat)
        worker_heartbeat.finished.connect(self.handle_heartbeat_result)
        worker_heartbeat.error.connect(self.handle_heartbeat_error)

        self.workers.append(worker_heartbeat)

        worker_heartbeat.finished.connect(lambda: self._cleanup_poll_worker(worker_heartbeat))
        worker_heartbeat.error.connect(lambda: self._cleanup_poll_worker(worker_heartbeat))

        worker_heartbeat.start()

    def _cleanup_poll_worker(self, worker):
        """
        polling 專用 cleanup

        作用：
        - 移除 worker（避免記憶體累積）
        - 釋放 polling_busy（允許下一次執行）
        """
        if worker in self.workers:
            self.workers.remove(worker)
        self.polling_busy = False

    def _cleanup_worker(self, worker):
        if worker in self.workers:
            self.workers.remove(worker)    
    
    def handle_worker_error(self, err):
        self.log(f"⚠️ Worker 錯誤: {err}")

    def get_task_data(self):
        room_id = self.config["ROOM_ID"]
        return self.db_manager.get_latest_task_for_room(room_id)
    
    # ====== 處理任務結果 ======
    def handle_task_result(self, task):

        room_id = self.config["ROOM_ID"]
        # debug worker 數量狂疊加會當掉
        # self.log(f"目前 worker 數量: {len(self.workers)}")  # ⭐ 放這

        if self.db_error:
            self.log("✅ 資料庫連線已恢復")
            self.db_manager.clear_room_error(room_id)  # ⭐ 新增：清除異常狀態
            self.db_error = False

        self.lbl_status_v1.setText("🟢 DB 正常")

        if not task:
            if self.last_task_id is not None or self.last_status is not None:
                self.log(f"ℹ️ {room_id} 目前沒有任務")
                self.last_task_id = None
                self.last_status = None
            return

        current_task_id = task["id"]
        current_status = task["status"]

        if current_task_id != self.last_task_id or current_status != self.last_status:

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

        if current_status == "Completed" and current_task_id != self.last_notified_task_id:
            self.show_notify("🚗 車輛到達", f"手術室 {room_id} 請卸貨")
            self.log(f"🔔 車已到達：{room_id}")

           
            if self.config["SOUND"]["ENABLE"]:
                winsound.Beep(
                    self.config["SOUND"]["FREQUENCY"],
                    self.config["SOUND"]["DURATION"]
                )

            self.last_notified_task_id = current_task_id

        if current_status == "Aborted" and current_task_id != self.last_notified_task_id:
            self.show_notify("⚠️ 任務中止", f"手術室 {room_id} 請聯絡控制室")
            self.log(f"⚠️ 任務中止：{room_id}")
            self.last_notified_task_id = current_task_id    
    
    
    def handle_task_error(self, err):
        if not self.db_error:
            self.log("⚠️ 資料庫連線異常，請確認網路")
            print("DB error:", err)
            self.db_manager.mark_room_error(self.config["ROOM_ID"], "DB_ERROR")  # ⭐ 新增
            self.db_error = True    
        self.lbl_status_v1.setText("🔴 DB 異常")



    def update_api_light(self, status):
        if status == "API_ERROR":
            self.lbl_status_v2.setText("🔴 API 異常")
        else:
            self.lbl_status_v2.setText("🟢 API 正常")


    def handle_api_error(self, err):
        self.log("⚠️ DB查詢失敗")
        print("DB error:", err)
        self.lbl_status_v2.setText("🔴 API 異常")






    def update_heartbeat(self):
        """背景執行緒中運行的方法 - 更新房間心跳"""
        room_id = self.config["ROOM_ID"]
        self.db_manager.update_room_heartbeat(room_id)
        return f"✅ {room_id} 心跳已更新"

    def handle_heartbeat_result(self, result):
        """接收心跳更新結果 - 心跳成功表示 DB 正常，清除異常狀態"""
        # 如果有異常標記，清除它（因為心跳成功 = DB 連接正常）
        try:
            self.db_manager.clear_room_error(self.config["ROOM_ID"])
        except:
            pass  # 忽略清除失敗，不影響心跳

    def handle_heartbeat_error(self, err):
        """處理心跳更新錯誤"""
        self.log(f"❌ 心跳更新失敗: {err}")

    # 檢查 host 是否合法
    def is_valid_host(self, host):
        import socket

        try:
            socket.gethostbyname(host)
            return True
        except:
            return False

    # ===== 環境切換 =====
    # 功能：
    # - 載入 config（INNER / OUTER）
    # - 切換 DB 連線（不同主控）
    # - 重新啟動 polling timer
    # - 重新載入 map / mission（目前仍用 API）
    def on_env_changed(self, text):

        # ⭐ 先防呆（避免 KeyError）
        if text not in self.CONFIG_MAP:
            QMessageBox.critical(self, "錯誤", f"未知環境: {text}")
            return

        # 判斷是不是 exe
        if getattr(sys, 'frozen', False):
            # ✅ exe模式 → 用 exe 的資料夾
            BASE_DIR = os.path.dirname(sys.executable)
        else:
            # ✅ 開發模式 → 用原始程式資料夾
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        CONFIG_DIR = "configs"
            
        config_path = os.path.join(BASE_DIR,CONFIG_DIR, self.CONFIG_MAP[text])

         # ⭐ 檔案存在檢查
        if not os.path.exists(config_path):
            QMessageBox.critical(self, "錯誤", f"找不到設定檔: {config_path}")
            return

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.env = text   # ⭐ 很重要（給下面用）

        # ⭐ 切換前清掉舊 DB（建議）
        if hasattr(self, "db_manager"):
            try:
                self.db_manager.close()
            except:
                pass

        self.db_manager = TaskDBManager(self.config["DB_CONFIG"])
        if not self.db_manager.connect():
            QMessageBox.critical(self, "錯誤", "無法連線到 PostgreSQL，請檢查 DB_CONFIG。")
            return

        print(f"切換到 {text}")
        # print("MIR_IP:", self.config["MIR_IP"])
        # print("SOUND:", self.config["SOUND"]["FREQUENCY"])

         # ⭐ 第一次不顯示
        if not self.is_first_load:
            QMessageBox.information(self, "環境切換", f"已切換到 {text}")

        self.is_first_load = False

        # ⭐ 加這行（切換時檢查）
        self.check_env_safety()
        worker_map = DBWorker(self.fetch_locations_from_db)
        worker_map.finished.connect(self.load_map_positions_from_db)
        self.workers.append(worker_map)
        worker_map.finished.connect(lambda: self._cleanup_worker(worker_map))
        worker_map.error.connect(lambda: self._cleanup_worker(worker_map))
        
        worker_map.start()

        worker_mission = DBWorker(self.fetch_missions_from_db)
        worker_mission.finished.connect(self.load_mission_groups_from_db)
        self.workers.append(worker_mission)
        worker_mission.finished.connect(lambda: self._cleanup_worker(worker_mission))
        worker_mission.error.connect(lambda: self._cleanup_worker(worker_mission))
        worker_mission.start()
        # 避免舊 timer 還在跑 + 新 timer 再跑 ❌
        self.poll_timer.stop()
        # 開始新的 timer
        self.poll_timer.start(self.config["POLL_INTERVAL"])
        


    # 寫內外環防呆 function 
    def check_env_safety(self):
        db_host = self.config["DB_CONFIG"]["host"]   # ⭐ 改這裡

        if not self.is_valid_host(db_host):
            QMessageBox.critical(None, "錯誤", f"❌ DB host 格式錯誤: {db_host}")
            return False

        if db_host in ["localhost", "127.0.0.1"]:
            print("⚠️ Local DB，跳過環境檢查")
            return True

        # 取得環境對應的 DB host
        expected_map = self.config.get("EXPECTED_DB_HOST", {})
         # ENV 告訴你「現在是哪個環境」，ENV 告訴你「現在是哪個環境」
        expected_host = expected_map.get(self.config.get("ENV"))

        if expected_host and db_host != expected_host:
            QMessageBox.critical(
                None,
                "錯誤",
                f"❌ {self.env} 環境 DB 設定錯誤\n目前: {db_host}\n應該: {expected_host}"
            )
            return False

        return True


    # 開機檢查
    def startup_check(self):

        if getattr(sys, 'frozen', False):
            BASE_DIR = os.path.dirname(sys.executable)
        else:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        CONFIG_DIR = os.path.join(BASE_DIR, "configs")

        if not os.path.exists(CONFIG_DIR):
            QMessageBox.critical(self, "錯誤", "❌ 找不到 configs 資料夾")
            sys.exit()

        if not os.listdir(CONFIG_DIR):
            QMessageBox.critical(self, "錯誤", "❌ 沒有任何 config 檔案")
            sys.exit()




    # 載入地圖位置與任務
    def init_data(self):

        """
        初始化資料（非同步）

        流程：
        Thread → 呼叫 API → 回傳資料 → 主執行緒更新 UI

        ⚠️ 不能直接呼叫 load_map_positions()
        因為裡面有 UI 操作
        """

        # ===== 地圖（改為從 DB 讀取）=====
        worker_map = DBWorker(self.fetch_locations_from_db)

        # DB → UI（ComboBox）
        worker_map.finished.connect(self.load_map_positions_from_db)

        # 錯誤處理
        worker_map.error.connect(self.handle_worker_error)

        # 管理 thread（避免被 GC 回收）
        self.workers.append(worker_map)

        # thread 結束後清理
        worker_map.finished.connect(lambda: self._cleanup_worker(worker_map))
        worker_map.error.connect(lambda: self._cleanup_worker(worker_map))

        # 啟動背景執行
        worker_map.start()

        worker_mission = DBWorker(self.fetch_missions_from_db)
        worker_mission.finished.connect(self.load_mission_groups_from_db)
        worker_mission.error.connect(self.handle_worker_error)

        self.workers.append(worker_mission)
        worker_mission.finished.connect(lambda: self._cleanup_worker(worker_mission))
        worker_mission.error.connect(lambda: self._cleanup_worker(worker_mission))

        worker_mission.start()

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