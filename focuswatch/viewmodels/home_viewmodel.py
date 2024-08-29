import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List, Optional, Tuple

from PySide6.QtCore import Property, Slot

from focuswatch.viewmodels.base_viewmodel import BaseViewModel
from focuswatch.viewmodels.components.timeline_viewmodel import TimelineViewModel

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class HomeViewModel(BaseViewModel):
  def __init__(self,
               activity_service: 'ActivityService',
               category_service: 'CategoryService'):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service
    self._timeline_viewmodel = TimelineViewModel(
        self._activity_service, self._category_service)

    self._period_start: datetime = datetime.now().date()
    self._period_end: Optional[datetime] = None
    self._period_type: str = "Day"

  @Property(datetime, notify=BaseViewModel.property_changed)
  def period_start(self) -> datetime:
    return self._period_start

  @Property(datetime, notify=BaseViewModel.property_changed)
  def period_end(self) -> Optional[datetime]:
    return self._period_end

  @Property(str, notify=BaseViewModel.property_changed)
  def period_type(self) -> str:
    return self._period_type

  @Slot(int)
  def shift_period(self, direction: int) -> None:
    if self._period_type == "Day":
      self._period_start += timedelta(days=direction)
      self._period_end = None
    elif self._period_type == "Week":
      self._period_start += timedelta(weeks=direction)
      self._period_end = self._period_start + timedelta(days=6)
    elif self._period_type == "Month":
      new_month = self._period_start.month + direction
      new_year = self._period_start.year + (new_month - 1) // 12
      new_month = ((new_month - 1) % 12) + 1
      self._period_start = self._period_start.replace(
        year=new_year, month=new_month, day=1)
      self._period_end = (self._period_start + timedelta(days=32)
                          ).replace(day=1) - timedelta(days=1)
    elif self._period_type == "Year":
      self._period_start = self._period_start.replace(
        year=self._period_start.year + direction, month=1, day=1)
      self._period_end = self._period_start.replace(
        year=self._period_start.year + 1) - timedelta(days=1)

    self.property_changed.emit('period_start')
    self.property_changed.emit('period_end')

  @Slot(str)
  def set_period_type(self, period_type: str) -> None:
    self._period_type = period_type
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if period_type == "Day":
      self._period_start = today
      self._period_end = None
    elif period_type == "Week":
      self._period_start = today - timedelta(days=today.weekday())
      self._period_end = self._period_start + timedelta(days=6)
    elif period_type == "Month":
      self._period_start = today.replace(day=1)
      self._period_end = (self._period_start + timedelta(days=32)
                          ).replace(day=1) - timedelta(days=1)
    elif period_type == "Year":
      self._period_start = today.replace(month=1, day=1)
      self._period_end = self._period_start.replace(
        year=self._period_start.year + 1) - timedelta(days=1)

    self.property_changed.emit('period_type')
    self.property_changed.emit('period_start')
    self.property_changed.emit('period_end')

  def get_timeline_data(self) -> List[Tuple[datetime, datetime, str, str, Optional[int]]]:
    return self._activity_service.get_period_entries(self._period_start, self._period_end)

  def get_top_categories_data(self) -> List[Tuple[str, int]]:
    return self._activity_service.get_period_entries_class_time_total(self._period_start, self._period_end)

  def get_top_applications_data(self) -> List[Tuple[str, Optional[int], int]]:
    return self._activity_service.get_period_entries_class_time_total(self._period_start, self._period_end)

  @Slot(datetime)
  def update_period_from_selected_date(self, date: datetime) -> None:
    self._period_start = date
    if self._period_type == "Week":
      self._period_start -= timedelta(days=self._period_start.weekday())
      self._period_end = self._period_start + timedelta(days=6)
    elif self._period_type == "Month":
      self._period_start = self._period_start.replace(day=1)
      self._period_end = (self._period_start + timedelta(days=32)
                          ).replace(day=1) - timedelta(days=1)
    elif self._period_type == "Year":
      self._period_start = self._period_start.replace(month=1, day=1)
      self._period_end = self._period_start.replace(
        year=self._period_start.year + 1) - timedelta(days=1)
    else:  # Day
      self._period_end = None

    self.property_changed.emit('period_start')
    self.property_changed.emit('period_end')
