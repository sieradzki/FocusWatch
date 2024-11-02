from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class Activity:
  """ Represents an activity. """
  id: Optional[int] = None
  time_start: Optional[datetime] = None
  time_stop: Optional[datetime] = None
  window_class: str = ""
  window_name: str = ""
  category_id: Optional[int] = None
  project_id: Optional[int] = None
  focused: bool = 0

  def __post_init__(self):
    """ Validate the activity data after initialization. """
    if self.time_stop is not None and self.time_start > self.time_stop:
      raise ValueError("time_start must be before time_stop")

  @property
  def duration(self) -> float:
    """ Returns the duration of the activity in seconds. """
    return (self.time_stop - self.time_start).total_seconds()
