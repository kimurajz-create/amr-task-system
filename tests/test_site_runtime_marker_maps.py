import json
import unittest
from pathlib import Path

from main import build_site_runtime_maps


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


if __name__ == "__main__":
    unittest.main()
