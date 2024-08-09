import logging
from typing import List, Optional

from PySide6.QtCore import Property, Slot

from focuswatch.models.category import Category
from focuswatch.models.keyword import Keyword
from focuswatch.services.category_service import CategoryService
from focuswatch.services.keyword_service import KeywordService
from focuswatch.ui.utils import get_category_color
from focuswatch.viewmodels.base_viewmodel import BaseViewModel

logger = logging.getLogger(__name__)


class CategoryDialogViewModel(BaseViewModel):
  def __init__(self, category_service: CategoryService, keyword_service: KeywordService, category_id: Optional[int] = None):
    super().__init__()
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._category = self._category_service.get_category_by_id(
      category_id) if category_id else Category(name="")
    self._keywords: List[Keyword] = []
    self._temp_keywords: List[Keyword] = []
    self.load_keywords()

  @Property(str, notify=BaseViewModel.property_changed)
  def name(self) -> str:
    return self._category.name

  @name.setter
  def name(self, value: str):
    if self._category.name != value:
      self._category.name = value
      self.property_changed.emit('name')

  @Property(int, notify=BaseViewModel.property_changed)
  def parent_category_id(self) -> Optional[int]:
    return self._category.parent_category_id

  @parent_category_id.setter
  def parent_category_id(self, value: Optional[int]):
    if self._category.parent_category_id != value:
      self._category.parent_category_id = value
      self.property_changed.emit('parent_category_id')

  @Property(str, notify=BaseViewModel.property_changed)
  def color(self) -> Optional[str]:
    return self._category.color

  @color.setter
  def color(self, value: Optional[str]):
    if self._category.color != value:
      self._category.color = value
      self.property_changed.emit('color')

  @Property(list, notify=BaseViewModel.property_changed)
  def keywords(self) -> List[Keyword]:
    return self._keywords + self._temp_keywords

  def load_keywords(self):
    if self._category.id:
      self._keywords = self._keyword_service.get_keywords_for_category(
        self._category.id)
    self.property_changed.emit('keywords')

  @Slot(Keyword)
  def add_keyword(self, keyword: Keyword):
    if self._category.id:  # editing existing category
      keyword.category_id = self._category.id
      if self._keyword_service.add_keyword(keyword):
        keyword_id = self._keyword_service.get_keyword_id(
          keyword.name, self._category.id)
        keyword = self._keyword_service.get_keyword(keyword_id)
        self._keywords.append(keyword)
    else:  # creating new category
      self._temp_keywords.append(keyword)

    self.property_changed.emit('keywords')

  @Slot(Keyword)
  def update_keyword(self, keyword: Keyword):
    if self._category.id:  # editing existing category
      if self._keyword_service.update_keyword(keyword):
        for i, k in enumerate(self._keywords):
          if k.id == keyword.id:
            self._keywords[i] = keyword
            break
        self.property_changed.emit('keywords')
    else:  # creating new category
      for i, k in enumerate(self._temp_keywords):
        if k.id == keyword.id:
          self._temp_keywords[i] = keyword
          break
      self.property_changed.emit('keywords')

  @Slot(int)
  def remove_keyword(self, keyword_id: Optional[int] = None, keyword_name: str = None):
    print(f"Calling remove_keyword with id: {
          keyword_id} and name: {keyword_name}")
    if self._category.id:  # editing existing category
      self._keywords = [k for k in self._keywords if k.id != int(keyword_id)]
    else:  # creating new category - remove by name
      self._temp_keywords = [
        k for k in self._temp_keywords if k.name != keyword_name]
    self.property_changed.emit('keywords')

  @Slot(result=bool)
  def save_category(self) -> bool:
    if self._category.id: # editing existing category
      success = self._category_service.update_category(self._category)
    else: # creating new category
      success = self._category_service.create_category(self._category)
      if success:
        for keyword in self._temp_keywords:
          # get the id of the newly created category
          self._category.id = self._category_service.get_category_id_from_name(self._category.name)
          keyword.category_id = self._category.id
          self._keyword_service.add_keyword(keyword)
        self._keywords.extend(self._temp_keywords)
        self._temp_keywords.clear()
    self.load_keywords()  # Reload keywords to ensure we have the latest data
    return success

  def get_all_categories(self) -> List[Category]:
    return self._category_service.get_all_categories()

  def can_delete_category(self) -> bool:
    return self._category.id is not None and self._category.name not in ['Uncategorized', 'AFK']

  @Slot(result=bool)
  def delete_category(self) -> bool:
    if self.can_delete_category():
      return self._category_service.delete_category(self._category.id)
    return False
