import unittest
from unittest.mock import MagicMock

from TaskDBManager import TaskDBManager


class DeleteTaskBlocksExecutingTests(unittest.TestCase):
    def test_delete_task_rejects_executing_status(self):
        manager = TaskDBManager.__new__(TaskDBManager)
        manager._execute_query = MagicMock(
            return_value=[{"status": "Executing"}]
        )

        deleted = manager.delete_task(42)

        self.assertFalse(deleted)
        manager._execute_query.assert_called_once()
        args, kwargs = manager._execute_query.call_args
        self.assertIn("SELECT status", args[0])

    def test_delete_task_allows_pending_status(self):
        manager = TaskDBManager.__new__(TaskDBManager)
        manager._execute_query = MagicMock(
            side_effect=[
                [{"status": "Pending"}],
                None,
            ]
        )

        deleted = manager.delete_task(7)

        self.assertTrue(deleted)
        self.assertEqual(2, manager._execute_query.call_count)
        delete_args, delete_kwargs = manager._execute_query.call_args_list[1]
        self.assertIn("DELETE FROM tasks", delete_args[0])
        self.assertTrue(delete_kwargs.get("commit"))


if __name__ == "__main__":
    unittest.main()
