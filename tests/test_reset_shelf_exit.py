import unittest

import reset_all


class ResetShelfExitTests(unittest.TestCase):
    def test_shelf_exit_pose_backs_up_along_heading(self):
        exit_x, exit_y, orientation = reset_all.shelf_exit_pose(10, 5, 0, 0.7)
        self.assertAlmostEqual(9.3, exit_x)
        self.assertAlmostEqual(5.0, exit_y)
        self.assertAlmostEqual(0.0, orientation)

        exit_x, exit_y, orientation = reset_all.shelf_exit_pose(10, 5, 90, 0.7)
        self.assertAlmostEqual(10.0, exit_x)
        self.assertAlmostEqual(4.3, exit_y)
        self.assertAlmostEqual(90.0, orientation)

    def test_lift_input_reads_matching_input_only(self):
        payload = {
            "inputs": [
                {"id": 2, "value": True},
                {"id": 3, "name": "3", "value": False},
            ],
            "outputs": [{"id": 3, "value": True}],
        }
        self.assertIs(False, reset_all.lift_input_is_on(payload, 3))
        self.assertIsNone(reset_all.lift_input_is_on(payload, 9))

    def test_choose_narrow_footprint_uses_default_name(self):
        chosen = reset_all.choose_narrow_footprint(
            [
                {"name": "Shelf wide", "guid": "wide"},
                {"name": "Default", "guid": "narrow"},
            ]
        )
        self.assertEqual("narrow", chosen["guid"])
        self.assertIsNone(reset_all.choose_narrow_footprint([{"name": "Shelf"}]))

    def test_footprints_match_ignores_spacing(self):
        wide = "[[0.80,-0.50],[0.80,0.50],[-0.80,0.50]]"
        narrow = "[[0.54, -0.38], [0.54, 0.38], [-0.54, 0.38]]"
        self.assertTrue(
            reset_all.footprints_match("[[0.54,-0.38],[0.54,0.38],[-0.54,0.38]]", narrow)
        )
        self.assertFalse(reset_all.footprints_match(wide, narrow))

    def test_protective_stop_detects_state_and_text(self):
        self.assertTrue(reset_all.status_is_protective_stop({"state_id": 10}))
        self.assertTrue(reset_all.status_is_protective_stop({"state_id": 12}))
        self.assertTrue(
            reset_all.status_is_protective_stop(
                {"state_id": 5, "mission_text": "Protective stop"}
            )
        )
        self.assertFalse(
            reset_all.status_is_protective_stop(
                {"state_id": 5, "mission_text": "Waiting for input '3'"}
            )
        )


if __name__ == "__main__":
    unittest.main()
