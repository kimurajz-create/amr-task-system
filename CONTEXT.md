# CONTEXT

> Project-level context for DDD work. Keep this file concise and current so future feature, refactor, and bugfix documents start from shared language instead of guesswork.

## Language

**MiR State ID**: The robot runtime state identifier returned by the MiR API. It is the source of truth for robot state presentation in the desktop UI.

**Status Label**: The top-right `label_Status_1` text block in `MainWindow` that shows robot state name and current mission text.

**Map Ring**: The circular outline rendered around the robot marker on the main map. It is a presentation layer for robot state, not a task-state indicator.

**Robot Marker**: The vehicle icon rendered on `label_car_overlay` above the map image.

**Unknown/Offline State**: A presentation fallback used when the UI cannot resolve a valid MiR state from polling or reconciliation.

## Relationships

`MainWindow` in `main.py` polls `functions.py` for MiR status, mission text, battery, and position, then renders the result into:

- the top-right status label
- the map robot marker and ring
- other task and notification widgets

Task execution state comes from the persistence and scheduler flow, but robot state presentation should come from MiR status polling rather than task table status.

## Architecture Boundaries

- `functions.py` owns MiR HTTP/API details and returns raw robot status data.
- `main.py` owns UI presentation decisions, including status text, map ring rendering, and fallback presentation.
- `site/*.json` owns site assets, markers, and location mappings. It is not the primary home for MiR state color semantics.
- `TaskDBManager.py` and `task_thread.py` own task persistence and dispatch flow, not robot lamp presentation rules.

## Flagged Ambiguities

- The exact official per-`state_id` color mapping source document is not stored in this repository yet.
- Map ring colors may intentionally differ from status label text colors for contrast, while preserving the same state meaning.
