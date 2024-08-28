from typing import TYPE_CHECKING, List, Tuple

from PySide6.QtCore import Property

from focuswatch.viewmodels.base_viewmodel import BaseViewModel
from focuswatch.viewmodels.categorization_viewmodel import \
    CategorizationViewModel
from focuswatch.viewmodels.dashboard_viewmodel import DashboardViewModel
from focuswatch.viewmodels.settings_viewmodel import SettingsViewModel

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.keyword_service import KeywordService
  from focuswatch.viewmodels.main_viewmodel import MainViewModel


class MainWindowViewModel(BaseViewModel):
  """ ViewModel for the main application window. """

  def __init__(self, main_viewmodel: 'MainViewModel',
               activity_service: 'ActivityService',
               category_service: 'CategoryService',
               keyword_service: 'KeywordService'):
    super().__init__()
    self._main_viewmodel = main_viewmodel

    # Initialize services
    self._activity_service = activity_service
    self._category_service = category_service
    self._keyword_service = keyword_service

    # Initialize child viewmodels
    self._settings_viewmodel = SettingsViewModel()
    self._categorization_viewmodel = CategorizationViewModel(
      activity_service, category_service, keyword_service)
    self._dashboard_viewmodel = DashboardViewModel(
      activity_service, category_service)

    # Initialize properties
    self._current_tab_index = 0
    self._tab_names = ["Dashboard", "Categorization", "Settings"]
    self._window_title = "FocusWatch"
    self._window_size = (1600, 900)

  @Property(int, notify=BaseViewModel.property_changed)
  def current_tab_index(self) -> int:
    return self._current_tab_index

  @current_tab_index.setter
  def current_tab_index(self, value: int) -> None:
    if 0 <= value < len(self._tab_names):
      self._set_property('_current_tab_index', value)

  @Property(list, notify=BaseViewModel.property_changed)
  def tab_names(self) -> List[str]:
    return self._tab_names

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
  def dashboard_viewmodel(self) -> DashboardViewModel:
    return self._dashboard_viewmodel

  def switch_tab(self, index: int) -> None:
    """Switch to a different tab."""
    self.current_tab_index = index

  def exit_application(self) -> None:
    """Exit the application."""
    # self._main_viewmodel.stop_monitoring()
    pass
