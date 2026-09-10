import unittest

from main import (
    resolve_login_bootstrap_settings,
    resolve_ui_defaults,
    translate_mir_mission_text,
    translate_mir_state_label,
)


class UiBootstrapHelpersTests(unittest.TestCase):
    def test_resolve_login_bootstrap_from_settings(self):
        settings = resolve_login_bootstrap_settings(
            {
                "skip_login": True,
                "auto_login_username": "apple",
                "auto_login_password": "apple",
            }
        )
        self.assertTrue(settings["skip_login"])
        self.assertEqual("apple", settings["username"])
        self.assertEqual("apple", settings["password"])

    def test_resolve_ui_defaults_merges_site_config(self):
        defaults = resolve_ui_defaults(
            {
                "ui_defaults": {
                    "start_point": "滅菌室",
                    "destination": "洗滌室",
                    "mission_content": "載運",
                    "auto_start_pending_scheduler": True,
                    "exclude_charging_station_from_combobox": True,
                }
            }
        )
        self.assertEqual("滅菌室", defaults["start_point"])
        self.assertEqual("洗滌室", defaults["destination"])
        self.assertEqual("載運", defaults["mission_content"])
        self.assertTrue(defaults["auto_start_pending_scheduler"])
        self.assertTrue(defaults["exclude_charging_station_from_combobox"])

    def test_translate_obstacle_and_replan_messages(self):
        self.assertEqual("偵測到障礙物", translate_mir_mission_text("Obstacle detected"))
        self.assertEqual("區域被占用", translate_mir_mission_text("Area occupied"))
        self.assertEqual("重新規劃路徑", translate_mir_mission_text("Replanning path"))
        self.assertEqual("等待新任務...", translate_mir_mission_text("Waiting for new missions..."))
        self.assertIn(
            "等待障礙物移除",
            translate_mir_mission_text(
                "Moving to 'MH_Shelf position OR 13'. Waiting for obstacles to be removed."
            ),
        )
        self.assertEqual("就緒", translate_mir_state_label("Ready"))


if __name__ == "__main__":
    unittest.main()
