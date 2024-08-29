import logging
from typing import TYPE_CHECKING, List, Tuple

from PySide6.QtCore import Property

from focuswatch.viewmodels.base_viewmodel import BaseViewModel
from focuswatch.viewmodels.categorization_viewmodel import \
    CategorizationViewModel
from focuswatch.viewmodels.home_viewmodel import HomeViewModel
from focuswatch.viewmodels.settings_viewmodel import SettingsViewModel

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.classifier_service import ClassifierService
  from focuswatch.services.keyword_service import KeywordService
  from focuswatch.viewmodels.main_viewmodel import MainViewModel

logger = logging.getLogger(__name__)


class MainWindowViewModel(BaseViewModel):
  """ ViewModel for the main application window. """

  def __init__(self, main_viewmodel: 'MainViewModel',
               activity_service: 'ActivityService',
               category_service: 'CategoryService',
               keyword_service: 'KeywordService',
               classifier_service: 'ClassifierService'):
    super().__init__()
    self._main_viewmodel = main_viewmodel

    # Initialize services
    self._activity_service = activity_service
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._classifier_service = classifier_service

    # Initialize child viewmodels
    self._settings_viewmodel = SettingsViewModel()
    self._categorization_viewmodel = CategorizationViewModel(
        activity_service, category_service, keyword_service, self._classifier_service)
    self._home_viewmodel = HomeViewModel(
      activity_service, category_service)

    # Initialize properties
    self._pages = ["home", "categories", "settings"]
    self._current_page_index = self.page_index("home")
    self._window_title = "focuswatch"
    self._window_size = (1600, 900)

  @Property(list, notify=BaseViewModel.property_changed)
  def pages(self) -> List[str]:
    return self._pages

  def page_index(self, page_name: str) -> int:
    return self._pages.index(page_name)

  @Property(int, notify=BaseViewModel.property_changed)
  def current_page_index(self) -> int:
    return self._current_page_index

  @current_page_index.setter
  def current_page_index(self, value: int) -> None:
    if value in range(len(self._pages)):
      self._set_property('_current_page_index', value)

  @Property(str, notify=BaseViewModel.property_changed)
  def window_title(self) -> str:
    return self._window_title

  @Property(tuple, notify=BaseViewModel.property_changed)
  def window_size(self) -> Tuple[int, int]:
    return self._window_size

  @window_size.setter
  def window_size(self, value: Tuple[int, int]) -> None:
    self._set_property('_window_size', value)

  @Property('QVariant', notify=BaseViewModel.property_changed)
  def settings_viewmodel(self) -> SettingsViewModel:
    return self._settings_viewmodel

  @Property('QVariant', notify=BaseViewModel.property_changed)
  def categorization_viewmodel(self) -> CategorizationViewModel:
    return self._categorization_viewmodel

  @Property('QVariant', notify=BaseViewModel.property_changed)
  def home_viewmodel(self) -> HomeViewModel:
    return self._home_viewmodel

  def exit_application(self) -> None:
    """Exit the application."""
    pass
