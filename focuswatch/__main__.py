""" Main file for the FocusWatch application. """
import logging.config
import logging.handlers
import os
import shutil
import sys
import threading

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from focuswatch.arguments import parse_arguments
from focuswatch.database.database_manager import DatabaseManager
from focuswatch.services.activity_service import ActivityService
from focuswatch.services.category_service import CategoryService
from focuswatch.services.keyword_service import KeywordService
from focuswatch.services.watcher_service import WatcherService
from focuswatch.utils.resource_utils import apply_stylesheet
from focuswatch.viewmodels.main_viewmodel import MainViewModel
from focuswatch.viewmodels.mainwindow_viewmodel import MainWindowViewModel
from focuswatch.views.mainwindow_view import MainWindowView
from focuswatch.services.classifier_service import ClassifierService
from focuswatch.logger import setup_logging

# from qt_material import apply_stylesheet

logger = logging.getLogger(__name__)


def start_watcher(watcher):
  logger.info("Starting the watcher")
  watcher.monitor()


def get_icon_path():
  if getattr(sys, "frozen", False):
    # If the application is frozen (packaged)
    return os.path.join(sys._MEIPASS, "icon.png")
  else:
    # If running in development mode
    return "icon.png"


def check_dependencies():
  # Linux dependencies
  if sys.platform.startswith("linux"):
    dependencies = ["xdotool", "xprintidle"]
    for dep in dependencies:
      if not shutil.which(dep):
        print(f"Error: {dep} is not installed.", file=sys.stderr)
        logger.error(f"Error: {dep} is not installed.")
        sys.exit(1)
  logger.info("Dependencies are met.")


def main():
  logger.info("Starting FocusWatch")
  check_dependencies()
  setup_logging()
  args = parse_arguments()

  # Instantiate the DatabaseManager and check if the database exists
  _ = DatabaseManager()

  logger.info("Creating QApplication")
  app = QApplication([])

  # TODO theme.qss ?
  apply_stylesheet(app, "mainwindow.qss")

  if not QSystemTrayIcon.isSystemTrayAvailable():
    # TODO retry - in wms like dwm tray might be not immediately available
    QMessageBox.critical(
      None, "Systray", "Couldn't detect any system tray on this system.")
    logger.error("Couldn't detect any system tray on this system.")
    sys.exit(1)

  # Don't quit the application when the window is closed
  app.setQuitOnLastWindowClosed(False)

  # Create the icon
  icon_path = get_icon_path()
  icon = QIcon(icon_path)  # TODO change the icon

  # Create the system tray
  logger.info("Creating the system tray")
  tray = QSystemTrayIcon()
  tray.setIcon(icon)
  tray.setVisible(True)

  # Create the menu
  menu = QMenu()

  # Create Services, ViewModels and MainWindowView
  activity_service = ActivityService()
  category_service = CategoryService()
  keyword_service = KeywordService()
  classifier_service = ClassifierService(category_service, keyword_service)

  watcher_service = WatcherService(
    activity_service,
    category_service,
    classifier_service,
    args.watch_interval if args.watch_interval else None,
    args.verbose if args.verbose else None, )

  main_viewmodel = MainViewModel(
    watcher_service, activity_service, category_service, keyword_service)

  mainwindow_viewmodel = MainWindowViewModel(
      main_viewmodel, activity_service, category_service, keyword_service, classifier_service)
  main_window = MainWindowView(mainwindow_viewmodel)

  # Add actions to the menu
  open_mainwindow = QAction("Open")
  open_mainwindow .triggered.connect(main_window.show)
  menu.addAction(open_mainwindow)

  # Open or hide home on double-click
  tray.activated.connect(
      lambda reason: main_window.hide() if reason == QSystemTrayIcon.Trigger and main_window.isVisible()
      else main_window.show() if reason == QSystemTrayIcon.Trigger else None
  )

  # Logs action
  # logs = QAction("Log")
  # logs.setEnabled(False)
  # menu.addAction(logs)

  # Quit action
  quit_action = QAction("Quit")
  quit_action.triggered.connect(app.quit)
  menu.addAction(quit_action)

  # Add menu to the system tray
  tray.setContextMenu(menu)

  # Create separate thread for the watcher
  watcher_thread = threading.Thread(
    target=start_watcher, args=(watcher_service,))
  watcher_thread.daemon = True  # This makes the thread exit when the main program exits
  watcher_thread.start()

  sys.exit(app.exec())


if __name__ == "__main__":
  main()
