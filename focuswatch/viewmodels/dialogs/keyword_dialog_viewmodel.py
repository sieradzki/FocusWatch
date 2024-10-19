import logging
from typing import Optional

from PySide6.QtCore import Property, Slot

from focuswatch.models.keyword import Keyword
from focuswatch.viewmodels.base_viewmodel import BaseViewModel

logger = logging.getLogger(__name__)


class KeywordDialogViewModel(BaseViewModel):
  def __init__(self, keyword: Optional[Keyword] = None):
    super().__init__()
    self._keyword = keyword or Keyword()

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

  def get_keyword(self) -> Keyword:
    return self._keyword

  def can_delete_keyword(self) -> bool:
    # The keyword can be deleted if it has an ID or is a new keyword # TODO?
    return True

  @Slot(result=bool)
  def is_input_valid(self) -> bool:
    # Check if the keyword name is not empty
    return bool(self._keyword.name.strip())
