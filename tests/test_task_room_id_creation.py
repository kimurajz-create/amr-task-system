import unittest
from types import SimpleNamespace
from unittest.mock import patch

from TaskDBManager import TaskDBManager
from main import MainWindow


class _RecordingAddTaskDb:
    def __init__(self, new_id):
        self.new_id = new_id
        self.calls = []

    def add_new_task(self, start_place, destination, mission_content, room_id=None):
        self.calls.append(
            {
                "start_place": start_place,
                "destination": destination,
                "mission_content": mission_content,
                "room_id": room_id,
            }
        )
        return self.new_id


class _RecordingEmergencyTaskDb:
    def __init__(self, new_id):
        self.new_id = new_id
        self.calls = []

    def emergency_insert_task(self, start_place, destination, mission_content, room_id=None):
        self.calls.append(
            {
                "start_place": start_place,
                "destination": destination,
                "mission_content": mission_content,
                "room_id": room_id,
            }
        )
        return self.new_id


class _FakeComboBox:
    def __init__(self, text):
        self._text = text

    def currentText(self):
        return self._text


class RecordingTaskDBManager(TaskDBManager):
    def __init__(self):
        super().__init__({})
        self.query_calls = []
        self.resequence_calls = 0

    def _execute_query(self, query, params=None, fetch=False, commit=False):
        self.query_calls.append(
            {
                "query": query,
                "params": params,
                "fetch": fetch,
                "commit": commit,
            }
        )
        if "RETURNING id" in query:
            return [{"id": 99}]
        return []

    def _resequence_pending_tasks(self):
        self.resequence_calls += 1


class TaskRoomIdCreationTests(unittest.TestCase):
    def test_create_new_db_task_keeps_existing_room_id_mapping_behavior(self):
        fake_window = SimpleNamespace(
            ROOM_ID_MAP={"Operating Room 1": "OR01"},
            task_db_manager=_RecordingAddTaskDb(123),
        )

        new_id = MainWindow.create_new_db_task(
            fake_window,
            "Sterilization",
            "Operating Room 1",
            "Deliver sterile items",
        )

        self.assertEqual(123, new_id)
        self.assertEqual(
            [
                {
                    "start_place": "Sterilization",
                    "destination": "Operating Room 1",
                    "mission_content": "Deliver sterile items",
                    "room_id": "OR01",
                }
            ],
            fake_window.task_db_manager.calls,
        )

    def test_emergency_insert_uses_same_room_id_mapping_as_normal_task_creation(self):
        fake_window = SimpleNamespace(
            ROOM_ID_MAP={"Operating Room 1": "OR01"},
            cmb_location2=_FakeComboBox("Sterilization"),
            cmb_location=_FakeComboBox("Operating Room 1"),
            cmb_mission=_FakeComboBox("Deliver sterile items"),
            task_db_manager=_RecordingEmergencyTaskDb(456),
            refresh_task_list_called=0,
        )
        fake_window.refresh_task_list = lambda: setattr(
            fake_window, "refresh_task_list_called", fake_window.refresh_task_list_called + 1
        )

        with patch("builtins.print"):
            MainWindow.on_emergency_cut_line_clicked(fake_window)

        self.assertEqual(
            [
                {
                    "start_place": "Sterilization",
                    "destination": "Operating Room 1",
                    "mission_content": "Deliver sterile items",
                    "room_id": "OR01",
                }
            ],
            fake_window.task_db_manager.calls,
        )
        self.assertEqual(1, fake_window.refresh_task_list_called)

    def test_emergency_insert_task_writes_room_id_without_changing_resequence_behavior(self):
        manager = RecordingTaskDBManager()

        with patch("builtins.print"):
            new_id = manager.emergency_insert_task(
                "Sterilization",
                "Operating Room 1",
                "Deliver sterile items",
                room_id="OR01",
            )

        self.assertEqual(99, new_id)
        self.assertEqual(1, manager.resequence_calls)
        self.assertEqual(1, len(manager.query_calls))
        self.assertIn("room_id", manager.query_calls[0]["query"])
        self.assertEqual(
            ("Sterilization", "Operating Room 1", "Deliver sterile items", "OR01"),
            manager.query_calls[0]["params"],
        )
        self.assertFalse(manager.query_calls[0]["commit"])


if __name__ == "__main__":
    unittest.main()
