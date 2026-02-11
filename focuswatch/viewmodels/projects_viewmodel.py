import logging
from typing import TYPE_CHECKING, List
from PySide6.QtCore import Property, QObject, Signal, Slot

from focuswatch.database.models.project import Project

if TYPE_CHECKING:
  from focuswatch.services.project_service import ProjectService


class ProjectsViewModel(QObject):
  """ Projects page view model for FocusWatch. """
  projects_changed = Signal()
  filter_text_changed = Signal()

  def __init__(self, project_service: "ProjectService"):
    super().__init__()
    self._project_service = project_service

    self._projects: List[Project] = []
    self._filter_text: str = ""

    self._load_projects()

  @Property(list, notify=projects_changed)
  def projects(self) -> List[Project]:
    """ Get the list of projects. """
    return self._projects

  @projects.setter
  def projects(self, value: List[Project]):
    if self._projects != value:
      self._projects = value
      self.projects_changed.emit()

  @Property(str, notify=filter_text_changed)
  def filter_text(self) -> str:
    return self._filter_text

  @filter_text.setter
  def filter_text(self, value: str):
    if self._filter_text != value.lower():
      self._filter_text = value.lower()
      self.filter_text_changed.emit()

  @Slot()
  def _load_projects(self):
    """ Load projects from the database. """
    self.projects = self._project_service.get_all_projects()
    self.projects_changed.emit()

  @Slot(str)
  def add_project(self, project_name: str, color: str = "", description: str = ""):
    """ Add a new project. """
    new_project = Project(name=project_name, color=color, description=description)
    project_id = self._project_service.create_project(new_project)
    if project_id is not None:
      self._load_projects()
    return project_id

  @Slot(int)
  def archive_project(self, project_id: int):
    """ Archive a project. """
    project = self._project_service.get_project_by_id(project_id)
    if project:
      project.archive()
      self._project_service.update_project(project)
      self._load_projects()
    else:
      logging.warning(f"Project with ID {project_id} not found for archiving.")

  @Slot(int)
  def activate_project(self, project_id: int):
    """ Activate a project. """
    project = self._project_service.get_project_by_id(project_id)
    if project:
      project.activate()
      self._project_service.update_project(project)
      self._load_projects()
    else:
      logging.warning(f"Project with ID {project_id} not found for activation.")
    
  @Slot(int, str, str, str)
  def update_project(self, project_id: int, name: str, color: str, description: str):
    """ Update a project's details. """
    project = self._project_service.get_project_by_id(project_id)
    if project:
      project.name = name
      project.color = color
      project.description = description
      self._project_service.update_project(project)
      self._load_projects()
    else:
      logging.warning(f"Project with ID {project_id} not found for updating.")
