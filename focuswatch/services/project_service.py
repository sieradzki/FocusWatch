""" Project Service Module """

import logging
from typing import Optional

from  sqlalchemy.exc import SQLAlchemyError

from focuswatch.database.database_connection import DatabaseConnection
from focuswatch.database.models.project import Project

logger = logging.getLogger(__name__)


class ProjectService:
  """ Service class for managing projects in the FocusWatch application. """

  def __init__(self, db_conn: Optional[DatabaseConnection] = None):
    """ Initialize the ProjectService. 
    
    Args:
      db_conn: Optional DatabaseConnection instance for dependency injection.
    """
    self._db_conn = db_conn or DatabaseConnection()

  def create_project(self, project: Project) -> Optional[int]:
    """ Create a new project. 
    
    Args:
      project: The Project object to be created.
      
    Returns:
      Optional[int]: The ID of the newly created project if successful, None otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        # Check if a project with the same name already exists
        existing_project = session.query(Project).filter(
          Project.name == project.name).first()
        if existing_project:
          logger.warning(f"Project with name '{project.name}' already exists.")
          return None
        session.add(project)
        session.commit()
        logger.info(f"Created new project: {project.name}")
        return project.id
      except SQLAlchemyError as e:
        logger.error(f"Failed to create project: {e}")
        session.rollback()
        return None

  def get_project_by_id(self, project_id: int) -> Optional[Project]:
    """ Retrieve a project from the database. 
    
    Args:
      project_id: The ID of the project.
      
    Returns:
      Optional[Project]: A Project object if found, None otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        return session.query(Project).filter(Project.id == project_id).first()
      except SQLAlchemyError as e:
        logger.error("Failed to retrieve project: {e}")
        return None

  def get_all_projects(self) -> list[Project]:
    """ Retrieve all projects from the database. 
    
    Returns:
      list[Project]: A list of all Project objects.
    """
    with self._db_conn.get_session() as session:
      try:
        return session.query(Project).all()
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve projects: {e}")
        return []

  def update_project(self, project: Project) -> bool:
    """ Update an existing project. 
    
    Args:
      project: The Project object with updated information.
      
    Returns:
      bool: True if the project was updated successfully, False otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        # Check if the project exists
        existing_project = session.query(Project).filter(
          Project.id == project.id).first()
        if not existing_project:
          logger.warning(f"Project with ID '{project.id}' not found.")
          return False
        # Check if a project with the same name already exists (excluding current project)
        duplicate_project = session.query(Project).filter(
          Project.name == project.name,
          Project.id != project.id).first()
        if duplicate_project:
          logger.warning(f"Project with name '{project.name}' already exists.")
          return False
        existing_project.name = project.name
        existing_project.description = project.description
        existing_project.color = project.color
        existing_project.status = project.status
        session.commit()
        logger.info(f"Updated project: {project.name}")
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to update project: {e}")
        session.rollback()
        return False

  def delete_project(self, project_id: int) -> bool:
    """ Delete a project by ID.
    
    Args:
      project_id: The ID of the project to delete.

    Returns:
      bool: True if the project was deleted successfully, False otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
          logger.warning(f"Project with ID '{project_id}' not found.")
          return False
        session.delete(project)
        session.commit()
        logger.info(f"Deleted project with ID: {project_id}")
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to delete project: {e}")
        session.rollback()
        return False