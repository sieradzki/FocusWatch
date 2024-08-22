from typing import Callable, Any
from PySide6.QtCore import QObject, Signal
import logging
from focuswatch.models.keyword import Keyword

logger = logging.getLogger(__name__)


class BaseViewModel(QObject):
  property_changed = Signal(str)

  def __init__(self):
    super().__init__()
    self._property_observers = {}

  def _set_property(self, property_name: str, value: Any):
    if getattr(self, property_name) != value:
      setattr(self, property_name, value)
      self.property_changed.emit(property_name)

  def add_property_observer(self, property_name: str, callback: Callable[[], None]) -> None:
    if property_name not in self._property_observers:
      self._property_observers[property_name] = []
    self._property_observers[property_name].append(callback)

  def _notify_observers(self, property_name: str) -> None:
    observers = self._property_observers.get(property_name, [])
    for callback in observers:
      callback()
    # logger.info(
      # f"Property '{property_name}' changed, notifying observers: {observers}")
