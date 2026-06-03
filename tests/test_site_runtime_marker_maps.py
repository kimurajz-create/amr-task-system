import json
import unittest
from pathlib import Path

from main import (
    build_site_runtime_maps,
    scale_marker_spec_to_display,
    scale_point_to_display,
    scale_point_to_source,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_site_profile(profile_name):
    site_path = REPO_ROOT / "site" / f"{profile_name}.json"
    return json.loads(site_path.read_text(encoding="utf-8"))


class SiteRuntimeMarkerMapTests(unittest.TestCase):
    def test_site_profiles_expose_marker_specs_and_valid_runtime_refs(self):
        for profile_name in ("company", "hospital"):
            with self.subTest(profile=profile_name):
                site_config = load_site_profile(profile_name)
                runtime_maps = build_site_runtime_maps(site_config)

                expected_marker_ids = {
                    marker["marker_id"] for marker in site_config["markers"]
                }

                self.assertEqual(
                    expected_marker_ids,
                    set(runtime_maps["marker_specs_by_id"]),
                )
                self.assertTrue(
                    set(runtime_maps["location_to_marker"].values()).issubset(
                        expected_marker_ids
                    )
                )

                for marker_id, marker_spec in runtime_maps["marker_specs_by_id"].items():
                    self.assertEqual(marker_id, marker_spec["marker_id"])
                    for key in ("x_px", "y_px", "width_px", "height_px"):
                        self.assertIn(key, marker_spec)
                        self.assertIsInstance(marker_spec[key], int)

    def test_runtime_maps_track_shared_and_unbound_locations_separately(self):
        site_config = load_site_profile("company")
        runtime_maps = build_site_runtime_maps(site_config)

        self.assertCountEqual(
            runtime_maps["marker_location_names_by_id"]["label_rp_1"],
            ["華陀會議室", "車架位置(華陀)"],
        )
        self.assertCountEqual(
            runtime_maps["locations_without_markers"],
            ["充電樁", "電梯橋"],
        )

    def test_runtime_maps_collect_duplicate_and_missing_marker_warnings(self):
        site_config = {
            "markers": [
                {
                    "marker_id": "label_rp_1",
                    "x_px": 10,
                    "y_px": 20,
                    "width_px": 30,
                    "height_px": 40,
                },
                {
                    "marker_id": "label_rp_1",
                    "x_px": 99,
                    "y_px": 88,
                    "width_px": 77,
                    "height_px": 66,
                },
            ],
            "locations": [
                {
                    "mir_name": "mir-a",
                    "display_name": "A 點",
                    "marker_id": "label_rp_1",
                },
                {
                    "mir_name": "mir-b",
                    "display_name": "B 點",
                    "marker_id": "label_missing",
                },
                {
                    "mir_name": "mir-c",
                    "display_name": "C 點",
                    "marker_id": None,
                },
            ],
            "missions": [],
        }

        runtime_maps = build_site_runtime_maps(site_config)
        warning_text = "\n".join(runtime_maps["marker_config_warnings"])

        self.assertIn("重複定義", warning_text)
        self.assertIn("未定義", warning_text)
        self.assertEqual("label_rp_1", runtime_maps["location_to_marker"]["A 點"])
        self.assertEqual("label_missing", runtime_maps["location_to_marker"]["B 點"])
        self.assertEqual(["A 點"], runtime_maps["marker_location_names_by_id"]["label_rp_1"])
        self.assertEqual(["B 點"], runtime_maps["marker_location_names_by_id"]["label_missing"])
        self.assertEqual(["C 點"], runtime_maps["locations_without_markers"])

class MapMarkerGeometryScalingTests(unittest.TestCase):
    def test_marker_geometry_scales_into_display_space(self):
        scaled = scale_marker_spec_to_display(
            {
                "marker_id": "label_rp_1",
                "x_px": 321,
                "y_px": 456,
                "width_px": 18,
                "height_px": 27,
            },
            source_width=3216,
            source_height=1824,
            display_width=1072,
            display_height=608,
        )

        self.assertEqual(107, scaled["x_px"])
        self.assertEqual(152, scaled["y_px"])
        self.assertEqual(6, scaled["width_px"])
        self.assertEqual(9, scaled["height_px"])

    def test_display_to_source_point_conversion_round_trips(self):
        display_x, display_y = scale_point_to_display(
            804,
            912,
            source_width=3216,
            source_height=1824,
            display_width=1072,
            display_height=608,
        )
        source_x, source_y = scale_point_to_source(
            display_x,
            display_y,
            source_width=3216,
            source_height=1824,
            display_width=1072,
            display_height=608,
        )

        self.assertAlmostEqual(804, source_x)
        self.assertAlmostEqual(912, source_y)

    def test_marker_scaling_keeps_tiny_markers_visible(self):
        scaled = scale_marker_spec_to_display(
            {
                "marker_id": "tiny",
                "x_px": 10,
                "y_px": 20,
                "width_px": 1,
                "height_px": 1,
            },
            source_width=3216,
            source_height=1824,
            display_width=1072,
            display_height=608,
        )

        self.assertEqual(1, scaled["width_px"])
        self.assertEqual(1, scaled["height_px"])

    def test_marker_geometry_can_anchor_from_world_coordinates(self):
        scaled = scale_marker_spec_to_display(
            {
                "marker_id": "world-marker",
                "world_x": -0.004,
                "world_y": 24.154,
                "width_px": 54,
                "height_px": 78,
            },
            source_width=3216,
            source_height=1824,
            display_width=1072,
            display_height=608,
            world_to_image_fn=lambda world_x, world_y: (851, 733),
        )

        self.assertEqual(284, scaled["x_px"])
        self.assertEqual(244, scaled["y_px"])
        self.assertEqual(18, scaled["width_px"])
        self.assertEqual(26, scaled["height_px"])


if __name__ == "__main__":
    unittest.main()
