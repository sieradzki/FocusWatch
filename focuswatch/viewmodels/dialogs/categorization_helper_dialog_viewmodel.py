import logging
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Property, QObject, Signal

from focuswatch.database.models.keyword import Keyword
from focuswatch.services.categorization_service import CategorizationService

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.classifier_service import ClassifierService
  from focuswatch.services.keyword_service import KeywordService

logger = logging.getLogger(__name__)


class CategorizationHelperDialogViewModel(QObject):
  """ ViewModel for the CategorizationHelperDialog. """
  categories_changed = Signal()
  has_more_classes_changed = Signal()
  has_more_names_changed = Signal()
  uncategorized_window_classes_changed = Signal()
  uncategorized_window_names_changed = Signal()
  retroactive_categorization_progress = Signal(int, int)

  def __init__(
      self,
      activity_service: "ActivityService",
      category_service: "CategoryService",
      keyword_service: "KeywordService",
      classifier: "ClassifierService"
  ):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._classifier = classifier
    self._categorization_service = CategorizationService(
      self._activity_service, self._classifier)

    self._categories: List = []
    self._uncategorized_window_classes: List = []
    self._uncategorized_window_names: List = []
    self._limit = 20
    self._offset_classes = 0
    self._offset_names = 0
    self._has_more_classes = True
    self._has_more_names = True
    self._threshold_seconds = 60

  @Property(list, notify=categories_changed)
  def categories(self) -> List:
    """ List of all categories. """
    return self._categories

  @Property(bool, notify=has_more_classes_changed)
  def has_more_classes(self) -> bool:
    """ Indicates if there are more uncategorized window classes to load. """
    return self._has_more_classes

  @Property(bool, notify=has_more_names_changed)
  def has_more_names(self) -> bool:
    """ Indicates if there are more uncategorized window names to load. """
    return self._has_more_names

  @Property(list, notify=uncategorized_window_classes_changed)
  def uncategorized_window_classes(self) -> List:
    """ List of uncategorized window classes. """
    return self._uncategorized_window_classes

  @Property(list, notify=uncategorized_window_names_changed)
  def uncategorized_window_names(self) -> List:
    """ List of uncategorized window names. """
    return self._uncategorized_window_names

  def load_categories(self) -> None:
    """ Load all categories into the ViewModel. """
    self._categories = self._category_service.get_all_categories()
    self.categories_changed.emit()

  def load_window_classes(self) -> None:
    """ Load uncategorized window classes into the ViewModel. """
    new_entries = self._activity_service.get_top_uncategorized_window_classes(
        limit=self._limit,
        offset=self._offset_classes,
        threshold_seconds=self._threshold_seconds
    )
    if new_entries:
      self._uncategorized_window_classes.extend(new_entries)
      self._offset_classes += len(new_entries)
      self._has_more_classes = len(new_entries) >= self._limit
      self.has_more_classes_changed.emit()
      self.uncategorized_window_classes_changed.emit()
    else:
      self._has_more_classes = False
      self.has_more_classes_changed.emit()

  def load_window_names(self) -> None:
    """ Load uncategorized window names into the ViewModel. """
    new_entries = self._activity_service.get_top_uncategorized_window_names(
        limit=self._limit,
        offset=self._offset_names,
        threshold_seconds=self._threshold_seconds
    )
    if new_entries:
      self._uncategorized_window_names.extend(new_entries)
      self._offset_names += len(new_entries)
      self._has_more_names = len(new_entries) >= self._limit
      self.has_more_names_changed.emit()
      self.uncategorized_window_names_changed.emit()
    else:
      self._has_more_names = False
      self.has_more_names_changed.emit()

  def save_categorization(
      self,
      activity_name: str,
      category_id: int,
      match_case: bool,
      save_as_keyword: bool
  ) -> None:
    """ Classify entries with activity_name or save as a new keyword. """
    if save_as_keyword:
      keyword = Keyword(
          name=activity_name,
          category_id=category_id,
          match_case=match_case
      )
      self._keyword_service.add_keyword(keyword)
    else:
      self._activity_service.bulk_update_category_by_name(
          activity_name, category_id)

  def perform_retroactive_categorization(self) -> None:
    """ Perform retroactive categorization of activities. """
    self._categorization_service.retroactive_categorization(
        progress_callback=self.retroactive_categorization_progress.emit
    )
