import unittest

from TaskDBManager import TaskDBManager
from main import build_ui_location_publish_rows, load_site_config


class RecordingTaskDBManager(TaskDBManager):
    def __init__(self):
        super().__init__({})
        self.query_calls = []
        self.batch_calls = []

    def _execute_query(self, query, params=None, fetch=False, commit=False):
        self.query_calls.append(
            {
                "query": query,
                "params": params,
                "fetch": fetch,
                "commit": commit,
            }
        )
        return None

    def _execute_batch(self, sql_template, data_list):
        self.batch_calls.append(
            {
                "sql_template": sql_template,
                "data_list": list(data_list),
            }
        )
        return True


class UiLocationsPublishingTests(unittest.TestCase):
    def test_build_ui_location_publish_rows_uses_site_config_and_skips_locations_without_room_id(self):
        site_config = load_site_config("hospital")

        rows = build_ui_location_publish_rows(site_config)

        self.assertEqual(rows, sorted(rows, key=lambda row: row[0]))
        self.assertIn(("手術室1", "MH_Robot position OA 1", "OR01"), rows)
        self.assertIn(("洗滌室", "MH_Robot position wash room", "WR01"), rows)
        self.assertFalse(any(display_name == "充電樁" for display_name, _, _ in rows))
        self.assertTrue(all(room_id for _, _, room_id in rows))

    def test_publish_ui_locations_replaces_existing_rows_with_site_projection(self):
        manager = RecordingTaskDBManager()
        rows = [
            ("手術室1", "MH_Robot position OA 1", "OR01"),
            ("洗滌室", "MH_Robot position wash room", "WR01"),
        ]

        success = manager.publish_ui_locations(rows)

        self.assertTrue(success)
        self.assertEqual(1, len(manager.query_calls))
        self.assertEqual("DELETE FROM ui_locations;", manager.query_calls[0]["query"].strip())
        self.assertTrue(manager.query_calls[0]["commit"])
        self.assertEqual(1, len(manager.batch_calls))
        self.assertIn(
            "INSERT INTO ui_locations (display_name, mir_code, room_id)",
            manager.batch_calls[0]["sql_template"],
        )
        self.assertEqual(rows, manager.batch_calls[0]["data_list"])


if __name__ == "__main__":
    unittest.main()
