""" Database connection module for FocusWatch. 

This module is responsible for managing the connection to the SQLite database used by FocusWatch. It provides methods for creating, updating, and querying the database. The class uses the sqlite3 module to interact with the database.
"""

import sqlite3
from focuswatch.config import Config
import logging


class DatabaseConnection:
  """ Class for managing the connection to the database. """

  def __init__(self):
    """ Initialize the database connection. """
    self.conn = None
    self._config = Config()
    self.db_name = self._config.get_value('Database', 'location')

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
      sqlite3.OperationalError: If there is an error connecting to the database.
    """

    try:
      dburi = f"file:{self.db_name}?mode=rw"
      self.conn = sqlite3.connect(
        dburi, uri=True, check_same_thread=False, timeout=1)
    except sqlite3.OperationalError as e:
      logging.error(f"Error connecting to database: {e}")
      raise ConnectionError(f"Failed to connect to the database: {e}")

  def connect_or_create(self):
    """ Connect to the database, creating it if it doesn't exist. """
    try:
      self.connect()
    except ConnectionError:
      logging.info("Database does not exist, creating new database.")
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
      logging.error(f"Error executing query: {e}")
      result = []
    finally:
      cur.close()
    return result

  def execute_update(self, query: str, params: tuple = ()) -> bool:
    """ Execute an update query on the database. 

    Args:
      query (str): The SQL query to execute.
      params (tuple): The parameters to pass to the query.

    Returns:
      bool: True if the update was successful, False otherwise.
    """
    if not self.conn:
      raise ConnectionError("Database connection is not established.")
    cur = self.conn.cursor()
    try:
      cur.execute(query, params)
      self.conn.commit()
      return self.conn.total_changes > 0
    except sqlite3.OperationalError as e:
      logging.error(f"Error executing update: {e}")
      self.conn.rollback()
      return False
    finally:
      cur.close()
