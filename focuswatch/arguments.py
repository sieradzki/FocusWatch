""" Command line arguments for the focuswatch application. """
import argparse
import sys

from focuswatch import __version__
from focuswatch.config import Config
from focuswatch.services.category_service import CategoryService
from focuswatch.services.keyword_service import KeywordService


def display_config():
  """ Display the current configuration """
  config = Config()
  config_contents = config
  for section in config_contents:
    print(f"[{section}]")
    for option, value in config_contents[section].items():
      print(f"{option} = {value}")
    print()


def display_categories():
  """ Display all categories from the database """
  category_service = CategoryService()
  categories = category_service.get_all_categories()
  print(f"{"id".ljust(4)}{"name".ljust(15)}{"parent category".ljust(4)}")
  for category in categories:
    id_str = str(category[0]).ljust(4)
    name_str = str(category[1]).ljust(15)
    parent_category_str = str(category[2]).ljust(4)
    print(f"{id_str}{name_str}{parent_category_str}")


def add_category(category):
  """ Add a category to the database """
  category_name, parent_category = category[0], int(category[1]) if len(
    category) > 1 else None
  category_service = CategoryService()
  if category_service.create_category(category_name, parent_category):
    display_categories()
  else:
    print("Error creating a category")


def display_keywords():
  """ Display all keywords from the database """
  keyword_service = KeywordService()
  keywords = keyword_service.get_all_keywords()
  print(f"{"id".ljust(4)}{"name".ljust(15)}{"category_id".ljust(4)}")
  for keyword in keywords:
    id_str = str(keyword[0]).ljust(4)
    name_str = str(keyword[1]).ljust(15)
    category_id_str = str(keyword[2]).ljust(4)
    print(f"{id_str}{name_str}{category_id_str}")


def add_keyword(keyword):
  """ Add a keyword to the database """
  keyword_service = KeywordService()
  if keyword_service.add_keyword(keyword[0], keyword[1]):
    display_keywords()
  else:
    print("Error adding a keyword")


def parse_arguments():
  """ Parse the arguments """
  parser = argparse.ArgumentParser(
    prog="focuswatch",
    description="Activity logging with categorization"
  )

  parser.add_argument("--version", action="version",
                      version=f"%(prog)s {__version__}")

  general_parser = parser.add_argument_group("General")
  categories_parser = parser.add_argument_group("Categories")
  keywords_parser = parser.add_argument_group("Keywords")
  config_parser = parser.add_argument_group("Config")

  # General arguments
  general_parser.add_argument("--show-config", action="store_true",
                              help="Display current configuraton and exit")
  general_parser.add_argument("-w", "--watch-interval", default=None,
                              help="Watcher interval", type=float)
  general_parser.add_argument("-v", "--verbose", action="store_true",
                              help="Verbose output", default=False)

  # Categories arguments
  categories_parser.add_argument("-c", "--categories", action="store_true",
                                 help="Display existing categories and exit")
  categories_parser.add_argument("--add-category", nargs="+", help="Add a category, PARENT_CATEGORY is optional",
                                 metavar=("CATEGORY", "PARENT_CATEGORY"))

  # Keywords arguments
  keywords_parser.add_argument(
    "-k", "--keywords", action="store_true", help="Display keywords")
  keywords_parser.add_argument(
    "--add-keyword", nargs=2, help="Add a keyword", metavar=("KEYWORD", "CATEGORY"))

  # Config arguments
  config_parser.add_argument(
    "--config-wi", help="Change default watch interval", type=float, metavar="WATCH_INTERVAL")
  config_parser.add_argument(
    "--config-verbose", help="Change default verbose to 'on'", action="store_true")
  config_parser.add_argument(
    "--config-no-verbose", help="Change default verbose to 'off'", action="store_true")
  config_parser.add_argument(
    "--config-db", help="Change database location", metavar="DB_LOCATION", type=str
  )

  args = parser.parse_args()

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
    config["general"]["watch_interval"] = args.config_wi
    sys.exit()

  if args.config_verbose:
    config = Config()
    config["general"]["verbose"] = True
    sys.exit()

  if args.config_no_verbose:
    config = Config()
    config["general"]["verbose"] = False
    sys.exit()

  if args.config_db:
    config = Config()
    config["database"]["location"] = args.config_db
    sys.exit()

  return args
