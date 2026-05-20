# MiR API Adapter

## Scope

Primary file: `functions.py`

Supporting config:
- `config.json`

## Responsibility

This module wraps MiR HTTP API calls and exposes Python functions that the UI and scheduler can call directly.

Its responsibilities include:

- loading and saving MiR connection config
- constructing request authorization headers
- querying robot status and mission text
- reading current map and position data
- dispatching robot missions and relative moves
- checking mission queue state
- clearing robot error state
- invoking device-side actions such as sound or lift movement

## Main Capability Groups

| Capability | Example Functions |
|---|---|
| Config | `load_config`, `save_config`, `load_ip`, `save_ip` |
| Authentication | `get_auth_headers` |
| Status | `check_MiR_status`, `check_api_status_v3`, `get_battery_level` |
| Map and Position | `check_MiR_status_position`, `get_curmaps_positions_cmb`, `post_position` |
| Mission Lookup | `get_mission_id`, `get_mission_groups_id_cmb`, `get_mission_point_uuid` |
| Mission Dispatch | `move_to_position`, `move_to_position_multi_var`, `run_combo_location_multi_var` |
| Mission Queue Monitoring | `get_mission_queue_max_id`, `get_mission_queue_id_state` |
| Recovery and Operations | `clear_MiR_error`, `stop_the_mission`, `set_lift_position`, `play_sound` |

## Consumers

- `MainWindow` in `main.py`
- `TaskThread` in `task_thread.py`

## Inputs

- MiR base URL from `config.json` or runtime updates
- static credentials currently stored in module constants
- mission/location identifiers coming from runtime maps or UI selection

## Outputs

- parsed JSON status data
- scalar status fields such as battery or state id
- mission queue identifiers and states
- side effects on the robot through HTTP requests

## Boundaries

- This module should know MiR API details.
- This module should not decide business priority or UI presentation.
- Consumers should treat this layer as the single place for robot HTTP operations.

## Known Risks

- It relies on module-level mutable globals like `MIR_IP` and `Full_IP`.
- Credentials are embedded in code, which is operationally risky.
- Error handling is inconsistent: some functions return `None`, some return `1`, and some raise exceptions.
- Timeout handling is present in some API calls but not consistently across all requests.

## Refactor Seams

- Replace module globals with a typed client object.
- Normalize error handling into one strategy.
- Group related functions into status, mission, queue, and config classes or modules.
