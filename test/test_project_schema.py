"""Regression tests for upgrading the pre-board SQLite schema."""

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from focuswatch.database.models import Base
from focuswatch.database.models.task import TaskPriority, TaskStatus
from focuswatch.services.task_service import TaskService


class MemoryConnection:
  """Provide the service connection API without loading a user's config."""

  def __init__(self, engine):
    self.engine = engine
    self._factory = sessionmaker(bind=engine)

  def get_session(self):
    """Return a real SQLAlchemy session."""
    return self._factory()


@pytest.fixture
def legacy_database():
  """Reproduce the tables and enum values from the committed task model."""
  engine = create_engine("sqlite:///:memory:")
  with engine.begin() as conn:
    conn.execute(text("""CREATE TABLE projects (
      id INTEGER PRIMARY KEY, name VARCHAR NOT NULL, color VARCHAR,
      description TEXT, status VARCHAR NOT NULL)"""))
    conn.execute(text("INSERT INTO projects VALUES (1, 'Legacy project', NULL, 'Keep me', 'active')"))
    conn.execute(text("""CREATE TABLE tasks (
      id INTEGER PRIMARY KEY, name TEXT NOT NULL, project_id INTEGER,
      start_date DATETIME, due_date DATETIME,
      priority VARCHAR NOT NULL, status VARCHAR NOT NULL)"""))
    conn.execute(text("""INSERT INTO tasks VALUES (
      1, 'Legacy task', 1, '2026-01-01 12:00:00', NULL, 'MEDIUM', 'NOT_STARTED')"""))
    for table in ("time_logs", "time_schedules"):
      conn.execute(text(f"""CREATE TABLE {table} (
        id INTEGER PRIMARY KEY, task_id INTEGER REFERENCES tasks(id),
        project_id INTEGER REFERENCES projects(id), start_time DATETIME NOT NULL,
        end_time DATETIME,
        CONSTRAINT check_task_or_project CHECK (task_id IS NULL != project_id IS NULL))"""))
      conn.execute(text(f"""INSERT INTO {table} VALUES (
        1, 1, NULL, '2026-01-01 12:00:00', '2026-01-01 12:30:00')"""))
  yield MemoryConnection(engine)
  engine.dispose()


@pytest.mark.parametrize("priority", list(TaskPriority))
@pytest.mark.parametrize("status", list(TaskStatus))
def test_upgrade_preserves_legacy_tasks(legacy_database, priority, status):
  """Every recognized enum name must remain readable after an upgrade."""
  with legacy_database.engine.begin() as conn:
    conn.execute(text("UPDATE tasks SET priority=:priority, status=:status"),
                 {"priority": priority.name, "status": status.name})
  service = TaskService(legacy_database)
  saved = service.get_task_by_id(1)
  assert saved.name == "Legacy task"
  assert saved.project_id == 1
  assert saved.priority is priority
  assert saved.status is status
  assert saved.start_date.isoformat() == "2026-01-01T12:00:00"
  assert saved.total_tracked_time == 1800
  assert saved.checklist == []


def test_upgrade_is_repeatable_and_new_tasks_remain_readable(legacy_database):
  """Starting twice must preserve history and allow normal board operations."""
  service = TaskService(legacy_database)
  new_id = service.create_task(1, "New task", tag_names=["Review"],
                               checklist=[{"text": "Check", "done": False}])
  assert new_id is not None
  service = TaskService(legacy_database)
  tasks = service.get_tasks_by_project(1)
  assert {task.id for task in tasks} == {1, new_id}
  assert service.get_task_by_id(1).total_tracked_time == 1800
  new_task = service.get_task_by_id(new_id)
  assert new_task.priority is TaskPriority.NONE
  assert [tag.name for tag in new_task.tags] == ["Review"]
  assert new_task.checklist == [{"text": "Check", "done": False}]
  assert len({task.order_index for task in tasks}) == len(tasks)


@pytest.mark.parametrize("status,column_name", [
  (TaskStatus.NOT_STARTED, "To Do"),
  (TaskStatus.IN_PROGRESS, "In Progress"),
  (TaskStatus.DONE, "Done"),
])
def test_legacy_tasks_keep_their_progress_on_the_board(legacy_database, status, column_name):
  """Importing a done task must not make it look like new work."""
  with legacy_database.engine.begin() as conn:
    conn.execute(text("UPDATE tasks SET status=:status"), {"status": status.name})
  service = TaskService(legacy_database)
  task = service.get_tasks_by_project(1)[0]
  columns = {column.id: column.name for column in service.get_columns_for_project(1)}
  assert task.status is status
  assert columns[task.column_id] == column_name


def test_deleting_a_task_with_history_preserves_its_time_logs(legacy_database):
  """The new relationships must not silently erase recorded work."""
  service = TaskService(legacy_database)
  assert service.delete_task(1) is False
  assert service.get_task_by_id(1).total_tracked_time == 1800


@pytest.mark.parametrize("table", ["time_logs", "time_schedules"])
def test_upgrade_repairs_old_time_constraints(legacy_database, table):
  """An existing table must also accept project entries and reject no owner."""
  TaskService(legacy_database)
  with legacy_database.engine.begin() as conn:
    assert conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one() == 1
    conn.execute(text(f"""INSERT INTO {table} VALUES (
      2, NULL, 1, '2026-01-01 13:00:00', '2026-01-01 14:00:00')"""))
    with pytest.raises(IntegrityError):
      conn.execute(text(f"""INSERT INTO {table} VALUES (
        3, NULL, NULL, '2026-01-01 13:00:00', '2026-01-01 14:00:00')"""))


def test_unknown_enum_aborts_upgrade_without_changing_existing_data(legacy_database):
  """Unrecognized data must not be silently reassigned or partly converted."""
  with legacy_database.engine.begin() as conn:
    conn.execute(text("UPDATE tasks SET status='CUSTOM_STATUS'"))
  with pytest.raises(ValueError, match="status"):
    TaskService(legacy_database)
  with legacy_database.engine.connect() as conn:
    assert conn.execute(text("SELECT priority, status FROM tasks")).one() == ("MEDIUM", "CUSTOM_STATUS")
  assert "checklist" not in {col["name"] for col in inspect(legacy_database.engine).get_columns("tasks")}


@pytest.mark.parametrize("table", ["time_logs", "time_schedules"])
def test_unassigned_legacy_time_is_preserved_when_upgrade_aborts(legacy_database, table):
  """The old constraint allowed ownerless entries; don't discard that history."""
  with legacy_database.engine.begin() as conn:
    conn.execute(text(f"UPDATE {table} SET task_id=NULL"))
    original_schema = conn.execute(text(
      "SELECT sql FROM sqlite_master WHERE name='time_logs'"
    )).scalar_one()
  with pytest.raises(ValueError, match=table):
    TaskService(legacy_database)
  with legacy_database.engine.connect() as conn:
    assert conn.execute(text(f"SELECT task_id, project_id FROM {table}")).one() == (None, None)
    assert conn.execute(text("SELECT priority FROM tasks")).scalar_one() == "MEDIUM"
    assert conn.execute(text(
      "SELECT sql FROM sqlite_master WHERE name='time_logs'"
    )).scalar_one() == original_schema
  assert "checklist" not in {col["name"] for col in inspect(legacy_database.engine).get_columns("tasks")}


def test_constraint_upgrade_preserves_indexes_triggers_and_foreign_keys(legacy_database):
  """Rebuilding a time table must preserve its dependents with FK checks on."""
  with legacy_database.engine.connect() as conn:
    conn.exec_driver_sql("PRAGMA foreign_keys=ON")
    conn.commit()
  with legacy_database.engine.begin() as conn:
    conn.exec_driver_sql("CREATE INDEX custom_time_log_index ON time_logs(start_time)")
    conn.exec_driver_sql("CREATE TABLE audit (entry_id INTEGER)")
    conn.exec_driver_sql("""CREATE TRIGGER time_log_audit AFTER INSERT ON time_logs
      BEGIN INSERT INTO audit VALUES (NEW.id); END""")
  TaskService(legacy_database)
  with legacy_database.engine.begin() as conn:
    assert not conn.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
    assert conn.execute(text(
      "SELECT COUNT(*) FROM sqlite_master WHERE name='custom_time_log_index'"
    )).scalar_one() == 1
    conn.exec_driver_sql("""INSERT INTO time_logs VALUES (
      2, NULL, 1, '2026-01-01 13:00:00', '2026-01-01 14:00:00')""")
    assert conn.execute(text("SELECT entry_id FROM audit")).scalar_one() == 2


def test_constraint_upgrade_preserves_unrecognized_columns(legacy_database):
  """A custom column is data, even when the application doesn't know it."""
  with legacy_database.engine.begin() as conn:
    conn.exec_driver_sql("ALTER TABLE time_logs ADD COLUMN notes TEXT")
    conn.exec_driver_sql("UPDATE time_logs SET notes='Keep custom history'")
  TaskService(legacy_database)
  with legacy_database.engine.connect() as conn:
    assert conn.execute(text("SELECT notes FROM time_logs")).scalar_one() == "Keep custom history"
    assert conn.execute(text("SELECT priority FROM tasks")).scalar_one() == "medium"


def test_database_manager_registers_all_models_before_creating_tables(monkeypatch):
  """Startup must create time tables even if no board has been opened."""
  from focuswatch.database.database_manager import DatabaseManager

  engine = create_engine("sqlite:///:memory:")
  connection = MemoryConnection(engine)
  monkeypatch.setattr("focuswatch.database.database_manager.DatabaseConnection", lambda: connection)
  DatabaseManager()
  assert set(inspect(engine).get_table_names()) == set(Base.metadata.tables)
  assert "time_schedules" in inspect(engine).get_table_names()
  engine.dispose()
