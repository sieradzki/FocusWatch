""" ViewModel for settings view. """
import logging
from typing import Any, Dict, List, Tuple

from PySide6.QtCore import Property, QObject, Signal

from focuswatch.autostart_manager import (add_to_autostart, is_frozen,
                                          is_in_autostart,
                                          remove_from_autostart)
from focuswatch.config import Config

logger = logging.getLogger(__name__)


def create_getter(config_path: List[str]):
  """ Create a getter function for a config option. """

  def getter(self):
    config_value = self._config
    for key in config_path:
      config_value = config_value[key]
    return config_value
  return getter


def create_setter(config_path: List[str], signal_name: str):
  """ Create a setter function for a config option. """

  def setter(self, value):
    config_section = self._config
    for key in config_path[:-1]:
      config_section = config_section[key]
    option = config_path[-1]
    if config_section[option] != value:
      config_section[option] = value
      getattr(self, signal_name).emit()
      self._config.write_config_to_file()
  return setter


def extract_config_options(config: Dict[str, Any], parent_keys: List[str] = None) -> List[Tuple[List[str], Any]]:
  """ Recursively extract config options and their paths. """
  parent_keys = parent_keys or []
  options = []
  for key, value in config.items():
    current_path = parent_keys + [key]
    if isinstance(value, dict):
      options.extend(extract_config_options(value, current_path))
    else:
      options.append((current_path, value))
  return options


def dynamic_properties(cls):
  """ Class decorator to dynamically add properties and signals to the class. """  # metaclass was crashing idk
  config = Config()
  options = extract_config_options(config)
  for config_path, value in options:
    prop_name = '_'.join(config_path)
    signal_name = f"{prop_name}_changed"
    value_type = type(value)

    # Avoid name collisions with existing attributes
    if hasattr(cls, prop_name):
      continue

    # Create Signal
    setattr(cls, signal_name, Signal())

    # Create getter and setter
    getter = create_getter(config_path)
    setter = create_setter(config_path, signal_name)

    # Create Property
    prop = Property(
        value_type, getter, setter, notify=getattr(cls, signal_name)
    )
    setattr(cls, prop_name, prop)

  return cls


@dynamic_properties
class SettingsViewModel(QObject):
  """ Settings ViewModel with dynamic properties based on the configuration. """

  # Signal for filter_text
  filter_text_changed = Signal()
  autostart_enabled_changed = Signal()
  autostart_available_changed = Signal()

  def __init__(self):
    super().__init__()
    self._config = Config()
    self._filter_text = ""
    self._autostart_available = self.is_autostart_available()
    self._autostart_enabled: bool = is_in_autostart()

  @Property(bool, notify=autostart_enabled_changed)
  def autostart_enabled(self) -> bool:
    return self._autostart_enabled

  @autostart_enabled.setter
  def autostart_enabled(self, value: bool):
    if self._autostart_enabled != value:
      self._autostart_enabled = value
      self.autostart_enabled_changed.emit()

  @Property(str, notify=filter_text_changed)
  def filter_text(self) -> str:
    """ Get the current filter text. """
    return self._filter_text

  @filter_text.setter
  def filter_text(self, value: str) -> None:
    """ Set a new filter text and notify observers. """
    if self._filter_text != value:
      self._filter_text = value
      self.filter_text_changed.emit()

  @Property(bool, notify=autostart_available_changed)
  def autostart_available(self) -> bool:
    """ Check if autostart is available based on the application's state. """
    return self._autostart_available

  @autostart_available.setter
  def autostart_available(self, value: bool):
    if self._autostart_available != value:
      self._autostart_available = value
      self.autostart_available_changed.emit()

  def is_autostart_available(self) -> bool:
    """ Determine if autostart is available - for now just check if the app is frozen. """
    return is_frozen()

  def toggle_autostart(self) -> None:
    """ Toggle autostart state. """
    if self._autostart_enabled:
      remove_from_autostart()
    else:
      add_to_autostart()
    self.autostart_enabled = not self._autostart_enabled
