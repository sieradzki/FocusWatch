from typing import List, Tuple, TYPE_CHECKING
from PySide6.QtCore import QObject, Signal, Property
import logging

from focuswatch.services.categorization_service import CategorizationService
from focuswatch.models.keyword import Keyword

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.keyword_service import KeywordService
  from focuswatch.services.classifier_service import ClassifierService

logger = logging.getLogger(__name__)


class CategorizationHelperDialogViewModel(QObject):
  property_changed = Signal(str)
  retroactive_categorization_progress = Signal(int, int)

  def __init__(self,
               activity_service: "ActivityService",
               category_service: "CategoryService",
               keyword_service: "KeywordService",
               classifier: 'ClassifierService'
               ):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._classifier = classifier
    self._categorization_service = CategorizationService(
      self._activity_service, self._classifier)

    self.categories = []
    self._uncategorized_window_classes = []
    self._uncategorized_window_names = []
    self._limit = 20
    self._offset_classes = 0
    self._offset_names = 0
    self.has_more_classes = True
    self.has_more_names = True
    self._threshold_seconds = 60

  def load_categories(self):
    self.categories = self._category_service.get_all_categories()
    self.property_changed.emit('categories')

  def load_window_classes(self):
    """ Load uncategorized window classes into the ViewModel. """
    new_entries = self._activity_service.get_top_uncategorized_window_classes(
        limit=self._limit,
        offset=self._offset_classes,
        threshold_seconds=self._threshold_seconds
    )
    if new_entries:
      self._uncategorized_window_classes.extend(new_entries)
      self._offset_classes += len(new_entries)
      if len(new_entries) < self._limit:
        self.has_more_classes = False
        self.property_changed.emit('no_more_window_classes')
      else:
        self.has_more_classes = True
      self.property_changed.emit('uncategorized_window_classes')
    else:
      self.has_more_classes = False
      self.property_changed.emit('no_more_window_classes')

  def load_window_names(self):
    """ Load uncategorized window names into the ViewModel. """
    new_entries = self._activity_service.get_top_uncategorized_window_names(
        limit=self._limit,
        offset=self._offset_names,
        threshold_seconds=self._threshold_seconds
    )
    if new_entries:
      self._uncategorized_window_names.extend(new_entries)
      self._offset_names += len(new_entries)
      if len(new_entries) < self._limit:
        self.has_more_names = False
        self.property_changed.emit('no_more_window_names')
      else:
        self.has_more_names = True
      self.property_changed.emit('uncategorized_window_names')
    else:
      self.has_more_names = False
      self.property_changed.emit('no_more_window_names')

  @property
  def uncategorized_window_classes(self):
    return self._uncategorized_window_classes

  @property
  def uncategorized_window_names(self):
    return self._uncategorized_window_names

  def save_categorization(self, activity_name: str, category_id: int, match_case: bool, save_as_keyword: bool):
    """ Classify entries with activity_name or save as a new keyword """

    if save_as_keyword:
      keyword = Keyword(name=activity_name,
                        category_id=category_id, match_case=match_case)

      self._keyword_service.add_keyword(keyword)
    else:
      self._activity_service.bulk_update_category_by_name(
        activity_name, category_id)

  def perform_retroactive_categorization(self):
    return self._categorization_service.retroactive_categorization(
      progress_callback=self.retroactive_categorization_progress.emit
    )
