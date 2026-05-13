import time

import debugpy
from PySide6.QtCore import QThread, Signal


class TaskThread(QThread):
    finished_task = Signal(int, str, str, str)
    log_message = Signal(str)

    def __init__(self, main_window_instance, parent=None):
        super().__init__(parent)
        self.main_window = main_window_instance
        self.is_running = True
        self.is_no_mission = False
        self._mir_connection_lost = False

        self.functions = self.main_window.functions
        self.db_manager = self.main_window.task_db_manager

        self.MIR_LOCATION_MAP = self.main_window.MIR_LOCATION_MAP
        self.MIR_MISSION_GROUP_MAP = self.main_window.MIR_MISSION_GROUP_MAP
        self.CHARGING_STATION_NAME = self.main_window.CHARGING_STATION_NAME

    def _set_mir_connection_state(self, connected, context):
        if connected:
            if self._mir_connection_lost:
                self._mir_connection_lost = False
                self.log_message.emit(f"MiR connection restored while {context}.")
            return

        if not self._mir_connection_lost:
            self._mir_connection_lost = True
            self.log_message.emit(f"MiR connection lost while {context}; waiting for recovery.")

    def _resolve_mission_queue_id(self, before_max_id):
        for _ in range(10):
            if not self.is_running:
                return None

            time.sleep(0.3)
            current_max_id = self.functions.get_mission_queue_max_id()

            if current_max_id is None:
                self._set_mir_connection_state(False, "resolving mission queue id")
                continue

            self._set_mir_connection_state(True, "resolving mission queue id")

            if before_max_id is None or current_max_id > before_max_id:
                return current_max_id

        return None

    def _wait_for_mission_completion(self, mission_id, mq_id):
        """
        Wait for the MiR mission queue entry to settle.

        When mq_id is unavailable we keep the old idle-flag fallback so the
        scheduler can still recover after reconnect.
        """
        if not mq_id:
            self.log_message.emit(
                f"Task ID:{mission_id} has no mq_id; fallback to is_AMR_idle waiting."
            )
            while self.is_running and not self.main_window.is_AMR_idle:
                time.sleep(0.5)
            return "Unknown"

        while self.is_running:
            state = self.functions.get_mission_queue_id_state(mq_id)

            if state is None:
                self._set_mir_connection_state(False, f"waiting for mq_id={mq_id}")
                time.sleep(1)
                continue

            self._set_mir_connection_state(True, f"waiting for mq_id={mq_id}")

            if state == "Done":
                self.main_window.is_AMR_idle = True
                return "Done"

            if state == "Aborted":
                self.main_window.is_AMR_idle = True
                return "Aborted"

            time.sleep(0.5)

        return "Stopped"

    def _send_robot_to_charge_station(self):
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
        self.log_message.emit("Task scheduler started.")

        while self.is_running:
            self.log_message.emit("Looking for the next pending task...")
            priority_tasks = self.db_manager.get_highest_priority_task()

            if not priority_tasks:
                self.is_no_mission = True
                self.log_message.emit("No pending tasks. Sending MiR back to charge station.")
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
            task_id = mission["id"]
            start_point = mission["start_point"]
            target_point = mission["target_point"]
            mission_content = mission["mission_content"]

            mir_start = self.MIR_LOCATION_MAP.get(start_point)
            mir_target = self.MIR_LOCATION_MAP.get(target_point)
            mir_mission = self.MIR_MISSION_GROUP_MAP.get(mission_content)

            self.log_message.emit(
                f"Dispatching task ID:{task_id} from {mir_start} to {mir_target}."
            )

            if not (mir_mission and mir_start and mir_target):
                self.log_message.emit("Mission mapping is incomplete; skip this cycle.")
                time.sleep(1)
                continue

            before_max_id = self.functions.get_mission_queue_max_id()
            try:
                self.functions.run_combo_location_multi_var(
                    mir_start, mir_target, mir_mission
                )
                self._set_mir_connection_state(True, f"sending task ID:{task_id}")
            except Exception as exc:
                self._set_mir_connection_state(False, f"sending task ID:{task_id}")
                self.log_message.emit(
                    f"Task ID:{task_id} failed to send due to MiR/API error: {exc}"
                )
                time.sleep(1)
                continue

            after_max_id = self._resolve_mission_queue_id(before_max_id)

            self.db_manager.update_task_status(
                task_id, new_status="Executing", command_sent=True
            )

            if after_max_id is not None:
                self.db_manager.update_task_mq_id(task_id, after_max_id)
            else:
                self.log_message.emit(
                    "Mission queue id was not resolved in time; reconciliation will handle it later."
                )

            self.main_window.is_AMR_idle = False
            self.log_message.emit(f"Task ID:{task_id} sent to MiR.")

            self.log_message.emit("Waiting for MiR to finish the task...")
            mission_state = self._wait_for_mission_completion(task_id, after_max_id)

            if mission_state == "Done":
                self.finished_task.emit(task_id, "Completed", start_point, target_point)
                self.log_message.emit(f"Task ID:{task_id} reported Done by MiR.")
            elif mission_state == "Aborted":
                self.finished_task.emit(task_id, "Aborted", start_point, target_point)
                self.log_message.emit(f"Task ID:{task_id} reported Aborted by MiR.")
            elif mission_state == "Unknown":
                self.log_message.emit(
                    f"Task ID:{task_id} finished waiting without mq_id; waiting for reconciliation."
                )
            elif mission_state == "Stopped":
                self.log_message.emit(f"Task ID:{task_id} stop requested before completion.")
                break

            if not self.is_running:
                self.log_message.emit(f"Stop requested after task ID:{task_id}.")
                break

            if self.main_window.is_low_battery:
                self.log_message.emit("Low battery detected. Sending MiR to charge station.")
                self._send_robot_to_charge_station()
                while self.main_window.is_low_battery and self.is_running:
                    time.sleep(1)

            time.sleep(0.1)

        self.log_message.emit("Task scheduler stopped.")
        self._send_robot_to_charge_station()

    def stop(self):
        """Request a graceful stop after the current mission finishes."""
        self.is_running = False
