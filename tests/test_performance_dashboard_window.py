import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from performance_dashboard import (
    PerformanceDashboardController,
    PerformanceDashboardWindow,
    build_performance_dashboard_snapshot,
    build_performance_dashboard_snapshot_from_db,
)


class FakeDashboardWindow:
    def __init__(self, snapshot_provider=None, parent=None):
        self.snapshot_provider = snapshot_provider
        self.parent = parent
        self.refresh_calls = 0
        self.raise_calls = 0
        self.activate_calls = 0
        self.show_calls = 0

    def set_snapshot_provider(self, snapshot_provider):
        self.snapshot_provider = snapshot_provider

    def show(self):
        self.show_calls += 1

    def refresh_dashboard(self):
        self.refresh_calls += 1

    def raise_(self):
        self.raise_calls += 1

    def activateWindow(self):
        self.activate_calls += 1


class FakeTaskStatisticsManager:
    def __init__(self):
        self.calls = []

    def get_task_status_summary(self):
        self.calls.append(("summary", None))
        return {
            "pending_count": 3,
            "executing_count": 2,
            "completed_count": 8,
            "aborted_count": 1,
            "total_count": 14,
        }

    def get_task_volume_by_mission(self):
        self.calls.append(("mission", None))
        return [{"mission_content": "Empty Cart", "task_count": 6}]

    def get_task_start_hotspots(self, limit=10):
        self.calls.append(("start", limit))
        return [{"start_point": "Lobby", "task_count": 5}]

    def get_task_target_hotspots(self, limit=10):
        self.calls.append(("target", limit))
        return [{"target_point": "Lab", "task_count": 4}]

    def get_task_route_hotspots(self, limit=10):
        self.calls.append(("route", limit))
        return [{"route_label": "Lobby -> Lab", "task_count": 3}]


class PerformanceDashboardWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_snapshot_builder_maps_summary_counts_and_top_n_rows(self):
        snapshot = build_performance_dashboard_snapshot(
            task_status_summary={
                "pending_count": 3,
                "executing_count": 2,
                "completed_count": 8,
                "aborted_count": 1,
                "total_count": 14,
            },
            task_volume_by_mission=[
                {"mission_content": "Empty Cart", "task_count": 6},
            ],
            start_hotspots=[
                {"start_point": "Lobby", "task_count": 5},
            ],
            target_hotspots=[
                {"target_point": "Lab", "task_count": 4},
            ],
            route_hotspots=[
                {"route_label": "Lobby -> Lab", "task_count": 3},
            ],
        )

        self.assertEqual("ready", snapshot["status_level"])
        self.assertEqual("3", snapshot["summary_cards"][0]["value"])
        self.assertEqual("14", snapshot["summary_cards"][-1]["value"])
        self.assertEqual(4, len(snapshot["sections"]))
        self.assertEqual(
            {"label": "Empty Cart", "value": "6"},
            snapshot["sections"][0]["rows"][0],
        )
        self.assertEqual(
            {"label": "Lobby -> Lab", "value": "3"},
            snapshot["sections"][-1]["rows"][0],
        )

    def test_window_refresh_applies_provider_snapshot(self):
        def snapshot_provider():
            return {
                "status_level": "warning",
                "status_text": "Summary is delayed.",
                "summary_cards": [
                    {
                        "key": "pending_count",
                        "title": "Pending",
                        "value": "9",
                        "caption": "queued",
                    }
                ],
                "sections": [
                    {
                        "key": "task-volume",
                        "title": "Task Volume",
                        "rows": [
                            {"label": "Empty Cart", "value": "9"},
                            {"label": "Cart Delivery", "value": "4"},
                        ],
                        "body": "Empty Cart: 9\nCart Delivery: 4",
                    }
                ],
            }

        window = PerformanceDashboardWindow(
            snapshot_provider=snapshot_provider,
            refresh_interval_ms=60_000,
        )
        self.addCleanup(window.deleteLater)
        window.refresh_timer.stop()

        self.assertEqual("Summary is delayed.", window.status_banner.text())
        self.assertEqual("9", window.summary_value_labels["pending_count"].text())
        self.assertEqual(
            "Empty Cart: 9\nCart Delivery: 4",
            window.section_body_labels["task-volume"].text(),
        )
        self.assertIn("60", window.last_refresh_label.text())

    def test_close_event_hides_window_for_reuse(self):
        window = PerformanceDashboardWindow(refresh_interval_ms=60_000)
        self.addCleanup(window.deleteLater)
        window.refresh_timer.stop()

        window.show()
        window.close()

        self.assertFalse(window.isVisible())

    def test_snapshot_builder_from_db_collects_all_statistics(self):
        manager = FakeTaskStatisticsManager()

        snapshot = build_performance_dashboard_snapshot_from_db(
            manager,
            hotspot_limit=3,
        )

        self.assertEqual("ready", snapshot["status_level"])
        self.assertEqual(
            [
                ("summary", None),
                ("mission", None),
                ("start", 3),
                ("target", 3),
                ("route", 3),
            ],
            manager.calls,
        )
        self.assertEqual(
            {"label": "Lobby", "value": "5"},
            snapshot["sections"][1]["rows"][0],
        )


class PerformanceDashboardControllerTests(unittest.TestCase):
    def test_controller_reuses_single_window_instance(self):
        controller = PerformanceDashboardController(window_factory=FakeDashboardWindow)

        window_one = controller.open(snapshot_provider=lambda: {"status_text": "one"})
        window_two = controller.open(snapshot_provider=lambda: {"status_text": "two"})

        self.assertIs(window_one, window_two)
        self.assertEqual(2, window_one.show_calls)
        self.assertEqual(2, window_one.refresh_calls)
        self.assertEqual(2, window_one.raise_calls)
        self.assertEqual(2, window_one.activate_calls)


if __name__ == "__main__":
    unittest.main()
