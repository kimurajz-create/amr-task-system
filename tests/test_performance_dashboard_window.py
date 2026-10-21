import os
import tempfile
import unittest
from zipfile import ZipFile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from performance_dashboard import (
    PerformanceDashboardController,
    PerformanceDashboardWindow,
    build_dashboard_export_blocks,
    build_performance_dashboard_snapshot,
    build_performance_dashboard_snapshot_from_db,
    render_performance_report_html,
    render_start_point_pie_image,
    write_performance_xlsx,
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
        self.assertEqual(
            "最高任務類型：Empty Cart (6)",
            snapshot["sections"][0]["summary"],
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
        self.assertEqual(
            2,
            window.section_chart_widgets["task-volume"].row_count(),
        )
        self.assertIn("60", window.last_refresh_label.text())

    def test_close_event_hides_window_for_reuse(self):
        window = PerformanceDashboardWindow(refresh_interval_ms=60_000)
        self.addCleanup(window.deleteLater)
        window.refresh_timer.stop()

        window.show()
        window.close()

        self.assertFalse(window.isVisible())

    def test_window_stays_top_level_even_with_parent_argument(self):
        parent = PerformanceDashboardWindow(refresh_interval_ms=60_000)
        self.addCleanup(parent.deleteLater)
        parent.refresh_timer.stop()

        window = PerformanceDashboardWindow(
            refresh_interval_ms=60_000,
            parent=parent,
        )
        self.addCleanup(window.deleteLater)
        window.refresh_timer.stop()

        self.assertIsNone(window.parentWidget())
        self.assertTrue(window.isWindow())

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
                ("start", 100),
                ("target", 3),
                ("route", 3),
            ],
            manager.calls,
        )
        self.assertEqual(
            {"label": "Lobby", "value": "5"},
            snapshot["start_point_pie"][0],
        )
        self.assertEqual(
            {"label": "Lobby", "value": "5"},
            snapshot["sections"][1]["rows"][0],
        )

    def test_snapshot_builder_from_db_passes_monitoring_range(self):
        class RangeAwareManager(FakeTaskStatisticsManager):
            def get_task_status_summary(self, start_at=None, end_at=None):
                self.calls.append(("summary", start_at, end_at))
                return super().get_task_status_summary()

            def get_task_volume_by_mission(self, start_at=None, end_at=None):
                self.calls.append(("mission", start_at, end_at))
                return super().get_task_volume_by_mission()

            def get_task_start_hotspots(self, limit=10, start_at=None, end_at=None):
                self.calls.append(("start", limit, start_at, end_at))
                return super().get_task_start_hotspots(limit=limit)

            def get_task_target_hotspots(self, limit=10, start_at=None, end_at=None):
                self.calls.append(("target", limit, start_at, end_at))
                return super().get_task_target_hotspots(limit=limit)

            def get_task_route_hotspots(self, limit=10, start_at=None, end_at=None):
                self.calls.append(("route", limit, start_at, end_at))
                return super().get_task_route_hotspots(limit=limit)

        manager = RangeAwareManager()
        snapshot = build_performance_dashboard_snapshot_from_db(
            manager,
            hotspot_limit=3,
            start_at="2026-10-01 00:00:00",
            end_at="2026-10-01 13:00:00",
        )

        self.assertEqual("ready", snapshot["status_level"])
        self.assertIn(
            ("summary", "2026-10-01 00:00:00", "2026-10-01 13:00:00"),
            manager.calls,
        )
        self.assertIn(
            ("route", 3, "2026-10-01 00:00:00", "2026-10-01 13:00:00"),
            manager.calls,
        )

    def test_window_can_filter_range_and_render_pdf_html(self):
        received = {}

        def snapshot_provider(start_at=None, end_at=None):
            received["start_at"] = start_at
            received["end_at"] = end_at
            return build_performance_dashboard_snapshot(
                task_status_summary={"pending_count": 4, "total_count": 4},
                task_volume_by_mission=[
                    {"mission_content": "載運", "task_count": 4},
                ],
                start_point_pie=[
                    {"label": "OR1", "value": 7},
                    {"label": "OR2", "value": 3},
                ],
            )

        window = PerformanceDashboardWindow(
            snapshot_provider=snapshot_provider,
            refresh_interval_ms=60_000,
        )
        self.addCleanup(window.deleteLater)
        window.refresh_timer.stop()

        self.assertIsNone(received["start_at"])
        self.assertEqual("監控區間：全部累積資料", window.range_status_label.text())
        self.assertEqual("匯出", window.export_pdf_button.text())

        window.range_checkbox.setChecked(True)
        self.assertIsNotNone(received["start_at"])
        self.assertIn("~", window.range_status_label.text())

        html = render_performance_report_html(
            window.latest_snapshot,
            "2026-10-01 00:00 ~ 2026-10-01 13:00",
        )
        self.assertIn("載運", html)
        self.assertIn("2026-10-01 00:00 ~ 2026-10-01 13:00", html)
        self.assertIn("起始點使用比例", html)
        self.assertIn("最常使用：OR1", html)
        self.assertIn("70.0%", html)
        self.assertIn("start-point-pie.png", html)
        self.assertEqual("最常使用：OR1（7 次，70.0%）", window.start_point_caption.text())

        image = render_start_point_pie_image(window.latest_snapshot["start_point_pie"])
        self.assertFalse(image.isNull())
        self.assertGreater(image.width(), 0)

        export_image = window.render_export_image()
        self.assertFalse(export_image.isNull())
        self.assertGreater(export_image.width(), 800)
        self.assertGreater(export_image.height(), 700)
        self.assertEqual(export_image.pixelColor(4, 4).name(), "#ffffff")

    def test_start_point_pie_skips_closed_cart_storage(self):
        snapshot = build_performance_dashboard_snapshot(
            task_status_summary={"total_count": 30},
            start_point_pie=[
                {"label": "封閉式架子放置處", "value": 20},
                {"label": "手術室1", "value": 8},
                {"label": "手術室2", "value": 2},
            ],
        )
        self.assertEqual(
            ["手術室1", "手術室2"],
            [row["label"] for row in snapshot["start_point_pie"]],
        )

    def test_export_blocks_keep_chart_rows_on_one_page(self):
        snapshot = build_performance_dashboard_snapshot(
            task_status_summary={"total_count": 8},
            task_volume_by_mission=[
                {"mission_content": f"任務{index}", "task_count": index + 1}
                for index in range(8)
            ],
            start_point_pie=[{"label": "手術室1", "value": 3}],
        )
        blocks = build_dashboard_export_blocks(
            snapshot,
            "全部累積資料",
            width=800,
            max_block_height=360,
        )
        self.assertTrue(blocks)
        self.assertTrue(all(block.height() <= 360 for block in blocks))
        self.assertGreater(len(blocks), 4)

    def test_excel_export_is_text_only(self):
        snapshot = build_performance_dashboard_snapshot(
            task_status_summary={"pending_count": 4, "total_count": 4},
            task_volume_by_mission=[{"mission_content": "載運", "task_count": 4}],
            start_point_pie=[
                {"label": "手術室1", "value": 7},
                {"label": "手術室2", "value": 3},
            ],
        )
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "report.xlsx")
            write_performance_xlsx(path, snapshot, "全部累積資料")
            with ZipFile(path) as workbook:
                sheet = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn("任務摘要", sheet)
        self.assertIn("載運", sheet)
        self.assertIn("起始點使用比例", sheet)
        self.assertIn("最常使用：手術室1", sheet)
        self.assertIn("70.0%", sheet)
        self.assertNotIn("png", sheet)


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
