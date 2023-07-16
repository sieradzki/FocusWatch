import configparser
import os

CONFIG_DIR_PATH = os.getcwd()
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR_PATH, "config.ini")

def initialize_config():
  if os.path.exists(CONFIG_FILE_PATH):
    return

  config = configparser.ConfigParser()

  try:
    # Set default values
    config['General'] = {'watch_interval': 1}
    config['Database'] = {'location': '../', 'name': 'focuswatch.sqlite'} # temporary location for dev purposes

    # Save configuration to a file
    with open(CONFIG_FILE_PATH, 'w') as config_file:
      config.write(config_file)

    print("Configuration file initialized successfully.") # Logging module?
  
  except Exception as e:
    print(f" An error occured while initializing the configuration file: {e}")

def load_config():
  if not os.path.exists(CONFIG_FILE_PATH):
    print(f"Configuration file {CONFIG_FILE_PATH} not found. Creating default configuration")
    initialize_config()

  config = configparser.ConfigParser()
  config.read(CONFIG_FILE_PATH)

  return config

if __name__ == '__main__':
  initialize_config()