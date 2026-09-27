""" Main file for the FocusWatch application. """
import logging.config
import logging.handlers
import os
import shutil
import sys
import threading

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPalette
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from focuswatch.arguments import parse_arguments
from focuswatch.config import Config
from focuswatch.database.database_manager import DatabaseManager
from focuswatch.logger import setup_logging
from focuswatch.services.activity_service import ActivityService
from focuswatch.services.category_service import CategoryService
from focuswatch.services.classifier_service import ClassifierService
from focuswatch.services.keyword_service import KeywordService
from focuswatch.services.project_service import ProjectService
from focuswatch.services.task_service import TaskService
from focuswatch.services.watcher_service import WatcherService
from focuswatch.utils.resource_utils import apply_stylesheet
from focuswatch.viewmodels.main_viewmodel import MainViewModel
from focuswatch.viewmodels.mainwindow_viewmodel import MainWindowViewModel
from focuswatch.views.mainwindow_view import MainWindowView

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

  # Set a dark palette so internal Qt widgets (like combo popup containers)
  # that fall back to palette instead of QSS don't show white artifacts.
  dark_palette = QPalette()
  dark_palette.setColor(QPalette.ColorRole.Window, QColor("#1b1c1e"))
  dark_palette.setColor(QPalette.ColorRole.WindowText, QColor("#F9F9F9"))
  dark_palette.setColor(QPalette.ColorRole.Base, QColor("#1b1c1e"))
  dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#1b1c1e"))
  dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1b1c1e"))
  dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#F9F9F9"))
  dark_palette.setColor(QPalette.ColorRole.Text, QColor("#F9F9F9"))
  dark_palette.setColor(QPalette.ColorRole.Button, QColor("#1b1c1e"))
  dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor("#F9F9F9"))
  dark_palette.setColor(QPalette.ColorRole.BrightText, QColor("#F9F9F9"))
  dark_palette.setColor(QPalette.ColorRole.Highlight, QColor("#334a7a"))
  dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#F9F9F9"))
  dark_palette.setColor(QPalette.ColorRole.Light, QColor("#2a2c2f"))
  dark_palette.setColor(QPalette.ColorRole.Midlight, QColor("#232527"))
  dark_palette.setColor(QPalette.ColorRole.Dark, QColor("#111213"))
  dark_palette.setColor(QPalette.ColorRole.Mid, QColor("#1b1c1e"))
  dark_palette.setColor(QPalette.ColorRole.Shadow, QColor("#000000"))
  app.setPalette(dark_palette)

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
  project_service = ProjectService()
  task_service = TaskService()

  watcher_service = WatcherService(
    activity_service,
    category_service,
    classifier_service,
    args.watch_interval if args.watch_interval else None,
    args.verbose if args.verbose else None, )

  main_viewmodel = MainViewModel(
    watcher_service, activity_service, category_service, keyword_service)

  mainwindow_viewmodel = MainWindowViewModel(
      main_viewmodel, activity_service, category_service, keyword_service, classifier_service, project_service, task_service)
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

  config = Config()
  if not config["general"]["start_minimized"]:
    main_window.show()

  sys.exit(app.exec())


if __name__ == "__main__":
  main()
