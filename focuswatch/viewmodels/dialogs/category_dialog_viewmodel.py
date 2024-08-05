import logging
from typing import List, Optional
from PySide6.QtCore import Property, Slot
from focuswatch.models.category import Category
from focuswatch.models.keyword import Keyword
from focuswatch.services.category_service import CategoryService
from focuswatch.services.keyword_service import KeywordService
from focuswatch.ui.utils import get_category_color
from focuswatch.viewmodels.base_viewmodel import BaseViewModel
import itertools
logger = logging.getLogger(__name__)


class CategoryDialogViewModel(BaseViewModel):
  def __init__(self, category_service: CategoryService, keyword_service: KeywordService, category_id: Optional[int] = None):
    super().__init__()
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._category = self._category_service.get_category_by_id(
        category_id) if category_id else None
    self._name = self._category.name if self._category else ""
    self._parent_category_id = self._category.parent_category_id if self._category else None
    self._color = get_category_color(
        category_id) if self._category else None
    self._keywords: List[Keyword] = []
    self._temp_keywords: List[Keyword] = []
    self.load_keywords()

  @Property(str, notify=BaseViewModel.property_changed)
  def name(self) -> str:
    return self._name

  @name.setter
  def name(self, value: str):
    self._set_property('_name', value)

  @Property(int, notify=BaseViewModel.property_changed)
  def parent_category_id(self) -> Optional[int]:
    return self._parent_category_id

  @parent_category_id.setter
  def parent_category_id(self, value: Optional[int]):
    self._set_property('_parent_category_id', value)

  @Property(str, notify=BaseViewModel.property_changed)
  def color(self) -> Optional[str]:
    return self._color

  @color.setter
  def color(self, value: Optional[str]):
    self._set_property('_color', value)

  @Property(list, notify=BaseViewModel.property_changed)
  def keywords(self) -> List[Keyword]:
    return self._keywords

  def load_keywords(self):
    if self._category:
      self._keywords = self._keyword_service.get_keywords_for_category(
          self._category.id)
    self._set_property('_keywords', self._keywords)

  @Slot(Keyword, result=bool)
  def add_or_update_keyword(self, keyword: Keyword) -> bool:
    if keyword.id is None:
      # New keyword
      if self._keyword_service.add_keyword(keyword):
        new_keywords = self._keywords + [keyword]
        self._set_property('_keywords', new_keywords)
        return True
    else:
      # Existing keyword
      if self._keyword_service.update_keyword(keyword):
        new_keywords = [k if k.id !=
                        keyword.id else keyword for k in self._keywords]
        self._set_property('_keywords', new_keywords)
        return True
    return False

  @Slot(Keyword, result=bool)
  def add_or_update_keyword(self, keyword: Keyword) -> bool:
    if keyword.id is None or keyword.id < 0:
      # New keyword
      if keyword.id is None:
        # Assign a temporary negative ID
        keyword.id = next(self._temp_id_counter)
      new_keywords = self._keywords + [keyword]
      self._set_property('_keywords', new_keywords)
      return True
    else:
      # Existing keyword
      new_keywords = [k if k.id !=
                      keyword.id else keyword for k in self._keywords]
      self._set_property('_keywords', new_keywords)
      return True

  @Slot(str, bool, result=bool)
  def add_keyword(self, name: str, match_case: bool = False) -> bool:
    logger.debug(f"Attempting to add keyword: {
                 name}, match_case: {match_case}")

    # Check if the keyword already exists in our local list
    if any(k.name == name and k.match_case == match_case for k in self._keywords):
      logger.debug(
        f"Keyword '{name}' already exists locally. Skipping addition.")
      return False

    keyword = Keyword(
      name=name, category_id=self._category.id if self._category else None, match_case=match_case)

    if self._category:
      res = self._keyword_service.add_keyword(keyword)
      logger.info(f"Keyword service add_keyword result: {res}")
      if res:
        new_keywords = self._keywords + [keyword]
        self._set_property('_keywords', new_keywords)
        return True
    else:
      # Store keyword temporarily
      self._temp_keywords.append(keyword)
      new_keywords = self._keywords + [keyword]
      self._set_property('_keywords', new_keywords)
      return True
    return False

  @Slot(int, result=bool)
  def remove_keyword(self, keyword_id: int) -> bool:
    if self._keyword_service.delete_keyword(keyword_id):
      new_keywords = [k for k in self._keywords if k.id != keyword_id]
      self._set_property('_keywords', new_keywords)
      return True
    return False

  @Slot(int, str, bool, result=bool)
  def update_keyword(self, keyword_id: int, name: str, match_case: bool) -> bool:
    new_keywords = self._keywords.copy()  # Create a new list
    for keyword in new_keywords:
      if keyword.id == keyword_id:
        keyword.name = name
        keyword.match_case = match_case
        if self._keyword_service.update_keyword(keyword):
          self._set_property('_keywords', new_keywords)
          return True
    return False

  @Slot(result=bool)
  def save_category(self) -> bool:
    if self._category:
      self._category.name = self._name
      self._category.parent_category_id = self._parent_category_id
      self._category.color = self._color
      success = self._category_service.update_category(self._category)
    else:
      new_category = Category(
        name=self._name, parent_category_id=self._parent_category_id, color=self._color)
      success = self._category_service.create_category(new_category)
      if success:
        self._category = new_category
        # Add temporary keywords to the database
        for keyword in self._temp_keywords:
          keyword.category_id = self._category.id
          self._keyword_service.add_keyword(keyword)
        self._temp_keywords.clear()
    return success

  def get_all_categories(self) -> List[Category]:
    return self._category_service.get_all_categories()

  def can_delete_category(self) -> bool:
    return self._category is not None and self._category.name not in ['Uncategorized', 'AFK']

  @Slot(result=bool)
  def delete_category(self) -> bool:
    if self._category and self.can_delete_category():
      return self._category_service.delete_category(self._category.id)
    return False
