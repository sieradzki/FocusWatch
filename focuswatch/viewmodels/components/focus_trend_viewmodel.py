import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class FocusTrendViewModel(QObject):
  """ ViewModel for the Focus Trend card. """
  trend_data_changed = Signal()

  def __init__(self,
               activity_service: "ActivityService",
               category_service: "CategoryService"
               ):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service
    # TODO why aren't we passing this as a parameter again?
    self._period_start = datetime.now().replace(
      hour=0, minute=0, second=0, microsecond=0)
    self._period_end = None
    self._trend_data: List[Dict[str, float]] = []
    # we could look at window_name but what if we allow user to classify other activities as AFK?
    self._afk_category_id = self._category_service.get_category_id_from_name(
      "AFK")

    self.compute_focus_trend()

  @Slot(datetime, datetime)
  def update_period(self, start: datetime, end: Optional[datetime]) -> None:
    """ Update the time period. """
    self.period_start = start
    self.period_end = end
    self.property_changed.emit("period_start")
    self.property_changed.emit("period_end")

  @Property(datetime, notify=trend_data_changed)
  def period_start(self) -> datetime:
    return self._period_start

  @period_start.setter
  def period_start(self, value: datetime) -> None:
    if self._period_start != value:
      self._period_start = value
      self.property_changed.emit("period_start")

  @Property(datetime, notify=trend_data_changed)
  def period_end(self) -> Optional[datetime]:
    return self._period_end

  @period_end.setter
  def period_end(self, value: Optional[datetime]) -> None:
    if self._period_end != value:
      self._period_end = value
      self.property_changed.emit("period_end")

  @Property(list, notify=trend_data_changed)
  def trend_data(self) -> List[Dict[str, float]]:
    return self._trend_data

  def compute_focus_trend(self) -> None:
    """ Compute the focus trend data for the specified period. """
    activities = self._activity_service.get_period_entries(
      self._period_start, self._period_end)

    # Initialize per-hour aggregation
    hour_totals: Dict[int, Dict[str, float]] = {
      hour: {"focused": 0.0, "distracted": 0.0, "idle": 0.0} for hour in range(24)
    }

    for activity in activities:
      current_time = activity.time_start

      while current_time < activity.time_stop:
        hour = current_time.hour
        next_hour = (current_time + timedelta(hours=1)
                     ).replace(minute=0, second=0, microsecond=0)
        segment_end = min(next_hour, activity.time_stop)
        duration = (segment_end - current_time).total_seconds()

        if self._afk_category_id and activity.category_id == self._afk_category_id:
          hour_totals[hour]["idle"] += duration
        elif activity.focused:
          hour_totals[hour]["focused"] += duration
        else:
          hour_totals[hour]["distracted"] += duration

        current_time = segment_end

    # Calculate percentages per hour
    trend_data: List[Dict[str, float]] = []
    for hour in range(24):
      focused = hour_totals[hour]["focused"]
      distracted = hour_totals[hour]["distracted"]
      idle = hour_totals[hour]["idle"]
      total = focused + distracted + idle

      if total > 0:
        focused_pct = (focused / total) * 100
        distracted_pct = (distracted / total) * 100
        idle_pct = (idle / total) * 100
      else:
        focused_pct = 0.0
        distracted_pct = 0.0
        idle_pct = 0.0

      trend_data.append({
        "hour": hour,
        "focused": focused_pct,
        "distracted": distracted_pct,
        "idle": idle_pct
      })

    self._trend_data = trend_data
    self.trend_data_changed.emit()
