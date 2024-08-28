from typing import Callable, Any
from PySide6.QtCore import QObject, Signal
import logging

logger = logging.getLogger(__name__)


class BaseViewModel(QObject):
  property_changed = Signal(str)

  def __init__(self):
    super().__init__()
    self._property_observers = {}

  def _set_property(self, property_name: str, value: Any):
    """ Set a property and notify observers if the value has changed. """
    if getattr(self, property_name) != value:
      setattr(self, property_name, value)
      self.property_changed.emit(property_name)
      logger.debug(f"Property '{property_name}' changed to '{value}'")

  def add_property_observer(self, property_name: str, callback: Callable[[], None]) -> None:
    """ Add a callback to be called when a property changes. """
    if property_name not in self._property_observers:
      logger.debug(f"Creating observer list for property '{property_name}'")
      self._property_observers[property_name] = []
    self._property_observers[property_name].append(callback)

  def _notify_observers(self, property_name: str) -> None:
    """ Notify observers that a property has changed. """
    observers = self._property_observers.get(property_name, [])
    for callback in observers:
      callback()
    logger.debug(
      f"Property '{property_name}' changed, notifying observers: {observers}")
