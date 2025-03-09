from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from focuswatch.database.models import Base


class TimeLog(Base):
  """ Represents a logged time entry for a task or project in FocusWatch. """
  __tablename__ = "time_logs"

  id = Column(Integer, primary_key=True, autoincrement=True)
  task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
  project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
  start_time = Column(DateTime, nullable=False)
  end_time = Column(DateTime, nullable=True)

  task = relationship("Task", back_populates="time_logs")
  project = relationship("Project", back_populates="time_logs")

  __table_args__ = (CheckConstraint('task_id IS NULL != project_id IS NULL',
                                    name='check_task_or_project'),)

  @property
  def duration(self) -> float:
    """ Returns the duration of the time log in seconds.

    Raises:
        ValueError: If end_time is None, as duration cannot be computed.
    """
    if self.end_time is None:
      raise ValueError("Cannot compute duration without an end time")
    return (self.end_time - self.start_time).total_seconds()

  def __repr__(self) -> str:
    duration_str = f"{self.duration}s" if self.end_time else "ongoing"
    return (f"TimeLog(id={self.id}, "
            f"task_id={self.task_id}, "
            f"project_id={self.project_id}, "
            f"start_time={self.start_time}, "
            f"end_time={self.end_time}, "
            f"duration={duration_str})")
