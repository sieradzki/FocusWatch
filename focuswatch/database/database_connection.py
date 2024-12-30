""" Database connection module for FocusWatch. 

This module is responsible for managing the connection to the SQLite database used by FocusWatch. It provides methods for creating, updating, and querying the database. The class uses the sqlite3 module to interact with the database.
"""

import sqlite3
from focuswatch.config import Config
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
  """ Class for managing the connection to the database. """

  def __init__(self):
    """ Initialize the database connection. """
    self.conn = None
    self._config = Config()
    self.db_name = self._config["database"]["location"]

  def __del__(self):
    """ Close the database connection when the object is deleted. """
    self.close()

  def close(self):
    """ Close the database connection. """
    if self.conn:
      self.conn.close()
      self.conn = None

  def connect(self):
    """ Connect to the database.

    Raises:
      ConnectionError: If there is an error connecting to the database.
    """
    try:
      dburi = f"file:{self.db_name}?mode=rw"
      self.conn = sqlite3.connect(
        dburi, uri=True, check_same_thread=False, timeout=1)
    except sqlite3.OperationalError as e:
      logger.error(f"Error connecting to database: {e}")
      raise ConnectionError(f"Failed to connect to the database: {e}")

  def connect_or_create(self):
    """ Connect to the database, creating it if it doesn't exist. """
    try:
      self.connect()
    except ConnectionError:
      logger.info("Database does not exist, creating new database.")
      self.conn = sqlite3.connect(
        self.db_name, check_same_thread=False, timeout=1)

  def execute_query(self, query: str, params: tuple = ()) -> list:
    """ Execute a query on the database.

    Args:
      query (str): The SQL query to execute.
      params (tuple): The parameters to pass to the query.

    Returns:
      list: The results of the query.
    """
    if not self.conn:
      raise ConnectionError("Database connection is not established.")
    cur = self.conn.cursor()
    try:
      cur.execute(query, params)
      result = cur.fetchall()
    except sqlite3.DatabaseError as e:
      logger.error(f"Error executing query: {e}")
      result = []
    finally:
      cur.close()
    return result

  def execute_update(self, query: str, params: tuple = (), return_cursor: bool = False):
    """ Execute an update query on the database.

    Args:
      query (str): The SQL query to execute.
      params (tuple): The parameters to pass to the query.
      return_cursor (bool): Whether to return the cursor object.

    Returns:
      int or sqlite3.Cursor: The number of rows affected by the update, or the cursor if return_cursor is True.
    """
    if not self.conn:
      raise ConnectionError("Database connection is not established.")
    cur = self.conn.cursor()
    try:
      cur.execute(query, params)
      self.conn.commit()
      rows_affected = cur.rowcount
      # logger.debug(
      # f"Execute update - Query: {query}, Params: {params}, Rows affected: {rows_affected}")
      if return_cursor:
        return cur
      else:
        cur.close()
        return rows_affected
    except sqlite3.OperationalError as e:
      logger.error(f"Error executing update {
                   query} with params: {params}: {e}")
      self.conn.rollback()
      cur.close()
      if return_cursor:
        return None
      else:
        return -1
