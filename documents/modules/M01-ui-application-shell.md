# UI Application Shell

## Scope

Primary file: `main.py`

Supporting generated UI files:
- `ui_main.py`
- `ui_login_window.py`
- `ui_admin_panel.py`
- `ui_selected_map.py`

## Responsibility

The UI application shell is responsible for:

- Bootstrapping the desktop application and main windows
- Wiring generated Qt UI classes into interactive widgets
- Holding shared runtime state such as site profile, runtime maps, robot status flags, and timers
- Coordinating DB managers, MiR API adapter calls, and background task thread events
- Reflecting robot/task state into tables, labels, notifications, and map markers

## Main Runtime Objects

| Object | Purpose |
|---|---|
| `LoginWindow` | User login entry and access gateway to the main system |
| `AdminPanel` | Admin-oriented user management or maintenance surface |
| `SelectedMap` | Interactive map selection dialog for choosing task start/destination |
| `MainWindow` | Main operational console for task dispatch, monitoring, status polling, and map updates |
| `DBWorker` | Helper worker thread for non-blocking DB/API calls initiated by UI |

## Key Dependencies

- `functions.py` for MiR robot API interactions
- `TaskDBManager.py` for task data
- `UserDBManager.py` for user data
- `task_thread.py` for background scheduling
- `site/*.json` for location, mission, marker, and asset definitions
- `app_settings.json` for active site profile

## Inputs

- User actions from buttons, combo boxes, dialogs, and tables
- Site profile from environment variable or `app_settings.json`
- MiR status from periodic polling
- Task/user records from PostgreSQL managers
- Mission completion events from `TaskThread`

## Outputs

- Updated UI status labels, notifications, task tables, and map markers
- MiR commands delegated via `functions.py`
- Task state updates delegated to `TaskDBManager`
- User-management operations delegated to `UserDBManager`

## Internal Subdomains

### 1. Boot and Runtime Configuration

`main.py` resolves runtime paths, loads app settings, loads `site/<profile>.json`, and derives runtime maps used across UI and scheduling.

### 2. Screen Composition

Qt Designer-generated classes are attached to custom widget classes that add behaviors not stored in `.ui` files.

### 3. Status Polling

`MainWindow` owns several timers:

- fast polling for MiR operational status and robot position
- slow polling for battery and room heartbeat
- refresh polling for task list and mission reconciliation

### 4. Task Interaction

`MainWindow` creates, displays, updates, and finalizes task information while delegating persistence and robot execution elsewhere.

## Boundaries

- This module should orchestrate behavior, not implement MiR HTTP details.
- This module should display task state, not own task queue persistence rules.
- This module currently contains some operational policy and mapping logic that may later deserve extraction.

## Known Risks

- `MainWindow` is very large and likely the main future refactor target.
- Shared mutable flags such as `is_AMR_idle`, `is_low_battery`, and polling state create coordination risk.
- UI polling and DB/API reconciliation logic are tightly interwoven.

## Refactor Seams

- Extract site/runtime mapping into a dedicated module.
- Extract task presentation logic from `MainWindow`.
- Extract status polling orchestration into a dedicated coordinator/service layer.
