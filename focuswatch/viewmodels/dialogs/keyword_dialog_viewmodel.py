from PySide6.QtCore import Property, Slot
from focuswatch.services.keyword_service import KeywordService
from focuswatch.models.keyword import Keyword
from typing import Optional
from focuswatch.viewmodels.base_viewmodel import BaseViewModel


class KeywordDialogViewModel(BaseViewModel):
  def __init__(self, keyword_service: KeywordService, category_id: int, keyword_id: Optional[int] = None):
    super().__init__()
    self._keyword_service = keyword_service
    self._category_id = category_id
    self._keyword = self._keyword_service.get_keyword(
        keyword_id) if keyword_id else None
    self._name = self._keyword.name if self._keyword else ""
    self._match_case = self._keyword.match_case if self._keyword else False

  @Property(str, notify=BaseViewModel.property_changed)
  def name(self) -> str:
    return self._name

  @name.setter
  def name(self, value: str):
    self._set_property('_name', value)

  @Property(bool, notify=BaseViewModel.property_changed)
  def match_case(self) -> bool:
    return self._match_case

  @match_case.setter
  def match_case(self, value: bool):
    self._set_property('_match_case', value)

  def get_keyword(self) -> Keyword:
    return Keyword(
      name=self._name,
      match_case=self._match_case,
      category_id=self._category_id,
      id=self._keyword.id if self._keyword else None
    )

  # @Slot(result=bool)
  # def save_keyword(self) -> bool:
  #   if self._keyword:
  #     self._keyword.name = self._name
  #     self._keyword.match_case = self._match_case
  #     return self._keyword_service.update_keyword(self._keyword)
  #   else:
  #     new_keyword = Keyword(
  #         name=self._name, match_case=self._match_case, category_id=self._category_id)
  #     return self._keyword_service.add_keyword(new_keyword)

  # @Slot(result=bool)
  # def delete_keyword(self) -> bool:
  #   if self._keyword:
  #     return self._keyword_service.delete_keyword(self._keyword.id)
  #   return False

  def can_delete_keyword(self) -> bool:
    return self._keyword is not None
