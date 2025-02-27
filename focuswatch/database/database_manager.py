""" Database manager for FocusWatch.

This module provides a class for managing the database setup and initialization for FocusWatch.
"""

import logging
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from focuswatch.database.database_connection import DatabaseConnection
from focuswatch.database.models import Base
from focuswatch.database.models.metadata import Metadata
from focuswatch.services.category_service import CategoryService
from focuswatch.services.keyword_service import KeywordService

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = "1.0"


class DatabaseManager:
  """ Class for managing the database setup for FocusWatch. """

  def __init__(self,
               category_service: Optional[CategoryService] = None,
               keyword_service: Optional[KeywordService] = None):
    """ Initialize the database manager.

    Args:
      category_service: Optional CategoryService instance for dependency injection.
      keyword_service: Optional KeywordService instance for dependency injection.
    """
    self._db_conn = DatabaseConnection()
    self._setup_database()

    self._category_service = category_service or CategoryService(
      db_conn=self._db_conn)
    self._keyword_service = keyword_service or KeywordService(
      db_conn=self._db_conn)

    if not self._is_defaults_inserted():
      logger.info("Defaults not yet inserted. Inserting default data.")
      self._insert_default_data()
      self._mark_defaults_inserted()

    self._ensure_schema_version()

  def _setup_database(self):
    """ Set up the database by creating tables if they don't exist. """
    try:
      Base.metadata.create_all(self._db_conn.engine)
      logger.info("Database tables checked/created successfully.")
    except SQLAlchemyError as e:
      logger.error(f"Error setting up database: {e}")
      raise

  def _is_defaults_inserted(self) -> bool:
    """ Check if default data has been inserted.

    Returns:
      bool: True if defaults have been inserted, False otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        result = session.query(Metadata).filter(
          Metadata.key == "defaults_inserted").first()
        return result.value.lower() == "true" if result else False
      except SQLAlchemyError as e:
        logger.error(f"Error checking defaults insertion status: {e}")
        return False

  def _mark_defaults_inserted(self):
    """ Mark that default data has been inserted in the database. """
    with self._db_conn.get_session() as session:
      try:
        metadata = Metadata(key="defaults_inserted", value="true")
        session.merge(metadata)
        session.commit()
        logger.info("Marked defaults as inserted.")
      except SQLAlchemyError as e:
        logger.error(f"Error marking defaults as inserted: {e}")
        session.rollback()

  def _ensure_schema_version(self):
    """ Ensure the schema version is recorded and log the current version. """
    with self._db_conn.get_session() as session:
      try:
        current_version = session.query(Metadata).filter(
          Metadata.key == "schema_version").first()
        if not current_version:
          metadata = Metadata(key="schema_version",
                              value=CURRENT_SCHEMA_VERSION)
          session.add(metadata)
          session.commit()
          logger.info(
            f"Schema version initialized to {CURRENT_SCHEMA_VERSION}.")
        else:
          logger.info(f"Current schema version: {current_version.value}")
          if current_version.value != CURRENT_SCHEMA_VERSION:
            logger.warning(
              f"Schema version {current_version.value} does not match expected {CURRENT_SCHEMA_VERSION}. "
              "Future migrations may be required."
            )
      except SQLAlchemyError as e:
        logger.error(f"Error ensuring schema version: {e}")
        session.rollback()

  def _insert_default_data(self):
    """ Insert default categories and keywords into the database. """
    try:
      self._category_service.insert_default_categories()
      self._keyword_service.insert_default_keywords()
      logger.info("Default data inserted successfully.")
    except SQLAlchemyError as e:
      logger.error(f"Error inserting default data: {e}")
      raise
