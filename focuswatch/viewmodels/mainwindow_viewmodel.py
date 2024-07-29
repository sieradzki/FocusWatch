from focuswatch.viewmodels.base_viewmodel import BaseViewModel
from focuswatch.viewmodels.main_viewmodel import MainViewModel


class MainWindowViewModel(BaseViewModel):
  """ ViewModel for the main application window. """

  def __init__(self, main_viewmodel: MainViewModel):
    super().__init__()
    self._main_viewmodel = main_viewmodel

    self._current_tab = "dashboard"

  @property
  def current_tab(self) -> str:
    return self._current_tab

  @current_tab.setter
  def current_tab(self, value: str) -> None:
    self._set_property('_current_tab', value)

  def switch_tab(self, tab_name: str) -> None:
    """ Switch to a different tab. """
    self.current_tab = tab_name
    pass

  def exit_application(self) -> None:
    """ Exit the application. """
    # self._main_viewmodel.stop_monitoring()
    # save entry? ^
    pass
