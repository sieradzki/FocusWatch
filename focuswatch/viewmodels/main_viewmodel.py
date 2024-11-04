from typing import TYPE_CHECKING

from PySide6.QtCore import Property, QObject, Signal

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.keyword_service import KeywordService
  from focuswatch.services.watcher_service import WatcherService


class MainViewModel(QObject):
  """ ViewModel for the main application window. """

  is_monitoring_changed = Signal()

  def __init__(self,
               watcher_service: "WatcherService",
               activity_service: "ActivityService",
               category_service: "CategoryService",
               keyword_service: "KeywordService"):
    super().__init__()
    self._watcher_service = watcher_service
    self._activity_service = activity_service
    self._category_service = category_service
    self._keyword_service = keyword_service

    self._is_monitoring = False

  @Property(bool, notify=is_monitoring_changed)
  def is_monitoring(self) -> bool:
    """ Indicates whether activity monitoring is active. """
    return self._is_monitoring

  @is_monitoring.setter
  def is_monitoring(self, value: bool) -> None:
    if self._is_monitoring != value:
      self._is_monitoring = value
      self.is_monitoring_changed.emit()

  def start_monitoring(self) -> None:
    """ Start the activity monitoring process. """
    if not self.is_monitoring:
      self._watcher_service.monitor()
      self.is_monitoring = True

  def stop_monitoring(self) -> None:
    """ Stop the monitoring process. """
    if self.is_monitoring:
      # self._watcher_service.stop() # TODO: Implement stop method in WatcherService
      self.is_monitoring = False

  def export_data(self, file_path: str) -> bool:  # TODO
    """ Export data to a file. """
    pass

  def import_data(self, file_path: str) -> bool:  # TODO
    """ Import data from a file. """
    pass
