import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

if TYPE_CHECKING:
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
      period_start: Optional[datetime] = None,
      period_end: Optional[datetime] = None,
  ):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service

    # Initialize period_start and period_end
    self._period_start = period_start or datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    self._period_end = period_end or self._period_start + timedelta(days=1)

    # TODO streamline data for all components in home viewmodel as a lot of it is shared between components
    self._period_data: List[Dict[str, float]] = []

    # Retrieve AFK category ID
    self._afk_category_id = self._category_service.get_category_id_from_name(
        "AFK")

    # temp
    self._focused_target: float = 8.

    # Compute initial period summary
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
    try:
      activities = self._activity_service.get_period_entries(
          self._period_start, self._period_end
      )
    except Exception as e:
      logger.error(f"Error fetching activities: {e}")
      self._period_data = {}
      self.period_data_changed.emit()
      return

    # Initialize totals
    totals = {"focused": 0.0, "distracted": 0.0, "idle": 0.0}

    for activity in activities:
      duration = (activity.time_stop - activity.time_start).total_seconds()

      if self._afk_category_id and activity.category_id == self._afk_category_id:
        totals["idle"] += duration
      elif getattr(activity, "focused", False):
        totals["focused"] += duration
      else:
        totals["distracted"] += duration

    # Prepare period_data
    self._period_data = {
        "focused": totals["focused"],
        "distracted": totals["distracted"],
        "idle": totals["idle"],
        "focused_target": self._focused_target * 3600.0,  # Convert hours to seconds
    }

    self.period_data_changed.emit()
