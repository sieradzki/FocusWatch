""" Category service module for the FocusWatch application. """

import logging
import sqlite3
from dataclasses import asdict
from datetime import datetime
from typing import List, Optional, Tuple

import yaml

from focuswatch.database.database_connection import DatabaseConnection
from focuswatch.models.category import Category
from focuswatch.models.keyword import Keyword
from focuswatch.services.keyword_service import KeywordService

logger = logging.getLogger(__name__)


class CategoryService:
  """ Service class for managing categories in the FocusWatch application."""

  def __init__(self):
    self._db_conn = DatabaseConnection()
    self._db_conn.connect()

    self._keyword_service = KeywordService()

  def create_category(self, category: Category) -> Optional[int]:
    """ Create a new category in the database.

    Args:
      category: The Category object to be created.

    Returns:
      int: The ID of the newly created category if successful, None otherwise.
    """
    # Check if category exists within current scope
    # For example: we can have work->programming and hobby->programming but not work->programming and work->programming
    if category.parent_category_id is None:
      query = "SELECT * FROM categories WHERE name=? AND parent_category IS NULL"
      params = (category.name,)
    else:
      # Don't allow category with the same name as parent category
      parent_category = self.get_category_by_id(category.parent_category_id)
      if parent_category and category.name == parent_category.name:
        logger.warning(
          f"Cannot create category with same name as parent: {category.name}")
        return None
      query = "SELECT * FROM categories WHERE name=? AND parent_category=?"
      params = (category.name, category.parent_category_id)

    try:
      if self._db_conn.execute_query(query, params):
        logger.warning(
          f"Category already exists within current scope: {category.name}")
        return None

      insert_query = "INSERT INTO categories (name, parent_category, color, focused) VALUES (?, ?, ?, ?)"
      insert_params = (
        category.name, category.parent_category_id, category.color, category.focused)

      cursor = self._db_conn.execute_update(
        insert_query, insert_params, return_cursor=True)
      new_category_id = cursor.lastrowid
      logger.info(f"Created new category: {
                  category.name} with ID {new_category_id}")
      return new_category_id
    except sqlite3.Error as e:
      logger.error(f"Failed to create category: {e}")
      return None

  def get_category_by_id(self, category_id: int) -> Optional[Category]:
    """ Retrieve a category by its ID.

    Args:
      category_id: The ID of the category to retrieve.

    Returns:
      Optional[Category]: A Category object if found, None otherwise.
    """
    query = "SELECT * FROM categories WHERE id = ?"
    params = (category_id,)

    try:
      result = self._db_conn.execute_query(query, params)
      if result:
        return Category(*result[0])
      return None
    except sqlite3.Error as e:
      logger.error(f"Failed to retrieve category: {e}")
      return None

  def get_all_categories(self) -> List[Category]:
    """ Retrieve all categories from the database.

    Returns:
        List[Category]: A list of all Category objects in the database.
    """
    query = "SELECT * FROM categories"

    try:
      results = self._db_conn.execute_query(query)
      return [Category(*row) for row in results]
    except sqlite3.Error as e:
      logger.error(f"Failed to retrieve categories: {e}")
      return []

  def update_category(self, category: Category) -> bool:
    """ Update an existing category in the database.

    Args:
      category: The Category object with updated information.

    Returns:
      bool: True if the update was successful, False otherwise.
    """
    # Check if category exists within current scope
    if category.parent_category_id is None:
      query = "SELECT * FROM categories WHERE name=? AND parent_category IS NULL AND id!=?"
      params = (category.name, category.id)
    else:
      # Don't allow category with the same name as parent category
      parent_category = self.get_category_by_id(category.parent_category_id)
      if parent_category and category.name == parent_category.name:
        logger.warning(
          f"Cannot update category to same name as parent: {category.name}")
        return False
      query = "SELECT * FROM categories WHERE name=? AND parent_category=? AND id!=?"
      params = (category.name, category.parent_category_id, category.id)

    try:
      if self._db_conn.execute_query(query, params):
        logger.warning(f"Category with name {category.name} and parent_id {
                       category.parent_category_id} already exists.")
        return False

      update_query = """UPDATE categories
                        SET name = ?, parent_category = ?, color = ?, focused = ?
                        WHERE id = ?"""
      update_params = (category.name, category.parent_category_id,
                       category.color, category.focused, category.id)

      self._db_conn.execute_update(update_query, update_params)
      logger.info(f"Updated category: {category.name}")
      return True
    except sqlite3.Error as e:
      logger.error(f"Failed to update category: {e}")
      return False

  def delete_category(self, category_id: int) -> bool:
    """ Delete a category from the database.

    Args:
      category_id: The ID of the category to delete.

    Returns:
      bool: True if the deletion was successful, False otherwise.
    """
    try:
      # Set the parent_category of children to NULL
      update_children_query = "UPDATE categories SET parent_category = NULL WHERE parent_category = ?"
      self._db_conn.execute_update(update_children_query, (category_id,))
      logger.info(f"Updated children of category ID {
                  category_id} to have no parent.")

      # Delete the category
      category_delete_query = "DELETE FROM categories WHERE id = ?"
      self._db_conn.execute_update(category_delete_query, (category_id,))
      logger.info(f"Deleted category with ID: {category_id}")

      # Delete keywords associated with the category
      keyword_delete_query = "DELETE FROM keywords WHERE category_id = ?"
      self._db_conn.execute_update(keyword_delete_query, (category_id,))
      logger.info(f"Deleted keywords for category ID: {category_id}")

      return True
    except sqlite3.Error as e:
      logger.error(f"Failed to delete category: {e}")
      return False

  def get_category_depth(self, category_id: int) -> int:
    """ Get the depth of a category in the hierarchy.

    Args:
      category_id: The ID of the category.

    Returns:
      int: The depth of the category (0 for root categories).
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

    try:
      result = self._db_conn.execute_query(query, params)
      return result[0][0] if result else 0
    except sqlite3.Error as e:
      logger.error(f"Failed to get category depth: {e}")
      return 0

  def insert_default_categories(self) -> None:
    """ Insert default categories into the database."""
    logger.info("Inserting default categories.")
    try:
      self._db_conn.execute_update("DELETE FROM categories;")
      self._db_conn.execute_update("DELETE FROM keywords;")

      categories = [
        ("Work", None, "#00cc00", True), ("Programming", "Work", None, True),
        ("Documents", "Work", None, True), ("Image", "Work", None, True),
        ("Audio", "Work", None, True), ("3D", "Work", None, True),
        ("Comms", None, "#33ccff", False), ("IM", "Comms", None, False),
        ("Email", "Comms", None, False), ("Media", None, "#ff0000", False),
        ("Games", "Media", None, False), ("Video", "Media", None, False),
        ("Social media", "Media", None, False), ("Music", "Media", None, False),
        ("Productivity", None, "#5546B5",
         True), ("Uncategorized", None, "#8c8c8c", False),
        ("AFK", None, "#3d3d3d", False)
      ]

      category_ids = {}
      for name, parent_name, color, focused in categories:
        parent_id = category_ids.get(parent_name)
        category = Category(
          name=name, parent_category_id=parent_id, color=color, focused=focused)
        if self.create_category(category):
          category_id = self.get_category_id_from_name(name)
          category_ids[name] = category_id
        else:
          logger.warning(f"Failed to create category: {name}")
    except sqlite3.Error as e:
      logger.error(f"Failed to insert default categories: {e}")

  def get_daily_category_time_totals(self) -> List[Tuple[int, int]]:
    """ Return the total time spent on each category for today.

    Returns:
      List[Tuple[int, int]]: A list of tuples containing (category_id, total_time_seconds).
    """
    query = """
      SELECT category_id,
      SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
      FROM activity
      WHERE strftime('%Y-%m-%d', time_start) = strftime('%Y-%m-%d', 'now')
      GROUP BY category_id
      ORDER BY total_time_seconds DESC;
    """
    try:
      return self._db_conn.execute_query(query)
    except sqlite3.Error as e:
      logger.error(f"Failed to get daily category time totals: {e}")

  def get_date_category_time_totals(self, date: datetime) -> List[Tuple[int, int]]:
    """ Return the total time spent on each category for a given date.

    Args:
      date: The date to retrieve entries for.

    Returns:
      List[Tuple[int, int]]: A list of tuples containing (category_id, total_time_seconds).
    """
    formatted_date = date.strftime("%Y-%m-%d")
    query = """
      SELECT category_id,
      SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
      FROM activity
      WHERE strftime('%Y-%m-%d', time_start) = strftime('%Y-%m-%d', ?)
      GROUP BY category_id
      ORDER BY total_time_seconds DESC;
    """
    params = (formatted_date,)
    try:
      return self._db_conn.execute_query(query, params)
    except sqlite3.Error as e:
      logger.error(f"Failed to get category time totals for {
                   formatted_date}: {e}")
      return []

  def get_period_category_time_totals(self, start_date: datetime, end_date: Optional[datetime] = None) -> List[Tuple[int, int]]:
    """ Return the total time spent on each category for a given period.

    Args:
      start_date: The start date of the period.
      end_date: The end date of the period. If None, only start_date is considered.

    Returns:
      List[Tuple[int, int]]: A list of tuples containing (category_id, total_time_seconds).
    """
    formatted_start_date = start_date.strftime("%Y-%m-%d")
    if end_date:
      formatted_end_date = end_date.strftime("%Y-%m-%d")
      query = """
        SELECT category_id,
        SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
        FROM activity
        WHERE strftime('%Y-%m-%d', time_start) BETWEEN ? AND ?
        GROUP BY category_id
        ORDER BY total_time_seconds DESC;
      """
      params = (formatted_start_date, formatted_end_date)
    else:
      query = """
        SELECT category_id,
        SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
        FROM activity
        WHERE strftime('%Y-%m-%d', time_start) = ?
        GROUP BY category_id
        ORDER BY total_time_seconds DESC;
      """
      params = (formatted_start_date,)
    try:
      return self._db_conn.execute_query(query, params)
    except sqlite3.Error as e:
      logger.error(f"Failed to get category time totals for period: {e}")
      return []

  def get_category_id_from_name(self, category_name: str) -> Optional[int]:
    """ Return the id of a category given its name.

    Args:
      category_name: The name of the category.

    Returns:
      Optional[int]: The ID of the category if found, None otherwise.
    """
    query = "SELECT id FROM categories WHERE name = ?"
    params = (category_name,)
    try:
      result = self._db_conn.execute_query(query, params)
      return result[0][0] if result else None
    except sqlite3.Error as e:
      logger.error(f"Failed to get category id from name: {e}")
      return None

  def get_category_by_name(self, category_name: str) -> Optional[Category]:
    """ Return a category given its name.

    Args:
      category_name: The name of the category.

    Returns:
      Optional[Category]: The Category object if found, None otherwise.
    """
    query = "SELECT * FROM categories WHERE name = ?"
    params = (category_name,)

    try:
      result = self._db_conn.execute_query(query, params)
      if result:
        return Category(*result[0])
      return None
    except sqlite3.Error as e:
      logger.error(f"Failed to retrieve category by name: {e}")
      return None

  # TODO remove on watcher service refactor
  def get_category_focused(self, category_id: int) -> bool:
    """ Return whether a category is focused.

    Args:
      category_id: The ID of the category.

    Returns:
      bool: True if the category is focused, False otherwise.
    """
    query = "SELECT focused FROM categories WHERE id = ?"
    params = (category_id,)
    try:
      result = self._db_conn.execute_query(query, params)
      return bool(result[0][0]) if result else False
    except sqlite3.Error as e:
      logger.error(f"Failed to retrieve category focused status: {e}")
      return False

  def export_categories_to_yml(self) -> str:
    """ Export categories and their keywords to a YAML string.

    Returns:
        str: The YAML string representing the categories and keywords.
    """
    try:
      categories = self.get_all_categories()
      categories_dict = []

      for category in categories:
        category_dict = asdict(category)

        # Retrieve parent_category_id
        parent_category_id = category_dict.get("parent_category_id")

        if parent_category_id is not None:
          # Get the parent category's name
          parent_category = self.get_category_by_id(parent_category_id)
          if parent_category:
            category_dict["parent_name"] = parent_category.name
          else:
            logger.warning(f"Parent category with ID {
                           parent_category_id} not found.")
            category_dict["parent_name"] = None
        else:
          category_dict["parent_name"] = None

        # Remove 'parent_category_id' from the dict
        category_dict.pop("parent_category_id", None)

        # Get keywords for this category
        keywords = self._keyword_service.get_keywords_for_category(category.id)
        keyword_dicts = [{"name": k.name, "match_case": k.match_case}
                         for k in keywords]
        category_dict["keywords"] = keyword_dicts

        categories_dict.append(category_dict)

      yaml_str = yaml.dump(categories_dict, sort_keys=False)
      logger.debug("Exported categories and keywords to YAML.")
      return yaml_str
    except (yaml.YAMLError, sqlite3.Error) as e:
      logger.error(f"Failed to export categories and keywords: {e}")
      raise

  def import_categories_from_yml(self, yml_str: str) -> bool:
    """ Import categories and their keywords from a YAML string.

    Args:
      yml_str: The YAML string representing the categories and keywords.

    Returns:
      bool: True if the import was successful, False otherwise.
    """
    try:
      categories = yaml.safe_load(yml_str)
      self._db_conn.execute_update("DELETE FROM categories;")
      self._db_conn.execute_update("DELETE FROM keywords;")

      name_to_id = {}

      for category_data in categories:
        parent_name = category_data.pop("parent_name", None)
        keywords_data = category_data.pop(
          "keywords", [])
        category_data.pop("id", None)

        parent_category_id = None

        if parent_name:
          parent_id = name_to_id.get(parent_name)
          if parent_id:
            parent_category_id = parent_id
          else:
            parent_category = self.get_category_by_name(parent_name)
            if parent_category:
              parent_id = parent_category.id
              name_to_id[parent_name] = parent_id
              parent_category_id = parent_id
            else:
              logger.warning(f"Parent category '{parent_name}' not found for '{
                             category_data["name"]}'")
              parent_category_id = None

        category = Category(
            name=category_data["name"],
            parent_category_id=parent_category_id,
            color=category_data.get("color"),
            focused=category_data.get("focused", 0)
        )

        new_category_id = self.create_category(category)
        if new_category_id:
          # Store the mapping from category name to new ID
          name_to_id[category.name] = new_category_id

          # Add keywords associated with this category
          for keyword_data in keywords_data:
            keyword = Keyword(
                name=keyword_data["name"],
                category_id=new_category_id,
                match_case=keyword_data.get("match_case", False)
            )
            self._keyword_service.add_keyword(keyword)
        else:
          logger.error(f"Failed to create category '{category.name}'")

      return True
    except (yaml.YAMLError, sqlite3.Error) as e:
      logger.error(f"Failed to import categories and keywords: {e}")
      return False
