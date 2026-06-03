import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from ui_main import Ui_MainWindow


REPO_ROOT = Path(__file__).resolve().parents[1]


class MapMarkerUiCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_ui_no_longer_declares_legacy_marker_widgets(self):
        window = QMainWindow()
        ui = Ui_MainWindow()

        ui.setupUi(window)

        self.assertFalse(hasattr(ui, "label_rp_1"))
        self.assertFalse(hasattr(ui, "label_rp_7"))

        legacy_marker_names = [
            widget.objectName()
            for widget in window.findChildren(QWidget)
            if widget.objectName().startswith("label_rp_")
        ]
        self.assertEqual([], legacy_marker_names)

    def test_main_ui_source_no_longer_contains_legacy_marker_widgets(self):
        main_ui_text = (REPO_ROOT / "main.ui").read_text(encoding="utf-8")

        self.assertNotIn('name="label_rp_1"', main_ui_text)
        self.assertNotIn('name="label_rp_7"', main_ui_text)


if __name__ == "__main__":
    unittest.main()
