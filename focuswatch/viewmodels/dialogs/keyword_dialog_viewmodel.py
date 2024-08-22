import logging
from typing import Optional

from PySide6.QtCore import Property, Slot

from focuswatch.models.keyword import Keyword
from focuswatch.services.keyword_service import KeywordService
from focuswatch.viewmodels.base_viewmodel import BaseViewModel

logger = logging.getLogger(__name__)


class KeywordDialogViewModel(BaseViewModel):
  def __init__(self, keyword_service: KeywordService, keyword_id: Optional[int] = None, keyword: Optional[Keyword] = None):
    super().__init__()
    self._keyword_service = keyword_service
    self._keyword = self._keyword_service.get_keyword(
        keyword_id) if keyword_id else keyword or Keyword()

  @Property(str, notify=BaseViewModel.property_changed)
  def name(self) -> str:
    return self._keyword.name

  @name.setter
  def name(self, value: str):
    if self._keyword.name != value:
      self._keyword.name = value
      self.property_changed.emit('name')

  @Property(bool, notify=BaseViewModel.property_changed)
  def match_case(self) -> bool:
    return self._keyword.match_case

  @match_case.setter
  def match_case(self, value: bool):
    if self._keyword.match_case != value:
      self._keyword.match_case = value
      self.property_changed.emit('match_case')

  @Property(int, notify=BaseViewModel.property_changed)
  def category_id(self) -> int:
    return self._keyword.category_id

  @category_id.setter
  def category_id(self, value: int):
    if self._keyword.category_id != value:
      self._keyword.category_id = value
      self.property_changed.emit('category_id')

  def get_keyword(self) -> Keyword:
    return self._keyword

  @Slot(result=bool)  # this probably too
  def delete_keyword(self) -> bool:
    if self._keyword and self._keyword.id:
      return self._keyword_service.delete_keyword(self._keyword.id)
    return False

  def can_delete_keyword(self) -> bool:
    return self._keyword.id is not None

  @Slot(result=bool)
  def is_input_valid(self) -> bool:
    # Check if the keyword name is not empty, potential for more validation
    return bool(self._keyword.name.strip())
