"""Integration tests for project/task time entries."""

from datetime import datetime, timedelta
import subprocess
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from focuswatch.database.models import Base
from focuswatch.database.models.project import Project
from focuswatch.database.models.task import Task
from focuswatch.database.models.time_log import TimeLog
from focuswatch.database.models.time_schedule import TimeSchedule


@pytest.fixture
def session():
  """Use a fresh database so constraints are enforced by SQLite."""
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  with Session(engine) as db_session:
    yield db_session
  engine.dispose()


@pytest.mark.parametrize("model", [TimeLog, TimeSchedule])
@pytest.mark.parametrize("owner", ["task", "project"])
def test_time_entry_round_trip(session, model, owner):
  """Both types of owner must survive saving and reloading."""
  project = Project(name="Project")
  task = Task(name="Task", project_id=None)
  session.add_all([project, task])
  session.flush()
  start = datetime(2026, 1, 1, 12)
  entry = model(start_time=start, end_time=start + timedelta(minutes=30))
  getattr(task if owner == "task" else project,
          "time_logs" if model is TimeLog else "schedules").append(entry)
  session.commit()
  session.expire_all()

  saved = session.get(model, entry.id)
  assert saved.duration == 1800
  assert (saved.task_id is not None) == (owner == "task")
  assert (saved.project_id is not None) == (owner == "project")
  if model is TimeLog and owner == "task":
    assert task.total_tracked_time == 1800


@pytest.mark.parametrize("model", [TimeLog, TimeSchedule])
@pytest.mark.parametrize("both_owners", [False, True])
def test_time_entry_requires_exactly_one_owner(session, model, both_owners):
  """An unassigned entry and a doubly assigned entry are both invalid."""
  project = Project(name="Project")
  task = Task(name="Task")
  session.add_all([project, task])
  session.flush()
  entry = model(
    task_id=task.id if both_owners else None,
    project_id=project.id if both_owners else None,
    start_time=datetime(2026, 1, 1, 12),
    end_time=datetime(2026, 1, 1, 13),
  )
  session.add(entry)
  with pytest.raises(IntegrityError):
    session.flush()


def test_project_model_can_be_used_without_importing_the_app():
  """Model registration must not depend on importing a GUI or service first."""
  result = subprocess.run(
    [sys.executable, "-c",
     "from focuswatch.database.models.project import Project; "
     "print(Project(name='Independent project').name)"],
    capture_output=True, text=True, check=False,
  )
  assert result.returncode == 0, result.stderr
  assert result.stdout.strip() == "Independent project"
