---
author: Codex
date: 2026-06-11
title: P06 P1 - MiR state UI mapping and offline fallback
uuid: 3150f9650d764f10b76430d38dff92b4
version: v1
---

# F03 - P06 P1 MiR State UI Mapping

## 1. Feature Overview
This implementation delivers `P06 / P1` by centralizing MiR `state_id` UI metadata in `main.py` and routing status label rendering through a shared helper. It also introduces a single fallback path for API or mission-queue disconnect conditions so the UI can consistently show `Unknown/Offline`.

## 2. Requirement / User Story
- As an operator
- I want the main status label to resolve MiR state text and fallback state from one shared mapping
- So that later robot-ring and refresh work can reuse the same source of truth without duplicating state logic

## 3. Acceptance Criteria
- Given a known MiR `state_id`
  - When the main window updates robot status
  - Then the status label text and color are resolved from `MIR_STATE_UI`
- Given the MiR API or mission-queue polling is disconnected
  - When the UI asks for state presentation
  - Then the UI falls back to `UNKNOWN_MIR_STATE_UI`
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
- Updated the final `_update_status_label()` implementation to consume the helper result instead of maintaining an inline `status_map`
- Wired fallback label refresh into:
  - `api_error_handler()`
  - `query_mir_info()` exception path
  - `query_mir_status_db()` disconnect / restore transitions

## 5. Test Scenarios
| ID | Scenario | Expected |
|---|---|---|
| TC1 | `state_id = 3` with healthy connections | Label shows `Ready` using mapped green label color |
| TC2 | `state_id = 12` with healthy connections | Label shows `Error` using mapped purple label color |
| TC3 | API error path triggers | Label falls back to `Unknown/Offline` |
| TC4 | mission queue state becomes unavailable | Label falls back to `Unknown/Offline` |
| TC5 | mission queue connection restores | Label returns to mapped state presentation |

## 6. Verification
Manual verification performed via code inspection and syntax validation target:

```bash
python -m py_compile main.py
```

## 7. Notes
- `P2` still needs to switch `draw_robot_marker()` to `state_ui["map_ring_color"]`.
- `P3` still owns broader presentation refresh orchestration beyond the fallback hooks added here.
