---
author: Codex
date: 2026-06-03
title: Site Marker Schema And Runtime Maps
uuid: 1e32fbc57d1e4ba6ab6571f1bb1ba833
version: v1
planning: documents/planning/P02-map-marker-externalization-and-scaled-positioning.md
status: completed
---

# R03 Site Marker Schema And Runtime Maps

## 1. Scope

P02 P1 focuses on moving main-map marker geometry into `site/*.json` and making `build_site_runtime_maps()` expose marker-oriented runtime structures for later UI work.

## 2. Goals

- Externalize marker geometry into site config instead of relying on Qt Designer geometry as the source of truth.
- Keep `locations[*].marker_id` as the business-to-marker binding.
- Let runtime maps distinguish between:
  - locations that intentionally have no marker
  - locations that reference a missing marker definition

## 3. Changes

### R1. Site schema adds `markers`

- `site/company.json` now contains a `markers` array seeded from the current `label_rp_1` to `label_rp_7` geometry in `ui_main.py`.
- `site/hospital.json` now contains a `markers` array for `label_rp_1` to `label_rp_13`.
- Each marker spec currently includes:
  - `marker_id`
  - `x_px`
  - `y_px`
  - `width_px`
  - `height_px`

### R2. Runtime maps expose marker structures

- `build_marker_specs_by_id()` normalizes marker records into a dictionary keyed by `marker_id`.
- `build_site_runtime_maps()` now returns:
  - `marker_specs_by_id`
  - `marker_location_names_by_id`
  - `locations_without_markers`
  - `marker_config_warnings`

### R3. Validation stays non-destructive for P1

- Duplicate marker definitions are collected as warnings.
- A location that points to an undefined `marker_id` is preserved in the runtime maps and also reported as a warning.
- Locations without `marker_id` are tracked separately so later phases can tell “no marker by design” from “broken marker reference”.

## 4. Test Coverage

| Test ID | Type | Coverage |
|---|---|---|
| R03-T1 | unit | `company` and `hospital` site profiles expose complete `marker_specs_by_id` maps and all runtime marker references resolve to defined marker ids |
| R03-T2 | unit | shared markers and marker-less locations are tracked separately in runtime maps |
| R03-T3 | unit | duplicate marker ids and missing marker references produce warnings without dropping runtime location bindings |

## 5. Verification

```bash
python -m unittest tests.test_site_runtime_marker_maps
```

## 6. Notes

- The hospital marker coordinates are an initial config-driven baseline taken from the current floor-plan asset and can be fine-tuned in P2/P3 without changing code.
- P2 can now consume `MARKER_SPECS_BY_ID` directly when replacing the legacy Designer marker widgets with runtime-built widgets.
