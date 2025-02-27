import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

from focuswatch.database.models.activity import Activity
from focuswatch.utils.ui_utils import get_category_color_or_parent

if TYPE_CHECKING:
  from focuswatch.config import Config
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class TimelineViewModel(QObject):
  """ Viewmodel for the Timeline component in the Dashboard. """
  period_start_changed = Signal()
  period_end_changed = Signal()
  timeline_data_changed = Signal()

  def __init__(self,
               activity_service: "ActivityService",
               category_service: "CategoryService",
               config: "Config"):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service
    self._config = config

    self._period_start: datetime = datetime.now().replace(
      hour=0, minute=0, second=0, microsecond=0)
    self._period_end: Optional[datetime] = None
    self._timeline_data: Dict[int, List[int]] = {}

    self.update_timeline_data()

  @Slot(datetime, datetime)
  def update_period(self, start: datetime, end: Optional[datetime]) -> None:
    """ Update the time period. """
    self.period_start = start
    self.period_end = end
    self.update_timeline_data()

  @Property(datetime, notify=period_start_changed)
  def period_start(self) -> datetime:
    return self._period_start

  @period_start.setter
  def period_start(self, value: datetime) -> None:
    if self._period_start != value:
      self._period_start = value
      self.period_start_changed.emit()

  @Property(datetime, notify=period_end_changed)
  def period_end(self) -> Optional[datetime]:
    return self._period_end

  @period_end.setter
  def period_end(self, value: Optional[datetime]) -> None:
    if self._period_end != value:
      self._period_end = value
      self.period_end_changed.emit()

  @Property(dict, notify=timeline_data_changed)
  def timeline_data(self) -> Dict[int, List[int]]:
    return self._timeline_data

  def update_timeline_data(self) -> None:
    period_entries: List[Activity] = self._activity_service.get_period_entries(
      self._period_start, self._period_end)
    self._period_entries = period_entries
    hour_chunk_entries = defaultdict(dict)
    hour_entries = {i: [0, 0, 0, 0, 0, 0]
                    for i in range(24)}  # 6 quarters in an hour

    afk_category_id = None
    if not self._config["dashboard"]["display_timeline_idle"]:
      afk_category_id = self._category_service.get_category_id_from_name(
          "AFK")

    for entry in period_entries:
      timestamp_start = entry.time_start
      timestamp_stop = entry.time_stop
      category_id = entry.category_id

      if not self._config["dashboard"]["display_timeline_idle"]:
        if entry.category_id == afk_category_id:
          continue

      while timestamp_start < timestamp_stop:
        hour_start = timestamp_start.hour
        minute_start = timestamp_start.minute // 10
        quarter_hour_start = f"{hour_start:02d}:{minute_start}"

        duration_in_this_quarter = min(
          10 - (timestamp_start.minute % 10),
          (timestamp_stop - timestamp_start).total_seconds() / 60
        )

        if category_id in hour_chunk_entries[quarter_hour_start]:
          hour_chunk_entries[quarter_hour_start][category_id] += duration_in_this_quarter
        else:
          hour_chunk_entries[quarter_hour_start][category_id] = duration_in_this_quarter

        timestamp_start += timedelta(minutes=duration_in_this_quarter)

    for quarter, entries in hour_chunk_entries.items():
      max_category = max(entries, key=lambda category_id,
                         # W0640 Capture 'entries' by value
                         entries=entries: entries[category_id])
      hour, index = quarter.split(sep=":")
      hour_entries[int(hour)][int(index)] = max_category

    self._timeline_data = dict(hour_entries)
    # logger.info(f"Timeline data updated")
    self.timeline_data_changed.emit()

  def get_top_entries(self, start_time_str: str, end_time_str: str) -> List[Dict[str, Any]]:
    """ Get top 5 entries between start_time and end_time.

    Args:
      start_time_str: Start time as a string in ISO format.
      end_time_str: End time as a string in ISO format.

    Returns:
      A list of dicts with keys 'window_class', 'window_name', and 'duration'.
    """
    start_time = datetime.fromisoformat(start_time_str)
    end_time = datetime.fromisoformat(end_time_str)

    # Extract the hour and minute
    start_hour = start_time.hour
    start_minute = start_time.minute
    end_hour = end_time.hour
    end_minute = end_time.minute

    # Filter activities within the time range, checking only hours/minutes
    activities_in_range = []
    for activity in self._period_entries:
      # Convert activity times to hour/minute for comparison
      activity_start_hour = activity.time_start.hour
      activity_start_minute = activity.time_start.minute
      activity_end_hour = activity.time_stop.hour
      activity_end_minute = activity.time_stop.minute

      # Check if the activity overlaps with our target time window
      activity_start_time = activity_start_hour * 60 + activity_start_minute
      activity_end_time = activity_end_hour * 60 + activity_end_minute
      target_start_time = start_hour * 60 + start_minute
      target_end_time = end_hour * 60 + end_minute

      # Handle cases where the activity spans midnight
      if activity_end_time < activity_start_time:
        activity_end_time += 24 * 60

      if target_end_time < target_start_time:
        target_end_time += 24 * 60

      if (activity_start_time <= target_end_time and
              activity_end_time >= target_start_time):
        activities_in_range.append(activity)

    # Compute durations per window_class and window_name
    entry_durations = defaultdict(float)
    for activity in activities_in_range:
      activity_time = activity.time_start.replace(
        year=start_time.year,
        month=start_time.month,
        day=start_time.day
      )
      activity_end_time = activity.time_stop.replace(
        year=end_time.year,
        month=end_time.month,
        day=end_time.day
      )

      overlap_start = max(activity_time, start_time)
      overlap_end = min(activity_end_time, end_time)
      duration = (overlap_end - overlap_start).total_seconds()

      key = (activity.window_class, activity.window_name)
      entry_durations[key] += duration

    # Get top 5 entries by duration
    sorted_entries = sorted(entry_durations.items(),
                            key=lambda x: x[1], reverse=True)
    top_entries = sorted_entries[:5]

    result = []
    for (window_class, window_name), duration in top_entries:
      result.append({
        "window_class": window_class,
        "window_name": window_name,
        "duration": duration
      })

    return result

  @Slot(int, result=str)
  def get_category_name(self, category_id: int) -> str:
    category = self._category_service.get_category_by_id(category_id)
    return category.name if category else ""

  def get_parent_category(self, category_id: int) -> Optional[str]:
    category = self._category_service.get_category_by_id(category_id)
    return category.parent_category_id if category else None

  @Slot(int, result=str)
  def get_category_color(self, category_id: int) -> str:
    return get_category_color_or_parent(category_id)  # TODO

  @Slot(result=int)
  def get_current_hour(self) -> int:
    return datetime.now().hour
