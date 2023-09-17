import argparse


def parse_arguments():
  parser = argparse.ArgumentParser(
    prog="focuswatch",
    description="Activity logging with categorization"
  )

  general_parser = parser.add_argument_group("General")
  categories_parser = parser.add_argument_group("Categories")
  keywords_parser = parser.add_argument_group("Keywords")
  config_parser = parser.add_argument_group("Config")

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

  # Config arguments
  config_parser.add_argument(
    '--config-wi', help="Change default watch interval", type=float, metavar='WATCH_INTERVAL')
  config_parser.add_argument(
    '--config-verbose', help="Change default verbose to 'on'", action='store_true')
  config_parser.add_argument(
    '--config-no-verbose', help="Change default verbose to 'off'", action='store_true')
  config_parser.add_argument(
    '--config-db', help="Change database location", metavar='DB_LOCATION', type=str
  )

  # TODO system tray icon
  # parser.add_argument('-t', '--tray', action='store_true',
  # help='Display tray icon')

  # TODO web gui
  # parser.add_argument('-g', '--gui', action='store_true', help='Run with GUI')

  args = parser.parse_args()

  return args
