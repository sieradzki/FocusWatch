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

  def _set_property(self, name: str, value: Any) -> None:
    current_value = getattr(self, name, None)
    # if name == "_keywords":
    # logger.info(f"Setting property '{name}' to {value}")
    # logger.info(f"Current value: {current_value}")
    # logger.info(f"old==new: {current_value == value}")
    # logger.info(f"len(old)==len(new): {len(current_value) == len(value)}")
    if self._values_differ(current_value, value):
      setattr(self, name, value)
      # logger.info(f"Property '{name}' changed from {
      # current_value} to {value}")
      self.property_changed.emit(name)
      self._notify_observers(name)

  def _values_differ(self, current_value: Any, new_value: Any) -> bool:
    if isinstance(current_value, list) and isinstance(new_value, list):
      if len(current_value) != len(new_value):
        return True
      return any(self._values_differ(c, n) for c, n in zip(current_value, new_value))
    elif isinstance(current_value, Keyword) and isinstance(new_value, Keyword):
      return (current_value.name != new_value.name or
              current_value.category_id != new_value.category_id or
              current_value.id != new_value.id or
              current_value.match_case != new_value.match_case)
    elif hasattr(current_value, '__dict__') and hasattr(new_value, '__dict__'):
      return current_value.__dict__ != new_value.__dict__
    else:
      return current_value != new_value

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
