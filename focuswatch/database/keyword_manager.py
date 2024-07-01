""" Keyword Manager Module

This module is responsible for managing the keywords in the database.
"""

import logging
from typing import List, Optional

from focuswatch.database.category_manager import CategoryManager
from focuswatch.database.database_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class KeywordManager:
  """ Class for managing keywords in the database. """

  def __init__(self) -> None:
    """ Initialize the keyword manager. """
    self._db_conn = DatabaseConnection()
    self._db_conn.connect()

  def insert_default_keywords(self) -> None:
    """ Insert default keywords into the database. """
    logger.info("Inserting default keywords.")
    keywords = [
        ("Google Docs", "Documents"), ("libreoffice", "Documents"),
        ("GitHub", "Programming"), ("Stack Overflow", "Programming"),
        ("BitBucket", "Programming"), ("Gitlab", "Programming"),
        ("vim", "Programming"), ("Spyder", "Programming"),
        ("kate", "Programming"), ("Visual Studio", "Programming"),
        ("code", "Programming"), ("QtCreator", "Programming"),
        ("Gimp", "Image"), ("Inkscape", "Image"),
        ("Audacity", "Audio"), ("Blender", "3D"),
        ("Messenger", "IM"), ("Signal", "IM"),
        ("WhatsApp", "IM"), ("Slack", "IM"), ("Discord", "IM"),
        ("Gmail", "Email"), ("Thunderbird", "Email"),
        ("mutt", "Email"), ("alpine", "Email"),
        ("Minecraft", "Games"), ("Steam", "Games"),
        ("YouTube", "Video"), ("mpv", "Video"),
        ("VLC", "Video"), ("Twitch", "Video"),
        ("reddit", "Social media"), ("Facebook", "Social media"),
        ("Instagram", "Social media"), ("Spotify", "Music"),
        ("FocusWatch", "Productivity"), ("notion", "Productivity"),
        ("obsidian", "Productivity")
    ]

    category_manager = CategoryManager()
    keyword_ids = {}
    for keyword, category_name in keywords:
      category_id = category_manager.get_category_id_from_name(
        category_name)
      if category_id is not None:
        success = self.add_keyword(keyword, category_id)
        if success:
          keyword_id = self.get_keyword_id(keyword, category_id)
          keyword_ids[(keyword, category_name)] = keyword_id
        else:
          logger.warning(f"Failed to add keyword: {keyword}")
      else:
        logger.warning(f"Category '{category_name}' not found.")

  def get_keyword(self, keyword_id: int) -> Optional[tuple]:
    """ Retrieve a keyword from the database. 

    Args:
      keyword_id: The id of the keyword.

    Returns:
      A tuple representing the keyword if it exists, None otherwise.
    """
    query = 'SELECT * FROM keywords WHERE id=?'
    params = (keyword_id,)
    result = self._db_conn.execute_query(query, params)
    return result[0] if result else None

  def add_keyword(self, keyword_name: str, category_id: int, match_case: Optional[bool] = False) -> bool:
    """ Add a keyword to a category. 

    Args:
      keyword_name: The name of the keyword.
      category_id: The id of the category.
      match_case: Whether the keyword should be case-sensitive.

    Returns:
      True if the keyword was added successfully, False otherwise.
    """
    # Check if the keyword already exists in the category
    query = 'SELECT * FROM keywords WHERE category_id = ? AND name = ?'
    params = (category_id, keyword_name)

    if self._db_conn.execute_query(query, params):
      logger.debug(f"Keyword with name {
          keyword_name} already exists in category {category_id}.")
      return False

    # Insert the keyword into the category
    query = 'INSERT INTO keywords (category_id, name, match_case) VALUES (?, ?, ?)'
    params = (category_id, keyword_name, match_case)
    return self._db_conn.execute_update(query, params)

  def update_keyword(self, keyword_id: int, keyword_name: str, category_id: int, match_case: Optional[bool] = False) -> bool:
    """ Update a keyword. 

    Args:
      keyword_id: The id of the keyword.
      keyword_name: The name of the keyword.
      category_id: The id of the category.
      match_case: Whether the keyword should be case-sensitive.

    Returns:
      True if the keyword was updated successfully, False otherwise.
    """
    query = 'UPDATE keywords SET category_id=?, name=?, match_case=? WHERE id=?'
    params = (category_id, keyword_name, match_case, keyword_id)
    return self._db_conn.execute_update(query, params)

  def delete_keyword(self, keyword_id: int) -> bool:
    """ Delete a keyword. 

    Args:
      keyword_id: The id of the keyword.

    Returns:
      True if the keyword was deleted successfully, False otherwise.
    """
    query = 'DELETE FROM keywords WHERE id=?'
    params = (keyword_id,)
    return self._db_conn.execute_update(query, params)

  def get_all_keywords(self) -> List[tuple]:
    """ Return all keyword entries in the database. """
    query = "SELECT * FROM keywords"
    result = self._db_conn.execute_query(query)
    return result if result else []

  def get_keywords_for_category(self, category_id: int) -> List[tuple]:
    """ Return all keywords for a category. 

    Args:
      category_id: The id of the category.
    """
    query = "SELECT * FROM keywords WHERE category_id=?"
    params = (category_id,)
    result = self._db_conn.execute_query(query, params)
    return result if result else []

  def get_categories_from_keyword(self, keyword: str) -> List[int]:
    """ Return the categories associated with a keyword sorted by depth. 

    Args:
      keyword: The keyword to retrieve categories for.
    """
    query = """
      WITH RECURSIVE CategoryHierarchy(id, name, parent_category, depth) AS (
        SELECT id, name, parent_category, 0 AS depth FROM categories WHERE parent_category IS NULL
        UNION ALL
        SELECT c.id, c.name, c.parent_category, ch.depth + 1
        FROM categories c
        JOIN CategoryHierarchy ch ON c.parent_category = ch.id
      )
      SELECT ch.id AS innermost_category
      FROM CategoryHierarchy ch
      JOIN keywords k ON ch.id = k.category_id
      WHERE LOWER(k.name) LIKE LOWER(?)
      ORDER BY ch.depth DESC; 
    """
    params = (f'%{keyword}%',)
    result = self._db_conn.execute_query(query, params)
    return [row[0] for row in result] if result else []

  def get_keyword_id(self, keyword_name: str, category_id: int) -> Optional[int]:
    """ Return the id of a keyword given its name and category_id. 

    Args:
      keyword_name: The name of the keyword.
      category_id: The id of the category.
    """
    query = 'SELECT id FROM keywords WHERE name=? AND category_id=?'
    params = (keyword_name, category_id)
    result = self._db_conn.execute_query(query, params)
    return result[0][0] if result else None
