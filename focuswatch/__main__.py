import argparse
import sys

from focuswatch.config import load_config
from focuswatch.database import DatabaseManager
from focuswatch.watcher import Watcher


def display_config():
  config = load_config()
  for section in config:
    if section != 'DEFAULT':  # TODO remove default config section
      print(f"[{section}]")
      for key, value in config.items(section):
        print(f"{key} = {value}")


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


def main():
  parser = argparse.ArgumentParser(
    prog="focuswatch",
    description="Activity logging with categorization"
  )

  general_parser = parser.add_argument_group("General")
  categories_parser = parser.add_argument_group("Categories")
  keywords_parser = parser.add_argument_group("Keywords")

  # General arguments
  general_parser.add_argument('--show-config', action='store_true',
                              help='Display current configuraton an exit')
  general_parser.add_argument('-w', '--watch-interval', default=None,
                              help='Watcher interval', type=float)
  general_parser.add_argument('-v', '--verbose', action='store_true',
                              help='Verbose output', default=False)

  # Categories arguments
  categories_parser.add_argument('-c', '--categories', action='store_true',
                                 help='Display existing categories and exit')
  categories_parser.add_argument('--add-category', nargs='+', help="Add a category, PARENT_CATEGORY is optional",
                                 metavar=('CATEGORY', 'PARENT_CATEGORY'))

  # Keywords arguments
  keywords_parser.add_argument(
    '-k', '--keywords', action='store_true', help='Display keywords')
  keywords_parser.add_argument(
    '--add-keyword', nargs=2, help="Add a keyword", metavar=('KEYWORD', 'CATEGORY'))

  # TODO config refactor
  """ Not implemented yet """
  # parser.add_argument('-db', '--db-location',
  #                     dest='db-location', help='Specify database location', type=str)

  # TODO system tray icon
  # parser.add_argument('-t', '--tray', action='store_true',
  # help='Display tray icon')

  # TODO web gui
  # parser.add_argument('-g', '--gui', action='store_true', help='Run with GUI')

  args = parser.parse_args()

  if args.show_config:
    display_config()
    sys.exit()

  if args.categories:
    display_categories()
    sys.exit()

  if args.add_category:
    add_category(args.add_category)
    sys.exit()

  if args.keywords:
    display_keywords()
    sys.exit()

  if args.add_keyword:
    add_keyword(args.add_keyword)
    sys.exit()

  if args.watch_interval:
    watch_interval = args.poll_time
  else:
    config = load_config()
    watch_interval = int(config['General']['watch_interval'])

  watcher = Watcher(args.verbose, watch_interval)
  print("Monitoring...")
  watcher.monitor()


if __name__ == '__main__':
  main()