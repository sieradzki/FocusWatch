import logging
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Tuple

from PySide6.QtCore import Property, Slot

from focuswatch.models.category import Category
from focuswatch.utils.ui_utils import get_category_color_or_parent
from focuswatch.viewmodels.base_viewmodel import BaseViewModel

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class TopCategoriesCardViewModel(BaseViewModel):
  """ ViewModel for the Top Categories Card component. """

  def __init__(self,
               activity_service: 'ActivityService',
               category_service: 'CategoryService',
               period_start: datetime,
               period_end: Optional[datetime] = None):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service
    self._period_start = period_start
    self._period_end = period_end
    self._top_categories: List[Tuple[int, int]] = []

    self._update_top_categories()

  @Slot(datetime, datetime)
  def update_period(self, start: datetime, end: Optional[datetime]) -> None:
    self._period_start = start
    self._period_end = end
    self._update_top_categories()

  @Property(datetime, notify=BaseViewModel.property_changed)
  def period_start(self) -> datetime:
    return self._period_start

  @period_start.setter
  def period_start(self, value: datetime) -> None:
    self._set_property('_period_start', value)
    self._update_top_categories()

  @Property(datetime, notify=BaseViewModel.property_changed)
  def period_end(self) -> Optional[datetime]:
    return self._period_end

  @period_end.setter
  def period_end(self, value: Optional[datetime]) -> None:
    self._set_property('_period_end', value)
    self._update_top_categories()

  @Property(list, notify=BaseViewModel.property_changed)
  def top_categories(self) -> List[Tuple[str, int]]:
    return self._top_categories

  def _update_top_categories(self) -> None:
    """Update the list of top categories based on the current period."""
    self._top_categories = self._category_service.get_period_category_time_totals(
      self._period_start, self._period_end)
    self._notify_observers('top_categories')

  def get_category_color(self, category_id: str) -> str:
    return get_category_color_or_parent(category_id)
