import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List, Optional, Tuple

from PySide6.QtCore import Property, Slot, Signal

from focuswatch.viewmodels.base_viewmodel import BaseViewModel
from focuswatch.viewmodels.components.timeline_viewmodel import TimelineViewModel
from focuswatch.viewmodels.components.top_categories_card_viewmodel import TopCategoriesCardViewModel
from focuswatch.viewmodels.components.top_applications_card_viewmodel import TopApplicationsCardViewModel
from focuswatch.viewmodels.components.top_titles_card_viewmodel import TopNamesCardViewModel

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class HomeViewModel(BaseViewModel):
  period_changed = Signal(datetime, datetime, str)
  refresh_triggered = Signal()

  def __init__(self,
               activity_service: 'ActivityService',
               category_service: 'CategoryService'):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service

    self._period_start: datetime = datetime.now().replace(
      hour=0, minute=0, second=0, microsecond=0)
    self._period_end: Optional[datetime] = None
    self._period_type: str = "Day"

    self._timeline_viewmodel = TimelineViewModel(
      self._activity_service,
      self._category_service
    )
    self._top_categories_card_viewmodel = TopCategoriesCardViewModel(
      self._activity_service,
      self._category_service,
      self._period_start,
      self._period_end
    )
    self._top_applications_card_viewmodel = TopApplicationsCardViewModel(
      self._activity_service,
      self._period_start,
      self._period_end
    )

    self._top_titles_card_viewmodel = TopNamesCardViewModel(
      self._activity_service,
      self._period_start,
      self._period_end
    )

    self.connect_period_changed()
    self.connect_refresh_triggered()

  @Property(datetime, notify=BaseViewModel.property_changed)
  def period_start(self) -> datetime:
    return self._period_start

  @Property(datetime, notify=BaseViewModel.property_changed)
  def period_end(self) -> Optional[datetime]:
    return self._period_end

  @Property(str, notify=BaseViewModel.property_changed)
  def period_type(self) -> str:
    return self._period_type

  @Property('QVariant', notify=BaseViewModel.property_changed)
  def timeline_viewmodel(self) -> TimelineViewModel:
    return self._timeline_viewmodel

  @Property('QVariant', notify=BaseViewModel.property_changed)
  def top_categories_card_viewmodel(self) -> TopCategoriesCardViewModel:
    return self._top_categories_card_viewmodel

  @Property('QVariant', notify=BaseViewModel.property_changed)
  def top_applications_card_viewmodel(self) -> TopApplicationsCardViewModel:
    return self._top_applications_card_viewmodel

  @Property('QVariant', notify=BaseViewModel.property_changed)
  def top_titles_card_viewmodel(self) -> TopNamesCardViewModel:
    return self._top_titles_card_viewmodel

  def connect_period_changed(self):
    for viewmodel in [
        self._timeline_viewmodel,
        self._top_categories_card_viewmodel,
        self._top_applications_card_viewmodel,
        self._top_titles_card_viewmodel
    ]:
      self.period_changed.connect(viewmodel.update_period)

  def connect_refresh_triggered(self):
    self.refresh_triggered.connect(
      self._timeline_viewmodel._update_timeline_data)
    for viewmodel in [
        self._top_categories_card_viewmodel,
        self._top_applications_card_viewmodel,
        self._top_titles_card_viewmodel
    ]:
      self.refresh_triggered.connect(viewmodel._update_top_items)

  def _update_period(self, start: datetime, end: Optional[datetime], period_type: str) -> None:
    self._period_start = start
    self._period_end = end
    self._period_type = period_type
    self.period_changed.emit(start, end, period_type)

  @Slot(int)
  def shift_period(self, direction: int) -> None:
    if self._period_type == "Day":
      new_start = self._period_start + timedelta(days=direction)
      self._update_period(new_start, None, "Day")
    elif self._period_type == "Week":
      new_start = self._period_start + timedelta(weeks=direction)
      new_end = new_start + timedelta(days=6)
      self._update_period(new_start, new_end, "Week")
    elif self._period_type == "Month":
      new_month = self._period_start.month + direction
      new_year = self._period_start.year + (new_month - 1) // 12
      new_month = ((new_month - 1) % 12) + 1
      new_start = self._period_start.replace(
        year=new_year, month=new_month, day=1)
      new_end = (new_start + timedelta(days=32)
                 ).replace(day=1) - timedelta(days=1)
      self._update_period(new_start, new_end, "Month")
    elif self._period_type == "Year":
      new_start = self._period_start.replace(
        year=self._period_start.year + direction, month=1, day=1)
      new_end = new_start.replace(year=new_start.year + 1) - timedelta(days=1)
      self._update_period(new_start, new_end, "Year")

  @Slot(str)
  def set_period_type(self, period_type: str) -> None:
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if period_type == "Day":
      self._update_period(today, None, "Day")
    elif period_type == "Week":
      start = today - timedelta(days=today.weekday())
      end = start + timedelta(days=6)
      self._update_period(start, end, "Week")
    elif period_type == "Month":
      start = today.replace(day=1)
      end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
      self._update_period(start, end, "Month")
    elif period_type == "Year":
      start = today.replace(month=1, day=1)
      end = start.replace(year=start.year + 1) - timedelta(days=1)
      self._update_period(start, end, "Year")

  @Slot(datetime)
  def update_period_from_selected_date(self, date: datetime) -> None:
    date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    if self._period_type == "Day":
        self._update_period(date, None, "Day")
    elif self._period_type == "Week":
      start = date - timedelta(days=date.weekday())
      end = start + timedelta(days=6)
      self._update_period(start, end, "Week")
    elif self._period_type == "Month":
      start = date.replace(day=1)
      end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
      self._update_period(start, end, "Month")
    else:  # Year
      start = date.replace(month=1, day=1)
      end = start.replace(year=start.year + 1) - timedelta(days=1)
      self._update_period(start, end, "Year")
