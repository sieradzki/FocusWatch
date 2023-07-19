import configparser
import os

CONFIG_DIR_PATH = os.getcwd()
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR_PATH, "config.ini")


def initialize_config(config_file_path=CONFIG_FILE_PATH):
  config = configparser.ConfigParser()

  try:
    # Set default values
    config['General'] = {'watch_interval': 1}
    # TODO allow changing default location
    config['Database'] = {'location': '../', 'name': 'focuswatch.sqlite'}

    # Save configuration to a file
    with open(config_file_path, 'w') as config_file:
      config.write(config_file)

    print("Configuration file initialized successfully.")  # TODO Logging?

  except Exception as e:
    print(f"An error occured while initializing the configuration file. {e}.")


def load_config(config_file_path=CONFIG_FILE_PATH):
  if not os.path.exists(config_file_path):
    print(
      f"Configuration file {config_file_path} not found. Creating default configuration")
    initialize_config()

  config = configparser.ConfigParser()
  config.read(config_file_path)

  return config


if __name__ == '__main__':
  initialize_config()
