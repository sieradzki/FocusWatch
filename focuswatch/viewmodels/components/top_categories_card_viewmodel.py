import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from PySide6.QtCore import Property, Slot, Signal
from focuswatch.models.category import Category
from focuswatch.utils.ui_utils import get_category_color_or_parent
# Updated to inherit
from focuswatch.viewmodels.components.top_items_card_viewmodel import TopItemsCardViewModel

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class TopCategoriesCardViewModel(TopItemsCardViewModel):
  """ ViewModel for the Top Categories Card component, refactored to use TopItemsCardViewModel. """

  category_visibility_changed = Signal(int, bool)

  def __init__(self,
               activity_service: 'ActivityService',
               category_service: 'CategoryService',
               period_start: datetime,
               period_end: Optional[datetime] = None):
    super().__init__(period_start, period_end)
    self._activity_service = activity_service
    self._category_service = category_service
    self._organized_categories: Dict[int, Dict] = {}

    self._update_top_items()

  @Property(dict, notify=TopItemsCardViewModel.property_changed)
  def organized_categories(self) -> Dict[int, Dict]:
    return self._organized_categories

  def _update_top_items(self) -> None:
    """ Update the list of top items."""
    top_categories = self._category_service.get_period_category_time_totals(
        self._period_start, self._period_end)

    # clear top items
    self._top_items.clear()
    for category_id, time in top_categories:
      color = self.get_category_color(category_id)
      self._top_items.append((str(category_id), time, color, None))

    self.organize_categories()  # uh, trigger on property changed?
    self.property_changed.emit('top_items')

  def get_category_color(self, category_id: int) -> Optional[str]:
    """ Get the color for a category. """
    return get_category_color_or_parent(category_id)

  def organize_categories(self) -> None:
    """ Organize top items (categories) hierarchically """
    temp_cat_dict = defaultdict(
      lambda: {'category': None, 'time': 0, 'children': [], 'visible': True}
    )

    for category_id, time, color, _ in self._top_items:
      category_id = int(category_id)  # uh?
      category = self._category_service.get_category_by_id(category_id)
      if category:
        # TODO does this search or create? or both i guss too
        cat_dict = temp_cat_dict[category_id]
        cat_dict['category'] = category
        cat_dict['time'] = time
        parent_id = category.parent_category_id
        while parent_id:  # find top parent
          parent_dict = temp_cat_dict[parent_id]
          # parent time should be sum of it's children (or not?) TODO test this
          parent_dict['time'] += time
          if parent_dict['category'] is None:
            parent = self._category_service.get_category_by_id(
              parent_id)  # get parent if it has no tracked time itself
            parent_dict['category'] = parent
          parent_id = parent_dict['category'].parent_category_id if parent_dict['category'] else None

    # TODO optimization?
    for category_id, cat_data in temp_cat_dict.items():  # add children to parents
      category = cat_data['category']
      parent_id = category.parent_category_id
      if category and parent_id:
        temp_cat_dict[parent_id]['children'].append({category_id: cat_data})

    for cat_data in temp_cat_dict.values():  # sort children by time
      cat_data['children'].sort(key=lambda x: list(
        x.values())[0]['time'], reverse=True
      )

    self._organized_categories = {  # remove children from the root level
      cat_id: cat_data for cat_id, cat_data in temp_cat_dict.items() if not cat_data['category'].parent_category_id
    }

    self.property_changed.emit("organized_categories")

  def _find_category_data(self, category_id: int, categories: Dict[int, Dict]) -> Optional[Dict]:
    """ Recursively find category data by ID in organized 'categories' dict. """
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
