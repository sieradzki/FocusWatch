import logging
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from PySide6.QtCore import Property, Signal, Slot

from focuswatch.utils.ui_utils import get_category_color_or_parent
from focuswatch.viewmodels.components.top_items_card_viewmodel import \
    TopItemsCardViewModel

if TYPE_CHECKING:
  from focuswatch.config import Config
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class TopCategoriesCardViewModel(TopItemsCardViewModel):
  """ ViewModel for the Top Categories Card component """
  organized_categories_changed = Signal()
  visible_categories_changed = Signal()

  def __init__(self,
               activity_service: "ActivityService",
               category_service: "CategoryService",
               config: "Config",
               period_start: datetime,
               period_end: Optional[datetime] = None
               ):
    super().__init__(period_start, period_end)
    self._activity_service = activity_service
    self._category_service = category_service
    self._config = config
    self._organized_categories: Dict[int, Dict] = {}

    self.update_top_items()

  @Property(dict, notify=organized_categories_changed)
  def organized_categories(self) -> Dict[int, Dict]:
    return self._organized_categories

  def update_top_items(self) -> None:
    """ Update the list of top items."""
    top_categories = self._category_service.get_period_category_time_totals(
      self._period_start, self._period_end)[:self._top_items_limit]

    # clear top items
    self._top_items.clear()
    for category_id, time in top_categories:
      color = self.get_category_color(category_id)
      self._top_items[str(category_id)] = (time, color, None)

    self.organize_categories()  # uh, trigger on property changed?
    self.top_items_changed.emit()

  def get_category_color(self, category_id: int) -> Optional[str]:
    """ Get the color for a category. """
    return get_category_color_or_parent(category_id)

  def organize_categories(self) -> None:
    """ Organize top items (categories) hierarchically """
    category_hierarchy = defaultdict(
      lambda: {"category": None, "time": 0, "children": [], "visible": True}
    )

    # First pass: Populate category_hierarchy with categories and sum children times
    for category_id, (time_spent, _, _) in self._top_items.items():
      if category_id == "None":
        continue
      category_id = int(category_id)
      category = self._category_service.get_category_by_id(category_id)
      if category:
        if not self._config["dashboard"]["display_cards_idle"]:
          if category.name == "AFK":
            continue

        category_data = category_hierarchy[category_id]
        category_data["category"] = category
        category_data["time"] += time_spent

        # Traverse up to the root parent and accumulate time
        parent_id = category.parent_category_id
        while parent_id:
          parent_data = category_hierarchy[parent_id]
          parent_data["time"] += time_spent
          if parent_data["category"] is None:
            parent = self._category_service.get_category_by_id(
              parent_id)
            parent_data["category"] = parent
          parent_id = parent_data["category"].parent_category_id if parent_data["category"] else None

    # Second pass: Establish parent-child relationships and filter top-level categories
    self._organized_categories = {}
    for category_id, category_data in category_hierarchy.items():
      category = category_data["category"]
      parent_id = category.parent_category_id if category else None
      if category and parent_id:
        category_hierarchy[parent_id]["children"].append(category_data)
      else:
        self._organized_categories[category_id] = category_data

    # Sort children by time in descending order
    for category_data in category_hierarchy.values():
      category_data["children"].sort(key=lambda x: x["time"], reverse=True)

    self.organized_categories_changed.emit()

  def _find_category_data(self, category_id: int, categories: Dict[int, Dict]) -> Optional[Dict]:
    """ Recursively find category data by ID in organized 'categories' dict. """
    for cat_id, cat_data in categories.items():
      if cat_id == category_id:
        return cat_data

      if cat_data["children"]:
        # Check if the category is directly within the children
        for child_data in cat_data["children"]:
          if child_data["category"].id == category_id:
            return child_data

        # Recurse into children categories
        for child_data in cat_data["children"]:
          found = self._find_category_data(
            category_id, {child_data["category"].id: child_data})
          if found:
            return found

    return None

  @Slot(int)
  def toggle_category_visibility(self, category_id: int) -> None:
    """ Toggle the visibility of a category's children. """
    cat_data = self._find_category_data(
      category_id, self._organized_categories)
    if cat_data:
      cat_data["visible"] = not cat_data["visible"]
      self.visible_categories_changed.emit()

  def is_category_visible(self, category_id: int) -> bool:
    """ Check if a category is currently visible. """
    cat_data = self._find_category_data(
      category_id, self._organized_categories)
    return cat_data["visible"] if cat_data else False

  def get_visible_categories(self) -> List[Tuple[int, int]]:
    """ Get the list of currently visible categories and their times. """
    visible_categories = []

    def add_visible_categories(cat_data: Dict):
      if cat_data["visible"]:
        visible_categories.append((cat_data["category"].id, cat_data["time"]))
        for child in cat_data["children"]:
          add_visible_categories(list(child.values())[0])

    for cat_data in self._organized_categories.values():
      add_visible_categories(cat_data)

    return visible_categories

  def get_category_depth(self, category_id: int) -> int:
    return self._category_service.get_category_depth(category_id)
