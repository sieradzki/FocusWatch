import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtCore import Property, Signal, Slot

from focuswatch.models.category import Category
from focuswatch.models.keyword import Keyword
from focuswatch.services.activity_service import ActivityService
from focuswatch.services.category_service import CategoryService
from focuswatch.services.keyword_service import KeywordService
from focuswatch.viewmodels.base_viewmodel import BaseViewModel

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.classifier_service import ClassifierService
  from focuswatch.services.keyword_service import KeywordService


class CategoriesViewModel(BaseViewModel):
  retroactive_categorization_progress = Signal(int, int)

  def __init__(self, activity_service: 'ActivityService',
               category_service: 'CategoryService',
               keyword_service: 'KeywordService',
               classifier_service: 'ClassifierService'):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._classifier = classifier_service

    self._categories: List[Category] = []
    self._filter_text: str = ""
    self._organized_categories: Dict[int, Dict[str, Any]] = {}

    self.load_categories()

  @Property(list, notify=BaseViewModel.property_changed)
  def categories(self) -> List[Category]:
    return self._categories

  @Property(str, notify=BaseViewModel.property_changed)
  def filter_text(self) -> str:
    return self._filter_text

  @filter_text.setter
  def filter_text(self, value: str):
    if self._filter_text != value.lower():
      self._filter_text = value.lower()
      self.property_changed.emit('filter_text')

  @Property(dict, notify=BaseViewModel.property_changed)
  def organized_categories(self) -> Dict:
    return self._organized_categories

  def load_categories(self):
    self._categories = self._category_service.get_all_categories()
    self.organize_categories()
    self.property_changed.emit('categories')

  def organize_categories(self):
    """ Organize categories into a hierarchical structure. """
    cat_key: Dict[int, List[str]] = defaultdict(list)
    for category in self._categories:
      category_keywords = self._keyword_service.get_keywords_for_category(
          category.id)
      cat_key[category.id] = [
          keyword.name for keyword in category_keywords]

    temp_cat_dict: Dict[int, Dict[str, Any]] = defaultdict(dict)
    for category in self._categories:
      category_dict = {
          'category': category,
          'keywords': cat_key[category.id],
          'children': [],
          'expanded': True,
      }
      if category.parent_category_id is None:
        temp_cat_dict[category.id] = category_dict
      elif category.parent_category_id not in temp_cat_dict:
        temp_cat_dict[category.parent_category_id] = {
            'category': None,
            'keywords': [],
            'children': [category.id],
            'expanded': True,
        }
        temp_cat_dict[category.id] = category_dict
      else:
        parent_category = temp_cat_dict[category.parent_category_id]
        parent_category['children'].append(category.id)
        temp_cat_dict[category.id] = category_dict

    cat_dict: Dict[int, Dict[str, Any]] = {}

    def organize_categories_recursive(cat_id):
      category_data = temp_cat_dict[cat_id]
      cat_dict[cat_id] = category_data
      for child_id in category_data['children']:
        organize_categories_recursive(child_id)

    root_categories = [
        category.id for category in self._categories if category.parent_category_id is None]
    for root_cat_id in root_categories:
      organize_categories_recursive(root_cat_id)

    self._organized_categories = cat_dict

    self.property_changed.emit('organized_categories')

  def get_category_depth(self, category_id: int) -> int:
    """ Get the depth of a category in the category hierarchy. """
    return self._category_service.get_category_depth(category_id)

  def add_category(
      self, name: str, parent_id: Optional[int] = None, color: Optional[str] = None
  ) -> bool:
    """ Add a new category. """
    result = self._category_service.create_category(name, parent_id, color)
    if result:
      self.load_categories()
    return result

  def update_category(self, category: Category) -> bool:
    """ Update an existing category. """
    result = self._category_service.update_category(category)
    if result:
      self.load_categories()
    return result

  def delete_category(self, category_id: int) -> bool:
    """ Delete a category by its ID. """
    result = self._category_service.delete_category(category_id)
    if result:
      self.load_categories()
    return result

  def restore_defaults(self) -> bool:
    """ Restore default categories and perform retroactive categorization. """
    self._category_service.insert_default_categories()
    self._keyword_service.insert_default_keywords()
    self.retroactive_categorization()
    self.load_categories()
    return True

  def retroactive_categorization(self) -> bool:
    """ Perform retroactive categorization of activities. """
    # Fetch all activities
    activities = self._activity_service.get_all_activities()
    total_activities = len(activities)
    self.retroactive_categorization_progress.emit(0, total_activities)

    # Group activities by (window_class, window_name)

    activity_groups = defaultdict(list)
    for activity in activities:
      key = (activity.window_class, activity.window_name)
      activity_groups[key].append(activity)

    # Process each group
    processed_activities = 0
    total_groups = len(activity_groups)
    self.retroactive_categorization_progress.emit(0, total_activities)

    for i, (key, group_activities) in enumerate(activity_groups.items(), start=1):
      window_class, window_name = key
      # Classify once per group
      category_id = self._classifier.classify_entry(
        window_class, window_name)

      # Find activities that need updating
      activities_to_update = [
          activity for activity in group_activities if activity.category_id != category_id
      ]

      if activities_to_update:
        # Update all activities in one query
        activity_ids = [activity.id for activity in activities_to_update]
        self._activity_service.bulk_update_category(
          activity_ids, category_id)

      processed_activities += len(group_activities)

      # Emit progress signal
      self.retroactive_categorization_progress.emit(
        processed_activities, total_activities)

    # Final progress update
    self.retroactive_categorization_progress.emit(
      total_activities, total_activities)
    return True

  def get_top_uncategorized_window_classes(self, limit: int = 10) -> List[tuple]:
    """ Get the top uncategorized window classes. """
    return self._activity_service.get_top_uncategorized_window_classes(limit)

  def get_top_uncategorized_window_names(self, limit: int = 10) -> List[tuple]:
    """ Get the top uncategorized window names. """
    return self._activity_service.get_top_uncategorized_window_names(limit)
