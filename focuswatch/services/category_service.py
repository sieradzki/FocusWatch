""" Category service module for the FocusWatch application. """

import logging
from datetime import datetime
from typing import List, Optional, Tuple

import yaml
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from focuswatch.database.database_connection import DatabaseConnection
from focuswatch.database.models.activity import Activity
from focuswatch.database.models.category import Category
from focuswatch.database.models.keyword import Keyword
from focuswatch.services.keyword_service import KeywordService

logger = logging.getLogger(__name__)


class CategoryService:
  """ Service class for managing categories in the FocusWatch application. """

  def __init__(self,
               db_conn: Optional[DatabaseConnection] = None,
               keyword_service: Optional[KeywordService] = None):
    """ Initialize the CategoryService.

    Args:
      db_conn: Optional DatabaseConnection instance for dependency injection.
      keyword_service: Optional KeywordService instance for dependency injection.
    """
    self._db_conn = db_conn or DatabaseConnection()
    self._keyword_service = keyword_service or KeywordService()

  def create_category(self, category: Category) -> Optional[int]:
    """ Create a new category in the database.

    Args:
      category: The Category object to be created.

    Returns:
      Optional[int]: The ID of the newly created category if successful, None otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        # Check for duplicate within scope
        query = session.query(Category).filter(Category.name == category.name)
        if category.parent_category_id is None:
          query = query.filter(Category.parent_category_id.is_(None))
        else:
          parent_category = self.get_category_by_id(
            category.parent_category_id)
          if parent_category and category.name == parent_category.name:
            logger.warning(
              f"Cannot create category with same name as parent: {category.name}")
            return None
          query = query.filter(Category.parent_category_id ==
                               category.parent_category_id)

        if query.first():
          logger.warning(
            f"Category already exists within current scope: {category.name}")
          return None

        session.add(category)
        session.commit()
        logger.info(
          f"Created new category: {category.name} with ID {category.id}")
        return category.id
      except SQLAlchemyError as e:
        logger.error(f"Failed to create category: {e}")
        session.rollback()
        return None

  def get_category_by_id(self, category_id: int) -> Optional[Category]:
    """ Retrieve a category by its ID.

    Args:
      category_id: The ID of the category to retrieve.

    Returns:
      Optional[Category]: A Category object if found, None otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        category = session.query(Category).filter(
          Category.id == category_id).first()
        return category
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve category: {e}")
        return None

  def get_all_categories(self) -> List[Category]:
    """ Retrieve all categories from the database.

    Returns:
      List[Category]: A list of all Category objects in the database.
    """
    with self._db_conn.get_session() as session:
      try:
        return session.query(Category).all()
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve categories: {e}")
        return []

  def update_category(self, category: Category) -> bool:
    """ Update an existing category in the database.

    Args:
      category: The Category object with updated information.

    Returns:
      bool: True if the update was successful, False otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        # Check for duplicate within scope
        query = session.query(Category).filter(
          Category.name == category.name,
          Category.id != category.id
        )
        if category.parent_category_id is None:
          query = query.filter(Category.parent_category_id.is_(None))
        else:
          parent_category = self.get_category_by_id(
            category.parent_category_id)
          if parent_category and category.name == parent_category.name:
            logger.warning(
              f"Cannot update category to same name as parent: {category.name}")
            return False
          query = query.filter(Category.parent_category_id ==
                               category.parent_category_id)

        if query.first():
          logger.warning(
            f"Category with name {category.name} and parent_id {category.parent_category_id} already exists.")
          return False

        session.merge(category)
        session.commit()
        logger.info(f"Updated category: {category.name}")
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to update category: {e}")
        session.rollback()
        return False

  def delete_category(self, category_id: int) -> bool:
    """ Delete a category from the database.

    Args:
      category_id: The ID of the category to delete.

    Returns:
      bool: True if the deletion was successful, False otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        # Update children to have no parent
        session.query(Category).filter(Category.parent_category_id == category_id).update(
          {Category.parent_category_id: None}
        )
        logger.info(
          f"Updated children of category ID {category_id} to have no parent.")

        # Delete the category
        category = session.query(Category).filter(
          Category.id == category_id).first()
        if category:
          session.delete(category)
          logger.info(f"Deleted category with ID: {category_id}")

        # Delete associated keywords
        session.query(Keyword).filter(
          Keyword.category_id == category_id).delete()
        logger.info(f"Deleted keywords for category ID: {category_id}")

        session.commit()
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to delete category: {e}")
        session.rollback()
        return False

  def get_category_depth(self, category_id: int) -> int:
    """ Get the depth of a category in the hierarchy.

    Args:
      category_id: The ID of the category.

    Returns:
      int: The depth of the category (0 for root categories).
    """
    with self._db_conn.get_session() as session:
      try:
        depth = 0
        category = session.query(Category).filter(
          Category.id == category_id).first()
        while category and category.parent_category_id:
          depth += 1
          category = session.query(Category).filter(
            Category.id == category.parent_category_id).first()
        return depth
      except SQLAlchemyError as e:
        logger.error(f"Failed to get category depth: {e}")
        return 0

  def insert_default_categories(self) -> None:
    """ Insert default categories into the database. """
    logger.info("Inserting default categories.")
    with self._db_conn.get_session() as session:
      try:
        # Clear existing data
        session.query(Category).delete()
        session.query(Keyword).delete()

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
          session.add(category)
          session.flush()  # Ensure ID is assigned
          category_ids[name] = category.id
          if category.id is None:
            logger.warning(f"Failed to create category: {name}")

        session.commit()
        logger.info("Default categories inserted successfully.")
      except SQLAlchemyError as e:
        logger.error(f"Failed to insert default categories: {e}")
        session.rollback()

  def get_daily_category_time_totals(self) -> List[Tuple[int, int]]:
    """ Return the total time spent on each category for today.

    Returns:
      List[Tuple[int, int]]: A list of tuples containing (category_id, total_time_seconds).
    """
    with self._db_conn.get_session() as session:
      try:
        today = datetime.now().date()
        result = (session.query(
            Activity.category_id,
            (func.sum(func.julianday(Activity.time_stop) -
             func.julianday(Activity.time_start)) * 86400).label("total_time_seconds")
          )
          .filter(func.date(Activity.time_start) == today)
          .group_by(Activity.category_id)
          .order_by(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)).desc())
          .all())
        # Filter out NULL category_ids
        return [(r[0], int(r[1])) for r in result if r[0] is not None]
      except SQLAlchemyError as e:
        logger.error(f"Failed to get daily category time totals: {e}")
        return []

  def get_date_category_time_totals(self, date: datetime) -> List[Tuple[int, int]]:
    """ Return the total time spent on each category for a given date.

    Args:
      date: The date to retrieve entries for.

    Returns:
      List[Tuple[int, int]]: A list of tuples containing (category_id, total_time_seconds).
    """
    with self._db_conn.get_session() as session:
      try:
        formatted_date = date.date()
        result = (session.query(
            Activity.category_id,
            (func.sum(func.julianday(Activity.time_stop) -
             func.julianday(Activity.time_start)) * 86400).label("total_time_seconds")
          )
          .filter(func.date(Activity.time_start) == formatted_date)
          .group_by(Activity.category_id)
          .order_by(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)).desc())
          .all())
        # Filter out NULL category_ids
        return [(r[0], int(r[1])) for r in result if r[0] is not None]
      except SQLAlchemyError as e:
        logger.error(
          f"Failed to get category time totals for {formatted_date}: {e}")
        return []

  def get_period_category_time_totals(
      self,
      start_date: datetime,
      end_date: Optional[datetime] = None
  ) -> List[Tuple[int, int]]:
    """ Return the total time spent on each category for a given period.

    Args:
      start_date: The start date of the period.
      end_date: The end date of the period. If None, only start_date is considered.

    Returns:
      List[Tuple[int, int]]: A list of tuples containing (category_id, total_time_seconds).
    """
    with self._db_conn.get_session() as session:
      try:
        start_date_str = start_date.date()
        query = (session.query(
            Activity.category_id,
            (func.sum(func.julianday(Activity.time_stop) -
             func.julianday(Activity.time_start)) * 86400).label("total_time_seconds")
          )
          .group_by(Activity.category_id)
          .order_by(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)).desc()))

        if end_date:
          end_date_str = end_date.date()
          query = query.filter(func.date(Activity.time_start).between(
            start_date_str, end_date_str))
        else:
          query = query.filter(
            func.date(Activity.time_start) == start_date_str)

        result = query.all()
        # Filter out NULL category_ids
        return [(r[0], int(r[1])) for r in result if r[0] is not None]
      except SQLAlchemyError as e:
        logger.error(f"Failed to get category time totals for period: {e}")
        return []

  def get_category_id_from_name(self, category_name: str) -> Optional[int]:
    """ Return the id of a category given its name.

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
        logger.error(f"Failed to get category id from name: {e}")
        return None

  def get_category_by_name(self, category_name: str) -> Optional[Category]:
    """ Return a category given its name.

    Args:
      category_name: The name of the category.

    Returns:
      Optional[Category]: The Category object if found, None otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        return session.query(Category).filter(Category.name == category_name).first()
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve category by name: {e}")
        return None

  def get_category_focused(self, category_id: int) -> bool:
    """ Return whether a category is focused.

    Args:
      category_id: The ID of the category.

    Returns:
      bool: True if the category is focused, False otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        category = session.query(Category).filter(
          Category.id == category_id).first()
        return category.focused if category else False
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve category focused status: {e}")
        return False

  def export_categories_to_yml(self) -> str:
    """ Export categories and their keywords to a YAML string.

    Returns:
      str: The YAML string representing the categories and keywords.
    """
    with self._db_conn.get_session() as session:
      try:
        categories = session.query(Category).all()
        categories_dict = []

        for category in categories:
          category_dict = {
            "id": category.id,
            "name": category.name,
            "color": category.color,
            "focused": category.focused
          }

          if category.parent_category_id:
            parent = session.query(Category).filter(
              Category.id == category.parent_category_id).first()
            category_dict["parent_name"] = parent.name if parent else None
          else:
            category_dict["parent_name"] = None

          keywords = self._keyword_service.get_keywords_for_category(
            category.id)
          category_dict["keywords"] = [
            {"name": k.name, "match_case": k.match_case} for k in keywords]
          categories_dict.append(category_dict)

        yaml_str = yaml.dump(categories_dict, sort_keys=False)
        logger.debug("Exported categories and keywords to YAML.")
        return yaml_str
      except (yaml.YAMLError, SQLAlchemyError) as e:
        logger.error(f"Failed to export categories and keywords: {e}")
        raise

  def import_categories_from_yml(self, yml_str: str) -> bool:
    """ Import categories and their keywords from a YAML string.

    Args:
      yml_str: The YAML string representing the categories and keywords.

    Returns:
      bool: True if the import was successful, False otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        categories = yaml.safe_load(yml_str)
        session.query(Category).delete()
        session.query(Keyword).delete()

        name_to_id = {}
        for category_data in categories:
          parent_name = category_data.pop("parent_name", None)
          keywords_data = category_data.pop("keywords", [])
          category_data.pop("id", None)

          parent_id = name_to_id.get(parent_name) if parent_name else None
          category = Category(
            name=category_data["name"],
            parent_category_id=parent_id,
            color=category_data.get("color"),
            focused=category_data.get("focused", False)
          )
          session.add(category)
          session.flush()  # Ensure ID is assigned
          name_to_id[category.name] = category.id

          for keyword_data in keywords_data:
            keyword = Keyword(
              name=keyword_data["name"],
              category_id=category.id,
              match_case=keyword_data.get("match_case", False)
            )
            session.add(keyword)

        session.commit()
        return True
      except (yaml.YAMLError, SQLAlchemyError) as e:
        logger.error(f"Failed to import categories and keywords: {e}")
        session.rollback()
        return False
