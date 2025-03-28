""" Configuration module for FocusWatch. """
import logging
import os
import sys
from collections.abc import MutableMapping
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


class Config(MutableMapping):
  """ Configuration class for FocusWatch """
  DEFAULT_CONFIG = {
    "general": {
      "watch_interval": 1.0,
      "verbose": 0,
      "watch_afk": True,
      "afk_timeout": 10,
      "start_minimized": False,
    },
    "database": {
      "location": None,
    },
    "logging": {
      "location": None,
      "logger_config": None,
      "log_level": "DEBUG",
    },
    "dashboard": {
      "focused_target_day": 8.0,
      "focused_target_week": 40.0,
      "focused_target_month": 160.0,
      "focused_target_year": 1920.0,
      "distracted_goal": 20.0,
      "display_cards_idle": True,
      "display_timeline_idle": True,
    }
  }

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

    self.DEFAULT_CONFIG["database"]["location"] = self.default_database_path
    self.DEFAULT_CONFIG["logging"]["location"] = self.default_log_path
    self.DEFAULT_CONFIG["logging"]["logger_config"] = self.default_logger_config_path

    self.config_file_path = config_file_path or self.default_config_path
    self.load_config()

  def initialize_config(self):
    """ Initialize the configuration file with default values """
    self._config = self.DEFAULT_CONFIG.copy()
    self.write_config_to_file()

  def write_config_to_file(self):
    """ Write the configuration to the configuration file. """
    try:
      os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
      os.makedirs(os.path.dirname(
        self._config["logging"]["location"]), exist_ok=True)
      with open(self.config_file_path, "w", encoding="utf-8") as config_file:
        yaml.dump(self._config, config_file, default_flow_style=False)
      # logger.info("Configuration file written successfully.")
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
        required_sections = self.DEFAULT_CONFIG.keys()
        if not all(section in self._config for section in required_sections):
          logger.info(
            "Missing sections in configuration file. Reinitializing configuration.")
          self.initialize_config()
          return

        self._validate_config_keys()

    except (IOError, yaml.YAMLError) as e:
      logger.error(f"Error loading configuration file: {e}")
      raise

  def _validate_config_keys(self):
    """ Check and optionally add missing sections/keys in the loaded config. """
    updated = False
    for section, defaults in self.DEFAULT_CONFIG.items():
      if section not in self._config:
        logger.warning(
          f"Section '{section}' missing from config. Adding with defaults: {defaults}")
        self._config[section] = defaults.copy()
        updated = True
        continue
      for key, default_value in defaults.items():
        if key not in self._config[section]:
          logger.warning(
            f"Key '{key}' missing in section '{section}' of config file {self.config_file_path}. "
            f"Adding default value: {default_value}"
          )
          self._config[section][key] = default_value
          updated = True
    if updated:
      self.write_config_to_file()

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


if __name__ == "__main__":
  config = Config()
  print(config)
