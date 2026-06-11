import os
import types
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from main import MainWindow


class _PlainTextRecorder:
    def __init__(self):
        self.messages = []

    def appendPlainText(self, value):
        self.messages.append(value)

    def setPlainText(self, value):
        self.messages = [value]


class _TaskDbStub:
    def __init__(self, executing_task=None):
        self.executing_task = executing_task
        self.marked_errors = []
        self.updated_mq_ids = []

    def mark_room_error(self, room_id, error_code):
        self.marked_errors.append((room_id, error_code))

    def get_currently_executing_task(self):
        return self.executing_task

    def update_task_mq_id(self, task_id, mq_id):
        self.updated_mq_ids.append((task_id, mq_id))


class MirStatusPresentationRefreshTests(unittest.TestCase):
    def _build_fake_window(self):
        fake = types.SimpleNamespace()
        fake.api_error = False
        fake.current_mir_state_id = 3
        fake.current_mission_text = "Initial"
        fake.last_mission_text = None
        fake.mir_status_poll_disconnected = False
        fake.robot_glow_phase = 0
        fake.last_robot_world_pos = (1.25, 2.5)
        fake.draw_calls = []
        fake.label_updates = []
        fake.plntxtEdit_Info = _PlainTextRecorder()
        fake.txtEdit_GetPM = _PlainTextRecorder()
        fake.task_db_manager = _TaskDbStub()
        fake.refresh_task_list_calls = 0
        fake.draw_car_position = lambda world_x, world_y: fake.draw_calls.append(
            (world_x, world_y)
        )
        fake._update_status_label = lambda state_id: fake.label_updates.append(state_id)
        fake.refresh_task_list = lambda: setattr(
            fake,
            "refresh_task_list_calls",
            fake.refresh_task_list_calls + 1,
        )
        fake._refresh_robot_status_presentation = (
            lambda state_id=None, advance_glow=False: MainWindow._refresh_robot_status_presentation(
                fake,
                state_id=state_id,
                advance_glow=advance_glow,
            )
        )
        return fake

    def test_refresh_helper_updates_label_and_marker_together(self):
        fake = self._build_fake_window()

        MainWindow._refresh_robot_status_presentation(
            fake,
            state_id=5,
            advance_glow=True,
        )

        self.assertEqual(5, fake.current_mir_state_id)
        self.assertEqual(1, fake.robot_glow_phase)
        self.assertEqual([(1.25, 2.5)], fake.draw_calls)
        self.assertEqual([5], fake.label_updates)

    def test_api_error_handler_marks_db_and_refreshes_presentation(self):
        fake = self._build_fake_window()

        with patch("builtins.print"):
            MainWindow.api_error_handler(fake)

        self.assertTrue(fake.api_error)
        self.assertEqual([("MASTER", "API_ERROR")], fake.task_db_manager.marked_errors)
        self.assertEqual([3], fake.label_updates)
        self.assertEqual([(1.25, 2.5)], fake.draw_calls)

    def test_query_mir_info_clears_api_error_and_uses_shared_refresh(self):
        fake = self._build_fake_window()
        fake.api_error = True

        with patch("main.functions.check_MiR_status", return_value={"mission_text": "Deliver meds"}), patch(
            "main.functions.get_pending_mission_names",
            return_value=["Alpha", "Beta"],
        ), patch("main.functions.check_MiR_status_state_ID", return_value=9):
            MainWindow.query_mir_info(fake)

        self.assertFalse(fake.api_error)
        self.assertEqual("Deliver meds", fake.current_mission_text)
        self.assertEqual(9, fake.current_mir_state_id)
        self.assertEqual(1, fake.robot_glow_phase)
        self.assertEqual([(1.25, 2.5)], fake.draw_calls)
        self.assertEqual([9], fake.label_updates)
        self.assertEqual(1, len(fake.txtEdit_GetPM.messages))
        self.assertIn("Alpha", fake.txtEdit_GetPM.messages[0])
        self.assertIn("Beta", fake.txtEdit_GetPM.messages[0])
        self.assertEqual(1, len(fake.plntxtEdit_Info.messages))

    def test_query_mir_status_db_refreshes_on_disconnect_and_restore(self):
        fake = self._build_fake_window()
        fake.task_db_manager = _TaskDbStub(
            executing_task={
                "id": 7,
                "start_point": "A",
                "target_point": "B",
                "mq_id": 42,
            }
        )

        with patch("main.functions.get_mission_queue_id_state", return_value=None):
            MainWindow.query_mir_status_db(fake)

        self.assertTrue(fake.mir_status_poll_disconnected)
        self.assertEqual([3], fake.label_updates)
        self.assertEqual([(1.25, 2.5)], fake.draw_calls)

        with patch("main.functions.get_mission_queue_id_state", return_value="Executing"):
            MainWindow.query_mir_status_db(fake)

        self.assertFalse(fake.mir_status_poll_disconnected)
        self.assertEqual([3, 3], fake.label_updates)
        self.assertEqual([(1.25, 2.5), (1.25, 2.5)], fake.draw_calls)
        self.assertEqual(1, fake.refresh_task_list_calls)


if __name__ == "__main__":
    unittest.main()
