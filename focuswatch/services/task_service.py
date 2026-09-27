""" Task Service Module """

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from focuswatch.database.database_connection import DatabaseConnection
from focuswatch.database.models import Base
from focuswatch.database.models.tag import Tag
from focuswatch.database.models.task import Task, TaskPriority, TaskRecurrence, TaskStatus
from focuswatch.database.models.task_column import TaskColumn
from focuswatch.database.schema_migrations import upgrade_project_schema

logger = logging.getLogger(__name__)


class TaskService:
  """Service class for managing tasks, tags and board columns."""

  def __init__(self, db_conn: Optional[DatabaseConnection] = None):
    self._db_conn = db_conn or DatabaseConnection()

    engine = self._db_conn.engine
    Base.metadata.create_all(engine)
    upgrade_project_schema(engine)

  @staticmethod
  def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
      return None
    clean = value.strip()
    if not clean:
      return None
    try:
      return datetime.fromisoformat(clean)
    except ValueError:
      return None

  def _ensure_default_columns(self, session, project_id: int) -> list[TaskColumn]:
    columns = (
      session.query(TaskColumn)
      .filter(TaskColumn.project_id == project_id)
      .order_by(TaskColumn.order_index.asc(), TaskColumn.id.asc())
      .all()
    )
    if columns:
      return columns

    defaults = ["To Do", "In Progress", "Done"]
    created = []
    for index, name in enumerate(defaults):
      col = TaskColumn(project_id=project_id, name=name, order_index=index)
      session.add(col)
      created.append(col)
    session.flush()
    return created

  def get_columns_for_project(self, project_id: int) -> list[TaskColumn]:
    with self._db_conn.get_session() as session:
      try:
        columns = self._ensure_default_columns(session, project_id)
        session.commit()
        return sorted(columns, key=lambda item: (item.order_index, item.id))
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve columns for project {project_id}: {e}")
        session.rollback()
        return []

  def create_column(self, project_id: int, name: str) -> Optional[int]:
    clean_name = name.strip()
    if not clean_name:
      return None
    with self._db_conn.get_session() as session:
      try:
        exists = (
          session.query(TaskColumn)
          .filter(TaskColumn.project_id == project_id, TaskColumn.name.ilike(clean_name))
          .first()
        )
        if exists:
          return None

        max_order = (
          session.query(TaskColumn.order_index)
          .filter(TaskColumn.project_id == project_id)
          .order_by(TaskColumn.order_index.desc())
          .first()
        )
        next_order = max_order[0] + 1 if max_order else 0

        column = TaskColumn(project_id=project_id, name=clean_name, order_index=next_order)
        session.add(column)
        session.commit()
        return column.id
      except SQLAlchemyError as e:
        logger.error(f"Failed to create column '{clean_name}': {e}")
        session.rollback()
        return None

  def rename_column(self, column_id: int, name: str) -> bool:
    clean_name = name.strip()
    if not clean_name:
      return False
    with self._db_conn.get_session() as session:
      try:
        column = session.query(TaskColumn).filter(TaskColumn.id == column_id).first()
        if not column:
          return False

        duplicate = (
          session.query(TaskColumn)
          .filter(
            TaskColumn.project_id == column.project_id,
            TaskColumn.id != column.id,
            TaskColumn.name.ilike(clean_name),
          )
          .first()
        )
        if duplicate:
          return False

        column.name = clean_name
        session.commit()
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to rename column {column_id}: {e}")
        session.rollback()
        return False

  def delete_column(self, column_id: int) -> bool:
    with self._db_conn.get_session() as session:
      try:
        column = session.query(TaskColumn).filter(TaskColumn.id == column_id).first()
        if not column:
          return False

        all_columns = (
          session.query(TaskColumn)
          .filter(TaskColumn.project_id == column.project_id)
          .order_by(TaskColumn.order_index.asc(), TaskColumn.id.asc())
          .all()
        )
        if len(all_columns) <= 1:
          return False

        target = next((item for item in all_columns if item.id != column.id), None)
        if not target:
          return False

        tasks = session.query(Task).filter(Task.column_id == column.id).all()
        target_tasks = (
          session.query(Task)
          .filter(Task.column_id == target.id)
          .order_by(Task.order_index.asc(), Task.id.asc())
          .all()
        )
        start_index = len(target_tasks)
        for offset, task in enumerate(tasks):
          task.column_id = target.id
          task.order_index = start_index + offset

        session.delete(column)

        remaining = (
          session.query(TaskColumn)
          .filter(TaskColumn.project_id == target.project_id)
          .order_by(TaskColumn.order_index.asc(), TaskColumn.id.asc())
          .all()
        )
        for index, item in enumerate(remaining):
          item.order_index = index

        session.commit()
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to delete column {column_id}: {e}")
        session.rollback()
        return False

  def move_column(self, column_id: int, direction: int) -> bool:
    """Move a column left/right by one slot. direction: -1 (left), +1 (right)."""
    if direction not in (-1, 1):
      return False
    with self._db_conn.get_session() as session:
      try:
        column = session.query(TaskColumn).filter(TaskColumn.id == column_id).first()
        if not column:
          return False

        columns = (
          session.query(TaskColumn)
          .filter(TaskColumn.project_id == column.project_id)
          .order_by(TaskColumn.order_index.asc(), TaskColumn.id.asc())
          .all()
        )
        if len(columns) < 2:
          return False

        current_index = next((i for i, c in enumerate(columns) if c.id == column.id), -1)
        if current_index < 0:
          return False

        target_index = current_index + direction
        if target_index < 0 or target_index >= len(columns):
          return False

        columns[current_index], columns[target_index] = columns[target_index], columns[current_index]
        for index, item in enumerate(columns):
          item.order_index = index

        session.commit()
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to move column {column_id}: {e}")
        session.rollback()
        return False

  def move_column_to_index(self, column_id: int, target_index: int) -> bool:
    with self._db_conn.get_session() as session:
      try:
        column = session.query(TaskColumn).filter(TaskColumn.id == column_id).first()
        if not column:
          return False

        columns = (
          session.query(TaskColumn)
          .filter(TaskColumn.project_id == column.project_id)
          .order_by(TaskColumn.order_index.asc(), TaskColumn.id.asc())
          .all()
        )
        if len(columns) < 2:
          return False

        current_index = next((i for i, c in enumerate(columns) if c.id == column.id), -1)
        if current_index < 0:
          return False

        bounded_index = max(0, min(target_index, len(columns) - 1))
        if bounded_index == current_index:
          return True

        moving = columns.pop(current_index)
        columns.insert(bounded_index, moving)

        for index, item in enumerate(columns):
          item.order_index = index

        session.commit()
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to reorder column {column_id}: {e}")
        session.rollback()
        return False

  def get_tasks_by_project(self, project_id: int) -> list[Task]:
    with self._db_conn.get_session() as session:
      try:
        columns = self._ensure_default_columns(session, project_id)
        session.flush()

        # Backfill tasks that do not yet have a column assigned.
        orphan_tasks = (
          session.query(Task)
          .filter(Task.project_id == project_id, Task.column_id.is_(None))
          .all()
        )
        if orphan_tasks:
          # Preserve the pre-board status instead of moving every legacy task
          # to To Do. Renamed/custom boards fall back to their first column.
          status_columns = {
            status: next((column for column in columns if column.name == name), columns[0])
            for status, name in (
              (TaskStatus.NOT_STARTED, "To Do"),
              (TaskStatus.IN_PROGRESS, "In Progress"),
              (TaskStatus.DONE, "Done"),
            )
          }
          next_orders = {
            column_id: (last_order or 0) + 1
            for column_id, last_order in session.query(Task.column_id, func.max(Task.order_index))
            .filter(Task.project_id == project_id, Task.column_id.is_not(None))
            .group_by(Task.column_id).all()
          }
          for task in orphan_tasks:
            column_id = status_columns[task.status].id
            task.column_id = column_id
            task.order_index = next_orders.get(column_id, 0)
            next_orders[column_id] = task.order_index + 1
          session.commit()

        return (
          session.query(Task)
          .options(
            selectinload(Task.tags),
            selectinload(Task.time_logs),
          )
          .filter(Task.project_id == project_id)
          .order_by(Task.column_id.asc(), Task.order_index.asc(), Task.id.asc())
          .all()
        )
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve tasks for project {project_id}: {e}")
        return []

  def get_task_by_id(self, task_id: int) -> Optional[Task]:
    with self._db_conn.get_session() as session:
      try:
        return (
          session.query(Task)
          .options(
            selectinload(Task.tags),
            selectinload(Task.time_logs),
          )
          .filter(Task.id == task_id)
          .first()
        )
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve task {task_id}: {e}")
        return None

  def create_task(self,
                  project_id: int,
                  name: str,
                  priority: TaskPriority = TaskPriority.NONE,
                  tag_names: Optional[list[str]] = None,
                  description: Optional[str] = None,
                  start_date: Optional[str] = None,
                  due_date: Optional[str] = None,
                  column_id: Optional[int] = None,
                  recurrence: TaskRecurrence = TaskRecurrence.NONE,
                  checklist: Optional[list[dict]] = None) -> Optional[int]:
    clean_name = name.strip()
    if not clean_name:
      return None

    with self._db_conn.get_session() as session:
      try:
        columns = self._ensure_default_columns(session, project_id)
        target_column_id = column_id or columns[0].id

        max_order = (
          session.query(Task.order_index)
          .filter(Task.column_id == target_column_id)
          .order_by(Task.order_index.desc())
          .first()
        )
        next_order = max_order[0] + 1 if max_order else 0

        task = Task()
        task.project_id = project_id
        task.name = clean_name
        task.description = (description or "").strip() or None
        task.priority = priority
        task.start_date = self._parse_datetime(start_date)
        task.due_date = self._parse_datetime(due_date)
        task.column_id = target_column_id
        task.order_index = next_order
        task.recurrence = recurrence
        task.checklist = checklist or []
        task.tags = self._get_or_create_tags(session, project_id, tag_names or [])

        session.add(task)
        session.commit()
        return task.id
      except SQLAlchemyError as e:
        logger.error(f"Failed to create task: {e}")
        session.rollback()
        return None

  def update_task(self,
                  task_id: int,
                  name: str,
                  priority: TaskPriority,
                  tag_names: Optional[list[str]] = None,
                  description: Optional[str] = None,
                  start_date: Optional[str] = None,
                  due_date: Optional[str] = None,
                  column_id: Optional[int] = None,
                  recurrence: TaskRecurrence = TaskRecurrence.NONE,
                  checklist: Optional[list[dict]] = None) -> bool:
    clean_name = name.strip()
    if not clean_name:
      return False

    with self._db_conn.get_session() as session:
      try:
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
          return False

        task.name = clean_name
        task.description = (description or "").strip() or None
        task.priority = priority
        task.start_date = self._parse_datetime(start_date)
        task.due_date = self._parse_datetime(due_date)
        task.recurrence = recurrence
        task.checklist = checklist if checklist is not None else (task.checklist or [])
        if column_id is not None:
          task.column_id = column_id
        task.tags = self._get_or_create_tags(session, task.project_id, tag_names or [])

        session.commit()
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to update task {task_id}: {e}")
        session.rollback()
        return False

  def delete_task(self, task_id: int) -> bool:
    with self._db_conn.get_session() as session:
      try:
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
          return False

        session.delete(task)
        session.commit()
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to delete task {task_id}: {e}")
        session.rollback()
        return False

  def move_task(self, task_id: int, target_column_id: int, target_index: int) -> bool:
    with self._db_conn.get_session() as session:
      try:
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
          return False

        source_column_id = task.column_id

        source_tasks = (
          session.query(Task)
          .filter(Task.column_id == source_column_id)
          .order_by(Task.order_index.asc(), Task.id.asc())
          .all()
        )
        source_tasks = [item for item in source_tasks if item.id != task.id]
        for index, item in enumerate(source_tasks):
          item.order_index = index

        target_tasks = (
          session.query(Task)
          .filter(Task.column_id == target_column_id)
          .order_by(Task.order_index.asc(), Task.id.asc())
          .all()
        )
        if source_column_id == target_column_id:
          target_tasks = [item for item in target_tasks if item.id != task.id]

        insert_index = max(0, min(target_index, len(target_tasks)))
        target_tasks.insert(insert_index, task)

        task.column_id = target_column_id
        for index, item in enumerate(target_tasks):
          item.order_index = index

        session.commit()
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to move task {task_id}: {e}")
        session.rollback()
        return False

  def get_tags_for_project(self, project_id: int) -> list[Tag]:
    with self._db_conn.get_session() as session:
      try:
        return (
          session.query(Tag)
          .filter(Tag.project_id == project_id)
          .order_by(Tag.name.asc())
          .all()
        )
      except SQLAlchemyError as e:
        logger.error(f"Failed to get tags for project {project_id}: {e}")
        return []

  def create_tag_for_project(self,
                             project_id: int,
                             name: str,
                             color: Optional[str] = None) -> Optional[Tag]:
    clean_name = name.strip()
    if not clean_name:
      return None

    with self._db_conn.get_session() as session:
      try:
        existing = (
          session.query(Tag)
          .filter(Tag.project_id == project_id, Tag.name.ilike(clean_name))
          .first()
        )
        if existing:
          if color and existing.color != color:
            existing.color = color
            session.commit()
          return existing

        tag = Tag(name=clean_name, project_id=project_id, color=color)
        session.add(tag)
        session.commit()
        session.refresh(tag)
        return tag
      except SQLAlchemyError as e:
        logger.error(f"Failed to create tag '{clean_name}' for project {project_id}: {e}")
        session.rollback()
        return None

  def update_tag(self, tag_id: int, name: str, color: Optional[str] = None) -> Optional[Tag]:
    """Update a tag's name and/or color."""
    clean_name = name.strip()
    if not clean_name:
      return None
    with self._db_conn.get_session() as session:
      try:
        tag = session.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
          return None
        tag.name = clean_name
        tag.color = color
        session.commit()
        session.refresh(tag)
        return tag
      except SQLAlchemyError as e:
        logger.error(f"Failed to update tag {tag_id}: {e}")
        session.rollback()
        return None

  def delete_tag(self, tag_id: int) -> bool:
    """Delete a tag and remove it from all tasks."""
    with self._db_conn.get_session() as session:
      try:
        tag = session.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
          return False
        session.delete(tag)
        session.commit()
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to delete tag {tag_id}: {e}")
        session.rollback()
        return False

  @staticmethod
  def _normalize_tag_names(tag_names: list[str]) -> list[str]:
    seen = set()
    names: list[str] = []
    for raw in tag_names:
      name = raw.strip()
      if not name:
        continue
      key = name.lower()
      if key in seen:
        continue
      seen.add(key)
      names.append(name)
    return names

  def _get_or_create_tags(self, session, project_id: int, tag_names: list[str]) -> list[Tag]:
    names = self._normalize_tag_names(tag_names)
    if not names:
      return []

    tags: list[Tag] = []
    for name in names:
      existing = (
        session.query(Tag)
        .filter(Tag.project_id == project_id, Tag.name.ilike(name))
        .first()
      )
      if existing:
        tags.append(existing)
      else:
        tag = Tag(name=name, project_id=project_id)
        session.add(tag)
        session.flush()
        tags.append(tag)
    return tags
