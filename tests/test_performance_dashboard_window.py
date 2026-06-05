import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from performance_dashboard import (
    PerformanceDashboardController,
    PerformanceDashboardWindow,
    build_performance_dashboard_snapshot,
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


class PerformanceDashboardWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_snapshot_builder_maps_summary_counts(self):
        snapshot = build_performance_dashboard_snapshot(
            task_status_summary={
                "pending_count": 3,
                "executing_count": 2,
                "completed_count": 8,
                "aborted_count": 1,
                "total_count": 14,
            }
        )

        self.assertEqual("ready", snapshot["status_level"])
        self.assertEqual("3", snapshot["summary_cards"][0]["value"])
        self.assertEqual("14", snapshot["summary_cards"][-1]["value"])
        self.assertEqual(4, len(snapshot["sections"]))

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
                        "body": "Waiting for P3 binding.",
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
            "Waiting for P3 binding.",
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
