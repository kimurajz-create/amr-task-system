import os
import types
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from task_thread import TaskThread


class _FunctionsStub:
    def run_combo_location(self, _charge_code):
        return None


class _TaskDbStub:
    def __init__(self):
        self.transitions = []

    def transition_task_status(self, task_id, from_status, to_status, command_sent=None):
        self.transitions.append((task_id, from_status, to_status, command_sent))
        return True


class TaskThreadInvalidMappingTests(unittest.TestCase):
    def _build_thread(self):
        fake_window = types.SimpleNamespace()
        fake_window.functions = _FunctionsStub()
        fake_window.task_db_manager = _TaskDbStub()
        fake_window.MIR_LOCATION_MAP = {"手術室1": "MH_Robot position OA 1"}
        fake_window.MIR_MISSION_GROUP_MAP = {"Demo_空車運送": "Lobby Demo Empty Cart Transport"}
        fake_window.CHARGING_STATION_NAME = "充電樁"
        fake_window.is_AMR_idle = True
        fake_window.is_low_battery = False
        return TaskThread(fake_window)

    def test_describe_missing_mapping_lists_all_missing_parts(self):
        thread = self._build_thread()

        missing = thread._describe_missing_mapping(
            start_point="舊場域起點",
            target_point="舊場域終點",
            mission_content="未知任務",
            mir_start=None,
            mir_target=None,
            mir_mission=None,
        )

        self.assertIn("start_point='舊場域起點'", missing)
        self.assertIn("target_point='舊場域終點'", missing)
        self.assertIn("mission_content='未知任務'", missing)

    def test_abort_invalid_pending_task_marks_task_aborted(self):
        thread = self._build_thread()
        log_messages = []
        thread.log_message.connect(log_messages.append)

        thread._abort_invalid_pending_task(
            task_id=807,
            start_point="Shelf position test only 01",
            target_point="Shelf position test only 02",
            mission_content="Demo_空車運送",
            mir_start=None,
            mir_target=None,
            mir_mission="Lobby Demo Empty Cart Transport",
        )

        self.assertEqual(
            [(807, "Pending", "Aborted", False)],
            thread.db_manager.transitions,
        )
        self.assertEqual(1, len(log_messages))
        self.assertIn("Task ID:807 has incomplete mission mapping", log_messages[0])
        self.assertIn("start_point='Shelf position test only 01'", log_messages[0])
        self.assertIn("target_point='Shelf position test only 02'", log_messages[0])


if __name__ == "__main__":
    unittest.main()
