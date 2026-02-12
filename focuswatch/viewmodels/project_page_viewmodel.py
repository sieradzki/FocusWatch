from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import Property, QObject, Signal

from focuswatch.database.models.project import Project

if TYPE_CHECKING:
  from focuswatch.services.project_service import ProjectService


class ProjectPageViewModel(QObject):
  """ ViewModel for a single project's page (details). """

  project_changed = Signal()

  def __init__(self, project_service: "ProjectService"):
    super().__init__()
    self._project_service = project_service
    self._project: Optional[Project] = None

  @Property(int, notify=project_changed)
  def project_id(self) -> int:
    return int(self._project.id) if self._project else -1

  @Property(str, notify=project_changed)
  def project_name(self) -> str:
    return self._project.name if self._project else ""

  @Property(str, notify=project_changed)
  def project_description(self) -> str:
    return self._project.description or "" if self._project else ""

  def load_project(self, project_id: int) -> None:
    self._project = self._project_service.get_project_by_id(project_id)
    self.project_changed.emit()
