import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication

from main import SelectedMap


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

    def test_dialog_hides_legacy_buttons_and_builds_runtime_widgets(self):
        dialog = self._build_dialog()

        self.assertFalse(dialog.btn_sm_rp1.isVisible())
        self.assertFalse(dialog.btn_sm_rp7.isVisible())
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

    def test_empty_state_is_shown_when_no_runtime_points_exist(self):
        dialog = self._build_dialog(runtime_points=[])

        self.assertEqual([], dialog.dynamic_location_buttons)
        self.assertTrue(dialog.empty_state_label.isVisible())
        self.assertFalse(dialog.btn_sm_enter.isEnabled())


if __name__ == "__main__":
    unittest.main()
