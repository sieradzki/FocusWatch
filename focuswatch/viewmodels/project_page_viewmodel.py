from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import Property, QObject, Signal

from focuswatch.database.models.project import Project
from focuswatch.database.models.tag import Tag
from focuswatch.database.models.task import Task, TaskPriority, TaskRecurrence
from focuswatch.database.models.task_column import TaskColumn

if TYPE_CHECKING:
  from focuswatch.services.project_service import ProjectService
  from focuswatch.services.task_service import TaskService


class ProjectPageViewModel(QObject):
  """ ViewModel for a single project's page (details). """

  project_changed = Signal()
  columns_changed = Signal()
  tasks_changed = Signal()

  def __init__(self,
               project_service: "ProjectService",
               task_service: "TaskService"):
    super().__init__()
    self._project_service = project_service
    self._task_service = task_service
    self._project: Optional[Project] = None
    self._columns: list[TaskColumn] = []
    self._tasks: list[Task] = []

  @Property(int, notify=project_changed)
  def project_id(self) -> int:
    return int(self._project.id) if self._project else -1

  @Property(str, notify=project_changed)
  def project_name(self) -> str:
    return self._project.name if self._project else ""

  @Property(str, notify=project_changed)
  def project_description(self) -> str:
    return self._project.description or "" if self._project else ""

  def load_project(self, project_id: int) -> None:
    self._project = self._project_service.get_project_by_id(project_id)
    self.project_changed.emit()
    self.refresh_board()

  @Property(int, notify=tasks_changed)
  def task_count(self) -> int:
    return len(self._tasks)

  def refresh_board(self) -> None:
    if not self._project:
      self._columns = []
      self._tasks = []
      self.columns_changed.emit()
      self.tasks_changed.emit()
      return
    self._columns = self._task_service.get_columns_for_project(self._project.id)
    self._tasks = self._task_service.get_tasks_by_project(self._project.id)
    self.columns_changed.emit()
    self.tasks_changed.emit()

  def columns(self) -> list[TaskColumn]:
    return self._columns

  def tasks_by_column(self) -> dict[int, list[Task]]:
    grouped: dict[int, list[Task]] = {column.id: [] for column in self._columns}
    for task in self._tasks:
      if task.column_id is not None:
        grouped.setdefault(task.column_id, []).append(task)
    for column_id in grouped:
      grouped[column_id] = sorted(grouped[column_id], key=lambda t: (t.order_index, t.id))
    return grouped

  def available_parent_tasks(self, exclude_task_id: Optional[int] = None) -> list[Task]:
    return [task for task in self._tasks if task.id != exclude_task_id]

  def create_column(self, name: str) -> bool:
    if not self._project:
      return False
    col_id = self._task_service.create_column(self._project.id, name)
    if not col_id:
      return False
    self.refresh_board()
    return True

  def rename_column(self, column_id: int, name: str) -> bool:
    success = self._task_service.rename_column(column_id, name)
    if success:
      self.refresh_board()
    return success

  def delete_column(self, column_id: int) -> bool:
    success = self._task_service.delete_column(column_id)
    if success:
      self.refresh_board()
    return success

  def move_column(self, column_id: int, direction: int) -> bool:
    success = self._task_service.move_column(column_id, direction)
    if success:
      self.refresh_board()
    return success

  def move_column_to_index(self, column_id: int, target_index: int) -> bool:
    success = self._task_service.move_column_to_index(column_id, target_index)
    if success:
      self.refresh_board()
    return success

  def create_task(self,
                  name: str,
                  priority: TaskPriority,
                  tags: list[str],
                  description: str,
                  start_date: str,
                  due_date: str,
                  column_id: int,
                  recurrence: TaskRecurrence = TaskRecurrence.NONE,
                  checklist: Optional[list[dict]] = None) -> bool:
    if not self._project:
      return False
    task_id = self._task_service.create_task(
      project_id=self._project.id,
      name=name,
      priority=priority,
      tag_names=tags,
      description=description,
      start_date=start_date,
      due_date=due_date,
      column_id=column_id,
      recurrence=recurrence,
      checklist=checklist or [],
    )
    if task_id is None:
      return False
    self.refresh_board()
    return True

  def update_task(self,
                  task_id: int,
                  name: str,
                  priority: TaskPriority,
                  tags: list[str],
                  description: str,
                  start_date: str,
                  due_date: str,
                  column_id: int,
                  recurrence: TaskRecurrence = TaskRecurrence.NONE,
                  checklist: Optional[list[dict]] = None) -> bool:
    success = self._task_service.update_task(
      task_id=task_id,
      name=name,
      priority=priority,
      tag_names=tags,
      description=description,
      start_date=start_date,
      due_date=due_date,
      column_id=column_id,
      recurrence=recurrence,
      checklist=checklist,
    )
    if success:
      self.refresh_board()
    return success

  def delete_task(self, task_id: int) -> bool:
    success = self._task_service.delete_task(task_id)
    if success:
      self.refresh_board()
    return success

  def move_task(self, task_id: int, target_column_id: int, target_index: int) -> bool:
    success = self._task_service.move_task(task_id, target_column_id, target_index)
    if success:
      self.refresh_board()
    return success

  def get_project_tags(self) -> list[Tag]:
    if not self._project:
      return []
    return self._task_service.get_tags_for_project(self._project.id)

  def create_project_tag(self, name: str, color: str = "") -> Optional[Tag]:
    if not self._project:
      return None
    return self._task_service.create_tag_for_project(
      project_id=self._project.id,
      name=name,
      color=color or None,
    )

  def update_project_tag(self, tag_id: int, name: str, color: str = "") -> Optional[Tag]:
    return self._task_service.update_tag(tag_id, name, color or None)

  def delete_project_tag(self, tag_id: int) -> bool:
    return self._task_service.delete_tag(tag_id)
