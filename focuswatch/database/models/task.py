""" Task model for Focuswatch. """

from enum import Enum as PyEnum

from sqlalchemy import Column, Enum, ForeignKey, Integer, Table, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from focuswatch.database.models import Base


class TaskPriority(PyEnum):
  NONE = "none"
  HIGH = "high"
  MEDIUM = "medium"
  LOW = "low"


class TaskStatus(PyEnum):
  NOT_STARTED = "not_started"
  IN_PROGRESS = "in_progress"
  DONE = "done"


class TaskRecurrence(PyEnum):
  NONE = "none"
  DAILY = "daily"
  WEEKLY = "weekly"
  MONTHLY = "monthly"
  YEARLY = "yearly"


class Task(Base):
  __tablename__ = "tasks"

  task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
  )

  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(Text, nullable=False)
  description = Column(Text, nullable=True)
  project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
  column_id = Column(Integer, ForeignKey("task_columns.id"), nullable=True)
  checklist = Column(JSON, nullable=True, default=list)
  order_index = Column(Integer, nullable=False, default=0)
  start_date = Column(DateTime, nullable=True)
  due_date = Column(DateTime, nullable=True)
  priority = Column(
    Enum(
      TaskPriority,
      values_callable=lambda enum_cls: [e.value for e in enum_cls],
      name="taskpriority",
    ),
    nullable=False,
    default=TaskPriority.NONE,
  )
  status = Column(
    Enum(
      TaskStatus,
      values_callable=lambda enum_cls: [e.value for e in enum_cls],
      name="taskstatus",
    ),
    nullable=False,
    default=TaskStatus.NOT_STARTED,
  )
  recurrence = Column(
    Enum(
      TaskRecurrence,
      values_callable=lambda enum_cls: [e.value for e in enum_cls],
      name="taskrecurrence",
    ),
    nullable=False,
    default=TaskRecurrence.NONE,
  )

  time_logs = relationship("TimeLog", back_populates="task")
  schedules = relationship("TimeSchedule", back_populates="task")
  tags = relationship("Tag", secondary=task_tags, back_populates="tasks")
  column = relationship("TaskColumn", back_populates="tasks")

  @property
  def total_tracked_time(self) -> int:
    return sum(log.duration or 0 for log in self.time_logs if log.end_time)

  def __repr__(self) -> str:
    """ Return a readable string representation of the Task. """
    return (f"Task(id={self.id}, name='{self.name}', "
            f"project_id={self.project_id}, "
            f"column_id={self.column_id}, "
            f"start_date={self.start_date}, "
            f"due_date={self.due_date}, "
            f"priority={self.priority.value}, "
            f"status={self.status.value}, "
            f"total_tracked_time={self.total_tracked_time}s)")
