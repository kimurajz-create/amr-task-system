from PySide6.QtCore import QThread, Signal
import time
import debugpy


class TaskThread(QThread):
    finished_task = Signal(int)
    log_message = Signal(str)

    def __init__(self, main_window_instance, parent=None):
        super().__init__(parent)
        self.main_window = main_window_instance
        self.is_running = True
        self.is_no_mission = False

        self.functions = self.main_window.functions
        self.db_manager = self.main_window.task_db_manager

        self.MIR_LOCATION_MAP = self.main_window.MIR_LOCATION_MAP
        self.MIR_MISSION_GROUP_MAP = self.main_window.MIR_MISSION_GROUP_MAP
        self.CHARGING_STATION_NAME = self.main_window.CHARGING_STATION_NAME

    def _resolve_mission_queue_id(self, before_max_id):
        # MiR 任務送出後，短時間輪詢 mission_queue 最大 id，
        # 把這次新建立的 queue id 綁回本地 DB，後續完成判斷都靠它。
        for _ in range(10):
            time.sleep(0.3)
            current_max_id = self.functions.get_mission_queue_max_id()
            if current_max_id is None:
                continue
            if before_max_id is None or current_max_id > before_max_id:
                return current_max_id
        return None

    def _wait_for_mission_completion(self, mission_id, mq_id):
        """
        Wait for the MiR mission queue entry to settle.

        This keeps completion ownership inside TaskThread so deleting the local
        DB row does not leave the scheduler blocked forever.
        """
        if not mq_id:
            # 極少數情況如果抓不到 mq_id，只能退回舊的 is_AMR_idle 備援等待。
            self.log_message.emit(
                f"⚠️ 任務 ID:{mission_id} 缺少 mq_id，改用 is_AMR_idle 備援等待。"
            )
            while not self.main_window.is_AMR_idle:
                time.sleep(0.5)
            return "Unknown"

        while True:
            # 這裡直接盯 MiR 的 mq_id 狀態，而不是只依賴 DB 裡是否還有 Executing。
            # 這樣就算使用者把執行中的任務從本地 DB 刪掉，thread 仍能知道 MiR 何時跑完。
            state = self.functions.get_mission_queue_id_state(mq_id)
            if state == "Done":
                self.main_window.is_AMR_idle = True
                return "Done"
            if state == "Aborted":
                self.main_window.is_AMR_idle = True
                return "Aborted"
            time.sleep(0.5)

    def _send_robot_to_charge_station(self):
        # 排程清空或手動 stop 後，統一走這個入口回充電站。
        charge_code = self.MIR_LOCATION_MAP.get(self.CHARGING_STATION_NAME)
        self.functions.run_combo_location(charge_code)

    def run(self):
        """
        Main scheduler loop:
        1. fetch the next pending task
        2. send it to MiR
        3. wait for its mq_id to finish
        """
        # debugpy.debug_this_thread()

        self.is_running = True
        self.log_message.emit("✅ 任務排程執行緒已啟動。")

        while self.is_running:
            self.log_message.emit("🔁 準備抓取下一筆 Pending 任務...")
            priority_tasks = self.db_manager.get_highest_priority_task()

            if not priority_tasks:
                self.is_no_mission = True
                self.log_message.emit("📢 任務清單為空，命令 MiR 前往充電站...")
                self._send_robot_to_charge_station()

                while self.is_no_mission and self.is_running:
                    time.sleep(1)

                    if not self.is_running:
                        break

                    priority_tasks = self.db_manager.get_highest_priority_task()
                    if priority_tasks:
                        self.is_no_mission = False
                        break

                if not self.is_running:
                    break

            mission = priority_tasks[0]
            mir_code_id = mission["id"]
            mir_code_s = self.MIR_LOCATION_MAP.get(mission["start_point"])
            mir_code_d = self.MIR_LOCATION_MAP.get(mission["target_point"])
            mir_code = self.MIR_MISSION_GROUP_MAP.get(mission["mission_content"])

            self.log_message.emit(
                f"➡️ 正在發送任務 ID:{mir_code_id} 從 {mir_code_s} 到 {mir_code_d}"
            )

            if not (mir_code and mir_code_s and mir_code_d):
                self.log_message.emit("❌ 地點或對應代碼無效，跳過此任務。")
                time.sleep(1)
                continue

            before_max_id = self.functions.get_mission_queue_max_id()
            self.functions.run_combo_location_multi_var(mir_code_s, mir_code_d, mir_code)

            after_max_id = self._resolve_mission_queue_id(before_max_id)

            # 先標記成 Executing，避免因為使用者刷新 UI 或 queue 更新較慢而重送同一筆。
            self.db_manager.update_task_status(
                mir_code_id, new_status="Executing", command_sent=True
            )

            if after_max_id is not None:
                self.db_manager.update_task_mq_id(mir_code_id, after_max_id)
            else:
                self.log_message.emit(
                    "⚠️ mission_queue id 沒有成功取得，後續只能用備援邏輯等待完成。"
                )

            self.main_window.is_AMR_idle = False
            self.log_message.emit(f"✅ 任務 ID:{mir_code_id} 已送出。")

            self.log_message.emit("⏳ 等待 MiR 完成任務...")
            mission_state = self._wait_for_mission_completion(mir_code_id, after_max_id)

            current = self.db_manager.get_currently_executing_task()

            if mission_state == "Done":
                if current and current["id"] == mir_code_id:
                    self.db_manager.update_task_status(mir_code_id, new_status="Completed")
                    self.finished_task.emit(mir_code_id)
                    self.log_message.emit(f"✅ 任務 ID:{mir_code_id} 已完成。")
                else:
                    # 任務可能在執行中被使用者從本地 DB 刪掉；
                    # MiR 已完成，但本地既然不再追蹤，就不要硬寫回 Completed。
                    self.log_message.emit(
                        f"⚠️ 任務 ID:{mir_code_id} 已在 MiR 完成，但本地任務已不在 Executing，略過 Completed 回寫。"
                    )
            elif mission_state == "Aborted":
                if current and current["id"] == mir_code_id:
                    self.db_manager.update_task_status(mir_code_id, new_status="Aborted")
                    self.log_message.emit(f"⚠️ 任務 ID:{mir_code_id} 已被 MiR 中止。")
                else:
                    self.log_message.emit(
                        f"⚠️ 任務 ID:{mir_code_id} 已在 MiR 中止，但本地任務已不在 Executing。"
                    )
            else:
                self.log_message.emit(
                    f"⚠️ 任務 ID:{mir_code_id} 完成狀態不明，保留目前 DB 狀態。"
                )

            if not self.is_running:
                # Stop 的語意不是立刻停車，而是「這趟完成後不要再接下一筆」。
                self.log_message.emit(f"🛑 任務 ID:{mir_code_id} 被手動中斷，退出排程。")
                break

            if self.main_window.is_low_battery:
                self.log_message.emit("⚠️ 電量低於閾值，命令 MiR 前往充電站...")
                self._send_robot_to_charge_station()
                while self.main_window.is_low_battery:
                    time.sleep(1)
                    if not self.is_running:
                        break

            time.sleep(0.1)

        self.log_message.emit("🛑 任務排程執行緒已停止。")
        self._send_robot_to_charge_station()

    def stop(self):
        """Request a graceful stop after the current mission finishes."""
        # 只停止後續排程，不會中斷 MiR 已經送出的當前任務。
        self.is_running = False
        # self.wait()
