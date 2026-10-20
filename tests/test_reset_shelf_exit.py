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
        self.assertIs(True, reset_all.lift_output_is_on(payload, 3))
        self.assertIsNone(reset_all.lift_output_is_on(payload, 2))
        self.assertIs(True, reset_all.shelf_lift_is_up(payload))
        self.assertIs(
            False,
            reset_all.shelf_lift_is_up({"outputs": [{"id": 3, "value": False}]}),
        )

    def test_choose_narrow_footprint_uses_mir250_dynamic(self):
        chosen = reset_all.choose_narrow_footprint(
            [
                {"name": "MIR250 MK2 shelf carrier base 0703", "guid": "wide"},
                {"name": "MiR250 Dynamic", "guid": "narrow"},
                {"name": "Shelf_Army_Hospital", "guid": "unused"},
            ]
        )
        self.assertEqual("narrow", chosen["guid"])
        self.assertEqual("MiR250 Dynamic", reset_all.NARROW_FOOTPRINT_NAME)
        self.assertIsNone(reset_all.choose_narrow_footprint([{"name": "Shelf_Army_Hospital"}]))

    def test_choose_wide_footprint_uses_shelf_carrier_base(self):
        chosen = reset_all.choose_footprint_by_name(
            [
                {"name": "MiR250 Dynamic", "guid": "narrow"},
                {"name": "MIR250 MK2 shelf carrier base 0703", "guid": "wide"},
                {"name": "Shelf_Army_Hospital", "guid": "unused"},
            ],
            reset_all.WIDE_FOOTPRINT_NAME,
        )
        self.assertEqual("wide", chosen["guid"])
        self.assertEqual(
            "MIR250 MK2 shelf carrier base 0703", reset_all.WIDE_FOOTPRINT_NAME
        )

    def test_set_footprint_action_copies_cart_mission_style(self):
        example = {
            "action_type": "set_footprint",
            "parameters": '[{"id": "footprint", "value": "/v2.0.0/footprints/old"}]',
        }
        chosen = reset_all.choose_set_footprint_action(
            [{"action_type": "relative_move"}, example]
        )
        self.assertEqual("set_footprint", chosen["action_type"])
        self.assertEqual("footprint", reset_all.footprint_parameter_id(example))
        self.assertEqual(
            "/v2.0.0/footprints/wide-guid",
            reset_all.footprint_action_value(
                example, {"guid": "wide-guid", "url": "/v2.0.0/footprints/wide-guid"}
            ),
        )
        action = reset_all.build_set_footprint_action(
            "set_footprint", "footprint", "narrow-guid", "mission-1"
        )
        self.assertEqual("mission-1", action["mission_id"])
        self.assertEqual("narrow-guid", action["parameters"][0]["value"])
        self.assertIsNone(reset_all.choose_set_footprint_action([{"action_type": "move"}]))

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
        self.assertFalse(
            reset_all.status_is_protective_stop(
                {
                    "state_id": 5,
                    "mission_text": "ReduceProtectiveFieldAction: Started!",
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
