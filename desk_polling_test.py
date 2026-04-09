import psycopg2
import time
from datetime import datetime
from psycopg2.extras import execute_values


class TaskDBManager:
    """
    用於管理 MiR 任務佇列 (tasks) 資料表的類別。
    封裝與 PostgreSQL 的連線和查詢操作。
    """
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None

    # --- 資料庫連線與關閉 ---
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

    # 執行 SQL 查詢
    def _execute_query(self, query, params=None, fetch=False, commit=False):
        """執行 SQL 查詢的內部方法"""
        if not self.conn:
            # 嘗試重新連線
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

    # --- 桌機 polling 用查詢 ---
    # psycopg2 要求 tuple。因此(room_id,)才對
    def get_latest_task_for_room(self, room_id):
        """
        查詢某手術室最新一筆任務
        優先依 mq_id 排序，若 mq_id 為 NULL 則再依 id 排序
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


# --- 桌機 polling 測試主程式 ---
if __name__ == "__main__":
    DB_CONFIG = {
        'user': 'postgres',
        'host': 'localhost',
        'database': 'military_mir250_project',
        'password': '123456',
        'port': 5432
    }

    ROOM_ID = "OR01"       # 要監看的手術室(之後可以改成讀取設定檔)
    POLL_INTERVAL = 2      # 每 2 秒查一次

    db_manager = TaskDBManager(DB_CONFIG)

    if db_manager.connect():
        print(f"📡 開始監看手術室 {ROOM_ID} 的任務狀態... (Ctrl+C 可停止)")

        last_task_id = None
        last_status = None
        last_notified_completed_task_id = None

        try:
            while True:
                task = db_manager.get_latest_task_for_room(ROOM_ID)

                # 1️⃣ 無任務控制
                # 若 DB 沒有任務，只在「從有任務 → 沒任務」時提示一次
                if not task:
                    if last_task_id is not None or last_status is not None:
                        print(f"ℹ️ {ROOM_ID} 目前沒有任務")
                        last_task_id = None
                        last_status = None
                    time.sleep(POLL_INTERVAL)
                    continue

                current_task_id = task["id"]
                current_status = task["status"]

                # 2️⃣ 狀態變化控制
                # 只有當 task_id 或 status 改變時才輸出 log，避免 polling 一直重複印
                if current_task_id != last_task_id or current_status != last_status:
                    print(
                        f"🔄 [{datetime.now().strftime('%H:%M:%S')}] "
                        f"room_id={task['room_id']} | "
                        f"id={task['id']} | "
                        f"mq_id={task['mq_id']} | "
                        f"status={task['status']} | "
                        f"{task['start_point']} -> {task['target_point']} | "
                        f"{task['mission_content']}"
                    )

                    last_task_id = current_task_id
                    last_status = current_status

                # 3️⃣ 事件通知控制
                # Completed / Aborted 狀態只提醒一次，避免 polling 重複通知
                if current_status == "Completed" and current_task_id != last_notified_completed_task_id:
                    print(f"🔔 車已到達 / 任務完成：{ROOM_ID}（task_id={current_task_id}）")
                    last_notified_completed_task_id = current_task_id

               
                if current_status == "Aborted" and current_task_id != last_notified_completed_task_id:
                    print(f"⚠️ 任務已中止：{ROOM_ID}（task_id={current_task_id}）")
                    last_notified_completed_task_id = current_task_id

                time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\n🛑 停止監看。")

        finally:
            db_manager.close()