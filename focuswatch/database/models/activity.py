""" Activity model for FocusWatch. """

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from focuswatch.database.models import Base


class Activity(Base):
  """ Represents an activity in the database. """

  __tablename__ = "activity"

  id = Column(Integer, primary_key=True, autoincrement=True)
  time_start = Column(String, nullable=False)
  time_stop = Column(String, nullable=False)
  window_class = Column(String, nullable=False)
  window_name = Column(String, nullable=False)
  category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
  # project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
  focused = Column(Boolean, nullable=False, default=False)

  def __init__(self,
               time_start: Optional[datetime] = None,
               time_stop: Optional[datetime] = None,
               window_class: str = "",
               window_name: str = "",
               category_id: Optional[int] = None,
               project_id: Optional[int] = None,
               focused: bool = False,
               id: Optional[int] = None):
    """ Initialize and validate the activity.

    Args:
      time_start: Start time as datetime or ISO string.
      time_stop: Stop time as datetime or ISO string.
      window_class: Window class name.
      window_name: Window name.
      category_id: ID of the associated category.
      project_id: ID of the associated project.
      focused: Whether the activity was focused.
      id: Optional ID if pre-assigned.
    """
    self.id = id
    self.window_class = window_class
    self.window_name = window_name
    self.category_id = category_id
    self.project_id = project_id
    self.focused = focused

    # Convert datetime to ISO string for storage
    if isinstance(time_start, str):
      time_start = datetime.fromisoformat(time_start)
    if isinstance(time_stop, str):
      time_stop = datetime.fromisoformat(time_stop)
    if time_stop is not None and time_start > time_stop:
      raise ValueError("time_start must be before time_stop")
    self.time_start = time_start.isoformat() if time_start else None
    self.time_stop = time_stop.isoformat() if time_stop else None

  @property
  def duration(self) -> float:
    """ Returns the duration of the activity in seconds. """
    start = datetime.fromisoformat(self.time_start)
    stop = datetime.fromisoformat(self.time_stop)
    return (stop - start).total_seconds()

  def __repr__(self):
    return (f"Activity(id={self.id}, time_start='{self.time_start}', "
            f"time_stop='{self.time_stop}', window_name='{self.window_name}')")
