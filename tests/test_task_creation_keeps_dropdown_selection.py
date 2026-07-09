import unittest
from types import SimpleNamespace
from unittest.mock import patch

from main import MainWindow


class _FakeComboBox:
    def __init__(self, text):
        self._text = text
        self.set_current_index_calls = []

    def currentText(self):
        return self._text

    def setCurrentIndex(self, index):
        self.set_current_index_calls.append(index)


class _EmergencyTaskDbStub:
    def __init__(self, new_id):
        self.new_id = new_id
        self.calls = []

    def emergency_insert_task(self, start_place, destination, mission_content):
        self.calls.append((start_place, destination, mission_content))
        return self.new_id


class TaskCreationKeepsDropdownSelectionTests(unittest.TestCase):
    def test_add_new_mission_success_does_not_reset_dropdowns(self):
        fake_window = SimpleNamespace()
        fake_window.cmb_location2 = _FakeComboBox("充電樁")
        fake_window.cmb_location = _FakeComboBox("手術室1")
        fake_window.cmb_mission = _FakeComboBox("國軍台中醫院空車運輸")
        fake_window.create_new_db_task = lambda start_place, destination, mission_content: 123
        fake_window.refresh_task_list_called = 0
        fake_window.refresh_task_list = lambda: setattr(
            fake_window, "refresh_task_list_called", fake_window.refresh_task_list_called + 1
        )

        with patch("builtins.print"):
            MainWindow.on_add_new_mission_clicked(fake_window)

        self.assertEqual(1, fake_window.refresh_task_list_called)
        self.assertEqual([], fake_window.cmb_location2.set_current_index_calls)
        self.assertEqual([], fake_window.cmb_location.set_current_index_calls)
        self.assertEqual([], fake_window.cmb_mission.set_current_index_calls)

    def test_emergency_insert_success_does_not_reset_dropdowns(self):
        fake_window = SimpleNamespace()
        fake_window.cmb_location2 = _FakeComboBox("充電樁")
        fake_window.cmb_location = _FakeComboBox("手術室1")
        fake_window.cmb_mission = _FakeComboBox("國軍台中醫院空車運輸")
        fake_window.task_db_manager = _EmergencyTaskDbStub(456)
        fake_window.refresh_task_list_called = 0
        fake_window.refresh_task_list = lambda: setattr(
            fake_window, "refresh_task_list_called", fake_window.refresh_task_list_called + 1
        )

        with patch("builtins.print"):
            MainWindow.on_emergency_cut_line_clicked(fake_window)

        self.assertEqual(
            [("充電樁", "手術室1", "國軍台中醫院空車運輸")],
            fake_window.task_db_manager.calls,
        )
        self.assertEqual(1, fake_window.refresh_task_list_called)
        self.assertEqual([], fake_window.cmb_location2.set_current_index_calls)
        self.assertEqual([], fake_window.cmb_location.set_current_index_calls)
        self.assertEqual([], fake_window.cmb_mission.set_current_index_calls)


if __name__ == "__main__":
    unittest.main()
