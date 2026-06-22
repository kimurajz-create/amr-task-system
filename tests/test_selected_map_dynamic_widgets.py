import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QComboBox

from main import MainWindow, SelectedMap

REPO_ROOT = Path(__file__).resolve().parents[1]


class SelectedMapDynamicWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _build_dialog(self, runtime_points=None, design_size=(1000, 500)):
        if runtime_points is None:
            runtime_points = [
                {
                    "point_id": "alpha",
                    "location_mir_name": "mir-a",
                    "location_display_name": "Alpha",
                    "selected_label": "Alpha Label",
                    "marker_id": "marker-a",
                    "x_px": 100,
                    "y_px": 120,
                    "width_px": 200,
                    "height_px": 80,
                    "order": 10,
                    "visible": True,
                },
                {
                    "point_id": "beta",
                    "location_mir_name": "mir-b",
                    "location_display_name": "Beta",
                    "selected_label": "Beta Label",
                    "marker_id": "marker-b",
                    "x_px": 400,
                    "y_px": 200,
                    "width_px": 150,
                    "height_px": 60,
                    "order": 20,
                    "visible": True,
                },
            ]

        dialog = SelectedMap()
        dialog.set_selected_map_runtime(
            runtime_points=runtime_points,
            design_size=design_size,
            empty_state_text="No points configured.",
        )
        dialog.show()
        self.app.processEvents()
        return dialog

    def test_dialog_builds_runtime_widgets_without_legacy_button_attrs(self):
        dialog = self._build_dialog()

        self.assertFalse(hasattr(dialog, "btn_sm_rp1"))
        self.assertFalse(hasattr(dialog, "btn_sm_rp7"))
        self.assertEqual(2, len(dialog.dynamic_location_buttons))
        self.assertEqual(
            ["dynamic_alpha", "dynamic_beta"],
            [button.objectName() for button in dialog.dynamic_location_buttons],
        )

    def test_runtime_button_click_preserves_emit_location_contract(self):
        dialog = self._build_dialog()
        selected_locations = []
        dialog.location_selected.connect(selected_locations.append)

        dialog.dynamic_location_buttons[0].click()
        dialog._confirm_selection()

        self.assertEqual("Alpha Label", dialog.lineEdit_sm_selectedpoint.text())
        self.assertEqual(["Alpha"], selected_locations)

    def test_runtime_button_geometry_reacts_to_selected_map_resize(self):
        dialog = self._build_dialog()
        original_geometry = dialog.dynamic_location_buttons[0].geometry()

        dialog.label_sm_map_1.resize(QSize(576, 336))
        dialog._position_selectable_widgets()
        self.app.processEvents()

        resized_geometry = dialog.dynamic_location_buttons[0].geometry()

        self.assertNotEqual(original_geometry.width(), resized_geometry.width())
        self.assertNotEqual(original_geometry.height(), resized_geometry.height())

    def test_runtime_button_width_expands_to_fit_full_label_text(self):
        runtime_points = [
            {
                "point_id": "long-label",
                "location_mir_name": "mir-long",
                "location_display_name": "手術室10",
                "selected_label": "手術室10",
                "marker_id": "marker-long",
                "x_px": 100,
                "y_px": 120,
                "width_px": 20,
                "height_px": 20,
                "order": 10,
                "visible": True,
            }
        ]
        dialog = self._build_dialog(runtime_points=runtime_points)
        button = dialog.dynamic_location_buttons[0]

        self.assertGreater(button.width(), 20)
        self.assertEqual("手術室10", button.text())

    def test_empty_state_is_shown_when_no_runtime_points_exist(self):
        dialog = self._build_dialog(runtime_points=[])

        self.assertEqual([], dialog.dynamic_location_buttons)
        self.assertTrue(dialog.empty_state_label.isVisible())
        self.assertFalse(dialog.btn_sm_enter.isEnabled())

    def test_selected_map_emit_can_drive_target_dropdown_selection(self):
        dialog = self._build_dialog()
        target_dropdown = QComboBox()
        target_dropdown.addItem("Placeholder")
        target_dropdown.addItem("Alpha")
        target_dropdown.addItem("Beta")

        dialog.location_selected.connect(
            lambda location_name: MainWindow._set_current_dropdown_value(
                None,
                location_name,
                target_dropdown,
            )
        )

        dialog.dynamic_location_buttons[1].click()
        dialog._confirm_selection()

        self.assertEqual("Beta", target_dropdown.currentText())

    def test_selected_map_ui_source_no_longer_declares_legacy_buttons(self):
        selected_map_ui_text = (REPO_ROOT / "selected_map.ui").read_text(encoding="utf-8")

        self.assertNotIn('name="btn_sm_rp1"', selected_map_ui_text)
        self.assertNotIn('name="btn_sm_rp7"', selected_map_ui_text)


if __name__ == "__main__":
    unittest.main()
