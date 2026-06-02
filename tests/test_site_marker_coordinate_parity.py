import json
import unittest
from pathlib import Path

import main


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_site_config(site_id):
    site_path = REPO_ROOT / "site" / f"{site_id}.json"
    return json.loads(site_path.read_text(encoding="utf-8"))


class SiteMarkerCoordinateParityTests(unittest.TestCase):
    def test_company_markers_derive_pixel_geometry_from_world_coordinates(self):
        site_config = load_site_config("company")
        affine_matrix = main._build_site_affine_matrix(site_config)
        runtime_maps = main.build_site_runtime_maps(site_config)

        for marker in site_config["markers"]:
            with self.subTest(marker_id=marker["marker_id"]):
                self.assertNotIn("x_px", marker)
                self.assertNotIn("y_px", marker)
                expected_x, expected_y = main._derive_marker_top_left_from_world(
                    marker,
                    marker["marker_id"],
                    affine_matrix,
                    marker["width_px"],
                    marker["height_px"],
                )
                runtime_marker = runtime_maps["marker_specs_by_id"][marker["marker_id"]]
                self.assertEqual((runtime_marker["x_px"], runtime_marker["y_px"]), (expected_x, expected_y))

    def test_hospital_markers_keep_explicit_pixel_geometry(self):
        site_config = load_site_config("hospital")
        runtime_maps = main.build_site_runtime_maps(site_config)

        for marker in site_config["markers"]:
            with self.subTest(marker_id=marker["marker_id"]):
                runtime_marker = runtime_maps["marker_specs_by_id"][marker["marker_id"]]
                self.assertEqual(runtime_marker["x_px"], marker["x_px"])
                self.assertEqual(runtime_marker["y_px"], marker["y_px"])

    def test_company_marker_geometry_scales_from_original_map_to_legacy_ui_size(self):
        site_config = load_site_config("company")
        runtime_maps = main.build_site_runtime_maps(site_config)

        scale_x = 1072 / 3216
        scale_y = 608 / 1824
        expected_geometry = {
            "label_rp_1": (281, 240, 6, 9),
            "label_rp_4": (597, 439, 9, 6),
            "label_rp_5": (504, 442, 9, 6),
            "label_rp_6": (403, 447, 9, 6),
            "label_rp_7": (849, 319, 9, 6),
        }

        for marker_id, expected_rect in expected_geometry.items():
            with self.subTest(marker_id=marker_id):
                marker_spec = runtime_maps["marker_specs_by_id"][marker_id]
                self.assertEqual(
                    main._scale_marker_geometry(marker_spec, scale_x, scale_y),
                    expected_rect,
                )

    def test_hospital_marker_geometry_keeps_legacy_ui_pixels_at_legacy_size(self):
        site_config = load_site_config("hospital")
        runtime_maps = main.build_site_runtime_maps(site_config)

        for marker in site_config["markers"]:
            with self.subTest(marker_id=marker["marker_id"]):
                marker_spec = runtime_maps["marker_specs_by_id"][marker["marker_id"]]
                self.assertEqual(
                    main._scale_marker_geometry(marker_spec, 1.0, 1.0),
                    (
                        marker["x_px"],
                        marker["y_px"],
                        marker["width_px"],
                        marker["height_px"],
                    ),
                )

    def test_company_sofa_locations_map_to_expected_marker_ids(self):
        site_config = load_site_config("company")
        runtime_maps = main.build_site_runtime_maps(site_config)
        locations_by_mir_name = {
            location["mir_name"]: location
            for location in site_config["locations"]
            if location.get("marker_id")
        }

        expected_marker_by_mir_name = {
            "LbV2_Robot position Sofa3": "label_rp_4",
            "LbV2_Robot position Sofa2": "label_rp_5",
            "LbV2_Robot position Sofa1": "label_rp_6",
            "LbV2_Shelf position Sofa3": "label_rp_4",
            "LbV2_Shelf position Sofa2": "label_rp_5",
            "LbV2_Shelf position Sofa1": "label_rp_6",
        }

        for mir_name, expected_marker_id in expected_marker_by_mir_name.items():
            with self.subTest(mir_name=mir_name):
                location = locations_by_mir_name[mir_name]
                self.assertEqual(location["marker_id"], expected_marker_id)
                self.assertEqual(
                    runtime_maps["location_to_marker"][location["display_name"]],
                    expected_marker_id,
                )


if __name__ == "__main__":
    unittest.main()
