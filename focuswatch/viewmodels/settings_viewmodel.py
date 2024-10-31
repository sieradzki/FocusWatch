import logging
from typing import Optional

from focuswatch.autostart_manager import (add_to_autostart, is_frozen,
                                          is_in_autostart,
                                          remove_from_autostart)
from focuswatch.config import Config
from focuswatch.viewmodels.base_viewmodel import BaseViewModel

logger = logging.getLogger(__name__)


class SettingsViewModel(BaseViewModel):

  def __init__(self):
    super().__init__()
    self.config: Config = Config()
    self._watch_interval: float = float(
      self.config.get_value('General', 'watch_interval'))
    self._watch_afk: bool = self.config.get_value(
      'General', 'watch_afk') == 'True'
    self._afk_timeout: float = float(
      self.config.get_value('General', 'afk_timeout'))
    self._autostart_enabled: bool = is_in_autostart()

    self._filter_text: str = ""

  @property
  def watch_interval(self) -> float:
    return self._watch_interval

  @watch_interval.setter
  def watch_interval(self, value: float):
    if value <= 0:
      logger.warning("Attempted to set a non-positive watch interval.")
      return
    self._set_property('_watch_interval', value)

  @property
  def watch_afk(self) -> bool:
    return self._watch_afk

  @watch_afk.setter
  def watch_afk(self, value: bool):
    self._set_property('_watch_afk', value)

  @property
  def afk_timeout(self) -> float:
    return self._afk_timeout

  @afk_timeout.setter
  def afk_timeout(self, value: float):
    if value < 0:
      logger.warning("Attempted to set a negative AFK timeout.")
      return
    self._set_property('_afk_timeout', value)

  @property
  def autostart_enabled(self) -> bool:
    return self._autostart_enabled

  @autostart_enabled.setter
  def autostart_enabled(self, value: bool):
    self._set_property('_autostart_enabled', value)

  @property
  def filter_text(self) -> str:
    """ Get the current filter text.

    Returns:
      The filter text as a string.
    """
    return self._filter_text

  @filter_text.setter
  def filter_text(self, value: str) -> None:
    """ Set a new filter text and notify observers.

    Args:
      value: The new filter text.
    """
    if self._filter_text != value:
      self._filter_text = value
      self.property_changed.emit('filter_text')

  def is_autostart_available(self) -> bool:
    """ Check if autostart is available based on the application's state.

      Returns:
        True if autostart is available; False otherwise.
    """
    return is_frozen()

  def apply_settings(self):
    self.config.set_value('General', 'watch_interval',
                          str(self._watch_interval))
    self.config.set_value('General', 'watch_afk', str(self._watch_afk))
    self.config.set_value('General', 'afk_timeout', str(self._afk_timeout))

    if self._autostart_enabled:
      add_to_autostart()
    else:
      remove_from_autostart()

    # Notify observers that settings have been applied
    self.property_changed.emit('settings_applied')
