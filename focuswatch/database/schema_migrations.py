"""Non-destructive upgrades from the pre-board SQLite schema."""

from sqlalchemy import CheckConstraint, MetaData, Table, inspect, select, text
from sqlalchemy.schema import CreateTable, DropTable

from focuswatch.database.models.task import TaskPriority, TaskRecurrence, TaskStatus
from focuswatch.database.models.time_log import TimeLog
from focuswatch.database.models.time_schedule import TimeSchedule


def upgrade_project_schema(engine) -> None:
  """Upgrade existing project tables atomically and allow repeated startup.

  Tables must already exist. Unknown enum values and unassigned legacy time
  entries require an explicit data repair; never guess or delete their history.
  """
  with engine.begin() as conn:
    # sqlite3 otherwise postpones BEGIN until DML, leaving ALTER outside the
    # transaction. Begin explicitly so a later error rolls back schema too.
    conn.exec_driver_sql("BEGIN")
    _upgrade_board_columns(conn)
    _normalize_task_enums(conn)
    for table in (TimeLog.__table__, TimeSchedule.__table__):
      _repair_time_constraint(conn, table)


def _upgrade_board_columns(conn) -> None:
  additions = {
    "tags": {
      "project_id": "INTEGER",
      "color": "TEXT",
    },
    "tasks": {
      "description": "TEXT",
      "column_id": "INTEGER",
      "order_index": "INTEGER DEFAULT 0",
      "recurrence": "TEXT DEFAULT 'none'",
      "checklist": "TEXT DEFAULT '[]'",
    },
  }
  for table_name, columns in additions.items():
    existing = {column["name"] for column in inspect(conn).get_columns(table_name)}
    for column_name, definition in columns.items():
      if column_name not in existing:
        # All identifiers and definitions here are constants, never user input.
        conn.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def _normalize_task_enums(conn) -> None:
  for column_name, enum_type in (
      ("priority", TaskPriority), ("status", TaskStatus), ("recurrence", TaskRecurrence)):
    values = set(conn.execute(text(f"SELECT DISTINCT {column_name} FROM tasks")).scalars())
    recognized = {entry.name for entry in enum_type} | {entry.value for entry in enum_type}
    if values - recognized:
      raise ValueError(f"Unsupported {column_name} values in tasks; project schema upgrade aborted")
    for entry in enum_type:
      if entry.name in values:
        conn.execute(text(f"UPDATE tasks SET {column_name}=:value WHERE {column_name}=:legacy"),
                     {"value": entry.value, "legacy": entry.name})


def _repair_time_constraint(conn, table) -> None:
  schema = conn.execute(
    text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:name"),
    {"name": table.name},
  ).scalar_one()
  if "task_id is null != project_id is null" not in " ".join(schema.lower().split()):
    return

  invalid = conn.execute(
    select(table.c.id).where(table.c.task_id.is_(None) == table.c.project_id.is_(None)).limit(1)
  ).first()
  if invalid is not None:
    raise ValueError(f"{table.name} entry {invalid.id} must have exactly one owner; upgrade aborted")
  # Preserve custom indexes and triggers as well as rows during SQLite's
  # required table rebuild. All operations belong to the outer transaction.
  dependent_ddl = conn.execute(
    text("SELECT sql FROM sqlite_master WHERE tbl_name=:name "
         "AND type IN ('index', 'trigger') AND sql IS NOT NULL"),
    {"name": table.name},
  ).scalars().all()
  metadata = MetaData()
  existing = Table(table.name, metadata, autoload_with=conn)
  replacement = existing.to_metadata(metadata, name=f"_focuswatch_upgrade_{table.name}")
  legacy_constraints = [
    constraint for constraint in replacement.constraints
    if isinstance(constraint, CheckConstraint)
    and "task_id is null != project_id is null" in " ".join(str(constraint.sqltext).lower().split())
  ]
  if len(legacy_constraints) != 1:
    raise ValueError(f"Cannot identify the legacy constraint in {table.name}; upgrade aborted")
  replacement.constraints.remove(legacy_constraints[0])
  replacement.append_constraint(CheckConstraint(
    "(task_id IS NULL) != (project_id IS NULL)", name="check_task_or_project"))
  conn.execute(CreateTable(replacement))
  conn.execute(replacement.insert().from_select(list(existing.columns.keys()), select(existing)))
  conn.execute(DropTable(table))
  conn.exec_driver_sql(f'ALTER TABLE "{replacement.name}" RENAME TO "{table.name}"')
  for statement in dependent_ddl:
    conn.exec_driver_sql(statement)
