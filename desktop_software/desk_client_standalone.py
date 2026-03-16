import sys
import psycopg2
from datetime import datetime
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QTextEdit, QMessageBox, QGroupBox, QGridLayout
)


# =========================
# 1. 資料庫設定
# =========================
DB_CONFIG = {
    "user": "postgres",
    "host": "localhost",
    "database": "military_mir250_project",
    "password": "123456",
    "port": 5432,
}


# =========================
# 2. 手術室 / 地點 mapping
#    這裡先沿用你現在主控的對照
# =========================
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
    "車架位置(華陀)": "OR11",
    "車架位置(演講廳_02)": "OR12",
    "車架位置(演講廳_01)": "OR13",
    "車架位置(沙發3)": "OR14",
    "車架位置(沙發2)": "OR15",
    "車架位置(沙發1)": "OR16",
    "車架位置(櫃台)": "OR17",
}

LOCATION_OPTIONS = list(ROOM_ID_MAP.keys())

MISSION_OPTIONS = [
    "Demo_空車運輸",
    "Demo_器械運送",
    "Demo_回收任務",
]

ROOM_OPTIONS = sorted(set(ROOM_ID_MAP.values()))


# =========================
# 3. DB Manager
# =========================
class TaskDBManager:
    """
    獨立桌機版 DB 操作類別
    風格沿用你原本 TaskDBManager
    """

    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None

    def connect(self):
        """嘗試連線到 PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print("✅ 成功連線到 PostgreSQL 任務資料庫。")
            return True
        except Exception as e:
            print(f"❌ 連線失敗: {e}")
            self.conn = None
            return False

    def close(self):
        """關閉資料庫連線"""
        if self.conn:
            self.conn.close()
            print("🔒 連線已關閉。")

    def _execute_query(self, query, params=None, fetch=False, commit=False):
        """執行 SQL 查詢的內部方法"""
        if not self.conn:
            if not self.connect():
                print("錯誤: 資料庫連線無效。")
                return [] if fetch else None

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)

                if commit:
                    self.conn.commit()

                if fetch:
                    col_names = [desc[0] for desc in cur.description]
                    return [dict(zip(col_names, row)) for row in cur.fetchall()]

                return None

        except Exception as e:
            print(f"❌ SQL 操作失敗: {e}")
            self.conn.rollback()
            return [] if fetch else None

    def add_new_task(self, start_point: str, target_point: str, content: str = "", room_id: str | None = None):
        """
        新增一個任務到佇列中，sequence 自動排到最後
        status 由 DB DEFAULT 自動填成 Pending
        """
        max_seq_query = "SELECT COALESCE(MAX(sequence), 0) FROM tasks WHERE status IN ('Pending', 'Executing');"
        result = self._execute_query(max_seq_query, fetch=True)
        next_sequence = result[0]["coalesce"] + 1 if result and result[0]["coalesce"] is not None else 1

        if room_id:
            insert_query = """
            INSERT INTO tasks
            (sequence, start_point, target_point, mission_content, room_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """
            params = (next_sequence, start_point, target_point, content, room_id)
        else:
            insert_query = """
            INSERT INTO tasks
            (sequence, start_point, target_point, mission_content)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """
            params = (next_sequence, start_point, target_point, content)

        rows = self._execute_query(insert_query, params, fetch=True, commit=True)

        if rows and "id" in rows[0]:
            new_id = rows[0]["id"]
            print(f"✅ 新增任務成功，Sequence: {next_sequence}, DB ID: {new_id}, room_id: {room_id}")
            return new_id
        else:
            print("❌ 警告：新增任務成功，但無法獲取返回的 ID。")
            return None

    def get_latest_task_for_room(self, room_id):
        """
        查詢某手術室最新一筆任務
        優先依 mq_id 排序；若 mq_id 為 NULL，則依 id 排序
        """
        query = """
        SELECT id, status, room_id, mq_id, start_point, target_point, mission_content, created_at
        FROM tasks
        WHERE room_id = %s
        ORDER BY mq_id DESC NULLS LAST, id DESC
        LIMIT 1;
        """
        result = self._execute_query(query, (room_id,), fetch=True)
        return result[0] if result else None


# =========================
# 4. 共用任務建立邏輯
# =========================
def create_new_db_task(db_manager, room_id_map, start_place, destination, mission_content):
    """
    共用的新增任務邏輯：
    依 destination 對應 room_id，並寫入 DB
    """
    room_id = room_id_map.get(destination)

    if not start_place or not destination or not mission_content:
        print("請填寫所有欄位！")
        return None

    new_id = db_manager.add_new_task(
        start_place,
        destination,
        mission_content,
        room_id=room_id
    )
    return new_id


# =========================
# 5. 桌機視窗
# =========================
class DeskClientWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("手術室桌機測試版")
        self.resize(760, 520)

        self.db_manager = TaskDBManager(DB_CONFIG)
        if not self.db_manager.connect():
            QMessageBox.critical(self, "錯誤", "無法連線到 PostgreSQL，請檢查 DB_CONFIG。")

        # 記錄狀態變化，避免重複提醒
        self.last_task_id = None
        self.last_status = None
        self.last_notified_task_id = None

        self._build_ui()
        self._setup_timer()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # ===== 監看區 =====
        watch_group = QGroupBox("手術室監看")
        watch_layout = QGridLayout()

        self.cmb_room = QComboBox()
        self.cmb_room.addItems(ROOM_OPTIONS)

        self.lbl_current_room = QLabel("目前手術室：")
        self.lbl_status = QLabel("狀態：--")
        self.lbl_task_id = QLabel("任務 ID：--")
        self.lbl_mq_id = QLabel("mq_id：--")
        self.lbl_route = QLabel("路線：--")
        self.lbl_mission = QLabel("任務內容：--")
        self.lbl_update_time = QLabel("最後更新：--")

        watch_layout.addWidget(QLabel("監看 room_id："), 0, 0)
        watch_layout.addWidget(self.cmb_room, 0, 1)
        watch_layout.addWidget(self.lbl_status, 1, 0, 1, 2)
        watch_layout.addWidget(self.lbl_task_id, 2, 0, 1, 2)
        watch_layout.addWidget(self.lbl_mq_id, 3, 0, 1, 2)
        watch_layout.addWidget(self.lbl_route, 4, 0, 1, 2)
        watch_layout.addWidget(self.lbl_mission, 5, 0, 1, 2)
        watch_layout.addWidget(self.lbl_update_time, 6, 0, 1, 2)

        watch_group.setLayout(watch_layout)
        root.addWidget(watch_group)

        # ===== 下達任務區 =====
        create_group = QGroupBox("新增任務")
        create_layout = QGridLayout()

        self.cmb_start = QComboBox()
        self.cmb_start.addItems(LOCATION_OPTIONS)

        self.cmb_destination = QComboBox()
        self.cmb_destination.addItems(LOCATION_OPTIONS)

        self.cmb_mission = QComboBox()
        self.cmb_mission.addItems(MISSION_OPTIONS)

        self.btn_create = QPushButton("新增任務")
        self.btn_refresh = QPushButton("立即刷新")

        create_layout.addWidget(QLabel("起點："), 0, 0)
        create_layout.addWidget(self.cmb_start, 0, 1)

        create_layout.addWidget(QLabel("目的地："), 1, 0)
        create_layout.addWidget(self.cmb_destination, 1, 1)

        create_layout.addWidget(QLabel("任務內容："), 2, 0)
        create_layout.addWidget(self.cmb_mission, 2, 1)

        create_layout.addWidget(self.btn_create, 3, 0)
        create_layout.addWidget(self.btn_refresh, 3, 1)

        create_group.setLayout(create_layout)
        root.addWidget(create_group)

        # ===== log 區 =====
        log_group = QGroupBox("事件紀錄")
        log_layout = QVBoxLayout()

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)

        log_layout.addWidget(self.txt_log)
        log_group.setLayout(log_layout)
        root.addWidget(log_group)

        # signals
        self.btn_create.clicked.connect(self.on_create_task_clicked)
        self.btn_refresh.clicked.connect(self.poll_room_status)
        self.cmb_room.currentTextChanged.connect(self.on_room_changed)

    def _setup_timer(self):
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_room_status)
        self.poll_timer.start(2000)  # 每 2 秒查一次

    def log(self, text):
        now = datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"[{now}] {text}")
        print(text)

    def on_room_changed(self):
        self.last_task_id = None
        self.last_status = None
        self.last_notified_task_id = None
        self.log(f"📡 切換監看手術室：{self.cmb_room.currentText()}")
        self.poll_room_status()

    def on_create_task_clicked(self):
        start_place = self.cmb_start.currentText()
        destination = self.cmb_destination.currentText()
        mission_content = self.cmb_mission.currentText()

        new_id = create_new_db_task(
            self.db_manager,
            ROOM_ID_MAP,
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

    def poll_room_status(self):
        room_id = self.cmb_room.currentText()
        task = self.db_manager.get_latest_task_for_room(room_id)

        if not task:
            self.lbl_status.setText("狀態：目前無任務")
            self.lbl_task_id.setText("任務 ID：--")
            self.lbl_mq_id.setText("mq_id：--")
            self.lbl_route.setText("路線：--")
            self.lbl_mission.setText("任務內容：--")
            self.lbl_update_time.setText(f"最後更新：{datetime.now().strftime('%H:%M:%S')}")

            if self.last_task_id is not None or self.last_status is not None:
                self.log(f"ℹ️ {room_id} 目前沒有任務")
                self.last_task_id = None
                self.last_status = None
            return

        current_task_id = task["id"]
        current_status = task["status"]

        self.lbl_status.setText(f"狀態：{current_status}")
        self.lbl_task_id.setText(f"任務 ID：{task['id']}")
        self.lbl_mq_id.setText(f"mq_id：{task['mq_id']}")
        self.lbl_route.setText(f"路線：{task['start_point']} -> {task['target_point']}")
        self.lbl_mission.setText(f"任務內容：{task['mission_content']}")
        self.lbl_update_time.setText(f"最後更新：{datetime.now().strftime('%H:%M:%S')}")

        # 只有任務 ID 或 status 改變時才印 log
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

        # Completed / Aborted 時只提醒一次
        if current_status in ("Completed", "Aborted") and current_task_id != self.last_notified_task_id:
            QApplication.beep()

            if current_status == "Completed":
                self.log(f"🔔 任務完成：{room_id}（task_id={current_task_id}）")
                QMessageBox.information(self, "通知", f"{room_id} 任務完成\nTask ID: {current_task_id}")
            elif current_status == "Aborted":
                self.log(f"⚠️ 任務中止：{room_id}（task_id={current_task_id}）")
                QMessageBox.warning(self, "通知", f"{room_id} 任務中止\nTask ID: {current_task_id}")

            self.last_notified_task_id = current_task_id

    def closeEvent(self, event):
        self.db_manager.close()
        super().closeEvent(event)


# =========================
# 6. 程式入口
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DeskClientWindow()
    window.show()
    sys.exit(app.exec())