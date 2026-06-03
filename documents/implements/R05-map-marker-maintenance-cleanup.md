---
author: Codex
date: 2026-06-03
title: Map Marker Maintenance Cleanup
uuid: b6fd3260f4ae4526a8a1317f8a2f0bb5
version: v1
planning: documents/planning/P02-map-marker-externalization-and-scaled-positioning.md
status: completed
---

# R05 Map Marker Maintenance Cleanup

## 1. Scope

P02 P3 removes the remaining Qt Designer marker dependencies from the main map so marker maintenance is fully config-driven from `site/*.json`.

## 2. Goals

- Remove the prebuilt `label_rp_*` widgets from `main.ui` / `ui_main.py`.
- Make `MainWindow._build_map_marker_widgets()` the only runtime creation path for main-map markers.
- Preserve the existing runtime marker contract:
  - `marker_id == widget.objectName() == self.<marker_id>`
  - `refresh_label_tooltip()` still resolves markers through `LOCATION_TO_MARKER` and `getattr()`
  - marker geometry still comes from `MARKER_SPECS_BY_ID`
- Keep `selected_map.ui` explicitly out of scope for this cleanup.

## 3. Changes

### R1. Remove legacy Designer markers from the main map UI

- Deleted the `label_rp_*` widget declarations from `main.ui`.
- Deleted the matching generated widget setup and tooltip text from `ui_main.py`.
- Left the rest of the main-map UI structure unchanged.

### R2. Simplify MainWindow marker lifecycle

- Removed the legacy marker collection fallback from `MainWindow`.
- Runtime markers are now always created directly from `self.MARKER_SPECS_BY_ID`.
- `_clear_map_marker_widgets()` and `_build_map_marker_widgets()` now operate only on runtime-created marker instances.

### R3. Keep config-driven marker behavior intact

- Marker ids still map back onto `self.<marker_id>` so the tooltip/task-highlighting flow remains compatible.
- `refresh_label_tooltip()` continues to work without any Designer-owned placeholder widgets.
- Existing runtime marker warning and location-binding behavior from P1 remains unchanged.

## 4. Test Coverage

| Test ID | Type | Coverage |
|---|---|---|
| R05-T1 | unit | `Ui_MainWindow` no longer declares `label_rp_*` widgets after setup |
| R05-T2 | unit | `main.ui` source no longer contains the legacy `label_rp_*` widget declarations |
| R05-T3 | unit | existing runtime marker map tests still pass after the cleanup |

## 5. Verification

```bash
python -m unittest tests.test_site_runtime_marker_maps tests.test_map_marker_ui_cleanup
```

## 6. Notes

- `selected_map.ui` is still the fixed button-based selection surface described in `P02`; this cleanup only applies to the main map overlay.
- `main.ui` was already not valid enough to regenerate cleanly with `pyside6-uic`, so P3 updates were applied directly to both `main.ui` and `ui_main.py` to keep the runtime code aligned with the intended cleanup result.
