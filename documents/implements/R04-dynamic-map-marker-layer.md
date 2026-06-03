---
author: Codex
date: 2026-06-03
title: Dynamic Map Marker Layer
uuid: 4c8e508f7d4d4e5f9c8b0d8e4dbf5b5b
version: v1
planning: documents/planning/P02-map-marker-externalization-and-scaled-positioning.md
status: completed
---

# R04 Dynamic Map Marker Layer

## 1. Scope

P02 P2 replaces the main-map `label_rp_*` Designer markers with runtime-built widgets driven by `MARKER_SPECS_BY_ID`, while keeping existing tooltip and task-highlighting behavior intact.

## 2. Goals

- Build marker widgets from site configuration instead of relying on hardcoded `main.ui` marker instances.
- Keep `marker_id` as the runtime widget attribute contract so existing code can still use `getattr(self, marker_id)`.
- Scale marker geometry against the displayed map size so robot overlay, task markers, and map-click translation stay aligned.
- Avoid breaking the existing main-map click workflow used for world-coordinate selection.

## 3. Changes

### R1. MainWindow owns a runtime marker lifecycle

- `MainWindow` now manages marker widgets through:
  - `_build_map_marker_widgets()`
  - `_position_map_marker_widgets()`
  - `_clear_map_marker_widgets()`
  - `_sync_main_map_overlay_geometry()`
- Runtime widgets are created from `self.MARKER_SPECS_BY_ID`.
- Legacy Designer `label_rp_*` widgets are hidden and no longer act as the runtime source of truth.

### R2. Marker and overlay scaling share one geometry contract

- New geometry helpers scale marker rectangles and point coordinates between:
  - original map image coordinates
  - displayed overlay coordinates
- `draw_car_position()` and map click handling both use the same scaling rules instead of hardcoded ratios.
- Marker widgets follow the overlay geometry whenever the main map shell changes size.

### R3. Existing tooltip/task behavior is preserved

- Runtime marker widgets are assigned back onto `self` using their `marker_id`.
- `refresh_label_tooltip()` continues to resolve markers with `getattr(self, marker_id)`.
- Marker widgets remain transparent to mouse events so map clicking still reaches the main map interaction flow.

## 4. Test Coverage

| Test ID | Type | Coverage |
|---|---|---|
| R04-T1 | unit | marker geometry scales from original map pixels into displayed overlay geometry |
| R04-T2 | unit | display-to-source point conversion stays aligned with source-to-display conversion |
| R04-T3 | unit | tiny marker specs still produce visible runtime widget sizes after scaling |

## 5. Verification

```bash
python -m unittest tests.test_site_runtime_marker_maps
```

## 6. Notes

- P2 intentionally keeps the `MainWindow`-local implementation so later P3 cleanup can remove the obsolete Designer markers without changing runtime behavior again.
- `CONTEXT.md` is still effectively empty, so this refactor is grounded on `P02`, `R03`, and the existing module docs rather than project-level domain terminology.
