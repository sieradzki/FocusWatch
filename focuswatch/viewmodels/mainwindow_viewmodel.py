import logging
from typing import TYPE_CHECKING, List, Tuple

from PySide6.QtCore import QObject, Property, Signal

from focuswatch.viewmodels.categories_viewmodel import \
    CategoriesViewModel
from focuswatch.viewmodels.home_viewmodel import HomeViewModel
from focuswatch.viewmodels.settings_viewmodel import SettingsViewModel

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.classifier_service import ClassifierService
  from focuswatch.services.keyword_service import KeywordService
  from focuswatch.viewmodels.main_viewmodel import MainViewModel

logger = logging.getLogger(__name__)


class MainWindowViewModel(QObject):
  """ ViewModel for the main application window. """

  pages_changed = Signal()
  current_page_index_changed = Signal()
  window_title_changed = Signal()
  window_size_changed = Signal()

  def __init__(self, main_viewmodel: "MainViewModel",
               activity_service: "ActivityService",
               category_service: "CategoryService",
               keyword_service: "KeywordService",
               classifier_service: "ClassifierService"):
    super().__init__()
    self._main_viewmodel = main_viewmodel

    # Initialize services
    self._activity_service = activity_service
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._classifier_service = classifier_service

    # Initialize child viewmodels
    self._settings_viewmodel = SettingsViewModel()
    self._categories_viewmodel = CategoriesViewModel(
        self._activity_service,
        self._category_service,
        self._keyword_service,
        self._classifier_service
    )
    self._home_viewmodel = HomeViewModel(
      self._activity_service,
      self._category_service
    )

    # Initialize properties
    self._pages = ["home", "categories", "settings"]
    self._current_page_index = self.page_index("home")
    self._window_title = "focuswatch"
    self._window_size = (1600, 900)

  @Property("QStringList", notify=pages_changed)
  def pages(self) -> List[str]:
    """ List of page names"""
    return self._pages

  def page_index(self, page_name: str) -> int:
    """ Get the index of a page by name. """
    return self._pages.index(page_name)

  @Property(int, notify=current_page_index_changed)
  def current_page_index(self) -> int:
    """ Index of the current page. """
    return self._current_page_index

  @current_page_index.setter
  def current_page_index(self, value: int) -> None:
    if self._current_page_index != value and 0 <= value < len(self._pages):
      self._current_page_index = value
      self.current_page_index_changed.emit()

  @Property(str, notify=window_title_changed)
  def window_title(self) -> str:
    """ Title of the window. """
    return self._window_title

  @window_title.setter
  def window_title(self, value: str) -> None:
    if self._window_title != value:
      self._window_title = value
      self.window_title_changed.emit()

  @Property("QVariant", notify=window_size_changed)
  def window_size(self) -> Tuple[int, int]:
    """ Size of the window as a tuple (width, height). """
    return self._window_size

  @window_size.setter
  def window_size(self, value: Tuple[int, int]) -> None:
    if self._window_size != value:
      self._window_size = value
      self.window_size_changed.emit()

  @Property(QObject, constant=True)
  def settings_viewmodel(self) -> SettingsViewModel:
    """ ViewModel for the settings page. """
    return self._settings_viewmodel

  @Property(QObject, constant=True)
  def categories_viewmodel(self) -> CategoriesViewModel:
    """ ViewModel for the categories page. """
    return self._categories_viewmodel

  @Property(QObject, constant=True)
  def home_viewmodel(self) -> HomeViewModel:
    """ ViewModel for the home page. """
    return self._home_viewmodel

  def exit_application(self) -> None:
    """Exit the application."""
    pass
