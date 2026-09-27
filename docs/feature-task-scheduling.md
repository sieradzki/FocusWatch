# Task Scheduling & Focused Work — Feature Plan

> **Historical design, not the specification for the new implementation.** This document belongs to the earlier Projects/task scheduling work. Its single-session model, migration requirements and statement that FocusWatch is not a blocker do not constrain the current product. See the [current brief](PROJECT_BRIEF.md), [decision status](architecture/DECISIONS.md) and [handoff](HANDOFF.md).

## Vision

FocusWatch tracks what users actually spend their time on (applications, window titles, categories). The **Task Scheduling** feature bridges the gap between *what users intend to work on* and *what they actually do*, by letting users schedule focused work sessions on specific tasks — or entire projects — and then comparing planned vs. actual activity.

---

## Core Concepts

### 1. Work Sessions

A **work session** is a planned block of focused time dedicated to a single task **or project**.

| Field | Type | Description |
|---|---|---|
| `id` | int (PK) | Unique session identifier |
| `task_id` | int (FK) \| null | Parent task (null for project-level sessions) |
| `project_id` | int (FK) | Parent project |
| `scheduled_start` | datetime \| null | Planned start time (null = unscheduled) |
| `scheduled_end` | datetime \| null | Planned end time |
| `actual_start` | datetime \| null | When tracking actually started |
| `actual_end` | datetime \| null | When tracking actually stopped |
| `status` | enum | `scheduled`, `in_progress`, `completed`, `skipped`, `cancelled` |
| `notes` | text | Optional session notes / retrospective |

- A task can have **many** work sessions (multi-session support). Each session independently tracks its own time.
- A project can have work sessions **without specifying a task** — useful when the user wants to dedicate time to a project in general (e.g., "work on FocusWatch for 2 hours") without committing to a specific task upfront.

### 2. Session Types

- **Scheduled session** — Has a specific `scheduled_start` + `scheduled_end`. Shows up on the timeline / calendar. The user is reminded when it's time to start.
- **Ad-hoc session** — Created on the fly via "Start Tracking" button. No pre-planned time slot. `scheduled_start` and `scheduled_end` are null; only `actual_start` / `actual_end` are populated.
- **Project-level session** — `task_id` is null, only `project_id` is set. Time is tracked against the project as a whole. The user can optionally assign a task to the session mid-tracking (e.g., they decide what to work on once they start).

### 3. Task Time Tracking (replaces current `total_tracked_time`)

The current single `total_tracked_time` integer on the Task model becomes a **computed aggregate** of all work session durations. This provides:

- Per-session granularity (when was time actually spent?)
- Scheduled vs. actual comparison
- Historical session log per task

### 4. Focused Mode (future)

When a work session is active, FocusWatch enters **Focused Mode**:

- The active task is pinned in the UI (tray icon, overlay, or sidebar).
- Activity classification is enhanced: time spent on relevant apps/websites is tagged as "on-task"; everything else is "off-task" or "distraction".
- Optional distraction alerts (configurable):
  - Gentle notification after N seconds on a non-task app.
  - Blocking is out of scope initially — FocusWatch is an awareness tool, not a blocker.
- A focus score is computed: `on-task time / session duration × 100`.

---

## Data Model Changes

### New Model: `WorkSession`

```python
class SessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

class WorkSession(Base):
    __tablename__ = "work_sessions"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.SCHEDULED)
    notes = Column(Text, nullable=True)

    task = relationship("Task", back_populates="work_sessions")
    project = relationship("Project", back_populates="work_sessions")
```

### Task Model Updates

```python
class Task(Base):
    # ... existing fields ...
    work_sessions = relationship("WorkSession", back_populates="task")

    @property
    def total_tracked_time(self) -> int:
        """Sum of completed session durations in seconds."""
        total = 0
        for s in self.work_sessions:
            if s.actual_start and s.actual_end:
                total += int((s.actual_end - s.actual_start).total_seconds())
        return total
```

### Project Model Updates

```python
class Project(Base):
    # ... existing fields ...
    work_sessions = relationship("WorkSession", back_populates="project", cascade="all, delete-orphan")

    @property
    def total_tracked_time(self) -> int:
        """Sum of all session durations (task-level + project-level)."""
        total = 0
        for s in self.work_sessions:
            if s.actual_start and s.actual_end:
                total += int((s.actual_end - s.actual_start).total_seconds())
        return total
```

### Migration

- Create `work_sessions` table.
- Migrate existing `total_tracked_time` values: for each task with tracked time > 0, create a single `completed` work session with `actual_start = task.created_at`, `actual_end = task.created_at + total_tracked_time`.
- Remove `total_tracked_time` column from tasks (or keep as a denormalized cache updated by triggers / service layer).

---

## Service Layer

### `WorkSessionService`

| Method | Description |
|---|---|
| `schedule_session(task_id, start, end)` | Create a scheduled session for a task at a future time slot |
| `schedule_project_session(project_id, start, end)` | Create a scheduled session for a project (no specific task) |
| `start_tracking(task_id)` | Start an ad-hoc or scheduled session for a task (sets `actual_start`, status → `in_progress`) |
| `start_project_tracking(project_id)` | Start tracking time against a project without a specific task |
| `assign_task_to_session(session_id, task_id)` | Assign a task to a project-level session mid-tracking |
| `stop_tracking(session_id)` | Stop the active session (sets `actual_end`, status → `completed`) |
| `get_active_session()` | Return the currently in-progress session (at most one) |
| `get_sessions_for_task(task_id)` | List all sessions for a task |
| `get_sessions_for_project(project_id)` | List all sessions for a project (including task-level sessions) |
| `get_sessions_for_date(date)` | List all sessions (scheduled + completed) for a given day |
| `skip_session(session_id)` | Mark a scheduled session as skipped |
| `cancel_session(session_id)` | Cancel a scheduled session |
| `update_session_notes(session_id, notes)` | Add retrospective notes |

### Integration with `WatcherService`

When a work session is `in_progress`, the watcher service can tag each activity log entry with the `session_id`. This enables post-session analysis:

- What apps were used during the session?
- How much time was on-task vs. off-task?
- What was the focus score?

---

## UI Changes

### Task Card (Kanban Board)

- **Tracked time badge** (already implemented): Shows total accumulated time across all sessions in the top-right corner of the card.
- **Active indicator**: When a session is in-progress for a task, show a pulsing/glowing border or a small "recording" dot on the card.
- **"Start Tracking" button**: Appears on hover or in the task dialog. Starts an ad-hoc session.

### Task Dialog

Replace the current simple start/due date with richer scheduling:

- **Schedule section**: List of work sessions (date, time, duration, status). Ability to add/remove sessions.
- **Quick schedule**: "Schedule for today at [time] for [duration]" shortcut.
- **Session log**: Expandable list of past sessions with actual durations and optional notes.
- **"Start Tracking" / "Stop Tracking" button**: Prominent button in the dialog header.

### Project Page / Board

- **Project-level "Start Tracking"**: A button on the project page header to start tracking time against the project without specifying a task. Useful for exploratory work, planning, or general project time.
- **Project total time**: Show total tracked time (sum of all task sessions + project-level sessions) in the project header.
- **Assign task mid-session**: When a project-level session is active, the user can click a task card to reassign the session to that task.

### Projects List

- **Tracked time column**: Show total tracked time per project in the projects list view.
- **Active indicator**: Show which project is currently being tracked.

### Home View Integration

- **Today's Schedule**: Show scheduled sessions for today on the home view timeline (alongside the existing activity timeline).
- **Upcoming sessions**: Small widget showing next scheduled session.

### Tray / System Integration

- When a session is active, update the tray icon tooltip with the current task name and elapsed time.
- Notification when a scheduled session is about to start (configurable lead time: 1, 5, 15 min).

---

## Implementation Phases

### Phase 1: Data Foundation
1. Create `WorkSession` model + migration.
2. Create `WorkSessionService` with basic CRUD.
3. Migrate existing `total_tracked_time` data to sessions.
4. Update `Task.total_tracked_time` to compute from sessions.
5. Unit tests for model + service.

### Phase 2: Manual Tracking
1. Add "Start Tracking" / "Stop Tracking" to task dialog.
2. Show active session indicator on task card.
3. Ensure only one session can be in-progress at a time.
4. Show session log in task dialog.
5. Update tracked time display on cards in real-time (timer).

### Phase 3: Scheduling
1. Add session scheduling UI (pick date + time range).
2. Show scheduled sessions on task cards and in task dialog.
3. Notification/reminder when a scheduled session approaches.
4. Auto-start option: when a scheduled time arrives, prompt "Start now?"
5. Skip / cancel / reschedule actions.

### Phase 4: Focused Mode
1. Tag activity log entries with active `session_id`.
2. Classify on-task vs. off-task activity during sessions.
3. Compute focus score per session.
4. Show focus score in session log / task dialog.
5. Optional distraction notifications during active sessions.

### Phase 5: Analytics
1. Per-task time breakdown (sessions over time chart).
2. Focus score trends.
3. Scheduled vs. actual comparison (were sessions completed as planned?).
4. Weekly/monthly summary: hours focused, focus score average, tasks completed.

---

## Open Questions

1. **Multiple active sessions?** Current plan: only one session at a time. Should there be an option to track multiple tasks simultaneously (e.g., context-switching between two tasks)?
2. **Calendar integration?** Export scheduled sessions as `.ics` / integrate with Google Calendar?
3. **Pomodoro mode?** Should sessions support pomodoro-style work/break cycles, or keep it simple with continuous sessions?
4. **Recurring sessions?** Tasks already have recurrence. Should individual sessions auto-generate based on the recurrence pattern (e.g., "Work on this task every day at 10:00 for 1h")?
5. **Break tracking?** Should there be a "pause session" action (without ending it), or should the user stop and start a new session?

---

## Summary

The task scheduling feature transforms FocusWatch from a passive time tracker into an active productivity tool:

| Current State | Future State |
|---|---|
| Tasks have a flat `total_tracked_time` | Time is tracked per work session |
| Start/due dates are metadata only | Sessions are schedulable time blocks |
| No concept of "working on a task" | Active sessions with tracking |
| Projects have no time tracking | Projects can be tracked independently or via tasks |
| Activity data is unlinked to tasks | Activity tagged by session for focus analysis |
