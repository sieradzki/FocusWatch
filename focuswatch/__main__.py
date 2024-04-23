import sys
import threading

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from focuswatch.arguments import parse_arguments
from focuswatch.gui.tray_settings import TraySettings
from focuswatch.gui.dashboard import Dashboard
from focuswatch.watcher import Watcher

# from qt_material import apply_stylesheet


def start_watcher(watcher):
  # print("Monitoring...")
  watcher.monitor()


def main():
  # Parse the arguments
  args = parse_arguments()

  """ System tray """
  app = QApplication([])

  if not QSystemTrayIcon.isSystemTrayAvailable():
    QMessageBox.critical(
      None, "Systray", "I couldn't detect any system tray on this system.")
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
  dashboard_window = Dashboard()
  # apply_stylesheet(app, theme='dark_red.xml')
  open_dashboard = QAction("Open dashboard")
  open_dashboard.triggered.connect(dashboard_window.show)
  menu.addAction(open_dashboard)

  tray_settings = TraySettings()

  open_settings = QAction("Settings")
  open_settings.triggered.connect(tray_settings.show)
  menu.addAction(open_settings)

  logs = QAction("Log")
  logs.setEnabled(False)
  menu.addAction(logs)

  quit = QAction("Quit")
  quit.triggered.connect(app.quit)
  menu.addAction(quit)

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


if __name__ == '__main__':
  main()
