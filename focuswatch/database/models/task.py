""" Task model for Focuswatch. """

from enum import Enum as PyEnum

from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Enum
from sqlalchemy.orm import relationship

from focuswatch.database.models import Base


class TaskPriority(PyEnum):
  HIGH = "high"
  MEDIUM = "medium"
  LOW = "low"


class TaskStatus(PyEnum):
  NOT_STARTED = "not_started"
  IN_PROGRESS = "in_progress"
  DONE = "done"


class Task(Base):
  __tablename__ = "tasks"
  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(Text, nullable=False)
  project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
  start_date = Column(DateTime, nullable=True)
  due_date = Column(DateTime, nullable=True)
  priority = Column(Enum(TaskPriority), nullable=False,
                    default=TaskPriority.MEDIUM.value)
  status = Column(Enum(TaskStatus), nullable=False,
                  default=TaskStatus.NOT_STARTED.value)

  time_logs = relationship("TimeLog", back_populates="task")

  @property
  def total_tracked_time(self) -> int:
    return sum(log.duration or 0 for log in self.time_logs if log.end_time)

  def __repr__(self) -> str:
    """ Return a readable string representation of the Task. """
    return (f"Task(id={self.id}, name='{self.name}', "
            f"project_id={self.project_id}, "
            f"start_date={self.start_date}, "
            f"due_date={self.due_date}, "
            f"priority={self.priority.value}, "
            f"status={self.status.value}, "
            f"total_tracked_time={self.total_tracked_time}s)")
