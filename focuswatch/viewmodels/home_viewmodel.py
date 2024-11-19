import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List, Optional, Tuple

from PySide6.QtCore import Property, QObject, Signal, Slot

from focuswatch.viewmodels.components.focus_breakdown_viewmodel import \
    FocusBreakdownViewModel
from focuswatch.viewmodels.components.period_summary_viewmodel import \
    PeriodSummaryViewModel
from focuswatch.viewmodels.components.timeline_viewmodel import \
    TimelineViewModel
from focuswatch.viewmodels.components.top_applications_card_viewmodel import \
    TopApplicationsCardViewModel
from focuswatch.viewmodels.components.top_categories_card_viewmodel import \
    TopCategoriesCardViewModel
from focuswatch.viewmodels.components.top_titles_card_viewmodel import \
    TopTitlesCardViewModel

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class HomeViewModel(QObject):
  """ Viewmodel for the Home view."""
  # Signals for property changes
  period_start_changed = Signal()
  period_end_changed = Signal()
  period_type_changed = Signal()

  # Custom signals
  period_changed = Signal(datetime, datetime, str)
  refresh_triggered = Signal()

  def __init__(self,
               activity_service: "ActivityService",
               category_service: "CategoryService"):
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

    self._top_titles_card_viewmodel = TopTitlesCardViewModel(
      self._activity_service,
      self._period_start,
      self._period_end
    )

    self._focus_breakdown_viewmodel = FocusBreakdownViewModel(
      self._activity_service,
      self._category_service
    )

    self._period_summary_viewmodel = PeriodSummaryViewModel(
      self._activity_service,
      self._category_service,
      self._period_start,
      self._period_end
    )

    self._connect_period_changed()
    self._connect_refresh_triggered()

  # Properties with individual notify signals
  @Property(datetime, notify=period_start_changed)
  def period_start(self) -> datetime:
    """ Start of the period. """
    return self._period_start

  @period_start.setter
  def period_start(self, value: datetime) -> None:
    if self._period_start != value:
      self._period_start = value
      self.period_start_changed.emit()

  @Property(datetime, notify=period_end_changed)
  def period_end(self) -> Optional[datetime]:
    """ End of the period. """
    return self._period_end

  @period_end.setter
  def period_end(self, value: Optional[datetime]) -> None:
    if self._period_end != value:
      self._period_end = value
      self.period_end_changed.emit()

  @Property(str, notify=period_type_changed)
  def period_type(self) -> str:
    """ Type of the period (e.g., Day, Week, Month, Year). """
    return self._period_type

  @period_type.setter
  def period_type(self, value: str) -> None:
    if self._period_type != value:
      self._period_type = value
      self.period_type_changed.emit()

  # Child ViewModels as properties
  @Property(QObject, constant=True)
  def timeline_viewmodel(self) -> TimelineViewModel:
    """ ViewModel for the timeline component. """
    return self._timeline_viewmodel

  @Property(QObject, constant=True)
  def top_categories_card_viewmodel(self) -> TopCategoriesCardViewModel:
    """ ViewModel for the top categories card. """
    return self._top_categories_card_viewmodel

  @Property(QObject, constant=True)
  def top_applications_card_viewmodel(self) -> TopApplicationsCardViewModel:
    """ ViewModel for the top applications card. """
    return self._top_applications_card_viewmodel

  @Property(QObject, constant=True)
  def top_titles_card_viewmodel(self) -> TopTitlesCardViewModel:
    """ ViewModel for the top titles card. """
    return self._top_titles_card_viewmodel

  @Property(QObject, constant=True)
  def focus_breakdown_viewmodel(self) -> FocusBreakdownViewModel:
    """ ViewModel for the focus breakdown component. """
    return self._focus_breakdown_viewmodel

  @Property(QObject, constant=True)
  def period_summary_viewmodel(self) -> PeriodSummaryViewModel:
    """ ViewModel for the period summary component. """
    return self._period_summary_viewmodel

  def _connect_period_changed(self):
    """ Connect the period_changed signal to child ViewModels. """
    for viewmodel in [
        self._timeline_viewmodel,
        self._top_categories_card_viewmodel,
        self._top_applications_card_viewmodel,
        self._top_titles_card_viewmodel,
        self._focus_breakdown_viewmodel,
        self._period_summary_viewmodel
    ]:
      self.period_changed.connect(viewmodel.update_period)

  def _connect_refresh_triggered(self):
    """ Connect the refresh_triggered signal to update methods in child ViewModels. """
    self.refresh_triggered.connect(
        self._timeline_viewmodel.update_timeline_data)
    for viewmodel in [
        self._top_categories_card_viewmodel,
        self._top_applications_card_viewmodel,
        self._top_titles_card_viewmodel
    ]:
      self.refresh_triggered.connect(viewmodel.update_top_items)
    self.refresh_triggered.connect(
        self._focus_breakdown_viewmodel.compute_focus_breakdown)
    self.refresh_triggered.connect(
        self._period_summary_viewmodel.compute_period_summary)

  def _update_period(self, start: datetime, end: Optional[datetime], period_type: str) -> None:
    """ Update the period and emit period_changed signal. """
    self.period_start = start
    self.period_end = end
    self.period_type = period_type
    self.period_changed.emit(start, end, period_type)

  @Slot(int)
  def shift_period(self, direction: int) -> None:
    """ Shift the period forward or backward. """
    if self.period_type == "Day":
      new_start = self.period_start + timedelta(days=direction)
      self._update_period(new_start, None, "Day")
    elif self.period_type == "Week":
      new_start = self.period_start + timedelta(weeks=direction)
      new_end = new_start + timedelta(days=6)
      self._update_period(new_start, new_end, "Week")
    elif self.period_type == "Month":
      month_increment = direction
      year_increment = (self.period_start.month -
                        1 + month_increment) // 12
      new_month = (self.period_start.month -
                   1 + month_increment) % 12 + 1
      new_year = self.period_start.year + year_increment
      new_start = self.period_start.replace(
        year=new_year, month=new_month, day=1)
      next_month = new_month % 12 + 1
      next_month_year = new_year + (new_month // 12)
      new_end = datetime(next_month_year, next_month,
                         1) - timedelta(days=1)
      self._update_period(new_start, new_end, "Month")
    elif self.period_type == "Year":
      new_start = self.period_start.replace(
          year=self.period_start.year + direction, month=1, day=1)
      new_end = new_start.replace(
        year=new_start.year + 1) - timedelta(days=1)
      self._update_period(new_start, new_end, "Year")

  @Slot(str)
  def set_period_type(self, period_type: str) -> None:
    """ Set the period type and update the period accordingly. """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if period_type == "Day":
      self._update_period(today, None, "Day")
    elif period_type == "Week":
      start = today - timedelta(days=today.weekday())
      end = start + timedelta(days=6)
      self._update_period(start, end, "Week")
    elif period_type == "Month":
      start = today.replace(day=1)
      next_month = (start.month % 12) + 1
      next_month_year = start.year + (start.month // 12)
      end = datetime(next_month_year, next_month, 1) - timedelta(days=1)
      self._update_period(start, end, "Month")
    elif period_type == "Year":
      start = today.replace(month=1, day=1)
      end = start.replace(year=start.year + 1) - timedelta(days=1)
      self._update_period(start, end, "Year")

  @Slot(datetime)
  def update_period_from_selected_date(self, date: datetime) -> None:
    """ Update the period based on a selected date. """
    date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    if self.period_type == "Day":
      self._update_period(date, None, "Day")
    elif self.period_type == "Week":
      start = date - timedelta(days=date.weekday())
      end = start + timedelta(days=6)
      self._update_period(start, end, "Week")
    elif self.period_type == "Month":
      start = date.replace(day=1)
      next_month = (start.month % 12) + 1
      next_month_year = start.year + (start.month // 12)
      end = datetime(next_month_year, next_month, 1) - timedelta(days=1)
      self._update_period(start, end, "Month")
    elif self.period_type == "Year":
      start = date.replace(month=1, day=1)
      end = start.replace(year=start.year + 1) - timedelta(days=1)
      self._update_period(start, end, "Year")
