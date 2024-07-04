""" Main file for the FocusWatch application. """
import atexit
import json
import logging.config
import logging.handlers
import os
import sys
import threading

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from focuswatch.arguments import parse_arguments
from focuswatch.config import Config
from focuswatch.database.database_manager import DatabaseManager
from focuswatch.ui.home import Home
from focuswatch.ui.tray_settings import TraySettings
from focuswatch.watcher import Watcher

# from qt_material import apply_stylesheet

logger = logging.getLogger(__name__)


def start_watcher(watcher):
  watcher.monitor()


def setup_logging():
  # Get logging file path from config
  config = Config()

  if getattr(sys, 'frozen', False):
    # If the application is frozen (packaged)
    config_file = config.default_logger_config_path
  else:
    # If running in development mode
    config_file = config.get_value("Logging", "logger_config")

  if not os.path.exists(config_file):
    raise FileNotFoundError(
      f"Logging configuration file not found: {config_file}")

  with open(config_file, encoding="utf-8") as f_in:
    log_config = json.load(f_in)

  # Replace the placeholder with the actual log file path
  log_file_path = config.default_log_path
  log_config['handlers']['file_json']['filename'] = log_file_path

  logging.config.dictConfig(log_config)
  queue_handler = logging.getHandlerByName("queue_handler")
  if queue_handler is not None:
    queue_handler.listener.start()
    atexit.register(queue_handler.listener.stop)


def get_icon_path():
  if getattr(sys, 'frozen', False):
    # If the application is frozen (packaged)
    return os.path.join(sys._MEIPASS, "icon.png")
  else:
    # If running in development mode
    return "icon.png"


def main():
  # Setup logging
  setup_logging()

  # Parse the arguments
  args = parse_arguments()

  # Instantiate the DatabaseManager and check if the database exists
  _ = DatabaseManager()

  """ System tray """
  app = QApplication([])

  if not QSystemTrayIcon.isSystemTrayAvailable():
    QMessageBox.critical(
      None, "Systray", "Couldn't detect any system tray on this system.")
    sys.exit(1)

  # Don't quit the application when the window is closed
  app.setQuitOnLastWindowClosed(False)

  # Create the icon
  icon_path = get_icon_path()
  icon = QIcon(icon_path)  # TODO change the icon

  # Create the system tray
  tray = QSystemTrayIcon()
  tray.setIcon(icon)
  tray.setVisible(True)

  # Create the menu
  menu = QMenu()

  # apply_stylesheet(app, theme='dark_blue.xml')

  # Add actions to the menu
  dashboard_window = Home()
  # apply_stylesheet(app, theme='dark_red.xml')
  open_dashboard = QAction("Open")
  open_dashboard.triggered.connect(dashboard_window.show)
  menu.addAction(open_dashboard)

  # Open or hide dashboard on double-click
  tray.activated.connect(
    lambda reason: dashboard_window.hide() if reason == QSystemTrayIcon.Trigger and dashboard_window.isVisible(
    ) else dashboard_window.show() if reason == QSystemTrayIcon.Trigger else None)

  # Settings action
  tray_settings = TraySettings()

  open_settings = QAction("Settings")
  open_settings.triggered.connect(tray_settings.show)
  menu.addAction(open_settings)

  # Logs action (TODO logs not implemented)
  logs = QAction("Log")
  logs.setEnabled(False)
  menu.addAction(logs)

  # Quit action
  quit_action = QAction("Quit")
  quit_action.triggered.connect(app.quit)
  menu.addAction(quit_action)

  # Add menu to the system tray
  tray.setContextMenu(menu)

  # Create the watcher
  watcher = Watcher(args.watch_interval if args.watch_interval else None,
                    args.verbose if args.verbose else None)

  # Create separate thread for the watcher
  watcher_thread = threading.Thread(target=start_watcher, args=(watcher,))
  watcher_thread.daemon = True  # This makes the thread exit when the main program exits
  watcher_thread.start()

  sys.exit(app.exec())


if __name__ == "__main__":
  main()
