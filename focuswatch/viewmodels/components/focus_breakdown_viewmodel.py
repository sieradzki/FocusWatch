import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

if TYPE_CHECKING:
  from focuswatch.config import Config
  from focuswatch.database.models.activity import Activity
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class FocusBreakdownViewModel(QObject):
  """ ViewModel for the Focus Breakdown card, displaying time spent in each state per hour. """

  period_start_changed = Signal()
  period_end_changed = Signal()
  breakdown_data_changed = Signal()

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

    # Initialize period_start and period_end
    self._period_start = period_start or datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    self._period_end = period_end or self._period_start + timedelta(days=1)

    self._breakdown_data: List[Dict[str, float]] = []

    # Retrieve AFK category ID
    self._afk_category_id = self._category_service.get_category_id_from_name(
        "AFK")

    self._activities_per_hour = {}

    # Compute initial focus breakdown
    self.compute_focus_breakdown()

  @Slot(datetime, datetime)
  def update_period(self, start: datetime, end: Optional[datetime]) -> None:
    """ Update the time period for analysis. """
    self.period_start = start
    self.period_end = end or start + timedelta(days=1)
    self.compute_focus_breakdown()

  @Property(datetime, notify=period_start_changed)
  def period_start(self) -> datetime:
    """ Get the start of the period for breakdown analysis. """
    return self._period_start

  @period_start.setter
  def period_start(self, value: datetime) -> None:
    """ Set the start of the period and recompute breakdown data. """
    if self._period_start != value:
      self._period_start = value
      self.period_start_changed.emit()

  @Property(datetime, notify=period_end_changed)
  def period_end(self) -> datetime:
    """ Get the end of the period for breakdown analysis. """
    return self._period_end

  @period_end.setter
  def period_end(self, value: datetime) -> None:
    """ Set the end of the period and recompute breakdown data. """
    if self._period_end != value:
      self._period_end = value
      self.period_end_changed.emit()

  @Property(list, notify=breakdown_data_changed)
  def breakdown_data(self) -> List[Dict[str, float]]:
    """
    Get the computed breakdown data.

    Each entry in the list corresponds to an hour and contains:
        - 'hour': int (0-23)
        - 'focused': float (seconds spent focused)
        - 'distracted': float (seconds spent distracted)
        - 'idle': float (seconds spent idle)
        # TODO add info about categories for each so we can have nice tooltips
    """
    return self._breakdown_data

  def compute_focus_breakdown(self) -> None:
    """ Compute the focus breakdown data for the specified period. """
    try:
      activities = self._activity_service.get_period_entries(
          self._period_start, self._period_end
      )
    except (ConnectionError, TimeoutError) as e:
      logger.error(f"Network-related error fetching activities: {e}")
      self._breakdown_data = []
      self.breakdown_data_changed.emit()
      return
    except ValueError as e:
      logger.error(f"Value error fetching activities: {e}")
      self._breakdown_data = []
      self.breakdown_data_changed.emit()
      return

    # Initialize per-hour aggregation in seconds
    hour_totals: Dict[int, Dict[str, float]] = {
        hour: {"focused": 0.0, "distracted": 0.0, "idle": 0.0} for hour in range(24)
    }

    # Initialize activities per hour
    self._activities_per_hour = {
        hour: {"focused": [], "distracted": [], "idle": []} for hour in range(24)
    }

    for activity in activities:
      if not self._config["dashboard"]["display_cards_idle"]:
        if activity.category_id == self._afk_category_id:
          continue
      current_time = activity.time_start

      while current_time < activity.time_stop:
        hour = current_time.hour
        next_hour = (current_time + timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        segment_end = min(next_hour, activity.time_stop)
        duration = (segment_end - current_time).total_seconds()

        if self._afk_category_id and activity.category_id == self._afk_category_id:
          hour_totals[hour]["idle"] += duration
          self._activities_per_hour[hour]["idle"].append(activity)
        elif getattr(activity, "focused", False):
          hour_totals[hour]["focused"] += duration
          self._activities_per_hour[hour]["focused"].append(activity)
        else:
          hour_totals[hour]["distracted"] += duration
          self._activities_per_hour[hour]["distracted"].append(activity)

        current_time = segment_end

    # Prepare breakdown_data with time spent in each state
    breakdown_data: List[Dict[str, float]] = []
    for hour in range(24):
      focused = hour_totals[hour]["focused"]
      distracted = hour_totals[hour]["distracted"]
      idle = hour_totals[hour]["idle"]

      total_time = focused + distracted + idle

      # Normalize total time to 1 hour
      if total_time > 3600:
        scale_factor = 3600 / total_time
        focused *= scale_factor
        distracted *= scale_factor
        idle *= scale_factor

      breakdown_data.append(
        {
          "hour": hour,
          "focused": focused,
          "distracted": distracted,
          "idle": idle,
        }
      )

    self._breakdown_data = breakdown_data
    self.breakdown_data_changed.emit()

  def get_activities_for_hour_and_category(self, hour: int, category: str) -> List["Activity"]:
    """ Return the list of activities for a given hour and category. """
    return self._activities_per_hour.get(hour, {}).get(category, [])

  def get_activity_duration_in_hour(self, activity: "Activity", hour: int) -> float:
    """ Calculate the duration of an activity within a specific hour. """
    hour_start = self._period_start.replace(
      hour=hour, minute=0, second=0, microsecond=0)
    hour_end = hour_start + timedelta(hours=1)
    activity_start = max(activity.time_start, hour_start)
    activity_end = min(activity.time_stop, hour_end)
    duration = (activity_end - activity_start).total_seconds()
    return duration if duration > 0 else 0.0
