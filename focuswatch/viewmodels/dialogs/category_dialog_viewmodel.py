import logging
from typing import TYPE_CHECKING, List, Optional

from PySide6.QtCore import Property, Slot

from focuswatch.models.category import Category
from focuswatch.models.keyword import Keyword
from focuswatch.utils.ui_utils import get_category_color
from focuswatch.viewmodels.base_viewmodel import BaseViewModel

if TYPE_CHECKING:
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.keyword_service import KeywordService

logger = logging.getLogger(__name__)


class CategoryDialogViewModel(BaseViewModel):
  def __init__(self,
               category_service: 'CategoryService',
               keyword_service: 'KeywordService',
               category_id: Optional[int] = None):
    super().__init__()
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._category = self._category_service.get_category_by_id(
        category_id) if category_id else Category(name="")
    self._original_keywords: List[Keyword] = []
    self._keywords: List[Keyword] = []
    self._added_keywords: List[Keyword] = []
    self._updated_keywords: List[Keyword] = []
    self._removed_keywords: List[Keyword] = []
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
    return self._keywords

  def load_keywords(self):
    """ Load keywords for the category if it exists. """
    if self._category.id:
      self._original_keywords = self._keyword_service.get_keywords_for_category(
          self._category.id)
      # Make a copy for editing
      self._keywords = self._original_keywords.copy()
    else:
      self._original_keywords = []
      self._keywords = []
    self.property_changed.emit('keywords')

  @Slot(str, bool)
  def add_keyword(self, keyword_name: str, match_case: bool):
    """ Add a keyword to the category. """
    keyword = Keyword(
        name=keyword_name,
        match_case=match_case,
        category_id=self._category.id  # Might be None for new category
    )
    self._keywords.append(keyword)
    self._added_keywords.append(keyword)
    self.property_changed.emit('keywords')

  @Slot(int, str, bool)
  def update_keyword(self, index: int, new_name: str, new_match_case: bool):
    """ Update a keyword in the category. """
    if 0 <= index < len(self._keywords):
      keyword = self._keywords[index]
      keyword.name = new_name
      keyword.match_case = new_match_case
      if keyword not in self._added_keywords and keyword not in self._updated_keywords:
        self._updated_keywords.append(keyword)
      self.property_changed.emit('keywords')
    else:
      logger.error(f"Keyword index {index} out of range.")

  @Slot(int)
  def remove_keyword(self, index: int):
    """ Remove a keyword from the category. """
    if 0 <= index < len(self._keywords):
      keyword = self._keywords.pop(index)
      if keyword in self._added_keywords:
        self._added_keywords.remove(keyword)
      elif keyword not in self._removed_keywords:
        self._removed_keywords.append(keyword)
      self.property_changed.emit('keywords')
    else:
      logger.error(f"Keyword index {index} out of range.")

  @Slot(result=bool)
  def save_category(self) -> bool:
    """ Save the category and apply keyword changes. """
    try:
      if self._category.id:  # Editing existing category
        success = self._category_service.update_category(
            self._category)
      else:  # Creating new category
        new_category_id = self._category_service.create_category(
            self._category)
        if new_category_id:
          self._category.id = new_category_id
          success = True
        else:
          success = False

      if success:
        # Apply keyword changes
        for keyword in self._added_keywords:
          keyword.category_id = self._category.id
          self._keyword_service.add_keyword(keyword)
        for keyword in self._updated_keywords:
          self._keyword_service.update_keyword(keyword)
        for keyword in self._removed_keywords:
          if keyword.id:
            self._keyword_service.delete_keyword(keyword.id)
        # Reload keywords to reflect changes
        self.load_keywords()
        # Clear change trackers
        self._added_keywords.clear()
        self._updated_keywords.clear()
        self._removed_keywords.clear()
      else:
        logger.error("Failed to save category.")
      return success
    except Exception as e:
      logger.error(f"Error saving category: {e}")
      return False

  def get_all_categories(self) -> List[Category]:
    """ Get all categories. """
    return self._category_service.get_all_categories()

  def can_delete_category(self) -> bool:
    """ Check if the category can be deleted. """
    return self._category.id is not None and self._category.name not in ['Uncategorized', 'AFK']

  @Slot(result=bool)
  def delete_category(self) -> bool:
    """ Delete the category. """
    if self.can_delete_category():
      try:
        return self._category_service.delete_category(self._category.id)
      except Exception as e:
        logger.error(f"Error deleting category: {e}")
        return False
    return False
