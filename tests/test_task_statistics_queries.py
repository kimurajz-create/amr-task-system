import unittest

from TaskDBManager import TaskDBManager


class RecordingTaskDBManager(TaskDBManager):
    def __init__(self, responses):
        super().__init__({})
        self.responses = list(responses)
        self.calls = []

    def _execute_query(self, query, params=None, fetch=False, commit=False):
        self.calls.append(
            {
                "query": query,
                "params": params,
                "fetch": fetch,
                "commit": commit,
            }
        )
        return self.responses.pop(0) if self.responses else []


class TaskStatisticsQueryTests(unittest.TestCase):
    def test_get_task_status_summary_returns_canonical_and_other_counts(self):
        manager = RecordingTaskDBManager(
            [[
                {"status": "Pending", "task_count": 2},
                {"status": "Executing", "task_count": 1},
                {"status": "Completed", "task_count": 4},
                {"status": "Aborted", "task_count": 3},
                {"status": "Paused", "task_count": 5},
            ]]
        )

        summary = manager.get_task_status_summary()

        self.assertEqual(2, summary["pending_count"])
        self.assertEqual(1, summary["executing_count"])
        self.assertEqual(4, summary["completed_count"])
        self.assertEqual(3, summary["aborted_count"])
        self.assertEqual(3, summary["active_count"])
        self.assertEqual(7, summary["finished_count"])
        self.assertEqual(5, summary["other_status_count"])
        self.assertEqual(15, summary["total_count"])
        self.assertEqual(5, summary["status_breakdown"]["Paused"])
        self.assertTrue(manager.calls[0]["fetch"])

    def test_get_task_volume_by_mission_applies_limit_and_blank_safe_grouping(self):
        manager = RecordingTaskDBManager(
            [[
                {"mission_content": "送藥", "task_count": 6},
                {"mission_content": "(未填寫)", "task_count": 2},
            ]]
        )

        rows = manager.get_task_volume_by_mission(limit=5)

        self.assertEqual(
            [
                {"mission_content": "送藥", "task_count": 6},
                {"mission_content": "(未填寫)", "task_count": 2},
            ],
            rows,
        )
        self.assertEqual((5,), manager.calls[0]["params"])
        self.assertIn(
            "GROUP BY COALESCE(NULLIF(BTRIM(mission_content), ''), '(未填寫)')",
            manager.calls[0]["query"],
        )

    def test_hotspot_queries_return_named_counts_and_route_labels(self):
        manager = RecordingTaskDBManager(
            [
                [{"start_point": "護理站", "task_count": 5}],
                [{"target_point": "檢驗室", "task_count": 4}],
                [{"start_point": "護理站", "target_point": "檢驗室", "task_count": 3}],
            ]
        )

        start_rows = manager.get_task_start_hotspots()
        target_rows = manager.get_task_target_hotspots()
        route_rows = manager.get_task_route_hotspots()

        self.assertEqual(
            [{"start_point": "護理站", "task_count": 5}],
            start_rows,
        )
        self.assertEqual(
            [{"target_point": "檢驗室", "task_count": 4}],
            target_rows,
        )
        self.assertEqual(
            [
                {
                    "start_point": "護理站",
                    "target_point": "檢驗室",
                    "route_label": "護理站 -> 檢驗室",
                    "task_count": 3,
                }
            ],
            route_rows,
        )
        self.assertEqual((10,), manager.calls[0]["params"])
        self.assertEqual((10,), manager.calls[1]["params"])
        self.assertEqual((10,), manager.calls[2]["params"])

    def test_invalid_top_n_limit_raises_value_error(self):
        manager = RecordingTaskDBManager([[]])

        with self.assertRaises(ValueError):
            manager.get_task_start_hotspots(limit=0)


if __name__ == "__main__":
    unittest.main()
