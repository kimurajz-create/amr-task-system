import psycopg2
from datetime import datetime
from psycopg2.extras import execute_values
from desktop_config import DB_CONFIG, ROOM_ID_MAP


# =========================
#   DB Manager
# =========================
class TaskDBManager:

    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print("✅ DB connected")
            return True
        except Exception as e:
            print("❌ DB connect error:", e)
            self.conn = None
            return False

    def close(self):
        if self.conn:
            self.conn.close()
            print("🔒 DB connection closed")

    def _execute_query(self, query, params=None, fetch=False, commit=False):
        """執行 SQL 查詢的內部方法"""
        if not self.conn:
            # 嘗試重新連線 (增強健壯性)
            if not self.connect():
                print("錯誤: 資料庫連線無效。")
                raise Exception("DB connect failed")
                # 如果是查詢（fetch=True）→ 回傳空列表 []
                # 如果是寫入（fetch=False）→ 回傳 None
                # return [] if fetch else None
            
        try:
            #核心: 這是真正執行 SQL 語法的地方，遊標(cursor)是資料庫中執行命令和獲取結果的介面。
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                #資料庫寫入與儲存 (commit)
                if commit:
                    self.conn.commit()
                # 取得查詢結果
                if fetch:
                    # 取得欄位名稱作為字典的 Key
                    col_names = [desc[0] for desc in cur.description]
                    return [dict(zip(col_names, row)) for row in cur.fetchall()]
                return None
        except Exception as e:
            print(f"❌ SQL 操作失敗: {e}")
            try:
                self.conn.rollback() # 發生錯誤時回滾，取消任何尚未 commit 的變動(像是執行了一半的交易被撤銷)
            except:
                pass
             # ⭐ 關鍵：標記連線失效
            self.conn = None
            raise e
        
    # =========================
    # 新增任務
    # =========================
    def add_new_task(self, start_point, target_point, mission_content, room_id):

        query_seq = """
        SELECT COALESCE(MAX(sequence),0)
        FROM tasks
        WHERE status IN ('Pending','Executing')
        """

        result = self._execute_query(query_seq, fetch=True)

        next_seq = result[0]["coalesce"] + 1

        insert_query = """
        INSERT INTO tasks
        (sequence,start_point,target_point,mission_content,room_id)
        VALUES (%s,%s,%s,%s,%s)
        RETURNING id
        """

        params = (next_seq, start_point, target_point, mission_content, room_id)

        result = self._execute_query(insert_query, params, fetch=True, commit=True)

        return result[0]["id"] if result else None

    # =========================
    # 查詢某 room 最新任務
    # =========================
    def get_latest_task_for_room(self, room_id):

        query = """
        SELECT id,status,room_id,mq_id,start_point,target_point,mission_content
        FROM tasks
        WHERE room_id=%s
        ORDER BY mq_id DESC NULLS LAST,id DESC
        LIMIT 1
        """
        result = self._execute_query(query, (room_id,), fetch=True)
        return result[0] if result else None

    # =========================
    #    刪除任務
    # =========================
    def delete_task(self, task_id: int):
        query = "DELETE FROM tasks WHERE id = %s;"
        params = (task_id,)
        self._execute_query(query, params, commit=True)
        print(f"✅ 任務 ID {task_id} 已刪除。")

    # =========================
    # 房間心跳更新
    # =========================
    def update_room_heartbeat(self, room_id):
        query = """
        INSERT INTO room_heartbeat (room_id, last_heartbeat)
        VALUES (%s, NOW())
        ON CONFLICT (room_id)
        DO UPDATE SET last_heartbeat = NOW();
        """
        params = (room_id,)
        self._execute_query(query, params, commit=True)
        # print(f"✅ 房間 {room_id} 心跳已更新。")

    # =========================
    # 標記房間異常狀態
    # =========================
    def mark_room_error(self, room_id, error_type):
        """標記房間異常狀態（DB/API 故障）"""
        query = """
        INSERT INTO room_heartbeat (room_id, error_status, last_heartbeat)
        VALUES (%s, %s, NOW())
        ON CONFLICT (room_id)
        DO UPDATE SET error_status = %s, last_heartbeat = NOW();
        """
        params = (room_id, error_type, error_type)
        try:
            self._execute_query(query, params, commit=True)
            print(f"✅ 房間 {room_id} 標記為 {error_type}")
        except Exception as e:
            print(f"❌ 標記房間異常失敗: {e}")

    # =========================
    # 清除房間異常狀態
    # =========================
    def clear_room_error(self, room_id):
        """清除房間異常狀態（DB/API 恢復）"""
        query = """
        UPDATE room_heartbeat 
        SET error_status = NULL, last_heartbeat = NOW()
        WHERE room_id = %s;
        """
        params = (room_id,)
        try:
            self._execute_query(query, params, commit=True)
            # print(f"✅ 房間 {room_id} 異常已清除")
        except Exception as e:
            pass  # 靜默處理，不洗版

    
    # =========================
    # 回傳Master API狀態
    # =========================
    def get_room_error(self, room_id):
        query ="""
          SELECT error_status
          FROM room_heartbeat
          WHERE room_id = %s
        """
        params = (room_id,)
        try:
            result = self._execute_query(query, params, fetch=True)
            if not result:
                return None

            row = result[0]

            # ⭐ 跟你其他 function 風格一致（安全寫法）
            return row["error_status"] if isinstance(row, dict) else row[0]

        except Exception as e:
            print(f"❌ 查詢房間異常狀態失敗: {e}")
            return None

# =========================
#    建立任務 helper
# =========================
def create_new_db_task(db, start_place, destination, mission):

    room_id = ROOM_ID_MAP.get(destination)

    new_id = db.add_new_task(
        start_place,
        destination,
        mission,
        room_id
    )

    print("✅ 新任務建立:", new_id)

    return new_id







# =========================
#    測試
# =========================
# if __name__ == "__main__":

#     db = TaskDBManager(DB_CONFIG)
#     db.connect()
    

#     # # 新增任務
#     # create_new_db_task(
#     #     db,
#     #     "櫃台",
#     #     "華陀會議室",
#     #     "Demo_器械運送"
#     # )


#     db.delete_task(641)


#     # 查詢任務
#     task = db.get_latest_task_for_room("OR01")

#     print("最新任務:", task)

#     db.close()