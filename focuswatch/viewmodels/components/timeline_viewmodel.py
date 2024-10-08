import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

from focuswatch.models.activity import Activity
from focuswatch.ui.utils import get_category_color_or_parent
from focuswatch.viewmodels.base_viewmodel import BaseViewModel

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class TimelineViewModel(BaseViewModel):
  data_changed = Signal()

  def __init__(self, activity_service: 'ActivityService', category_service: 'CategoryService'):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service
    self._period_start: datetime = datetime.now().replace(
      hour=0, minute=0, second=0, microsecond=0)
    self._period_end: Optional[datetime] = None
    self._timeline_data: Dict[int, List[int]] = {}

    self._update_timeline_data()

  @Slot(datetime, datetime)
  def update_period(self, start: datetime, end: Optional[datetime]) -> None:
    """ Update the time period. """
    self.period_start = start
    self.period_end = end

  @Property(datetime, notify=data_changed)
  def period_start(self) -> datetime:
    return self._period_start

  @period_start.setter
  def period_start(self, value: datetime) -> None:
    if self._period_start != value:
      self._period_start = value
      self._update_timeline_data()

  @Property(datetime, notify=data_changed)
  def period_end(self) -> Optional[datetime]:
    return self._period_end

  @period_end.setter
  def period_end(self, value: Optional[datetime]) -> None:
    if self._period_end != value:
      self._period_end = value
      self._update_timeline_data()

  @Property(dict, notify=data_changed)
  def timeline_data(self) -> Dict[int, List[int]]:
    return self._timeline_data

  def _update_timeline_data(self) -> None:
    period_entries: List[Activity] = self._activity_service.get_period_entries(
      self._period_start, self._period_end)
    hour_chunk_entries = defaultdict(dict)
    hour_entries = {i: [0, 0, 0, 0, 0, 0]
                    for i in range(24)}  # 6 quarters in an hour

    for entry in period_entries:
      timestamp_start = entry.time_start
      timestamp_stop = entry.time_stop
      timestamp_start = datetime.strptime(
        timestamp_start, "%Y-%m-%dT%H:%M:%S.%f")
      timestamp_stop = datetime.strptime(
        timestamp_stop, "%Y-%m-%dT%H:%M:%S.%f")
      category_id = entry.category_id

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
      max_category = max(entries, key=lambda category_id: entries[category_id])
      hour, index = quarter.split(sep=":")
      hour_entries[int(hour)][int(index)] = max_category

    self._timeline_data = dict(hour_entries)
    # logger.info(f"Timeline data updated")
    self.data_changed.emit()

  @Slot(int, result=str)
  def get_category_name(self, category_id: int) -> str:
    category = self._category_service.get_category_by_id(category_id)
    return category.name if category else ""

  @Slot(int, result=str)
  def get_category_color(self, category_id: int) -> str:
    return get_category_color_or_parent(category_id)  # TODO

  @Slot(result=int)
  def get_current_hour(self) -> int:
    return datetime.now().hour
