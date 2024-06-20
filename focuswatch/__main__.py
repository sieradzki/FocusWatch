""" Main file for the FocusWatch application. """
import sys
import threading

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from focuswatch.arguments import parse_arguments
from focuswatch.ui.tray_settings import TraySettings
from focuswatch.ui.home import Home
from focuswatch.watcher import Watcher
from focuswatch.database.database_manager import DatabaseManager

# from qt_material import apply_stylesheet


def start_watcher(watcher):
  # print("Monitoring...")
  watcher.monitor()


def main():
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
  icon = QIcon("icon.png")  # TODO change the icon

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
