from typing import Any, Callable
from PySide6.QtCore import QObject, Signal


class BaseViewModel(QObject):
  property_changed = Signal(str)  # Signal to notify property changes

  def __init__(self):
    super().__init__()
    self._property_observers = {}

  def _set_property(self, name: str, value: Any) -> None:
    """Set a property and notify observers if it has changed."""
    if getattr(self, name, None) != value:
      setattr(self, name, value)
      self.property_changed.emit(name)
      self._notify_observers(name)

  def add_property_observer(self, property_name: str, callback: Callable[[], None]) -> None:
    """Add an observer for a specific property."""
    if property_name not in self._property_observers:
      self._property_observers[property_name] = []
    self._property_observers[property_name].append(callback)

  def _notify_observers(self, property_name: str) -> None:
    """Notify all observers of a property change."""
    observers = self._property_observers.get(property_name, [])
    for callback in observers:
      callback()
