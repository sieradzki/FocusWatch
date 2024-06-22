""" Keyword Manager Module

This module is responsible for managing the keywords in the database.
"""

from typing import List, Optional
import logging

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
    keywords = [
      ("Google Docs", 1), ("libreoffice", 1), ("GitHub", 2), ("Stack Overflow", 2),
      ("BitBucket", 2), ("Gitlab", 2), ("vim", 2), ("Spyder", 2), ("kate", 2),
      ("Visual Studio", 2), ("code", 2), ("QtCreator", 2), ("Gimp", 4),
      ("Inkscape", 4), ("Audacity", 5), ("Blender", 6), ("Messenger", 8),
      ("Signal", 8), ("WhatsApp", 8), ("Slack", 8), ("Discord", 8),
      ("Gmail", 9), ("Thunderbird", 9), ("mutt", 9), ("alpine", 9),
      ("Minecraft", 11), ("Steam", 11), ("YouTube", 12), ("mpv", 12),
      ("VLC", 12), ("Twitch", 12), ("reddit", 13), ("Facebook", 13),
      ("Instagram", 13), ("Spotify", 14), ("FocusWatch", 15), ("notion", 15),
      ("obsidian", 15)
    ]
    for keyword, category_id in keywords:
      self.add_keyword(keyword, category_id)

  def add_keyword(self, keyword_name: str, category_id: int, match_case: Optional[bool] = False) -> bool:
    """ Add a keyword to a category. 

    Args:
      keyword_name: The name of the keyword.
      category_id: The id of the category.
      match_case: Whether the keyword should be case-sensitive.

    Returns:
      True if the keyword was added successfully, False otherwise.
    """
    query = 'INSERT INTO keywords (category_id, name, match_case) VALUES (?, ?, ?)'
    params = (category_id, keyword_name, match_case)
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
