""" Configuration module for FocusWatch. """
import configparser
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class Config:
  """ Configuration class for FocusWatch """

  def __init__(self, config_file_path: Optional[str] = None):
    self.project_root = os.path.dirname(
      os.path.dirname(os.path.abspath(__file__)))
    self.default_config_path = os.path.join(
      self.project_root, "config.ini")
    self.config_file_path = config_file_path or self.default_config_path
    self.config = configparser.ConfigParser()
    self.load_config()
    # self.config.read(self.config_file_path)

  def initialize_config(self):
    """ Initialize the configuration file with default values """
    if "General" not in self.config:
      self.config["General"] = {
        "watch_interval": 1.0,
        "verbose": 0,
        "watch_afk": True,
        "afk_timeout": 10
      }
    if "Database" not in self.config:
      self.config["Database"] = {
        "location": os.path.join(self.project_root, "focuswatch.sqlite"),
      }

    if "Logging" not in self.config:
      self.config["Logging"] = {
        "location": os.path.join(self.project_root, "logs", "focuswatch.log.jsonl"),
        "logger_config": os.path.join(self.project_root, "logging.json"),
        "log_level": "DEBUG",
      }

    self.write_config_to_file()

  def write_config_to_file(self):
    """ Write the configuration to the configuration file """
    try:
      os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
      os.makedirs(os.path.dirname(
        self.config["Logging"]["location"]), exist_ok=True)
      with open(self.config_file_path, "w", encoding="utf-8") as config_file:
        self.config.write(config_file)
      logger.info("Configuration file written successfully.")
    except FileNotFoundError as e:
      logger.error(f"The configuration file was not found. {e}.")
    except IOError as e:
      logger.error(
        f"An error occurred while writing the configuration file. {e}.")

  def load_config(self):
    """ Load config from the configuration file """
    try:
      if not os.path.exists(self.config_file_path):
        logger.info(f"Configuration file {
            self.config_file_path} not found. Creating default configuration")
        self.initialize_config()
      else:
        self.config.read(self.config_file_path)
        if "Logging" not in self.config or not os.path.exists(self.config["Logging"].get("location", "")):
          logger.info(
            "Logging file not found. Creating default configuration")
          self.initialize_config()
    except (IOError, configparser.Error) as e:
      logger.error(f"Error loading configuration file: {e}")
      raise

  def set_value(self, section, option, value):
    """ Update the configuration with a new value """
    if section in self.config and option in self.config[section]:
      self.config[section][option] = str(value)
      self.write_config_to_file()
    else:
      return ValueError(f"Section '{section}' or option '{option}' does not exist.")

  def get_value(self, section, option):
    """ Get a configuration value """
    if section in self.config and option in self.config[section]:
      return self.config[section][option]
    else:
      return ValueError(f"Section '{section}' or option '{option}' does not exist.")

  def get_config(self):
    """ Get all configuration values """
    all_config = {}
    for section in self.config.sections():
      all_config[section] = dict(self.config[section])
    return all_config


if __name__ == "__main__":
  config = Config()
  print(config.get_config())
  config.set_value("General", "verbose", "1")
  print(config.get_config())
