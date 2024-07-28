from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class Activity:
  """ Represents an activity. """
  id: Optional[int] = None
  window_class: str
  window_name: str
  time_start: datetime
  time_stop: datetime
  category_id: Optional[int] = None
  project_id: Optional[int] = None

  def __post_init__(self):
    """ Validate the activity data after initialization. """
    if self.time_start > self.time_stop:
      raise ValueError("time_start must be before time_stop")
    if not self.window_class:
      raise ValueError("window_class cannot be empty")
    if not self.window_name:
      raise ValueError("window_name cannot be empty")

  @property
  def duration(self) -> float:
    """ Returns the duration of the activity in seconds. """
    return (self.time_stop - self.time_start).total_seconds()
