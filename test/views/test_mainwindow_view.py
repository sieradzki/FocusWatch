import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from focuswatch.viewmodels.mainwindow_viewmodel import MainWindowViewModel
from focuswatch.views.mainwindow_view import MainWindowView
from PySide6.QtCore import QSize


@pytest.fixture(scope="session")
def qt_app():
  """ Fixture to initialize QApplication for Qt tests. """
  app = QApplication.instance(
  )  # Check if QApplication already exists - avoid creating multiple instances and crashing the tests
  if app is None:
    app = QApplication([])
  yield app
  if not QApplication.instance().thread() == app.thread():
    app.quit()  # Ensure QApplication is properly quit


@pytest.fixture
def viewmodel():
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
      classifier_service=mock_classifier_service
  )


@pytest.fixture
def main_window(qt_app, viewmodel):
  """ Fixture to provide an instance of MainWindowView. """
  window = MainWindowView(viewmodel)
  window.show()  # Show the window for testing
  return window


def test_initialization(main_window):
  """ Test the initial state of the MainWindowView. """
  assert main_window.windowTitle() == "focuswatch"
  assert main_window.stackedWidget.currentIndex() == 0  # home page
  assert main_window.sidebar_button_home.isChecked()
  assert not main_window.sidebar_button_categories.isChecked()
  assert not main_window.sidebar_button_settings.isChecked()


def test_switch_page(main_window, qt_app):
  """ Test that switching pages updates the UI correctly. """
  main_window.sidebar_button_categories.click()
  qt_app.processEvents()  # Process events to ensure UI updates
  assert main_window.stackedWidget.currentIndex() == 1  # categories page
  assert not main_window.sidebar_button_home.isChecked()
  assert main_window.sidebar_button_categories.isChecked()
  assert not main_window.sidebar_button_settings.isChecked()


def test_property_change_updates_ui(main_window, viewmodel, qt_app):
  """ Test that ViewModel property changes are reflected in the UI. """
  viewmodel.current_page_index = viewmodel.page_index("settings")
  qt_app.processEvents()  # Process events to ensure UI updates
  assert main_window.stackedWidget.currentIndex() == 2  # settings page
  assert not main_window.sidebar_button_home.isChecked()
  assert not main_window.sidebar_button_categories.isChecked()
  assert main_window.sidebar_button_settings.isChecked()


def test_signal_handling(main_window, viewmodel):
  """ Test that signals are connected and handled correctly. """
  # Connect a mock signal handler to check if it is triggered
  mock_handler = MagicMock()
  viewmodel.property_changed.connect(mock_handler)

  # Trigger a property change
  viewmodel.current_page_index = viewmodel.page_index("categories")

  # Check if the mock handler was called
  mock_handler.assert_called_with('_current_page_index')
