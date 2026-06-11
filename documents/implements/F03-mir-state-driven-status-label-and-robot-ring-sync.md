---
author: Codex
date: 2026-06-11
title: P06 P1-P4 - MiR state UI mapping, status label, robot ring, presentation refresh, and cross-site fallback verification
uuid: 3150f9650d764f10b76430d38dff92b4
version: v1
---

# F03 - P06 P1-P4 MiR State UI Mapping, Presentation Sync, and Cross-Site Fallback Verification

## 1. Feature Overview
This implementation now delivers `P06 / P1-P4` by centralizing MiR `state_id` UI metadata in `main.py`, routing status label rendering through a shared helper, drawing the main-map robot ring from that same shared state presentation, and refreshing both through one presentation-sync path whenever MiR polling state changes. It also verifies that API or mission-queue disconnect conditions use one shared `Unknown/Offline` fallback regardless of `site_profile`, so `company` and `hospital` stay behaviorally aligned.

## 2. Requirement / User Story
- As an operator
- I want the main status label and robot ring to resolve MiR state presentation from one shared mapping
- So that the main map and status area stay visually in sync without duplicating state logic

## 3. Acceptance Criteria
- Given a known MiR `state_id`
  - When the main window updates robot status
  - Then the status label text and color are resolved from `MIR_STATE_UI`
- Given a known MiR `state_id`
  - When the main map redraws the robot marker
  - Then the robot ring color is resolved from the same `MIR_STATE_UI` entry
- Given the MiR API or mission-queue polling is disconnected
  - When the UI asks for state presentation
  - Then the status label and robot ring both fall back to `UNKNOWN_MIR_STATE_UI`
- Given different `site_profile` values
  - When `_get_mir_state_ui()` is called
  - Then the returned state UI is independent from `site_profile`

## 4. Implementation Notes
- Added top-level constants:
  - `MIR_STATE_UI`
  - `UNKNOWN_MIR_STATE_UI`
- Added `MainWindow` helpers:
  - `_has_mir_state_connection_issue()`
  - `_get_mir_state_ui(state_id)`
- Added presentation refresh helper:
  - `_refresh_robot_status_presentation(state_id=None, advance_glow=False)`
- Updated the final `_update_status_label()` implementation to consume the helper result instead of maintaining an inline `status_map`
- Updated `draw_robot_marker()` so the robot ring and motion glow derive from `state_ui["map_ring_color"]`
- Confirmed via focused tests that `_get_mir_state_ui()` remains independent from `site_profile`
- Confirmed via focused tests that `company` and `hospital` share the same `Unknown/Offline` fallback for API-error and mission-queue disconnect states
- Wired presentation refresh orchestration into:
  - `_print_mission_text()`
  - `api_error_handler()`
  - `query_mir_info()` success and exception paths
  - `query_mir_status_db()` disconnect / restore transitions
  - manual `on_update_info_clicked()` refresh

## 5. Test Scenarios
| ID | Scenario | Expected |
|---|---|---|
| TC1 | `state_id = 3` with healthy connections | Label shows `Ready` using mapped green label color |
| TC2 | `state_id = 12` with healthy connections | Label shows `Error` using mapped purple label color |
| TC3 | API error path triggers | Label falls back to `Unknown/Offline` |
| TC4 | mission queue state becomes unavailable | Label falls back to `Unknown/Offline` |
| TC5 | mission queue connection restores | Label returns to mapped state presentation |
| TC6 | `state_id = 12` on map redraw | Robot ring uses mapped purple ring color |
| TC7 | disconnect fallback on map redraw | Robot ring uses `Unknown/Offline` white ring color |
| TC8 | `state_id = 12` across `company` and `hospital` | `_get_mir_state_ui()` returns the same mapped state presentation |
| TC9 | API error or mission-queue disconnect across `company` and `hospital` | `_get_mir_state_ui()` returns the shared `UNKNOWN_MIR_STATE_UI` fallback |

## 6. Verification
Verification performed via focused regression tests and syntax validation:

```bash
python -m unittest tests.test_mir_status_presentation_refresh
python -c "import ast, pathlib; ast.parse(pathlib.Path('main.py').read_text(encoding='utf-8'))"
```
