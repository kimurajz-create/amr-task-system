import psycopg2
from datetime import datetime
from psycopg2.extras import execute_values
class TaskDBManager:
    """
    用於管理 MiR 任務佇列 (tasks) 資料表的類別。
    封裝了所有與 PostgreSQL 的連線和操作。
    """
    def __init__(self, db_config):
        # 你的資料庫連線設定
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
            print("連線已關閉。")

    # 執行 SQL 查詢
    def _execute_query(self, query, params=None, fetch=False, commit=False):
        """執行 SQL 查詢的內部方法"""
        if not self.conn:
            # 嘗試重新連線 (增強健壯性)
            if not self.connect():
                print("錯誤: 資料庫連線無效。")
                return [] if fetch else None
            
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
            self.conn.rollback() # 發生錯誤時回滾，取消任何尚未 commit 的變動(像是執行了一半的交易被撤銷)
            return [] if fetch else None

    # 批次執行 SQL
    def _execute_batch(self, sql_template, data_list):
        """
        使用 execute_values 高效地執行批次插入。
        sql_template: 帶有 VALUES %s 的 SQL 模板。
        data_list: 要插入的 (sequence, start_point, ...) 數據列表。
        """
        if not self.conn:
            if not self.connect():
                print("錯誤: 資料庫連線無效，批次操作失敗。")
                return False
                
        try:
            with self.conn.cursor() as cur:
                execute_values(cur, sql_template, data_list)
                self.conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ SQL 批次操作失敗: {e}")
            self.conn.rollback()
            return False


    # --- 核心任務排程功能 (供 PySide6 GUI 使用) ---
    #-------------------------------------新增系列---------------------------------------------#
    def add_new_task(self, start_point: str, target_point: str, content: str = ""):
        """
        新增一個任務到佇列中， sequence 會自動設為目前的最後一個。
        """
        # 1. 取得task table目前最大的 sequence 值
        # 使用 COALESCE 確保如果表格為空，MAX(sequence) 傳回 0
        max_seq_query = "SELECT COALESCE(MAX(sequence), 0) FROM tasks WHERE status IN ('Pending', 'Executing');"
        result = self._execute_query(max_seq_query, fetch=True)
        # 如果查詢成功，將 sequence 設為 Max + 1，否則設為 1
        next_sequence = result[0]['coalesce'] + 1 if result and result[0]['coalesce'] is not None else 1
        
        # 2. 插入新任務
        # 注意: 我們只傳入 sequence, start_point, target_point, mission_content
        # 其他欄位 (id, status, mir_command_sent, created_at) 會使用資料庫的 DEFAULT 值
        insert_query = """
        INSERT INTO tasks 
        (sequence, start_point, target_point, mission_content)
        VALUES (%s, %s, %s, %s)
        RETURNING id; -- 返回新增任務的 ID (可選) 這是 PostgreSQL (Postgres) 資料庫特有的強大功能
        """
        params = (
            next_sequence,  # 來自步驟 1 計算出來的數值
            start_point, 
            target_point, 
            content
        )
        # 💥 關鍵修正 A: 呼叫 _execute_query 時，設定 fetch=True 來獲取 RETURNING 的結果
        # 💥 關鍵修正 B: 將回傳值賦給 rows 變數
        rows = self._execute_query(insert_query, params, fetch=True, commit=True)
        
        # 3. 處理回傳的 ID
        if rows and 'id' in rows[0]:
            new_id = rows[0]['id']
            print(f"✅ 新增任務成功，Sequence: {next_sequence} ({start_point} -> {target_point}), DB ID: {new_id}")
            # 💥 關鍵修正 C: 回傳 new_id
            return new_id
        else:
            # 即使 DB 操作成功，如果沒有獲取到 ID，則視為失敗或邏輯異常
            print(f"❌ 警告：新增任務成功，但無法獲取返回的 ID。")
            # 由於 DB 寫入已成功 (commit=True)，我們將讓它繼續運行
            # 但為了滿足外部的 `if new_id` 檢查，我們返回 None (如果獲取 ID 失敗)
            return None
        
    def emergency_insert_task(self, start_point: str, target_point: str, content: str = ""):
        """
        緊急插單：將新任務插入 sequence 極小值，然後呼叫重排序確保它排在第一位 (sequence=1)。
        """
        try:
            insert_query = """
            INSERT INTO tasks 
            (sequence, start_point, target_point, mission_content)
            VALUES (0, %s, %s, %s)
            RETURNING id; -- 返回新增任務的 ID (可選) 這是 PostgreSQL (Postgres) 資料庫特有的強大功能
            """
            params = (start_point, target_point, content)

             # 執行插入，但暫不提交 (commit=False)
            rows = self._execute_query(insert_query, params, fetch=True, commit=False)

            if not rows or 'id' not in rows[0]:
                # 如果插入失敗，直接返回 None，並假設 _execute_query 會處理回滾
                print("❌ 插入緊急任務失敗。")
                return None
                
            new_id = rows[0]['id']

            # 2. 呼叫重排序函式，將所有未完成任務的 sequence 重新編號
            # 由於新任務的 sequence 是 0，它將會被重新編號為 1。
            print("💡 正在執行任務重排序...")
            # 注意: 你的 _resequence_pending_tasks 裡面應該有 commit=True
            self._resequence_pending_tasks() 

            # 3. 返回新任務 ID
            print(f"🚨 緊急插單成功，DB ID: {new_id}，已重排序。")
            return new_id


        except Exception as e:
            # 錯誤處理
            print(f"❌ 緊急插單操作失敗: {e}")
            return None



    def add_batch_tasks(self, missions_list):
        """
        一次性將多個任務批次插入資料庫 (高效)。
        missions_list 格式: [(start_point, target_point, mission_content), ...]
        """
        if not missions_list:
            return True # 沒有任務要新增，視為成功
            
        try:
            # 1. 獲取當前最大的 sequence 號碼
            # 由於我們要取結果，這裡使用 fetch=True
            max_seq_result = self._execute_query("SELECT MAX(sequence) FROM public.tasks;", fetch=True)
            
            # 提取 MAX(sequence) 的值。max_seq_result 是一個 [{'max': N}] 的列表
            if max_seq_result and max_seq_result[0]['max'] is not None:
                last_sequence = max_seq_result[0]['max']
            else:
                last_sequence = -1
                
            # 2. 準備數據：為每個任務計算 sequence 號碼，並添加預設值
            data_to_insert = []
            for i, (start, target, content) in enumerate(missions_list):
                new_sequence = last_sequence + i + 1
                data_to_insert.append((
                    new_sequence,          # sequence (INT)
                    start,                 # start_point (Varying)
                    target,                # target_point (Varying)
                    content,               # mission_content (Varying)
                    'Pending',             # status (Varying)
                    False                  # mir_command_sent (Boolean)
                ))
                
            # 3. 構建 SQL 模板並執行批次插入
            cols = "(sequence, start_point, target_point, mission_content, status, mir_command_sent)"
            sql_template = f"INSERT INTO public.tasks {cols} VALUES %s;"
            
            # 呼叫新的內部批次執行方法
            return self._execute_batch(sql_template, data_to_insert)
            
        except Exception as e:
            print(f"❌ 任務批次處理錯誤: {e}")
            return False




    #-------------------------------------讀取系列---------------------------------------------#

    def get_pending_tasks(self):
        """
        取得所有「待執行」和「執行中」的任務，並依 sequence 排序 (隊伍順序)。
        用於填充 GUI 的 QTableWidget (實現「掛號清單」)。
        """
        query = """
        SELECT id, sequence, start_point, target_point, mission_content, status
        FROM tasks 
        WHERE status IN ('Pending', 'Executing') 
        ORDER BY sequence ASC;
        """
        # 注意: 此處返回的是 List of Dicts，方便在 PySide6 中迭代填充 QTableWidget
        return self._execute_query(query, fetch=True)
    
    def get_currently_executing_task(self):
        query = """
        SELECT id, sequence, start_point, target_point, mission_content, status
        FROM tasks 
        WHERE status = 'Executing'
        ORDER BY sequence ASC
        LIMIT 1;
        """
        result = self._execute_query(query, fetch=True)
        return result[0] if result else None

    
    def get_highest_priority_task(self):
        query = """
        SELECT id, sequence, start_point, target_point, mission_content, status
        FROM tasks 
        WHERE status = 'Pending'
        ORDER BY sequence ASC
        LIMIT 1;
        """
        return self._execute_query(query, fetch=True)



    #-------------------------------------更新系列---------------------------------------------#

    def update_task_status(self, task_id: int, new_status: str, command_sent: bool = None):
        """
        更新特定任務的狀態 (例如從 Pending 變成 Executing 或 Completed)。
        """
        if new_status == "Completed":
            # 這是關鍵修正：Completed 任務必須強制將 sequence 設為 0
            # 只有在明確傳入 command_sent 時才更新
            if command_sent is not None:
                query = "UPDATE tasks SET status = %s, mir_command_sent = %s, sequence = 0 WHERE id = %s;"
                params = (new_status, command_sent, task_id)
            else:
                query = "UPDATE tasks SET status = %s, sequence = 0 WHERE id = %s;"
                params = (new_status, task_id)
        else:
            if command_sent is not None:
                query = "UPDATE tasks SET status = %s, mir_command_sent = %s WHERE id = %s;"
                params = (new_status, command_sent, task_id)
            else:
                query = "UPDATE tasks SET status = %s WHERE id = %s;"
                params = (new_status, task_id)

        self._execute_query(query, params, commit=True)
        print(f"✅ 任務 ID {task_id} 狀態更新為 {new_status}")

        # 新增的關鍵邏輯 - 僅在任務完成後執行重編號
        if new_status == "Completed":
            self._resequence_pending_tasks() 
            print("🔧 任務隊列重編號完成。")

    def _resequence_pending_tasks(self):
        """
        重新編號所有狀態不是 'Completed' 的任務，確保 sequence 從 1 開始連續。
        """
        # 這是 PostgreSQL 的一個高級用法，用於批量更新並重編序號
        # 它會選出所有未完成的任務，並為它們分配一個新的 row_number (即 1, 2, 3...)
        resequence_query = """
        WITH ordered_tasks AS (
            SELECT 
                id,
                ROW_NUMBER() OVER (ORDER BY sequence ASC) as new_sequence
            FROM tasks
            WHERE status IN ('Pending', 'Executing') -- 只對未完成的任務重編號
        )
        UPDATE tasks AS t
        SET sequence = ot.new_sequence
        FROM ordered_tasks AS ot
        WHERE t.id = ot.id;
        """
        self._execute_query(resequence_query, commit=True)

    def delete_task(self, task_id: int):
        query = "DELETE FROM tasks WHERE id = %s;"
        params = (task_id,)
        self._execute_query(query, params, commit=True)
        print(f"✅ 任務 ID {task_id} 已刪除。")



# # --- 測試你的 TaskDBManager 類別 (可選) ---
# # DB_CONFIG用途： 這份配置只在你自己單獨運行 TaskDBManager.py 檔案時（例如你之前做的測試）才會被執行。
# if __name__ == '__main__':
#     # *** 請修改成你的資料庫連線資訊！ ***
#     DB_CONFIG = {
#         'user': 'postgres',
#         'host': 'localhost',
#         'database': 'military_mir250_project',
#         'password': '123456',
#         'port': 5432
#     }

#     manager = TaskDBManager(DB_CONFIG)
#     if manager.connect():
#         # # 1. 測試新增任務
#         # manager.add_new_task("櫃台", "實驗室C", "運送文件")
#         # manager.add_new_task("實驗室A", "Lobby區", "取回物品")

#         # 2. 測試查詢待執行任務
#         print("\n--- 待執行任務清單 (初次) ---")
#         tasks = manager.get_pending_tasks()
#         print(tasks)
#         for task in tasks:
#             print(f"ID:{task['id']} | Seq:{task['sequence']} | 狀態:{task['status']} | 內容:{task['mission_content']}")
        
#         # 3. 測試任務完成 (假設第一個任務 ID 是 1)
#         if tasks:
#             first_task_id = tasks[0]['id']
#             # 當 MiR 完成任務後，更新狀態為 Completed
#             manager.update_task_status(first_task_id, 'Completed')

#         # 4. 再次查詢，驗證第一個任務已從清單中「上移/消失」
#         print("\n--- 待執行任務清單 (任務完成後) ---")
#         tasks_after = manager.get_pending_tasks()
#         for task in tasks_after:
#             print(f"ID:{task['id']} | Seq:{task['sequence']} | 狀態:{task['status']} | 內容:{task['mission_content']}")

#     manager.close()
