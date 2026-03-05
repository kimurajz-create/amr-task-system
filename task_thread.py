from PySide6.QtCore import QThread, Signal
import time
import debugpy


# 注意: 這個類別需要能夠訪問到你的 MiR 控制邏輯和資料庫管理器
# 這裡假設你的主視窗會傳遞必要的物件給它
# 參數傳遞方式是：透過物件實例的「引用」（Reference)
# main.py 創建 task_thread self.task_thread = TaskThread(self)
# TaskThread 的 __init__ 中，您接收 self.main_window = main_window_instance

class TaskThread(QThread):
    # 定義訊號，用於在執行緒完成操作時通知主執行緒 (UI)
    # 例如，發送任務完成的訊息，或更新 UI 的狀態
    finished_task = Signal(int) # 傳遞完成任務的 ID
    log_message = Signal(str)    # 傳遞日誌訊息給主介面顯示

    def __init__(self, main_window_instance, parent=None):
        super().__init__(parent)
        # 接收主視窗的實例，這樣就可以訪問到 self.db_manager, self.is_running, self.is_AMR_idle 等變數
        self.main_window = main_window_instance
        self.is_running = True # 執行緒自己的運行旗標，由主介面控制
        self.is_no_mission = False
        
        # 為了簡潔，從主視窗實例中獲取這些物件
        self.functions = self.main_window.functions # 假設你的 MiR 函數被存放在這
        self.db_manager = self.main_window.task_db_manager
        
        
        # 輔助常數
        self.MIR_LOCATION_MAP = self.main_window.MIR_LOCATION_MAP
        self.MIR_MISSION_GROUP_MAP = self.main_window.MIR_MISSION_GROUP_MAP
        self.CHARGING_STATION_NAME = self.main_window.CHARGING_STATION_NAME


    def run(self):
        """
        將你原來的 on_map_location_clicked 裡面的 while 迴圈邏輯移動到這裡
        """
        # 執行debug才需要打開
        # debugpy.debug_this_thread()

        self.is_running = True
        self.log_message.emit("✅ 任務排程執行緒已啟動。")

        while self.is_running:
            self.log_message.emit("🔁 準備抓取下一筆 Pending 任務...")
            # 1. 從資料庫獲取當前最優先任務
            priority_tasks = self.db_manager.get_highest_priority_task()
            
            if not priority_tasks:
                self.is_no_mission = True
                self.log_message.emit("📢 任務清單為空，命令 MiR 前往充電站...")
                
                # 命令AMR去充電站 (cccccccc)
                charge_code = self.MIR_LOCATION_MAP.get(self.CHARGING_STATION_NAME)
                self.functions.run_combo_location(charge_code) 
                # self.is_running 確保當用戶按下「停止」按鈕時，執行緒能即時退出。
                while self.is_no_mission and self.is_running:
                    time.sleep(1) # 這裡可以睡久一點，因為任務不頻繁
                    
                    # 檢查是否有停止訊號
                    if not self.is_running:
                        break
                        
                    # 再次檢查是否有新任務
                    priority_tasks = self.db_manager.get_highest_priority_task()
                    if priority_tasks:
                        self.is_no_mission = False
                        break
                
                if not self.is_running:
                     break
            
            # 2. 處理任務
            mission = priority_tasks[0]
            mir_code_id = mission['id']
            mir_code_s = self.MIR_LOCATION_MAP.get(mission['start_point'])
            mir_code_d = self.MIR_LOCATION_MAP.get(mission['target_point'])      
            mir_code = self.MIR_MISSION_GROUP_MAP.get(mission['mission_content'])
            
            self.log_message.emit(f"➡️ 正在發送任務 ID:{mir_code_id} 從 {mir_code_s} 到 {mir_code_d}")

            # 3. 發送任務指令
            # (省略充電判斷邏輯，直接發送任務)
            if mir_code and mir_code_s and mir_code_d:
                self.functions.run_combo_location_multi_var(mir_code_s, mir_code_d, mir_code)
                self.db_manager.update_task_status(mir_code_id, new_status="Executing", command_sent=True)
                
                # ⭐ 關鍵修正點：AMR 狀態設為忙碌 (False)
                self.main_window.is_AMR_idle = False 
                
                self.log_message.emit(f"✅ 任務 ID:{mir_code_id} 已送出。")
            else:
                self.log_message.emit("❌ 地點或對應代碼無效，跳過此任務。")
                time.sleep(1) # 避免連續出錯
                continue # 跳到下一個迴圈，檢查新任務

            # 4. 等待任務完成 (is_AMR_idle = False 時就會一直卡在這個 while 裡 sleep，直到別的地方把它改成 True 才會跳出，代表任務被判定完成。)
            self.log_message.emit("⏳ 等待 MiR 完成任務...")
            while not self.main_window.is_AMR_idle:
                time.sleep(0.5) # 降低等待頻率以節省資源

            # 5. 任務完成後的處理
            self.db_manager.update_task_status(mir_code_id, new_status="Completed")
            self.finished_task.emit(mir_code_id) # 通知主介面更新清單
            self.log_message.emit(f"✅ 任務 ID:{mir_code_id} 已完成。")
            
            # 💥 關鍵修正：確保跳出阻塞後，立即檢查中斷旗標
            if not self.is_running:
                # 這是手動中斷，不應該設為 Completed
                self.log_message.emit(f"🛑 任務 ID:{mir_code_id} 被手動中斷，退出排程。")
                break # 立即跳出最外層的 while self.is_running 迴圈
            
            # 檢查低電量 20%
            if self.main_window.is_low_battery:
                self.log_message.emit("⚠️ 電量過低，下一個任務為強制充電。")
                charge_code = self.MIR_LOCATION_MAP.get(self.CHARGING_STATION_NAME)
                self.functions.run_combo_location(charge_code) 
                while self.main_window.is_low_battery:
                    time.sleep(1) # 這裡可以睡久一點，因為任務不頻繁
                    if not self.is_running:
                        break
            time.sleep(0.1) # 避免主迴圈頻繁檢查

        self.log_message.emit("🛑 任務排程執行緒已停止。")
        charge_code = self.MIR_LOCATION_MAP.get(self.CHARGING_STATION_NAME)
        self.functions.run_combo_location(charge_code) 


    def stop(self):
        """用於從主執行緒安全停止這個執行緒"""
        self.is_running = False
        # self.wait() # 等待 run() 函式安全退出，不mark掉會報錯當掉，暫時停用