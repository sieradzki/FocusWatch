""" Database connection module for FocusWatch.

This module manages the database connection and sessions using SQLAlchemy for FocusWatch.
"""

import logging
from typing import Callable, Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from focuswatch.config import Config

logger = logging.getLogger(__name__)


class DatabaseConnection:
  """ Manages the database connection and sessions using SQLAlchemy. """

  _engine = None
  _SessionFactory: Optional[Callable[[], Session]] = None

  def __init__(self):
    """ Initialize the database connection configuration. """
    self._config = Config()
    self.db_name = self._config["database"]["location"]
    if self._engine is None:
      self._initialize_engine(self.db_name)

  @classmethod
  def _initialize_engine(cls, db_name: str):
    """ Initialize the SQLAlchemy engine and session factory if not already done.

    Args:
      db_name: The database file path or URI suffix (e.g., path for SQLite).
    """
    if cls._engine is None:
      try:
        db_uri = f"sqlite:///{db_name}"
        cls._engine = create_engine(db_uri, pool_pre_ping=True)
        cls._SessionFactory = sessionmaker(bind=cls._engine)
        logger.info("Database engine initialized.")
      except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database engine: {e}")
        raise

  @property
  def engine(self):
    """ Get the SQLAlchemy engine.

    Returns:
      sqlalchemy.engine.Engine: The database engine instance.
    """
    if self._engine is None:
      self._initialize_engine(self.db_name)
    return self._engine

  def get_session(self) -> Session:
    """ Create and return a new database session.

    Returns:
      Session: A new SQLAlchemy session object.
    """
    if self._SessionFactory is None:
      self._initialize_engine(self.db_name)
    return self._SessionFactory() # pylint: disable=not-callable

  def test_connection(self) -> bool:
    """ Test the database connection.

    Returns:
      bool: True if the connection is successful, False otherwise.
    """
    try:
      with self.engine.connect() as connection:
        connection.execute("SELECT 1")
        logger.info("Database connection successful.")
        return True
    except SQLAlchemyError as e:
      logger.error(f"Database connection failed: {e}")
      return False

  def close_engine(self):
    """ Close the database engine and reset internal state. """
    if self._engine:
      self._engine.dispose()
      self._engine = None
      self._SessionFactory = None
      logger.info("Database engine closed.")
