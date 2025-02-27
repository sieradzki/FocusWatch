""" Activity Service Module """

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError

from focuswatch.database.database_connection import DatabaseConnection
from focuswatch.database.models.activity import Activity
from focuswatch.database.models.category import Category

logger = logging.getLogger(__name__)


class ActivityService:
  """ Service class for managing activities in the FocusWatch application. """

  def __init__(self, db_conn: Optional[DatabaseConnection] = None):
    """ Initialize the ActivityService.

    Args:
      db_conn: Optional DatabaseConnection instance for dependency injection.
    """
    self._db_conn = db_conn or DatabaseConnection()

  def insert_activity(self, activity: Activity) -> bool:
    """ Insert an activity into the database.

    Args:
      activity: The Activity object to be inserted.

    Returns:
      bool: True if the activity was inserted successfully, False otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        session.add(activity)
        session.commit()
        # logger.debug(f"Inserted new activity: {activity.window_name}")
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to insert activity: {e}")
        session.rollback()
        return False

  def update_category(self, activity_id: int, category_id: int) -> bool:
    """ Update the category ID of an activity.

    Args:
      activity_id: The ID of the activity to update.
      category_id: The new category ID.

    Returns:
      bool: True if the category ID was updated successfully, False otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        session.query(Activity).filter(Activity.id == activity_id).update(
          {Activity.category_id: category_id}
        )
        session.commit()
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to update category for activity: {e}")
        session.rollback()
        return False

  def bulk_update_category(self, activity_ids: List[int], category_id: int) -> bool:
    """ Bulk update the category_id for multiple activities.

    Args:
      activity_ids: List of activity IDs to update.
      category_id: The new category ID.

    Returns:
      bool: True if the categories were updated successfully, False otherwise.
    """
    if not activity_ids:
      return True

    with self._db_conn.get_session() as session:
      try:
        session.query(Activity).filter(Activity.id.in_(activity_ids)).update(
          {Activity.category_id: category_id}, synchronize_session=False
        )
        session.commit()
        return True
      except SQLAlchemyError as e:
        logger.error(f"Failed to bulk update categories for activities: {e}")
        session.rollback()
        return False

  def bulk_update_category_by_name(self, activity_name: str, category_id: int) -> bool:
    """ Bulk update the category_id for multiple activities by activity name.

    Args:
      activity_name: Name of the activity.
      category_id: The new category ID.

    Returns:
      bool: True if the categories were updated successfully, False otherwise.
    """
    with self._db_conn.get_session() as session:
      try:
        session.query(Activity).filter(
          or_(Activity.window_class == activity_name,
              Activity.window_name == activity_name)
        ).update({Activity.category_id: category_id}, synchronize_session=False)
        session.commit()
        return True
      except SQLAlchemyError as e:
        logger.error(
          f"Failed to bulk update categories for activity_name {activity_name}: {e}")
        session.rollback()
        return False

  def get_all_activities(self) -> List[Activity]:
    """ Return all activity entries in the database.

    Returns:
      List[Activity]: A list of all Activity objects in the database.
    """
    with self._db_conn.get_session() as session:
      try:
        return session.query(Activity).all()
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve activities: {e}")
        return []

  def get_by_category_id(self, category_id: int) -> List[Activity]:
    """ Return all activity entries with a given category ID.

    Args:
      category_id: The category ID to retrieve entries for.

    Returns:
      List[Activity]: A list of Activity objects with the specified category ID.
    """
    with self._db_conn.get_session() as session:
      try:
        return session.query(Activity).filter(Activity.category_id == category_id).all()
      except SQLAlchemyError as e:
        logger.error(
          f"Failed to retrieve activities for category {category_id}: {e}")
        return []

  def get_todays_entries(self) -> List[Activity]:
    """ Return all entries for today.

    Returns:
      List[Activity]: A list of Activity objects for today.
    """
    with self._db_conn.get_session() as session:
      try:
        today = datetime.now().date()
        return session.query(Activity).filter(func.date(Activity.time_start) == today).all()
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve today's activities: {e}")
        return []

  def get_date_entries(self, date: datetime) -> List[Activity]:
    """ Return all entries for a given date.

    Args:
      date: The date to retrieve entries for.

    Returns:
      List[Activity]: A list of Activity objects for the specified date.
    """
    with self._db_conn.get_session() as session:
      try:
        formatted_date = date.date()
        return session.query(Activity).filter(func.date(Activity.time_start) == formatted_date).all()
      except SQLAlchemyError as e:
        logger.error(
          f"Failed to retrieve activities for date {formatted_date}: {e}")
        return []

  def get_period_entries(self, period_start: datetime, period_end: Optional[datetime] = None) -> List[Activity]:
    """ Return all entries for a given period.

    Args:
      period_start: The start date of the period.
      period_end: The end date of the period. If None, only period_start is considered.

    Returns:
      List[Activity]: A list of Activity objects for the specified period.
    """
    with self._db_conn.get_session() as session:
      try:
        start_date = period_start.date()
        if period_end:
          end_date = period_end.date()
          query = session.query(Activity).filter(
            func.date(Activity.time_start).between(start_date, end_date)
          )
        else:
          query = session.query(Activity).filter(
            func.date(Activity.time_start) == start_date)

        activities = query.all()
        for activity in activities:
          activity.time_start = datetime.fromisoformat(activity.time_start)
          activity.time_stop = datetime.fromisoformat(
            activity.time_stop) if activity.time_stop else None
        return activities
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve activities for period: {e}")
        return []

  def get_date_entries_class_time_total(self, date: datetime) -> List[Tuple[str, Optional[int], int]]:
    """ Return the total time spent on each window class for a given date.

    Args:
      date: The date to retrieve entries for.

    Returns:
      List[Tuple[str, Optional[int], int]]: A list of tuples containing
      (window_class, category_id, total_time_seconds).
    """
    with self._db_conn.get_session() as session:
      try:
        formatted_date = date.date()
        result = (session.query(
            Activity.window_class,
            Activity.category_id,
            (func.sum(func.julianday(Activity.time_stop) -
             func.julianday(Activity.time_start)) * 86400).label("total_time_seconds")
          )
          .filter(func.date(Activity.time_start) == formatted_date)
          .group_by(Activity.window_class)
          .order_by(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)).desc())
          .all())
        return [(r[0], r[1], int(r[2])) for r in result]
      except SQLAlchemyError as e:
        logger.error(
          f"Failed to retrieve class time totals for date {formatted_date}: {e}")
        return []

  def get_period_entries_class_time_total(
      self,
      period_start: datetime,
      period_end: Optional[datetime] = None
  ) -> List[Tuple[str, Optional[int], int]]:
    """ Return the total time spent on each window class for a given period.

    Args:
      period_start: The start date of the period.
      period_end: The end date of the period. If None, only period_start is considered.

    Returns:
      List[Tuple[str, Optional[int], int]]: A list of tuples containing
      (window_class, category_id, total_time_seconds).
    """
    with self._db_conn.get_session() as session:
      try:
        start_date = period_start.date()
        query = (session.query(
            Activity.window_class,
            Activity.category_id,
            (func.sum(func.julianday(Activity.time_stop) -
             func.julianday(Activity.time_start)) * 86400).label("total_time_seconds")
          )
          .group_by(Activity.window_class)
          .order_by(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)).desc()))

        if period_end:
          end_date = period_end.date()
          query = query.filter(
            func.date(Activity.time_start).between(start_date, end_date))
        else:
          query = query.filter(func.date(Activity.time_start) == start_date)

        result = query.all()
        return [(r[0], r[1], int(r[2])) for r in result]
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve class time totals for period: {e}")
        return []

  def get_period_entries_name_time_total(
      self,
      period_start: datetime,
      period_end: Optional[datetime] = None
  ) -> List[Tuple[str, Optional[int], int]]:
    """ Return the total time spent on each window name for a given period.

    Args:
      period_start: The start date of the period.
      period_end: The end date of the period. If None, only period_start is considered.

    Returns:
      List[Tuple[str, Optional[int], int]]: A list of tuples containing
      (window_name, category_id, total_time_seconds).
    """
    with self._db_conn.get_session() as session:
      try:
        start_date = period_start.date()
        query = (session.query(
            Activity.window_name,
            Activity.category_id,
            (func.sum(func.julianday(Activity.time_stop) -
             func.julianday(Activity.time_start)) * 86400).label("total_time_seconds")
          )
          .group_by(Activity.window_name)
          .order_by(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)).desc()))

        if period_end:
          end_date = period_end.date()
          query = query.filter(
            func.date(Activity.time_start).between(start_date, end_date))
        else:
          query = query.filter(func.date(Activity.time_start) == start_date)

        result = query.all()
        return [(r[0], r[1], int(r[2])) for r in result]
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve name time totals for period: {e}")
        return []

  def get_longest_duration_category_id_for_window_class_on_date(
      self,
      date: datetime,
      window_class: str
  ) -> Optional[int]:
    """ Return the category with the longest duration for a given window class on a given date.

    Args:
      date: The date to retrieve entries for.
      window_class: The window class to retrieve entries for.

    Returns:
      Optional[int]: The category ID with the longest duration, or None if not found.
    """
    with self._db_conn.get_session() as session:
      try:
        formatted_date = date.date()
        result = (session.query(Activity.category_id)
                  .filter(
            func.date(Activity.time_start) == formatted_date,
            Activity.window_class == window_class
        )
            .group_by(Activity.category_id)
            .order_by(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)).desc())
            .first())
        return result[0] if result else None
      except SQLAlchemyError as e:
        logger.error(
          f"Failed to retrieve longest duration category for window class {window_class} on date {formatted_date}: {e}")
        return None

  def get_longest_duration_category_id_for_window_class_in_period(
      self,
      period_start: datetime,
      window_class: str,
      period_end: Optional[datetime] = None
  ) -> Optional[int]:
    """ Return the category with the longest duration for a given window class in a given period.

    Args:
      period_start: The start date of the period.
      window_class: The window class to retrieve entries for.
      period_end: The end date of the period. If None, only period_start is considered.

    Returns:
      Optional[int]: The category ID with the longest duration, or None if not found.
    """
    with self._db_conn.get_session() as session:
      try:
        start_date = period_start.date()
        query = (session.query(Activity.category_id)
                 .filter(Activity.window_class == window_class)
                 .group_by(Activity.category_id)
                 .order_by(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)).desc()))

        if period_end:
          end_date = period_end.date()
          query = query.filter(
            func.date(Activity.time_start).between(start_date, end_date))
        else:
          query = query.filter(func.date(Activity.time_start) == start_date)

        result = query.first()
        return result[0] if result else None
      except SQLAlchemyError as e:
        logger.error(
          f"Failed to retrieve longest duration category for window class {window_class} in period: {e}")
        return None

  def get_top_uncategorized_window_classes(
      self,
      limit: int = 10,
      offset: int = 0,
      threshold_seconds: int = 60
  ) -> List[Tuple[str, int]]:
    """ Return the top uncategorized window classes sorted by total time spent.

    Entries with total time less than the threshold are excluded.

    Args:
      limit: The maximum number of entries to return.
      offset: The number of entries to skip before starting to collect the result set.
      threshold_seconds: The minimum total time in seconds for an entry to be included.

    Returns:
      List[Tuple[str, int]]: A list of tuples containing (window_class, total_time_seconds).
    """
    with self._db_conn.get_session() as session:
      try:
        uncategorized_id = session.query(Category.id).filter(
          Category.name == "Uncategorized").scalar()
        query = (session.query(
            Activity.window_class,
            (func.sum(func.julianday(Activity.time_stop) -
             func.julianday(Activity.time_start)) * 86400).label("total_time_seconds")
          )
          .filter(or_(Activity.category_id.is_(None), Activity.category_id == uncategorized_id))
          .group_by(Activity.window_class)
          .having(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)) * 86400 >= threshold_seconds)
          .order_by(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)).desc())
          .limit(limit)
          .offset(offset))

        result = query.all()
        return [(r[0], int(r[1])) for r in result]
      except SQLAlchemyError as e:
        logger.error(
          f"Failed to retrieve top uncategorized window classes: {e}")
        return []

  def get_top_uncategorized_window_names(
      self,
      limit: int = 10,
      offset: int = 0,
      threshold_seconds: int = 60
  ) -> List[Tuple[str, int]]:
    """ Return the top uncategorized window names sorted by total time spent.

    Entries with total time less than the threshold are excluded.

    Args:
      limit: The maximum number of entries to return.
      offset: The number of entries to skip before starting to collect the result set.
      threshold_seconds: The minimum total time in seconds for an entry to be included.

    Returns:
      List[Tuple[str, int]]: A list of tuples containing (window_name, total_time_seconds).
    """
    with self._db_conn.get_session() as session:
      try:
        uncategorized_id = session.query(Category.id).filter(
          Category.name == "Uncategorized").scalar()
        query = (session.query(
            Activity.window_name,
            (func.sum(func.julianday(Activity.time_stop) -
             func.julianday(Activity.time_start)) * 86400).label("total_time_seconds")
          )
          .filter(or_(Activity.category_id.is_(None), Activity.category_id == uncategorized_id))
          .group_by(Activity.window_name)
          .having(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)) * 86400 >= threshold_seconds)
          .order_by(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)).desc())
          .limit(limit)
          .offset(offset))

        result = query.all()
        return [(r[0], int(r[1])) for r in result]
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve top uncategorized window names: {e}")
        return []

  def get_top_uncategorized_entries(
      self,
      limit: int = 10,
      offset: int = 0
  ) -> List[Tuple[str, str, int]]:
    """ Return the top uncategorized entries sorted by total time spent.

    Args:
      limit: The maximum number of entries to return.
      offset: The number of entries to skip before starting to collect the result set.

    Returns:
      List[Tuple[str, str, int]]: A list of tuples containing (window_class, window_name, total_time_seconds).
    """
    with self._db_conn.get_session() as session:
      try:
        uncategorized_id = session.query(Category.id).filter(
          Category.name == "Uncategorized").scalar()
        query = (session.query(
            Activity.window_class,
            Activity.window_name,
            (func.sum(func.julianday(Activity.time_stop) -
             func.julianday(Activity.time_start)) * 86400).label("total_time_seconds")
          )
          .filter(or_(Activity.category_id.is_(None), Activity.category_id == uncategorized_id))
          .group_by(Activity.window_class, Activity.window_name)
          .order_by(func.sum(func.julianday(Activity.time_stop) - func.julianday(Activity.time_start)).desc())
          .limit(limit)
          .offset(offset))

        result = query.all()
        return [(r[0], r[1], int(r[2])) for r in result]
      except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve top uncategorized entries: {e}")
        return []
