import logging
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from PySide6.QtCore import Property, Slot, Signal

from focuswatch.models.category import Category
from focuswatch.utils.ui_utils import get_category_color_or_parent
from focuswatch.viewmodels.base_viewmodel import BaseViewModel

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class TopCategoriesCardViewModel(BaseViewModel):
  """ ViewModel for the Top Categories Card component. """

  category_visibility_changed = Signal(int, bool)

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
    self._organized_categories: Dict[int, Dict] = {}

    self._update_top_categories()

  @Slot(datetime, datetime)
  def update_period(self, start: datetime, end: Optional[datetime]) -> None:
    """ Update the time period for category analysis. """
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

  @Property(dict, notify=BaseViewModel.property_changed)
  def organized_categories(self) -> Dict[int, Dict]:
    return self._organized_categories

  def _update_top_categories(self) -> None:
    """ Update the list of top categories and organize them hierarchically. """
    self._top_categories = self._category_service.get_period_category_time_totals(
      self._period_start, self._period_end)
    self._organize_categories()

  def _organize_categories(self) -> None:
    """ Organize the top categories hierarchically. """
    temp_cat_dict = defaultdict(
      lambda: {'category': None, 'time': 0, 'children': [], 'visible': True})

    for category_id, time in self._top_categories:
      category = self._category_service.get_category_by_id(category_id)
      if category:
        cat_dict = temp_cat_dict[category_id]
        cat_dict['category'] = category
        cat_dict['time'] = time
        parent_id = category.parent_category_id
        while parent_id:
          parent_dict = temp_cat_dict[parent_id]
          parent_dict['time'] += time
          if parent_dict['category'] is None:
            parent = self._category_service.get_category_by_id(parent_id)
            parent_dict['category'] = parent
          parent_id = parent_dict['category'].parent_category_id if parent_dict['category'] else None

    for category_id, cat_data in temp_cat_dict.items():
      category = cat_data['category']
      if category and category.parent_category_id:
        parent_id = category.parent_category_id
        temp_cat_dict[parent_id]['children'].append({category_id: cat_data})

    for cat_data in temp_cat_dict.values():
      cat_data['children'].sort(key=lambda x: list(
        x.values())[0]['time'], reverse=True)

    self._organized_categories = {
      cat_id: cat_data for cat_id, cat_data in temp_cat_dict.items() if not cat_data['category'].parent_category_id
    }
    self.property_changed.emit('organized_categories')

  def _find_category_data(self, category_id: int, categories: Dict[int, Dict]) -> Optional[Dict]:
    """ Recursively find category data by ID. """
    for cat_id, cat_data in categories.items():
      if cat_id == category_id:
        return cat_data

      if cat_data['children']:
        for child in cat_data['children']:
          child_id, child_data = next(iter(child.items()))
          if child_id == category_id:
            return child_data

        # Only recurse if we haven't found the category yet
        for child in cat_data['children']:
          found = self._find_category_data(category_id, child)
          if found:
            return found

    return None

  def get_category_color(self, category_id: int) -> str:
    """ Get the color for a category. """
    return get_category_color_or_parent(category_id)

  @Slot(int)
  def toggle_category_visibility(self, category_id: int) -> None:
    """ Toggle the visibility of a category's children. """
    cat_data = self._find_category_data(
      category_id, self._organized_categories)
    if cat_data:
      cat_data['visible'] = not cat_data['visible']
      self.category_visibility_changed.emit(category_id, cat_data['visible'])
      self.property_changed.emit('organized_categories')

  def is_category_visible(self, category_id: int) -> bool:
    """ Check if a category is currently visible. """
    cat_data = self._find_category_data(
      category_id, self._organized_categories)
    return cat_data['visible'] if cat_data else False

  def get_visible_categories(self) -> List[Tuple[int, int]]:
    """ Get the list of currently visible categories and their times. """
    visible_categories = []

    def add_visible_categories(cat_data: Dict):
      if cat_data['visible']:
        visible_categories.append((cat_data['category'].id, cat_data['time']))
        for child in cat_data['children']:
          add_visible_categories(list(child.values())[0])

    for cat_data in self._organized_categories.values():
      add_visible_categories(cat_data)

    return visible_categories

  def get_category_depth(self, category_id: int) -> int:
    return self._category_service.get_category_depth(category_id)
