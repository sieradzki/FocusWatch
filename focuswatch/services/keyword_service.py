""" Keyword Service Module """

import logging
from typing import List, Optional, Tuple
from focuswatch.models.keyword import Keyword
from focuswatch.database.database_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class KeywordService:
  """Service class for managing keywords in the FocusWatch application."""

  def __init__(self):
    self._db_conn = DatabaseConnection()
    self._db_conn.connect()

  def insert_default_keywords(self) -> None:
    """Insert default keywords into the database."""
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
      ("obsidian", "Productivity"), ("afk", "AFK")
    ]

    for keyword, category_name in keywords:
      category_id = self._get_category_id_by_name(category_name)
      if category_id is not None:
        self.add_keyword(Keyword(name=keyword, category_id=category_id))
      else:
        logger.warning(
          f"Category '{category_name}' not found for keyword '{keyword}'.")

  def get_keyword(self, keyword_id: int) -> Optional[Keyword]:
    """Retrieve a keyword from the database.

    Args:
        keyword_id: The id of the keyword.

    Returns:
        Optional[Keyword]: A Keyword object if found, None otherwise.
    """
    query = 'SELECT name, category_id, id, match_case FROM keywords WHERE id = ?'
    params = (keyword_id,)
    try:
      result = self._db_conn.execute_query(query, params)
      if result:
        return Keyword(*result[0])
      return None
    except Exception as e:
      logger.error(f"Failed to retrieve keyword: {e}")
      return None

  def add_keyword(self, keyword: Keyword) -> bool:
    """ Add a keyword to a category. 

    Args:
      keyword: The Keyword object to add.

    Returns:
      bool: True if the keyword was added successfully, False otherwise.
    """
    logger.debug(f"Attempting to add keyword: {keyword}")

    query = 'SELECT * FROM keywords WHERE category_id = ? AND name = ? AND match_case = ?'
    params = (keyword.category_id, keyword.name, keyword.match_case)

    existing_keywords = self._db_conn.execute_query(query, params)
    logger.debug(f"Existing keywords query result: {existing_keywords}")

    if existing_keywords:
      logger.debug(f"Keyword with name {keyword.name} already exists in category {
                  keyword.category_id}.")
      return True  # Consider it a success if the keyword already exists

    insert_query = 'INSERT INTO keywords (category_id, name, match_case) VALUES (?, ?, ?)'
    insert_params = (keyword.category_id, keyword.name, keyword.match_case)

    logger.debug(f"Executing insert query: {
                insert_query} with params: {insert_params}")
    rows_affected = self._db_conn.execute_update(insert_query, insert_params)
    logger.debug(f"Rows affected by insert: {rows_affected}")

    if rows_affected > 0:
      logger.info(f"Added new keyword: {keyword.name}")
      return True
    else:
      logger.error(f"Failed to add keyword: {keyword.name}. No rows affected.")
      return False

  def update_keyword(self, keyword: Keyword) -> bool:
    """Update a keyword.

    Args:
      keyword: The Keyword object with updated information.

    Returns:
      bool: True if the keyword was updated successfully, False otherwise.
    """
    logger.debug(f"Attempting to update keyword: {keyword}")

    query = 'UPDATE keywords SET category_id = ?, name = ?, match_case = ? WHERE id = ?'
    params = (keyword.category_id, keyword.name,
              keyword.match_case, keyword.id)

    logger.debug(f"Executing update query: {query} with params: {params}")
    rows_affected = self._db_conn.execute_update(query, params)
    logger.debug(f"Rows affected by update: {rows_affected}")

    if rows_affected > 0:
      logger.info(f"Updated keyword: {keyword.name}")
      return True
    elif rows_affected == 0:
      logger.warning(f"No changes made to keyword: {
                     keyword.name}. It might not exist or no values were changed.")
      return True  # Consider it a success if no changes were needed
    else:
      logger.error(f"Failed to update keyword: {
                   keyword.name}. Unexpected number of rows affected: {rows_affected}")
      return False

  def delete_keyword(self, keyword_id: int) -> bool:
    """Delete a keyword.

    Args:
      keyword_id: The id of the keyword to delete.

    Returns:
      bool: True if the keyword was deleted successfully, False otherwise.
    """
    logger.debug(f"Attempting to delete keyword with ID: {keyword_id}")

    query = 'DELETE FROM keywords WHERE id = ?'
    params = (keyword_id,)

    logger.debug(f"Executing delete query: {query} with params: {params}")
    rows_affected = self._db_conn.execute_update(query, params)
    logger.debug(f"Rows affected by delete: {rows_affected}")

    if rows_affected > 0:
      logger.info(f"Deleted keyword with ID: {keyword_id}")
      return True
    elif rows_affected == 0:
      logger.warning(f"No keyword found with ID: {
                     keyword_id}. Nothing was deleted.")
      return True  # Consider it a success if the keyword didn't exist
    else:
      logger.error(f"Failed to delete keyword with ID: {
                   keyword_id}. Unexpected number of rows affected: {rows_affected}")
      return False

  def get_all_keywords(self) -> List[Keyword]:
    """Return all keyword entries in the database.

    Returns:
        List[Keyword]: A list of all Keyword objects in the database.
    """
    query = "SELECT name, category_id, id, match_case FROM keywords"
    try:
      results = self._db_conn.execute_query(query)
      return [Keyword(*row) for row in results]
    except Exception as e:
      logger.error(f"Failed to retrieve keywords: {e}")
      return []

  def get_keywords_for_category(self, category_id: int) -> List[Keyword]:
    """Return all keywords for a category.

    Args:
        category_id: The id of the category.

    Returns:
        List[Keyword]: A list of Keyword objects for the specified category.
    """
    query = "SELECT name, category_id, id, match_case FROM keywords WHERE category_id = ?"
    params = (category_id,)
    try:
      results = self._db_conn.execute_query(query, params)
      return [Keyword(*row) for row in results]
    except Exception as e:
      logger.error(f"Failed to retrieve keywords for category {
          category_id}: {e}")
      return []

  def get_categories_from_keyword(self, keyword: str) -> List[int]:
    """Return the categories associated with a keyword sorted by depth.

    Args:
      keyword: The keyword to retrieve categories for.

    Returns:
      List[int]: A list of category IDs associated with the keyword, sorted by depth.
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
    try:
      results = self._db_conn.execute_query(query, params)
      return [row[0] for row in results]
    except Exception as e:
      logger.error(f"Failed to retrieve categories for keyword '{
                   keyword}': {e}")
      return []

  def get_keyword_id(self, keyword_name: str, category_id: int) -> Optional[int]:
    """Return the id of a keyword given its name and category_id.

    Args:
      keyword_name: The name of the keyword.
      category_id: The id of the category.

    Returns:
      Optional[int]: The ID of the keyword if found, None otherwise.
    """
    query = 'SELECT id FROM keywords WHERE name = ? AND category_id = ?'
    params = (keyword_name, category_id)
    try:
      result = self._db_conn.execute_query(query, params)
      return result[0][0] if result else None
    except Exception as e:
      logger.error(f"Failed to retrieve keyword ID: {e}")
      return None

  def _get_category_id_by_name(self, category_name: str) -> Optional[int]:
    """Helper method to get category ID by name.

    Args:
      category_name: The name of the category.

    Returns:
      Optional[int]: The ID of the category if found, None otherwise.
    """
    query = 'SELECT id FROM categories WHERE name = ?'
    params = (category_name,)
    try:
      result = self._db_conn.execute_query(query, params)
      return result[0][0] if result else None
    except Exception as e:
      logger.error(f"Failed to retrieve category ID: {e}")
      return None
