# Persistence Layer

## Scope

Primary files:

- `TaskDBManager.py`
- `UserDBManager.py`

## Responsibility

This module encapsulates PostgreSQL access for operational data.

It is responsible for:

- creating and reusing DB connections
- executing SQL queries and batch inserts
- persisting task queue lifecycle data
- sequencing pending tasks
- storing task mission queue identifiers and statuses
- maintaining user records and password hashes
- supporting room heartbeat-related data access used by the application

## Main Runtime Objects

| Object | Purpose |
|---|---|
| `TaskDBManager` | General task and operational DB access layer |
| `UserDBManager` | User-focused extension built on top of `TaskDBManager` |

## Task Data Responsibilities

Observed task responsibilities include:

- add single task
- add emergency task
- add batch tasks
- read highest-priority pending task
- update task status
- persist MiR mission queue id
- reorder or resequence pending tasks
- query currently executing task

## User Data Responsibilities

Observed user responsibilities include:

- initialize default admin account
- retrieve stored password hash
- list all usernames
- add user
- delete user
- update user password

## Inputs

- PostgreSQL connection configuration
- task creation data from UI
- task execution results from scheduler/UI reconciliation
- user-management requests from admin features

## Outputs

- persisted rows in task-related and user-related tables
- task/user query results returned as dictionaries or lists

## Boundaries

- This module should own SQL and transaction behavior.
- It should not know about widget concerns.
- It currently returns simple Python structures that upper layers interpret.

## Known Risks

- Connection lifecycle appears manual and may be fragile under long-running failures.
- Error handling is largely print-based and may hide important operational problems.
- The DB manager mixes generic DB utilities with domain-specific task logic in the same class.
- `UserDBManager` inherits from `TaskDBManager`, which is convenient but couples two different subdomains.

## Refactor Seams

- Split generic DB session handling from task/user repositories.
- Introduce explicit repository interfaces for tasks and users.
- Standardize error signaling so callers can distinguish retryable vs terminal failures.
