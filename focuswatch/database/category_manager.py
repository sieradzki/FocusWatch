""" Category Manager Module 

This module is responsible for managing the categories in the database.
"""

from datetime import datetime
import sqlite3
from typing import List, Optional, Tuple, Union
import logging

from focuswatch.config import Config
from focuswatch.database.database_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class CategoryManager:
  """ Class for managing categories in the database. """

  def __init__(self) -> None:
    """ Initialize the category manager. """
    self._db_conn = DatabaseConnection()
    self._db_conn.connect()

  def insert_default_categories(self) -> None:
    """ Insert default categories into the database. """
    logger.info("Inserting default categories.")
    self._db_conn.execute_update('DELETE FROM categories;')
    self._db_conn.execute_update('DELETE FROM keywords;')

    categories = [
        ("Work", None, "#00cc00"), ("Programming", "Work", None),
        ("Documents", "Work", None), ("Image", "Work", None),
        ("Audio", "Work", None), ("3D", "Work", None),
        ("Comms", None, "#33ccff"), ("IM", "Comms", None),
        ("Email", "Comms", None), ("Media", None, "#ff0000"),
        ("Games", "Media", None), ("Video", "Media", None),
        ("Social media", "Media", None), ("Music", "Media", None),
        ("Productivity", None, "#332032"), ("Uncategorized", None, "#8c8c8c"),
        ("AFK", None, "#3d3d3d")
    ]

    category_ids = {}
    for name, parent_name, color in categories:
      parent_id = None
      if parent_name:
        parent_id = category_ids.get(parent_name)
      success = self.create_category(name, parent_id, color)
      if success:
        category_id = self.get_category_id_from_name(name)
        category_ids[name] = category_id
      else:
        logger.warning(f"Failed to create category: {name}")

  def create_category(self, category_name: str, parent_id: Optional[int] = None, color: Optional[str] = None) -> bool:
    """ Create a category. 

    Args:
      category_name: The name of the category.
      parent_id: The parent category id of the category.
      color: The color of the category.

    Returns:
      True if the category was created successfully, False otherwise."""

    # Check if category exists withing current scope
    # For example: we can have work->programming and hobby->programming but not work->programming and work->programming
    if parent_id is None:
      query = 'SELECT * FROM categories WHERE name=? AND parent_category IS NULL'
      params = (category_name,)
    else:
      # Don't allow category with the same name as parent category
      parent_category_name = self.get_category_by_id(parent_id)[1]
      if category_name == parent_category_name:
        return False
      query = 'SELECT * FROM categories WHERE name=? AND parent_category=?'
      params = (category_name, parent_id)

    if self._db_conn.execute_query(query, params):
      return False

    query = 'INSERT INTO categories (name, parent_category, color) VALUES (?, ?, ?)'
    params = (category_name, parent_id, color)
    return self._db_conn.execute_update(query, params)

  def delete_category(self, category_id: int) -> bool:
    """ Delete a category. 

    Args:
      category_id: The id of the category.

    Returns:
      True if the category was deleted successfully, False otherwise."""
    query = 'DELETE FROM categories WHERE id=?'
    params = (category_id,)
    return self._db_conn.execute_update(query, params)

  def update_category(self, category_id: int, name: str, parent_id: Optional[int], color: Optional[str]) -> bool:
    """ Update a category. 

    Args:
      category_id: The id of the category.
      name: The name of the category.
      parent_id: The parent category of the category.
      color: The color of the category.

    Returns:
      True if the category was updated successfully, False otherwise.
    """
    # Check if category exists withing current scope
    if parent_id is None:
      query = 'SELECT * FROM categories WHERE name=? AND parent_category IS NULL AND id!=?'
      params = (name, category_id)
    else:
      if name == self.get_category_by_id(parent_id)[1]:
        return False
      query = 'SELECT * FROM categories WHERE name=? AND parent_category=? AND id!=?'
      params = (name, parent_id, category_id)

    if self._db_conn.execute_query(query, params):
      logger.debug(f"Category with name {name} and parent_id {
                   parent_id} already exists.")
      return False

    query = 'UPDATE categories SET name=?, parent_category=?, color=? WHERE id = ?'
    params = (name, parent_id, color, category_id)
    return self._db_conn.execute_update(query, params)

  def get_all_categories(self) -> List[Tuple]:
    """ Return all category entries in the database. """
    query = "SELECT * FROM categories"
    result = self._db_conn.execute_query(query)
    return result if result else []

  def get_category_by_id(self, category_id: int) -> Optional[Tuple]:
    """ Returns a category by id. 

    Args:
      category_id: The id of the category.
    """
    query = "SELECT * FROM categories WHERE id=?"
    params = (category_id,)
    result = self._db_conn.execute_query(query, params)
    return result[0] if result else None

  def get_daily_category_time_totals(self) -> List[Tuple[int, int]]:
    """ Return the total time spent on each category for today. """
    query = """
      SELECT category_id,
      SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
      FROM activity_log
      WHERE strftime('%Y-%m-%d', time_start) = strftime('%Y-%m-%d', 'now')
      GROUP BY category_id
      ORDER BY total_time_seconds DESC;
    """
    return self._db_conn.execute_query(query)

  def get_date_category_time_totals(self, date: datetime) -> List[Tuple[int, int]]:
    """ Return the total time spent on each category for a given date. 

    Args:
      date: The date to retrieve entries for.
    """
    formatted_date = date.strftime("%Y-%m-%d")
    query = """
      SELECT category_id,
      SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
      FROM activity_log
      WHERE strftime('%Y-%m-%d', time_start) = strftime('%Y-%m-%d', ?)
      GROUP BY category_id
      ORDER BY total_time_seconds DESC;
    """
    params = (formatted_date,)
    return self._db_conn.execute_query(query, params)

  def get_period_category_time_totals(self, start_date: datetime, end_date: Optional[datetime] = None) -> List[Tuple[int, int]]:
    """ Return the total time spent on each category for a given period.

    Args:
        start_date: The start date of the period.
        end_date: The end date of the period. If None, only start_date is considered.
    """
    formatted_start_date = start_date.strftime("%Y-%m-%d")
    if end_date:
      formatted_end_date = end_date.strftime("%Y-%m-%d")
      query = """
        SELECT category_id,
        SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
        FROM activity_log
        WHERE strftime('%Y-%m-%d', time_start) BETWEEN ? AND ?
        GROUP BY category_id
        ORDER BY total_time_seconds DESC;
      """
      params = (formatted_start_date, formatted_end_date)
    else:
      query = """
        SELECT category_id,
        SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
        FROM activity_log
        WHERE strftime('%Y-%m-%d', time_start) = ?
        GROUP BY category_id
        ORDER BY total_time_seconds DESC;
      """
      params = (formatted_start_date,)

    return self._db_conn.execute_query(query, params)

  def get_category_depth(self, category_id: int) -> int:
    """ Return the depth of a category. 

    Args:
      category_id: The id of the category.

    Returns:
      The depth of the category.
    """
    query = """
      WITH RECURSIVE CategoryHierarchy(id, depth) AS (
        SELECT id, 0 as depth FROM categories WHERE parent_category IS NULL
        UNION ALL
        SELECT c.id, ch.depth + 1 FROM categories c
        JOIN CategoryHierarchy ch ON c.parent_category = ch.id
      )
      SELECT depth FROM CategoryHierarchy WHERE id = ?;
    """
    params = (category_id,)
    result = self._db_conn.execute_query(query, params)
    return result[0][0] if result else 0

  def get_category_id_from_name(self, category_name: str) -> Union[int, None]:
    """ Return the id of a category given its name. 

    Args:
      category_name: The name of the category.
    """
    query = 'SELECT id FROM categories WHERE name=?'
    params = (category_name,)
    result = self._db_conn.execute_query(query, params)
    return result[0][0] if result else None
