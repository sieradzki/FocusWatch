import unittest
from unittest.mock import MagicMock
from focuswatch.viewmodels.mainwindow_viewmodel import MainWindowViewModel
from focuswatch.viewmodels.settings_viewmodel import SettingsViewModel
from focuswatch.viewmodels.categories_viewmodel import CategoriesViewModel
from focuswatch.viewmodels.home_viewmodel import HomeViewModel
from focuswatch.services.classifier_service import ClassifierService


class TestMainWindowViewModel(unittest.TestCase):
  PAGES = ["home", "categories", "settings"]

  def setUp(self) -> None:
    self.mock_activity_service = MagicMock()
    self.mock_category_service = MagicMock()
    self.mock_keyword_service = MagicMock()
    self.mock_main_viewmodel = MagicMock()
    self.mock_classifier_service = MagicMock()

    self.viewmodel = MainWindowViewModel(
        main_viewmodel=self.mock_main_viewmodel,
        activity_service=self.mock_activity_service,
        category_service=self.mock_category_service,
        keyword_service=self.mock_keyword_service,
        classifier_service=self.mock_classifier_service
    )

  def test_initialization(self) -> None:
    """ Test that the MainWindowViewModel initializes correctly. """
    self.assertEqual(self.viewmodel.pages, self.PAGES)
    self.assertEqual(self.viewmodel.current_page_index,
                     self.viewmodel.page_index("home"))
    self.assertEqual(self.viewmodel.window_title, "focuswatch")
    self.assertEqual(self.viewmodel.window_size, (1600, 900))
    self.assertIsInstance(
        self.viewmodel.settings_viewmodel, SettingsViewModel)
    self.assertIsInstance(
        self.viewmodel.categories_viewmodel, CategoriesViewModel)
    self.assertIsInstance(
        self.viewmodel.home_viewmodel, HomeViewModel)

  def test_page_index(self) -> None:
    """ Test that the page index method returns the correct index. """
    for page in self.PAGES:
      self.assertEqual(self.viewmodel.page_index(
          page), self.PAGES.index(page))

  def test_current_page_index_getter(self) -> None:
    """ Test that the current_page_index property returns the correct value. """
    self.assertEqual(self.viewmodel.current_page_index, 0)

  def test_current_page_index_setter(self) -> None:
    """ Test that the current_page_index property sets the correct value. """
    self.viewmodel.current_page_index = 1
    self.assertEqual(self.viewmodel.current_page_index, 1)

  def test_current_page_index_setter_out_of_bounds(self) -> None:
    """ Test that the current_page_index property remains unchanged if the value is out of bounds. """
    self.viewmodel.current_page_index = -1
    self.assertEqual(self.viewmodel.current_page_index, 0)

    self.viewmodel.current_page_index = len(self.PAGES)
    self.assertEqual(self.viewmodel.current_page_index, 0)

  def test_window_title_property(self) -> None:
    """ Test that the window_title property returns the correct value. """
    self.assertEqual(self.viewmodel.window_title, "focuswatch")

  def test_window_size_property(self) -> None:
    """ Test that the window_size property returns the correct value. """
    self.assertEqual(self.viewmodel.window_size, (1600, 900))
    self.viewmodel.window_size = (800, 600)
    self.assertEqual(self.viewmodel.window_size, (800, 600))

  def test_exit_application(self) -> None:
    """ Test that the exit_application method does not raise an error. 
    In the future test that it closes the application, stops the watcher and saves the last entry. 
    """
    self.viewmodel.exit_application()  # Just ensure it doesn't raise an error


if __name__ == "__main__":
  unittest.main()
