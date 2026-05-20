# Module Overview

## Purpose

This project is a PySide6 desktop application for dispatching MiR robot missions, tracking task execution, and reflecting robot/task state in the UI.

## Current Module Map

| Module | Primary Files | Responsibility |
|---|---|---|
| UI Application Shell | `main.py`, `ui_main.py`, `ui_login_window.py`, `ui_admin_panel.py`, `ui_selected_map.py` | Compose screens, bind widgets, react to timers, and orchestrate DB/API/thread usage |
| Site Configuration and Runtime Mapping | `main.py`, `site/*.json`, `app_settings.json` | Load site profile, assets, calibration, location names, mission names, marker mapping, and charging-station rules |
| MiR API Adapter | `functions.py`, `config.json` | Wrap MiR HTTP APIs for status, missions, maps, positions, lift, sound, and mission queue state |
| Task Scheduler | `task_thread.py` | Pull pending tasks from DB, send MiR missions, wait for mission queue completion, and handle charge fallback |
| Persistence Layer | `TaskDBManager.py`, `UserDBManager.py` | Read/write task queue data, user data, sequencing, execution state, and room heartbeat-related data |

## High-Level Runtime Flow

1. `main.py` boots the application, creates DB managers, and opens the login flow.
2. `MainWindow` loads site configuration and derives runtime maps for UI labels and MiR identifiers.
3. UI timers poll MiR status, battery, room state, task list, and mission reconciliation.
4. `TaskThread` continuously fetches the highest-priority pending task from PostgreSQL.
5. `TaskThread` uses `functions.py` to submit MiR missions and monitor mission queue state.
6. `TaskDBManager` persists task lifecycle changes such as `Pending`, `Executing`, `Completed`, and `Aborted`.

## Boundaries

- `main.py` is currently both application shell and feature orchestration layer.
- `functions.py` is the external-integration layer for MiR.
- `task_thread.py` owns background scheduling behavior.
- `TaskDBManager.py` and `UserDBManager.py` own database access concerns.
- `site/*.json` and `app_settings.json` provide environment/site variability without code changes.

## Current Architectural Risks

- `main.py` contains multiple responsibilities and is the biggest coordination hotspot.
- `functions.py` relies on module-level globals such as MiR IP and credentials, which increases coupling.
- UI logic, runtime mapping, and operational policies are partially mixed together in `main.py`.
- Scheduler behavior depends on both MiR API state and DB state reconciliation, which makes failures subtle.

## Suggested Next Documentation

- A screen/module document for each major UI surface if the team plans active UI changes.
- A task lifecycle document describing all task states and transitions.
- A site-profile schema document for `site/*.json` and `app_settings.json`.
