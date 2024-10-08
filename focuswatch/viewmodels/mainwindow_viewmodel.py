from typing import List

from focuswatch.services.activity_service import ActivityService
from focuswatch.services.category_service import CategoryService
from focuswatch.services.keyword_service import KeywordService
from focuswatch.viewmodels.base_viewmodel import BaseViewModel
from focuswatch.viewmodels.main_viewmodel import MainViewModel
from focuswatch.viewmodels.settings_viewmodel import SettingsViewModel
from focuswatch.viewmodels.categorization_viewmodel import CategorizationViewModel
from focuswatch.viewmodels.dashboard_viewmodel import DashboardViewModel


class MainWindowViewModel(BaseViewModel):
  """ ViewModel for the main application window. """

  def __init__(self, main_viewmodel: MainViewModel,
               activity_service: ActivityService,
               category_service: CategoryService,
               keyword_service: KeywordService):
    super().__init__()
    self._main_viewmodel = main_viewmodel
    self._activity_service = activity_service
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._settings_viewmodel = SettingsViewModel()
    self._categorization_viewmodel = CategorizationViewModel(
      activity_service, category_service, keyword_service)
    self._dashboard_viewmodel = DashboardViewModel(
      activity_service, category_service)

    self._current_tab_index = 0
    self._tab_names = ["Dashboard", "Categorization", "Settings"]
    self._window_title = "FocusWatch"
    self._window_size = (1600, 900)

  @property
  def current_tab_index(self) -> int:
    return self._current_tab_index

  @current_tab_index.setter
  def current_tab_index(self, value: int) -> None:
    if 0 <= value < len(self._tab_names):
      self._set_property('_current_tab_index', value)

  @property
  def tab_names(self) -> List[str]:
    return self._tab_names

  @property
  def window_title(self) -> str:
    return self._window_title

  @property
  def window_size(self) -> tuple[int, int]:
    return self._window_size

  @window_size.setter
  def window_size(self, value: tuple[int, int]) -> None:
    self._set_property('_window_size', value)

  def get_activity_service(self) -> ActivityService:
    return self._activity_service

  def get_category_service(self) -> CategoryService:
    return self._category_service

  def get_keyword_service(self) -> KeywordService:
    return self._keyword_service

  def get_settings_viewmodel(self) -> SettingsViewModel:
    return self._settings_viewmodel

  def get_categorization_viewmodel(self) -> CategorizationViewModel:
    return self._categorization_viewmodel

  def get_dashboard_viewmodel(self) -> DashboardViewModel:
    return self._dashboard_viewmodel

  def switch_tab(self, index: int) -> None:
    """Switch to a different tab."""
    self.current_tab_index = index

  def exit_application(self) -> None:
    """Exit the application."""
    # self._main_viewmodel.stop_monitoring()
    pass
