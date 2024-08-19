import logging
from typing import List, Tuple, Dict

from PySide6.QtCore import Property, Signal, Slot

from focuswatch.models.category import Category
from focuswatch.models.keyword import Keyword
from focuswatch.services.activity_service import ActivityService
from focuswatch.services.category_service import CategoryService
from focuswatch.services.keyword_service import KeywordService
from focuswatch.viewmodels.base_viewmodel import BaseViewModel

logger = logging.getLogger(__name__)


class CategorizationHelperViewModel(BaseViewModel):
  categorization_progress = Signal(int, int)

  def __init__(self, activity_service: ActivityService, category_service: CategoryService,
               keyword_service: KeywordService):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._uncategorized_applications: List[Tuple[int, str, int]] = []
    self._uncategorized_titles: List[Tuple[int, str, int]] = []
    self._categories: List[Category] = []
    self.load_data()

  def load_data(self):
    self._uncategorized_applications = self._activity_service.get_top_uncategorized_window_classes(
      10)
    self.property_changed.emit('uncategorized_applications')

    self._uncategorized_titles = self._activity_service.get_top_uncategorized_window_names(
      10)
    self.property_changed.emit('uncategorized_titles')

    self._categories = self._category_service.get_all_categories()
    self.property_changed.emit('categories')
    logger.info("CategorizationHelperViewModel loaded")

  @Property(list, notify=BaseViewModel.property_changed)
  def uncategorized_applications(self):
    return self._uncategorized_applications

  @Property(list, notify=BaseViewModel.property_changed)
  def uncategorized_titles(self):
    return self._uncategorized_titles

  @Property(list, notify=BaseViewModel.property_changed)
  def categories(self):
    return self._categories

  @Slot(str, int, bool)
  def save_categorization(self, name: str, category_id: int, match_case: bool):
    keyword = Keyword(name=name, category_id=category_id,
                      match_case=match_case)
    self._keyword_service.add_keyword(keyword)
    logger.info(f"Saved categorization: {name} to category {category_id}")

  @Slot(result=bool)
  def perform_retroactive_categorization(self) -> bool:
    pass
    # return self._retroactive_categorization_service.categorize_all_activities(self.categorization_progress.emit)

  @Slot(result=int)
  def get_uncategorized_category_id(self) -> int:
    return self._category_service.get_uncategorized_category_id()
