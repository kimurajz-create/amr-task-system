---
author: Codex
date: 2026-06-05
title: MiR performance dashboard phase 2 KPI planning
status: draft
version: v1
uuid: 9f3e8d8d6df2480eaf9e8bf78a8b6b42
---

# P05 MiR performance dashboard phase 2 KPI planning

## 1. Why this phase exists

`P04` delivered a first usable dashboard focused on task volume and route hotspots. That gives operators a fast read on queue shape, completion mix, and repeated traffic paths, but it does not yet answer the next layer of operational questions:

- Which tasks are waiting too long before execution
- Which routes or missions are slow to finish
- Whether failures are trending up for a specific mission or destination
- Whether robot health and room heartbeat issues are correlated with task outcomes

This phase turns those follow-up questions into a concrete KPI roadmap so the next implementation cycle can build on a stable v1 dashboard instead of mixing exploratory metrics into the already-shipped view.

## 2. Phase goal

Define the next KPI set for the performance dashboard, including required schema support, query shape, UI presentation, and rollout sequencing.

## 3. Inputs from P04

### Confirmed outcomes

- Dashboard window entry exists and refreshes safely from `MainWindow`
- `TaskDBManager` already exposes reusable read-only statistics queries
- Operators can view:
  - task status summary
  - task volume by mission
  - start-point hotspots
  - target-point hotspots
  - route hotspots

### Remaining gaps observed after v1

- No time-based KPI yet
- No failure-rate KPI yet
- No heartbeat/API correlation KPI yet
- No filtering by recent time window yet
- No distinction between historic totals and currently-relevant recent trends

## 4. In scope

- Define phase 2 KPI candidates and order them by operational value
- Specify data dependencies for each KPI
- Decide which KPIs can be computed from current `tasks` schema and which require schema expansion
- Define a phased implementation path that keeps dashboard refresh cheap

## 5. Out of scope

- Implementing new KPI code in this document
- Adding charts/BI tooling outside the existing desktop dashboard
- Reworking the v1 dashboard layout unless a KPI cannot fit the current structure

## 6. Candidate KPI set

### Priority A: task timing KPIs

- Average wait time
  - Definition: task creation to execution start
  - Value: reveals queueing pressure
- Average execution time
  - Definition: execution start to completion/abort
  - Value: reveals slow missions or route friction
- Longest waiting tasks
  - Definition: top N tasks by wait duration
  - Value: reveals operational backlog quickly

### Priority B: reliability KPIs

- Mission failure count
  - Group by `mission_content`
  - Value: identifies fragile mission types
- Destination failure count
  - Group by `target_point`
  - Value: shows problematic receiving points
- Abort rate
  - Definition: `Aborted / (Completed + Aborted)`
  - Value: compact reliability signal

### Priority C: system correlation KPIs

- Room heartbeat anomaly count
  - Value: shows unstable physical endpoints
- MiR API/polling error count
  - Value: separates robot/system instability from task design issues
- Task outcome vs. system health correlation
  - Value: helps explain whether failures are operational or infrastructure-driven

## 7. Data readiness assessment

### Ready with current schema

- Abort rate
- Mission failure count
- Destination failure count
- Historic completed/aborted volume trends based on existing status rows

### Requires new task lifecycle timestamps

- Average wait time
- Average execution time
- Longest waiting tasks

Required fields previously identified in `P04`:

- `started_at`
- `completed_at`
- `aborted_at`
- `wait_seconds`
- `execution_seconds`

### Requires additional non-task telemetry persistence

- Room heartbeat anomaly count
- MiR API/polling error count
- Task-to-system correlation views

## 8. Recommended implementation order

### Phase 2A

Add task lifecycle timestamps and derived durations, then expose:

- average wait time
- average execution time
- longest waiting tasks

Reason: highest operational value, lowest ambiguity, directly extends the existing `tasks` domain.

### Phase 2B

Add reliability summaries:

- abort rate
- failure count by mission
- failure count by target point

Reason: can reuse the same dashboard surface and query patterns as `P04`.

### Phase 2C

Add telemetry correlation KPIs only after persistent error-event storage exists.

Reason: otherwise the dashboard would mix durable task data with transient runtime state and produce misleading results.

## 9. Acceptance direction for the next implementation doc

The next implementation cycle should only start after we have a document that pins down:

- exact lifecycle field names and meaning
- how timestamps are written during task transitions
- whether duration values are persisted or derived in SQL
- whether dashboard KPIs are all-time, recent-window, or both
- refresh budget for new queries

## 10. Deliverables

- `FXX`: task lifecycle timing instrumentation
- `RXX`: duration and reliability statistics queries
- optional follow-up `PXX`: telemetry persistence and correlation KPIs
