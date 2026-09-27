"""Register all models before SQLAlchemy configures relationships or tables."""

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# These imports follow Base deliberately: each model imports the shared registry.
# Explicit imports also let PyInstaller discover every model.
# pylint: disable=wrong-import-position
from focuswatch.database.models.activity import Activity
from focuswatch.database.models.category import Category
from focuswatch.database.models.keyword import Keyword
from focuswatch.database.models.metadata import Metadata
from focuswatch.database.models.project import Project
from focuswatch.database.models.tag import Tag
from focuswatch.database.models.task import Task
from focuswatch.database.models.task_column import TaskColumn
from focuswatch.database.models.time_log import TimeLog
from focuswatch.database.models.time_schedule import TimeSchedule

__all__ = [
  "Base", "Activity", "Category", "Keyword", "Metadata", "Project", "Tag",
  "Task", "TaskColumn", "TimeLog", "TimeSchedule",
]
