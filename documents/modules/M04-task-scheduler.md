# Task Scheduler

## Scope

Primary file: `task_thread.py`

## Responsibility

This module owns background task dispatch execution outside the UI thread.

It is responsible for:

- polling PostgreSQL for the highest-priority pending task
- translating task data into MiR mission submission calls
- waiting for mission queue completion
- updating task execution state through the DB manager
- sending the robot back to the charging station when no work exists or battery is low
- surfacing execution logs and completion signals back to the UI

## Main Runtime Object

| Object | Purpose |
|---|---|
| `TaskThread` | Long-running scheduler thread that dispatches and monitors tasks |

## Dependencies

- `main.py` for runtime maps and shared flags
- `functions.py` for MiR dispatch and mission queue state
- `TaskDBManager.py` for task selection and task-state persistence

## Execution Flow

1. Read highest-priority pending task from DB.
2. If no task exists, mark no-mission state and send MiR to charge station.
3. Translate `start_point`, `target_point`, and `mission_content` through runtime maps.
4. Submit a combined mission to MiR.
5. Resolve the resulting MiR mission queue id.
6. Mark task as `Executing` and persist `mq_id` when available.
7. Wait until mission queue state becomes `Done` or `Aborted`.
8. Emit completion back to the UI and continue the loop.

## Inputs

- pending task rows from PostgreSQL
- runtime mappings from `MainWindow`
- battery and idle flags shared by the UI

## Outputs

- DB status updates such as `Executing`
- `finished_task` signal to the UI
- log messages describing scheduler state
- MiR mission submissions and charge-station fallback commands

## Operational Policies Currently Embedded Here

- No pending work means send MiR to the charging station.
- Missing runtime mission/location mapping causes the cycle to be skipped.
- Temporary MiR disconnection is tolerated and retried while waiting for queue state.
- Low battery triggers a return-to-charge behavior after mission handling.

## Boundaries

- The scheduler owns dispatch sequencing and mission-completion waiting.
- It should not own widget manipulation beyond emitting signals.
- It depends on `MainWindow` state today, which is practical but tightly coupled.

## Known Risks

- `TaskThread` reaches into `MainWindow` for shared flags and maps, which reduces independence.
- Reconciliation depends on external MiR queue availability and can leave tasks in uncertain intermediate states.
- No-mission and low-battery policies are embedded as thread behavior rather than explicit domain rules.

## Refactor Seams

- Inject a narrower scheduler context instead of the full `MainWindow`.
- Separate dispatch policy from thread lifecycle.
- Add a formal task-state machine document and implementation guardrails.
