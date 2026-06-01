---
author: Codex
date: 2026-06-01
title: Site Marker Schema And Runtime Maps
uuid: 4f0bd7b39c3f4c3ca29a0fa41bc2ea3b
version: v1
planning: documents/planning/P02-map-marker-externalization-and-scaled-positioning.md
status: completed
---

# R03 Site Marker Schema And Runtime Maps

## 1. Goal

P02 P1 moves map-marker geometry out of Qt Designer-only ownership and into `site/*.json`, while keeping existing location-to-marker behavior stable for the current UI.

## 2. User Story

- **As a** maintainer of multiple site profiles
- **I want** marker ids and marker geometry to live in site configuration and be exposed through stable runtime maps
- **So that** later UI work can build and position marker widgets from configuration instead of hardcoded `label_rp_*` geometry

## 3. Scope And Impact

| Area | Before | R03 change |
|---|---|---|
| `site/company.json` | Marker ids existed only on locations | Adds `markers[*]` records and now stores the real MiR world coordinates alongside the existing pixel geometry |
| `site/hospital.json` | Marker ids on locations only | Adds `markers[*]` geometry records derived from MiR world coordinates |
| `main.py` / `load_site_config()` | No explicit `markers` default | Normalizes `markers` to an empty list for every site profile |
| `main.py` / `build_site_runtime_maps()` | Produced location/mission/room maps only | Adds `marker_specs_by_id` and `marker_locations_by_id`, with validation for defined marker schemas |
| `MainWindow` runtime state | No direct marker geometry runtime contract | Stores `MARKER_SPECS_BY_ID` and `MARKER_LOCATIONS_BY_ID` for later P2 use |

## 4. Acceptance Notes

- `company` site profile now contains configuration-owned marker geometry for `label_rp_1` through `label_rp_7`, plus the real MiR world coordinates for those markers.
- Runtime mapping now exposes:
  - `location_to_marker`
  - `marker_locations_by_id`
  - `marker_specs_by_id`
- If a site defines `markers`, every referenced `locations[*].marker_id` must exist in that marker schema.
- A marker may be defined with direct `x_px/y_px`, or with `world_x_m/world_y_m` so runtime can derive the pixel geometry through calibration.
- Hospital marker geometry is now populated from MiR world coordinates converted through site calibration, and OR 4 is intentionally absent from this site profile.

## 5. Risks

- Company still keeps its current UI pixel geometry as the source of truth for this iteration, because its existing on-screen marker layout is not yet fully recalculated from the world-coordinate dataset.
- Validation is strict once a site starts defining `markers`; malformed geometry or duplicate ids will now fail fast.

## 6. Implementation Record

### Final behavior in this iteration

- `load_site_config()` always returns a `markers` collection.
- `build_site_runtime_maps()` derives reverse marker lookups and validated marker geometry maps.
- `company` marker geometry still matches the current `ui_main.py` label positions, while also preserving the real MiR world coordinates in config.
- `hospital` now contains marker geometry for OR 1-3 and OR 5-13, derived from MiR world coordinates.
- `hospital` removes OR 4 robot/shelf references to match the real site naming scheme.

### Files changed

- `main.py`
- `site/company.json`
- `site/hospital.json`
- `documents/modules/M02-site-configuration-and-runtime-mapping.md`

### Verification target

- JSON files remain parseable.
- `main.py` remains syntactically valid.
- Runtime maps for `company` include both marker geometry and reverse marker-location lookup.

## 7. Next Step

Provide the hospital marker coordinates/sizes so the same schema can be populated there, then proceed to P2 dynamic marker-layer construction.
