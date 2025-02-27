""" Keyword Service Module """

import logging
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from focuswatch.database.database_connection import DatabaseConnection
from focuswatch.database.models.category import Category
from focuswatch.database.models.keyword import Keyword

logger = logging.getLogger(__name__)


class KeywordService:
  """ Service class for managing keywords in the FocusWatch application. """

  def __init__(self, db_conn: Optional[DatabaseConnection] = None):
    """ Initialize the KeywordService.

    Args:
      db_conn: Optional DatabaseConnection instance for dependency injection.
    """
    self._db_conn = db_conn or DatabaseConnection()

  def insert_default_keywords(self) -> None:
    """ Insert default keywords into the database. """
    logger.info("Inserting default keywords.")
    with self._db_conn.get_session() as session:
      try:
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

        for keyword_name, category_name in keywords:
          category = session.query(Category).filter(
            Category.name == category_name).first()
          if category:
            keyword = Keyword(name=keyword_name, category_id=category.id)
            session.add(keyword)
          else:
            logger.warning(
              f"Category '{category_name}' not found for keyword '{keyword_name}'.")

        session.commit()
        logger.info("Default keywords inserted successfully.")
      except SQLAlchemyError as e:
        logger.error(f"Failed to insert default keywords: {e}")
        session.rollback()

  def get_keyword(self, keyword_id: int) -> Optional[Keyword]:
    """ Retrieve a keyword from the database.

    Args:
      keyword_id: The ID of the keyword.

    Returns:
      Optional[Keyword]: A Keyword object if found, None otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        return session.query(Keyword).filter(Keyword.id == keyword_id).first()
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve keyword: {e}")
        return None

  def add_keyword(self, keyword: Keyword) -> bool:
    """ Add a keyword to a category.

    Args:
      keyword: The Keyword object to add.

    Returns:
      bool: True if the keyword was added successfully or already exists, False otherwise.
    """
    logger.debug(f"Attempting to add keyword: {keyword}")
    with self._db_conn.get_session() as session:
      try:
        # Check for existing keyword
        existing = session.query(Keyword).filter(
          Keyword.category_id == keyword.category_id,
          Keyword.name == keyword.name,
          Keyword.match_case == keyword.match_case
        ).first()
        if existing:
          logger.debug(
            f"Keyword with name {keyword.name} already exists in category {keyword.category_id}.")
          return True

        session.add(keyword)
        session.commit()
        logger.info(f"Added new keyword: {keyword.name}")
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to add keyword: {e}")
        session.rollback()
        return False

  def update_keyword(self, keyword: Keyword) -> bool:
    """ Update a keyword.

    Args:
      keyword: The Keyword object with updated information.

    Returns:
      bool: True if the keyword was updated successfully or no changes needed, False otherwise.
    """
    logger.debug(f"Attempting to update keyword: {keyword}")
    with self._db_conn.get_session() as session:
      try:
        session.merge(keyword)
        session.commit()
        logger.info(f"Updated keyword: {keyword.name}")
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to update keyword: {e}")
        session.rollback()
        return False

  def delete_keyword(self, keyword_id: int) -> bool:
    """ Delete a keyword.

    Args:
      keyword_id: The ID of the keyword to delete.

    Returns:
      bool: True if the keyword was deleted successfully or didn’t exist, False otherwise.
    """
    logger.debug(f"Attempting to delete keyword with ID: {keyword_id}")
    with self._db_conn.get_session() as session:
      try:
        keyword = session.query(Keyword).filter(
          Keyword.id == keyword_id).first()
        if keyword:
          session.delete(keyword)
          session.commit()
          logger.info(f"Deleted keyword with ID: {keyword_id}")
        else:
          logger.warning(
            f"No keyword found with ID: {keyword_id}. Nothing was deleted.")
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to delete keyword: {e}")
        session.rollback()
        return False

  def get_all_keywords(self) -> List[Keyword]:
    """ Return all keyword entries in the database.

    Returns:
      List[Keyword]: A list of all Keyword objects in the database.
    """
    with self._db_conn.get_session() as session:
      try:
        return session.query(Keyword).all()
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve keywords: {e}")
        return []

  def get_keywords_for_category(self, category_id: int) -> List[Keyword]:
    """ Return all keywords for a category.

    Args:
      category_id: The ID of the category.

    Returns:
      List[Keyword]: A list of Keyword objects for the specified category.
    """
    with self._db_conn.get_session() as session:
      try:
        return session.query(Keyword).filter(Keyword.category_id == category_id).all()
      except SQLAlchemyError as e:
        logger.error(
          f"Failed to retrieve keywords for category {category_id}: {e}")
        return []

  def get_categories_from_keyword(self, keyword: str) -> List[int]:
    """ Return the categories associated with a keyword sorted by depth.

    Args:
      keyword: The keyword to retrieve categories for.

    Returns:
      List[int]: A list of category IDs associated with the keyword, sorted by depth.
    """
    with self._db_conn.get_session() as session:
      try:
        # Get keywords matching the input (case-insensitive)
        keywords = session.query(Keyword).filter(
          func.lower(Keyword.name).like(f"%{keyword.lower()}%")
        ).all()

        category_ids_with_depth = []
        for kw in keywords:
          depth = 0
          category = session.query(Category).filter(
            Category.id == kw.category_id).first()
          while category:
            category_ids_with_depth.append((category.id, depth))
            depth += 1
            category = (session.query(Category)
                        .filter(Category.id == category.parent_category_id)
                        .first() if category.parent_category_id else None)

        # Sort by depth (descending) and extract unique category IDs
        sorted_pairs = sorted(category_ids_with_depth,
                              key=lambda x: x[1], reverse=True)
        # Remove duplicates, preserve order
        return list(dict.fromkeys(pair[0] for pair in sorted_pairs))
      except SQLAlchemyError as e:
        logger.error(
          f"Failed to retrieve categories for keyword '{keyword}': {e}")
        return []

  def get_keyword_id(self, keyword_name: str, category_id: int) -> Optional[int]:
    """ Return the ID of a keyword given its name and category_id.

    Args:
      keyword_name: The name of the keyword.
      category_id: The ID of the category.

    Returns:
      Optional[int]: The ID of the keyword if found, None otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        keyword = session.query(Keyword).filter(
          Keyword.name == keyword_name,
          Keyword.category_id == category_id
        ).first()
        return keyword.id if keyword else None
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve keyword ID: {e}")
        return None

  def _get_category_id_by_name(self, category_name: str) -> Optional[int]:
    """ Helper method to get category ID by name.

    Args:
      category_name: The name of the category.

    Returns:
      Optional[int]: The ID of the category if found, None otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        category = session.query(Category).filter(
          Category.name == category_name).first()
        return category.id if category else None
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve category ID: {e}")
        return None
