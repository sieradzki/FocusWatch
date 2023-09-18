import sys
import threading

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from focuswatch.arguments import parse_arguments
from focuswatch.config import Config
from focuswatch.database import DatabaseManager
from focuswatch.watcher import Watcher


def display_config():
  config = Config()
  config_contents = config.get_all_config()
  for section in config_contents:
    print(f"[{section}]")
    for option, value in config_contents[section].items():
      print(f"{option} = {value}")
    print()


def display_categories():
  db = DatabaseManager()
  categories = db.get_all_categories()
  print(f"{'id'.ljust(4)}{'name'.ljust(15)}{'parent category'.ljust(4)}")
  for category in categories:
    id_str = str(category[0]).ljust(4)
    name_str = str(category[1]).ljust(15)
    parent_category_str = str(category[2]).ljust(4)
    print(f"{id_str}{name_str}{parent_category_str}")


def add_category(category):
  category_name, parent_category = category[0], category[1] if len(
    category) > 1 else None
  db = DatabaseManager()
  if db.create_category(category_name, parent_category):
    display_categories()
  else:
    print("Error creating a category")


def display_keywords():
  db = DatabaseManager()
  keywords = db.get_all_keywords()
  print(f"{'id'.ljust(4)}{'name'.ljust(15)}{'category_id'.ljust(4)}")
  for keyword in keywords:
    id_str = str(keyword[0]).ljust(4)
    name_str = str(keyword[2]).ljust(15)
    category_id_str = str(keyword[1]).ljust(4)
    print(f"{id_str}{name_str}{category_id_str}")


def add_keyword(keyword):
  db = DatabaseManager()
  if db.add_keyword(keyword[0], keyword[1]):
    display_keywords()
  else:
    print("Error adding a keyword")


def start_watcher(watcher):
  print("Monitoring...")
  watcher.monitor()


def main():
  args = parse_arguments()

  # General
  if args.show_config:
    display_config()
    sys.exit()

  # Categories
  if args.categories:
    display_categories()
    sys.exit()

  if args.add_category:
    add_category(args.add_category)
    sys.exit()

  # Keywords
  if args.keywords:
    display_keywords()
    sys.exit()

  if args.add_keyword:
    add_keyword(args.add_keyword)
    sys.exit()

  # Config
  if args.config_wi:
    config = Config()
    config.update_config('General', 'watch_interval', args.config_wi)
    sys.exit()

  if args.config_verbose:
    config = Config()
    config.update_config('General', 'verbose', True)
    sys.exit()

  if args.config_no_verbose:
    config = Config()
    config.update_config('General', 'verbose', False)
    sys.exit()

  if args.config_db:
    config = Config()
    config.update_config('Database', 'location', args.config_db)
    sys.exit()

  """ System tray """
  app = QApplication([])

  if not QSystemTrayIcon.isSystemTrayAvailable():
    QMessageBox.critical(
      None, "Systray", "I couldn't detect any system tray on this system.")
    sys.exit(1)

  app.setQuitOnLastWindowClosed(False)

  # Create the icon
  icon = QIcon("icon.png")

  # Create the system tray
  tray = QSystemTrayIcon()
  tray.setIcon(icon)
  tray.setVisible(True)

  # Create the menu
  menu = QMenu()

  # Add actions to the menu
  # settings = QAction("Settings")
  # menu.addAction(settings)

  webgui = QAction("Open WebGUI")
  menu.addAction(webgui)

  logs = QAction("Open log")
  menu.addAction(logs)

  quit = QAction("Quit")
  quit.triggered.connect(app.quit)
  menu.addAction(quit)

  # Add menu to the system tray
  tray.setContextMenu(menu)

  watcher = Watcher(args.watch_interval if args.watch_interval else None,
                    args.verbose if args.verbose else None)

  # Create separate thread for the watcher
  watcher_thread = threading.Thread(target=start_watcher, args=(watcher,))
  watcher_thread.daemon = True  # This makes the thread exit when the main program exits
  watcher_thread.start()

  sys.exit(app.exec())


if __name__ == '__main__':
  main()
