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
        display_name_counts = {
            name: count
            for name, count in (
                (
                    location["display_name"],
                    sum(
                        1
                        for item in site_config["locations"]
                        if item["display_name"] == location["display_name"]
                    ),
                )
                for location in site_config["locations"]
            )
        }

        shared_marker_locations = runtime_maps["marker_location_names_by_id"]["label_rp_1"]
        self.assertEqual(2, len(shared_marker_locations))
        self.assertGreaterEqual(display_name_counts[shared_marker_locations[0]], 1)
        self.assertGreaterEqual(display_name_counts[shared_marker_locations[1]], 1)
        self.assertCountEqual(
            runtime_maps["locations_without_markers"],
            [
                location["display_name"]
                for location in site_config["locations"]
                if not location.get("marker_id")
            ],
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
                    "display_name": "Alpha",
                    "marker_id": "label_rp_1",
                },
                {
                    "mir_name": "mir-b",
                    "display_name": "Beta",
                    "marker_id": "label_missing",
                },
                {
                    "mir_name": "mir-c",
                    "display_name": "Gamma",
                    "marker_id": None,
                },
            ],
            "missions": [],
        }

        runtime_maps = build_site_runtime_maps(site_config)
        warning_text = "\n".join(runtime_maps["marker_config_warnings"])

        self.assertIn("label_rp_1", warning_text)
        self.assertIn("marker_id 'label_missing'", warning_text)
        self.assertEqual("label_rp_1", runtime_maps["location_to_marker"]["Alpha"])
        self.assertEqual("label_missing", runtime_maps["location_to_marker"]["Beta"])
        self.assertEqual(["Alpha"], runtime_maps["marker_location_names_by_id"]["label_rp_1"])
        self.assertEqual(["Beta"], runtime_maps["marker_location_names_by_id"]["label_missing"])
        self.assertEqual(["Gamma"], runtime_maps["locations_without_markers"])

    def test_site_profiles_expose_selected_map_runtime_points(self):
        for profile_name in ("company", "hospital"):
            with self.subTest(profile=profile_name):
                site_config = load_site_profile(profile_name)
                runtime_maps = build_site_runtime_maps(site_config)

                configured_point_ids = {
                    point["point_id"]
                    for point in site_config["selected_map"]["selectable_points"]
                    if point.get("visible", True) is not False
                }

                self.assertEqual(
                    configured_point_ids,
                    set(runtime_maps["selected_map_points_by_id"]),
                )
                self.assertEqual(
                    configured_point_ids,
                    {point["point_id"] for point in runtime_maps["selected_map_points"]},
                )
                self.assertEqual(
                    site_config["selected_map"]["empty_state_text"],
                    runtime_maps["selected_map_empty_state_text"],
                )
                self.assertEqual(
                    (
                        site_config["selected_map"]["design_width_px"],
                        site_config["selected_map"]["design_height_px"],
                    ),
                    runtime_maps["selected_map_design_size"],
                )
                self.assertTrue(runtime_maps["selected_map_asset_path"])

                for point in runtime_maps["selected_map_points"]:
                    self.assertIn(point["location_mir_name"], runtime_maps["user_location_map"])
                    self.assertEqual(
                        runtime_maps["user_location_map"][point["location_mir_name"]],
                        point["location_display_name"],
                    )
                    self.assertTrue(point["width_px"] > 0)
                    self.assertTrue(point["height_px"] > 0)

    def test_site_profiles_no_longer_include_legacy_map_button_ids(self):
        for profile_name in ("company", "hospital"):
            with self.subTest(profile=profile_name):
                site_config = load_site_profile(profile_name)

                for location in site_config["locations"]:
                    self.assertNotIn("map_button_id", location)

    def test_selected_map_runtime_falls_back_label_marker_and_order(self):
        site_config = {
            "assets": {"selected_map": "picture/example.png"},
            "locations": [
                {
                    "mir_name": "mir-a",
                    "display_name": "Alpha",
                    "marker_id": "marker-alpha",
                },
                {
                    "mir_name": "mir-b",
                    "display_name": "Beta",
                    "marker_id": "marker-beta",
                },
            ],
            "markers": [],
            "missions": [],
            "selected_map": {
                "design_width_px": 1000,
                "design_height_px": 500,
                "selectable_points": [
                    {
                        "point_id": "beta",
                        "location_mir_name": "mir-b",
                        "x_px": 10,
                        "y_px": 20,
                        "width_px": 30,
                        "height_px": 40,
                    },
                    {
                        "point_id": "alpha",
                        "location_mir_name": "mir-a",
                        "label": "A label",
                        "x_px": 50,
                        "y_px": 60,
                        "width_px": 70,
                        "height_px": 80,
                        "order": 1,
                    },
                ],
            },
        }

        runtime_maps = build_site_runtime_maps(site_config)

        self.assertEqual(
            ["alpha", "beta"],
            [point["point_id"] for point in runtime_maps["selected_map_points"]],
        )
        self.assertEqual(
            "A label",
            runtime_maps["selected_map_points_by_id"]["alpha"]["selected_label"],
        )
        self.assertEqual(
            "Beta",
            runtime_maps["selected_map_points_by_id"]["beta"]["selected_label"],
        )
        self.assertEqual(
            "marker-beta",
            runtime_maps["selected_map_points_by_id"]["beta"]["marker_id"],
        )
        self.assertEqual(
            ["Alpha", "Beta"],
            runtime_maps["selected_map_location_names"],
        )

    def test_selected_map_runtime_skips_invalid_points_and_collects_warnings(self):
        site_config = {
            "assets": {"selected_map": "picture/example.png"},
            "locations": [
                {
                    "mir_name": "mir-a",
                    "display_name": "Alpha",
                    "marker_id": "marker-alpha",
                }
            ],
            "markers": [],
            "missions": [],
            "selected_map": {
                "design_width_px": 1000,
                "design_height_px": 500,
                "selectable_points": [
                    {
                        "point_id": "valid",
                        "location_mir_name": "mir-a",
                        "x_px": 1,
                        "y_px": 2,
                        "width_px": 3,
                        "height_px": 4,
                    },
                    {
                        "point_id": "valid",
                        "location_mir_name": "mir-a",
                        "x_px": 1,
                        "y_px": 2,
                        "width_px": 3,
                        "height_px": 4,
                    },
                    {
                        "point_id": "missing-location",
                        "location_mir_name": "mir-missing",
                        "x_px": 1,
                        "y_px": 2,
                        "width_px": 3,
                        "height_px": 4,
                    },
                    {
                        "point_id": "bad-geometry",
                        "location_mir_name": "mir-a",
                        "x_px": 1,
                        "y_px": 2,
                        "width_px": 0,
                        "height_px": 4,
                    },
                    {
                        "point_id": "hidden",
                        "location_mir_name": "mir-a",
                        "x_px": 1,
                        "y_px": 2,
                        "width_px": 3,
                        "height_px": 4,
                        "visible": False,
                    },
                ],
            },
        }

        runtime_maps = build_site_runtime_maps(site_config)
        warning_text = "\n".join(runtime_maps["selected_map_config_warnings"])

        self.assertEqual(
            ["valid"],
            [point["point_id"] for point in runtime_maps["selected_map_points"]],
        )
        self.assertNotIn("hidden", runtime_maps["selected_map_points_by_id"])
        self.assertIn("duplicated", warning_text)
        self.assertIn("unknown location_mir_name", warning_text)
        self.assertIn("non-positive geometry", warning_text)


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
