import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

if TYPE_CHECKING:
  from focuswatch.config import Config
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class PeriodSummaryViewModel(QObject):
  """ ViewModel for the Period Summary card, displaying time spent in each state per hour. """

  period_start_changed = Signal()
  period_end_changed = Signal()
  period_data_changed = Signal()

  def __init__(
      self,
      activity_service: "ActivityService",
      category_service: "CategoryService",
      config: "Config",
      period_start: Optional[datetime] = None,
      period_end: Optional[datetime] = None,
  ):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service
    self._config = config

    self._period_start = period_start or datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    self._period_end = period_end or self._period_start + timedelta(days=1)

    # TODO streamline data for all components in home viewmodel as a lot of it is shared between components
    self._period_data: List[Dict[str, float]] = []

    self._afk_category_id = self._category_service.get_category_id_from_name(
      "AFK")

    # temp
    self._focused_target_hours: float = 8.

    self.compute_period_summary()

  @Slot(datetime, datetime)
  def update_period(self, start: datetime, end: Optional[datetime]) -> None:
    """ Update the time period for analysis. """
    self.period_start = start
    self.period_end = end or start + timedelta(days=1)
    self.compute_period_summary()

  @Property(datetime, notify=period_start_changed)
  def period_start(self) -> datetime:
    return self._period_start

  @period_start.setter
  def period_start(self, value: datetime) -> None:
    if self._period_start != value:
      self._period_start = value
      self.period_start_changed.emit()

  @Property(datetime, notify=period_end_changed)
  def period_end(self) -> datetime:
    return self._period_end

  @period_end.setter
  def period_end(self, value: datetime) -> None:
    if self._period_end != value:
      self._period_end = value
      self.period_end_changed.emit()

  @Property(list, notify=period_data_changed)
  def period_data(self) -> List[Dict[str, float]]:
    return self._period_data

  def compute_period_summary(self) -> None:
    """ Compute the period summary data. """
    activities = self._activity_service.get_period_entries(
        self._period_start, self._period_end
    )

    # Initialize totals in seconds
    totals = {"focused": 0.0, "distracted": 0.0, "idle": 0.0}

    for activity in activities:
      if not self._config["dashboard"]["display_cards_idle"]:
        if activity.category_id == self._afk_category_id:
          continue

      duration = (activity.time_stop -
                  activity.time_start).total_seconds()

      if self._afk_category_id and activity.category_id == self._afk_category_id:
        totals["idle"] += duration
      elif getattr(activity, "focused", False):
        totals["focused"] += duration
      else:
        totals["distracted"] += duration

    # Calculate total active time (excluding idle time)
    total_active_time = totals["focused"] + totals["distracted"]

    # Total time including idle
    total_time = total_active_time + totals["idle"]

    # Calculate percentages
    focused_target_seconds = self._focused_target_hours * 3600.0
    focused_percent_of_target = (
        (totals["focused"] / focused_target_seconds) * 100
        if focused_target_seconds > 0
        else 0
    )

    distracted_percent_of_active = (
        (totals["distracted"] / total_active_time) * 100
        if total_active_time > 0
        else 0
    )

    # Prepare period_data
    self._period_data = {
        "focused": totals["focused"],
        "distracted": totals["distracted"],
        "idle": totals["idle"],
        "focused_target_seconds": focused_target_seconds,
        "focused_percent_of_target": focused_percent_of_target,
        "distracted_percent_of_active": distracted_percent_of_active,
        "focused_target_str": self._format_time(focused_target_seconds),
        "total_active_time": total_active_time,
        "total_time": total_time,
        "focused_time_str": self._format_time(totals["focused"]),
        "distracted_time_str": self._format_time(totals["distracted"]),
    }

    self.period_data_changed.emit()

  @staticmethod
  def _format_time(seconds: float) -> str:
    """ Format the given time in seconds to a human-readable string. """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours > 0:
      return f"{hours}h {minutes}m"
    elif minutes > 0:
      return f"{minutes}m"
    else:
      return f"{total_seconds % 60}s"
