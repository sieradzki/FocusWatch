from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from focuswatch.viewmodels.mainwindow_viewmodel import MainWindowViewModel
from focuswatch.views.mainwindow_view import MainWindowView


@pytest.fixture(scope="session", autouse=True)
def app():
  """ Session-scoped fixture to initialize and finalize QApplication for Qt tests. """
  qapp = QApplication.instance()
  if qapp is None:
    qapp = QApplication([])
  yield qapp
  # Finalize logic
  if not QApplication.instance().thread() == qapp.thread():
    qapp.quit()


class TestMainWindowView:
  """ Test the MainWindowView. """

  @pytest.fixture
  def viewmodel(self):
    """ Fixture to provide a MainWindowViewModel instance. """
    mock_activity_service = MagicMock()
    mock_category_service = MagicMock()
    mock_keyword_service = MagicMock()
    mock_main_viewmodel = MagicMock()
    mock_classifier_service = MagicMock()

    return MainWindowViewModel(
        main_viewmodel=mock_main_viewmodel,
        activity_service=mock_activity_service,
        category_service=mock_category_service,
        keyword_service=mock_keyword_service,
        classifier_service=mock_classifier_service,
    )

  @pytest.fixture
  def window(self, viewmodel):
    """ Fixture to provide an instance of MainWindowView. """
    window = MainWindowView(viewmodel)
    window.show()  # Show the window for testing
    return window

  def test_initialization(self, window):
    """ Test the initial state of the MainWindowView. """
    assert window.windowTitle() == "focuswatch"
    assert window.stacked_widget.currentIndex() == 0  # home page
    assert window.sidebar_button_home.isChecked()
    assert not window.sidebar_button_categories.isChecked()
    assert not window.sidebar_button_settings.isChecked()

  def test_switch_page(self, window):
    """ Test that switching pages updates the UI correctly. """
    window.sidebar_button_categories.click()
    QApplication.processEvents()  # Process events to ensure UI updates
    assert window.stacked_widget.currentIndex() == 1  # categories page
    assert not window.sidebar_button_home.isChecked()
    assert window.sidebar_button_categories.isChecked()
    assert not window.sidebar_button_settings.isChecked()

  def test_property_change_updates_ui(self, window, viewmodel):
    """ Test that ViewModel property changes are reflected in the UI. """
    viewmodel.current_page_index = viewmodel.page_index("settings")
    QApplication.processEvents()  # Process events to ensure UI updates
    assert window.stacked_widget.currentIndex() == 2  # settings page
    assert not window.sidebar_button_home.isChecked()
    assert not window.sidebar_button_categories.isChecked()
    assert window.sidebar_button_settings.isChecked()
