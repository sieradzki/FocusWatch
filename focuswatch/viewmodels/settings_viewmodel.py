import logging
from typing import Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

from focuswatch.autostart_manager import (add_to_autostart, is_frozen,
                                          is_in_autostart,
                                          remove_from_autostart)
from focuswatch.config import Config

logger = logging.getLogger(__name__)


class SettingsViewModel(QObject):
  watch_interval_changed = Signal()
  watch_afk_changed = Signal()
  afk_timeout_changed = Signal()
  autostart_enabled_changed = Signal()
  filter_text_changed = Signal()
  settings_applied = Signal()

  def __init__(self):
    super().__init__()
    self.config: Config = Config()
    self._watch_interval: float = float(
      self.config["General"]["watch_interval"])
    self._watch_afk: bool = self.config["General"]["watch_afk"] == True
    self._afk_timeout: float = float(self.config["General"]["afk_timeout"])
    self._autostart_enabled: bool = is_in_autostart()

    self._filter_text: str = ""

  @Property(float, notify=watch_interval_changed)
  def watch_interval(self) -> float:
    return self._watch_interval

  @watch_interval.setter
  def watch_interval(self, value: float):
    if value <= 0:
      logger.warning("Attempted to set a non-positive watch interval.")
      return
    if self._watch_interval != value:
      self._watch_interval = value
      self.watch_interval_changed.emit()

  @Property(bool, notify=watch_afk_changed)
  def watch_afk(self) -> bool:
    return self._watch_afk

  @watch_afk.setter
  def watch_afk(self, value: bool):
    if self._watch_afk != value:
      self._watch_afk = value
      self.watch_afk_changed.emit()

  @Property(float, notify=afk_timeout_changed)
  def afk_timeout(self) -> float:
    return self._afk_timeout

  @afk_timeout.setter
  def afk_timeout(self, value: float):
    if value < 0:
      logger.warning("Attempted to set a negative AFK timeout.")
      return
    if self._afk_timeout != value:
      self._afk_timeout = value
      self.afk_timeout_changed.emit()

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
    """Get the current filter text."""
    return self._filter_text

  @filter_text.setter
  def filter_text(self, value: str) -> None:
    """ Set a new filter text and notify observers. """
    if self._filter_text != value:
      self._filter_text = value
      self.filter_text_changed.emit()

  def is_autostart_available(self) -> bool:
    """ Check if autostart is available based on the application's state.

    Returns:
        True if autostart is available; False otherwise.
    """
    return is_frozen()

  @Slot()
  def apply_settings(self):  # TODO more intelligent way to apply settings
    self.config["General"]["watch_interval"] = self._watch_interval
    self.config["General"]["watch_afk"] = self._watch_afk
    self.config["General"]["afk_timeout"] = self._afk_timeout

    if self._autostart_enabled:
      add_to_autostart()
    else:
      remove_from_autostart()

    self.settings_applied.emit()
