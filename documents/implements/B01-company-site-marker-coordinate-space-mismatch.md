---
author: Codex
date: 2026-06-01
title: Company Site Marker Coordinate Space Mismatch
uuid: 653d2f94f0e3465cb8b69cf9b6fd2b98
version: v1
status: draft
---
# Bug Fix B01

## 1. Bug Overview

`site/company.json` currently mixes two different coordinate spaces inside the same marker records.

- `x_px/y_px` match the existing fixed marker widget geometry in `ui_main.py` (`label_rp_1` through `label_rp_7`) and therefore match the company UI that users see now.
- The same records also store `world_x_m/world_y_m`, but when those values are projected back through the current `company` calibration in `main.py`, the resulting pixels land in a different large-image space rather than the current small-map UI space.

Observed examples from the current data:

- `label_rp_1`: stored top-left `(290, 230)`, derived from world/calibration `(842, 720)`
- `label_rp_7`: stored top-left `(870, 320)`, derived from world/calibration `(2548, 956)`

This means the `company` profile is internally inconsistent even though the current UI still looks correct, because the runtime is still showing the old fixed widgets from `ui_main.py`.

`hospital` is the control case: its stored `x_px/y_px` and calibration-derived pixel positions match.

## 2. Fix Objective

Define this as an independent bug: for the current product iteration, a company marker record must resolve to one coherent on-screen coordinate space.

The correct coordinate space for this bug is:

- the current fixed marker-widget top-left pixel space used by `ui_main.py`
- relative to the existing company map shell that the user actually sees now
- not a separate raw large-image pixel space

This bug fix must:

- keep `x_px/y_px`
- keep the existing fixed marker widgets in `ui_main.py`
- avoid P2 work
- avoid converting this iteration to dynamic marker widget creation

## 3. Acceptance Criteria

- **Scenario 1: Company marker world coordinates map back to the current UI space**
  - **Given** the `company` site profile and its marker records in `site/company.json`
  - **When** each marker with `world_x_m/world_y_m` is projected through the company calibration and converted to marker top-left pixel coordinates using its `width_px/height_px`
  - **Then** the derived top-left pixel result matches the intended current company UI marker position in the same coordinate space, within a tolerance of `+/- 1 px` per axis

- **Scenario 2: Company keeps the current visible marker layout**
  - **Given** the existing `ui_main.py` fixed marker widgets `label_rp_1` through `label_rp_7`
  - **When** the app loads with `site_profile = company`
  - **Then** the visible marker positions remain aligned with the current company small-map UI and do not jump to a second large-image space

- **Scenario 3: Stored pixel geometry remains part of the contract**
  - **Given** the `company` marker schema
  - **When** this bug is fixed
  - **Then** `x_px/y_px` remain present in `site/company.json` and continue to represent the current UI marker top-left coordinates for this iteration

- **Scenario 4: Hospital behavior does not regress**
  - **Given** the `hospital` site profile
  - **When** the same calibration-to-pixel consistency check is applied
  - **Then** hospital markers continue to resolve to their existing stored `x_px/y_px` positions without regression

## 4. Test Scenarios / Examples

| ID | Scenario | Given | When | Then | Priority |
|---|---|---|---|---|---|
| TC1 | Detect current company mismatch | Current `company` marker/calibration data | Reproject `world_x_m/world_y_m` to top-left pixels | At least one marker currently fails parity against stored `x_px/y_px`; this reproduces the bug | High |
| TC2 | Validate company parity after fix | Updated `company` marker/calibration data | Reproject all company markers | Every derived top-left matches stored/intended UI geometry within `+/- 1 px` | High |
| TC3 | Preserve current company UI layout | Existing fixed `label_rp_*` widgets in `ui_main.py` | Launch company profile and inspect markers | Visible marker positions stay at the current small-map locations | High |
| TC4 | Prevent hospital regression | Current `hospital` site profile | Run the same parity check | Hospital markers still pass without changes to their displayed positions | Medium |

## 5. Implementation Notes

- `ui_main.py` still owns the visible company marker geometry through fixed `QLabel` widgets (`label_rp_1` to `label_rp_7`).
- `refresh_label_tooltip()` currently decorates existing widgets only; it does not reposition them from `MARKER_SPECS_BY_ID`.
- `_build_marker_specs_by_id()` only derives pixel coordinates from `world_x_m/world_y_m` when `x_px/y_px` are absent, so the inconsistency is currently latent data debt rather than an active runtime repositioning bug.
- The fix should make `company` data internally coherent without pulling P2 into scope.
- Acceptable implementation directions include:
  - correcting the company calibration so it targets the current displayed map space
  - correcting the company marker world/pixel data pairing so world back-projection lands on the current displayed UI positions
- Out of scope for this bug:
  - dynamic marker widget creation
  - removal of `x_px/y_px`
  - replacing the current `ui_main.py` marker layout system

## 6. Additional Notes

- This bug formalizes the known `company` risk already noted in `R03-site-marker-schema-and-runtime-maps.md`: company kept UI pixel geometry as the working truth, but the preserved world-coordinate dataset does not belong to the same rendered map space.
- The main value of this B01 is to make the coordinate-space contract explicit before any later marker-layer work resumes.
