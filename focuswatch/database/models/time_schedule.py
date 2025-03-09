from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from focuswatch.database.models import Base


class TimeSchedule(Base):
  """ Represents a scheduled time block for a task or project in FocusWatch. """
  __tablename__ = "time_schedules"

  id = Column(Integer, primary_key=True, autoincrement=True)
  task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
  project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
  start_time = Column(DateTime, nullable=False)
  end_time = Column(DateTime, nullable=False)

  task = relationship("Task", back_populates="schedules")
  project = relationship("Project", back_populates="schedules")

  __table_args__ = (CheckConstraint('task_id IS NULL != project_id IS NULL',
                                    name='check_task_or_project'),)

  @property
  def duration(self) -> float:
    """ Returns the duration of the scheduled block in seconds. """
    return (self.end_time - self.start_time).total_seconds()

  def __repr__(self) -> str:
    return (f"TimeSchedule(id={self.id}, "
            f"task_id={self.task_id}, "
            f"project_id={self.project_id}, "
            f"start_time={self.start_time}, "
            f"end_time={self.end_time}, "
            f"duration={self.duration}s)")
