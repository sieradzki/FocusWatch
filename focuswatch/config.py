""" Configuration module for FocusWatch. """
import logging
import os
import sys
import yaml
from collections.abc import MutableMapping
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Config(MutableMapping):
  """ Configuration class for FocusWatch """

  def __init__(self, config_file_path: Optional[str] = None):
    self.is_frozen = getattr(sys, "frozen", False)

    if self.is_frozen:
      if sys.platform.startswith("linux"):
        self.project_root = os.path.expanduser("~/.focuswatch")
      elif sys.platform.startswith("win"):
        self.project_root = os.path.join(
          os.getenv("LOCALAPPDATA"), "FocusWatch")
      else:
        raise EnvironmentError("Unsupported platform")

      self.default_config_path = os.path.join(
        self.project_root, "config.yml")
      self.default_database_path = os.path.join(
        self.project_root, "focuswatch.sqlite")
      self.default_logger_config_path = os.path.join(
        sys._MEIPASS, "logging.json")
      self.default_log_path = os.path.join(
        self.project_root, "logs", "focuswatch.log.jsonl")
    else:
      self.project_root = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
      self.default_config_path = os.path.join(
        self.project_root, "config.yml")
      self.default_database_path = os.path.join(
        self.project_root, "focuswatch.sqlite")
      self.default_logger_config_path = os.path.join(
        self.project_root, "logging.json")
      self.default_log_path = os.path.join(
        self.project_root, "logs", "focuswatch.log.jsonl")

    os.makedirs(os.path.dirname(self.default_log_path), exist_ok=True)

    self.config_file_path = config_file_path or self.default_config_path
    self.config = []
    self.load_config()

  def initialize_config(self):
    """ Initialize the configuration file with default values """
    self._config = {
      "General": {
        "watch_interval": 1.0,
        "verbose": 0,
        "watch_afk": True,
        "afk_timeout": 10,
      },
      "Database": {
        "location": self.default_database_path,
      },
      "Logging": {
        "location": self.default_log_path,
        "logger_config": self.default_logger_config_path,
        "log_level": "DEBUG",
      },
    }
    self.write_config_to_file()

  def write_config_to_file(self):
    """ Write the configuration to the configuration file. """
    try:
      os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
      os.makedirs(os.path.dirname(
        self._config["Logging"]["location"]), exist_ok=True)
      with open(self.config_file_path, "w", encoding="utf-8") as config_file:
        yaml.dump(self._config, config_file, default_flow_style=False)
      logger.info("Configuration file written successfully.")
    except FileNotFoundError as e:
      logger.error(f"The configuration file was not found. {e}")
    except IOError as e:
      logger.error(
        f"An error occurred while writing the configuration file. {e}")

  def load_config(self):
    """ Load config from the configuration file. """
    try:
      if not os.path.exists(self.config_file_path):
        logger.info(
          f"Configuration file {
            self.config_file_path} not found. Creating default configuration."
        )
        self.initialize_config()
      else:
        with open(self.config_file_path, "r", encoding="utf-8") as config_file:
          self._config = yaml.safe_load(config_file) or {}
        # Check for required sections
        required_sections = ["General", "Database", "Logging"]
        if not all(section in self._config for section in required_sections):
          logger.info(
            "Missing sections in configuration file. Reinitializing configuration.")
          self.initialize_config()
    except (IOError, yaml.YAMLError) as e:
      logger.error(f"Error loading configuration file: {e}")
      raise

  def set_value(self, section, option, value):
    """ Update the configuration with a new value """
    if section in self.config and option in self.config[section]:
      self.config[section][option] = str(value)
      self.write_config_to_file()
    else:
      return ValueError(f"Section '{section}' or option '{option}' does not exist.")

  def __getitem__(self, key: str) -> Any:
    return self._config[key]

  def __setitem__(self, key: str, value: Any):
    self._config[key] = value
    self.write_config_to_file()

  def __delitem__(self, key: str):
    del self._config[key]
    self.write_config_to_file()

  def __iter__(self):
    return iter(self._config)

  def __len__(self):
    return len(self._config)

  def __repr__(self):
    return f"{self.__class__.__name__}({self._config})"

  """ Legacy methods """

  def set_value(self, section: str, option: str, value: Any):
    """ Update the configuration with a new value. """
    if section in self._config:
      self._config[section][option] = value
      self.write_config_to_file()
    else:
      raise ValueError(f"Section '{section}' does not exist.")

  def get_value(self, section: str, option: str) -> Any:
    """ Get a configuration value. """
    try:
      return self._config[section][option]
    except KeyError:
      raise ValueError(f"Section '{section}' or option '{
                       option}' does not exist.")

  def get_config(self) -> dict:
    """ Get all configuration values. """
    return self._config

  def save(self):
    """ Save the current configuration to the file. """
    self.write_config_to_file()


if __name__ == "__main__":
  config = Config()
  print(config.get_config())
  config.set_value("General", "verbose", "1")
  print(config.get_config())
