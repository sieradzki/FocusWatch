""" Project model for FocusWatch. """

from enum import Enum as PyEnum
from typing import Optional
import re

from sqlalchemy import Column, Enum, Integer, String, Text

from focuswatch.database.models import Base
from focuswatch.utils.ui_utils import validate_color_format


class ProjectStatus(PyEnum):
  """ Enumm for project statuses. """
  ACTIVE = "active"
  ARCHIVED = "archived"


class Project(Base):
  """ Respresents a project in the database. """

  __tablename__ = "projects"

  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String, nullable=False)
  color = Column(String, nullable=True)
  description = Column(Text, nullable=True)
  status = Column(Enum(ProjectStatus), nullable=False,
                  default=ProjectStatus.ACTIVE.value)

  def __init__(self,
               name: str = "",
               color: Optional[str] = None,
               description: Optional[str] = None,
               status: ProjectStatus = ProjectStatus.ACTIVE):
    """ Initialize and validate the project.

    Args:
      name (str): The name of the project.
      color (Optional[str]): The color associated with the project (e.g., for UI display).
      description (Optional[str]): A description of the project.
      status (ProjectStatus): The status of the project (default: active).
    """
    self.name = name
    self.color = color
    self.description = description
    self.status = status.value
    if color is not None:
      if validate_color_format(color):
        self.color = color
      else:
        raise ValueError(
          f"Invalid color format: {color}. Use #RRGGBB or rgb(r,g,b).")
    else:
      self.color = None

  def archive(self):
    """ Archive the project. """
    self.status = ProjectStatus.ARCHIVED.value

  def activate(self):
    """ Activate the project. """
    self.status = ProjectStatus.ACTIVE.value

  def __repr__(self):
    return f"<Project(id={self.id}, name={self.name}, status={self.status})>"
