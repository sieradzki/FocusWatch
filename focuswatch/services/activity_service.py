""" Activity Service Module """

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from focuswatch.database.database_connection import DatabaseConnection
from focuswatch.models.activity import Activity

logger = logging.getLogger(__name__)


class ActivityService:
  """Service class for managing activities in the FocusWatch application."""

  def __init__(self):
    self._db_conn = DatabaseConnection()
    self._db_conn.connect()

  def insert_activity(self, activity: Activity) -> bool:
    """Insert an activity into the database.

    Args:
      activity: The Activity object to be inserted.

    Returns:
      bool: True if the activity was inserted successfully, False otherwise.
    """
    query = '''
      INSERT INTO activity_log 
      (time_start, time_stop, window_class, window_name, category_id, project_id) 
      VALUES (?, ?, ?, ?, ?, ?)
    '''
    params = (
      activity.time_start.isoformat(),
      activity.time_stop.isoformat() if activity.time_stop else None,
      activity.window_class,
      activity.window_name,
      activity.category_id,
      activity.project_id
    )

    try:
      self._db_conn.execute_update(query, params)
      logger.debug(f"Inserted new activity: {activity.window_name}")
      return True
    except Exception as e:
      logger.error(f"Failed to insert activity: {e}")
      return False

  def update_category(self, activity_id: int, category_id: int) -> bool:
    """Update the category id of an activity.

    Args:
      activity_id: The id of the activity to update.
      category_id: The new category id.

    Returns:
      bool: True if the category id was updated successfully, False otherwise.
    """
    query = 'UPDATE activity_log SET category_id = ? WHERE id = ?'
    params = (category_id, activity_id)

    try:
      self._db_conn.execute_update(query, params)
      return True
    except Exception as e:
      logger.error(f"Failed to update category for activity: {e}")
      return False

  def bulk_update_category(self, activity_ids: List[int], category_id: int) -> bool:
    """Bulk update the category_id for multiple activities.

    Args:
      activity_ids: List of activity IDs to update.
      category_id: The new category ID.

    Returns:
      bool: True if the categories were updated successfully, False otherwise.
    """
    if not activity_ids:
      return True

    # Construct placeholders for parameterized query
    placeholders = ','.join(['?'] * len(activity_ids))
    query = f'UPDATE activity_log SET category_id = ? WHERE id IN ({
        placeholders})'
    params = [category_id] + activity_ids

    try:
      self._db_conn.execute_update(query, params)
      return True
    except Exception as e:
      logger.error(f"Failed to bulk update categories for activities: {e}")
      return False

  def get_all_activities(self) -> List[Activity]:
    """Return all activity entries in the database.

    Returns:
      List[Activity]: A list of all Activity objects in the database.
    """
    query = "SELECT * FROM activity_log"

    try:
      results = self._db_conn.execute_query(query)
      return [Activity(*row) for row in results]
    except Exception as e:
      logger.error(f"Failed to retrieve activities: {e}")
      return []

  def get_by_category_id(self, category_id: int) -> List[Activity]:
    """Return all activity entries with a given category id.

    Args:
      category_id: The category id to retrieve entries for.

    Returns:
      List[Activity]: A list of Activity objects with the specified category id.
    """
    query = "SELECT * FROM activity_log WHERE category_id = ?"
    params = (category_id,)

    try:
      results = self._db_conn.execute_query(query, params)
      return [Activity(*row) for row in results]
    except Exception as e:
      logger.error(f"Failed to retrieve activities for category {
                   category_id}: {e}")
      return []

  def get_todays_entries(self) -> List[Activity]:
    """Return all entries for today.

    Returns:
      List[Activity]: A list of Activity objects for today.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    query = "SELECT * FROM activity_log WHERE time_start LIKE ?"
    params = (f'{today}%',)

    try:
      results = self._db_conn.execute_query(query, params)
      return [Activity(*row) for row in results]
    except Exception as e:
      logger.error(f"Failed to retrieve today's activities: {e}")
      return []

  def get_date_entries(self, date: datetime) -> List[Activity]:
    """Return all entries for a given date.

    Args:
      date: The date to retrieve entries for.

    Returns:
      List[Activity]: A list of Activity objects for the specified date.
    """
    formatted_date = date.strftime("%Y-%m-%d")
    query = "SELECT * FROM activity_log WHERE time_start LIKE ?"
    params = (f'{formatted_date}%',)

    try:
      results = self._db_conn.execute_query(query, params)
      return [Activity(*row) for row in results]
    except Exception as e:
      logger.error(f"Failed to retrieve activities for date {
                   formatted_date}: {e}")
      return []

  def get_period_entries(self, period_start: datetime, period_end: Optional[datetime] = None) -> List[Activity]:
    """Return all entries for a given period.

    Args:
      period_start: The start date of the period.
      period_end: The end date of the period. If None, only period_start is considered.

    Returns:
      List[Activity]: A list of Activity objects for the specified period.
    """
    if period_end:
      query = "SELECT * FROM activity_log WHERE time_start BETWEEN ? AND ?"
      params = (period_start.isoformat(), period_end.isoformat())
    else:
      query = "SELECT * FROM activity_log WHERE date(time_start) = date(?)"
      params = (period_start.isoformat(),)

    try:
      results = self._db_conn.execute_query(query, params)
      return [Activity(*row) for row in results]
    except Exception as e:
      logger.error(f"Failed to retrieve activities for period: {e}")
      return []

  def get_date_entries_class_time_total(self, date: datetime) -> List[Tuple[str, Optional[int], int]]:
    """Return the total time spent on each window class for a given date.

    Args:
      date: The date to retrieve entries for.

    Returns:
      List[Tuple[str, Optional[int], int]]: A list of tuples containing 
      (window_class, category_id, total_time_seconds).
    """
    formatted_date = date.strftime("%Y-%m-%d")
    query = """
      SELECT window_class, category_id,
      SUM(strftime('%s', time_stop, 'utc') - strftime('%s', time_start, 'utc')) AS total_time_seconds
      FROM activity_log
      WHERE strftime('%Y-%m-%d', time_start) = strftime('%Y-%m-%d', ?)
      GROUP BY window_class
      ORDER BY total_time_seconds DESC
    """
    params = (formatted_date,)

    try:
      return self._db_conn.execute_query(query, params)
    except Exception as e:
      logger.error(f"Failed to retrieve class time totals for date {
                   formatted_date}: {e}")
      return []

  def get_period_entries_class_time_total(self, period_start: datetime, period_end: Optional[datetime] = None) -> List[Tuple[str, Optional[int], int]]:
    """Return the total time spent on each window class for a given period.

    Args:
      period_start: The start date of the period.
      period_end: The end date of the period. If None, only period_start is considered.

    Returns:
      List[Tuple[str, Optional[int], int]]: A list of tuples containing 
      (window_class, category_id, total_time_seconds).
    """
    if period_end:
      query = """
        SELECT window_class, category_id,
        SUM(strftime('%s', time_stop, 'utc') - strftime('%s', time_start, 'utc')) AS total_time_seconds
        FROM activity_log
        WHERE time_start BETWEEN ? AND ?
        GROUP BY window_class
        ORDER BY total_time_seconds DESC
      """
      params = (period_start.isoformat(), period_end.isoformat())
    else:
      query = """
        SELECT window_class, category_id,
        SUM(strftime('%s', time_stop, 'utc') - strftime('%s', time_start, 'utc')) AS total_time_seconds
        FROM activity_log
        WHERE strftime('%Y-%m-%d', time_start) = strftime('%Y-%m-%d', ?)
        GROUP BY window_class
        ORDER BY total_time_seconds DESC
      """
      params = (period_start.strftime("%Y-%m-%d"),)

    try:
      return self._db_conn.execute_query(query, params)
    except Exception as e:
      logger.error(f"Failed to retrieve class time totals for period: {e}")
      return []

  def get_period_entries_name_time_total(self, period_start: datetime, period_end: Optional[datetime] = None) -> List[Tuple[str, Optional[int], int]]:
    """Return the total time spent on each window name for a given period.

    Args:
      period_start: The start date of the period.
      period_end: The end date of the period. If None, only period_start is considered.

    Returns:
      List[Tuple[str, Optional[int], int]]: A list of tuples containing 
      (window_name, category_id, total_time_seconds).
    """
    if period_end:
      query = """
        SELECT window_name, category_id,
        SUM(strftime('%s', time_stop, 'utc') - strftime('%s', time_start, 'utc')) AS total_time_seconds
        FROM activity_log
        WHERE time_start BETWEEN ? AND ?
        GROUP BY window_name
        ORDER BY total_time_seconds DESC
      """
      params = (period_start.isoformat(), period_end.isoformat())
    else:
      query = """
        SELECT window_name, category_id,
        SUM(strftime('%s', time_stop, 'utc') - strftime('%s', time_start, 'utc')) AS total_time_seconds
        FROM activity_log
        WHERE strftime('%Y-%m-%d', time_start) = strftime('%Y-%m-%d', ?)
        GROUP BY window_name
        ORDER BY total_time_seconds DESC
      """
      params = (period_start.strftime("%Y-%m-%d"),)

    try:
      return self._db_conn.execute_query(query, params)
    except Exception as e:
      logger.error(f"Failed to retrieve name time totals for period: {e}")
      return []

  def get_longest_duration_category_id_for_window_class_on_date(self, date: datetime, window_class: str) -> Optional[int]:
    """Return the category with the longest duration for a given window class on a given date.

    Args:
      date: The date to retrieve entries for.
      window_class: The window class to retrieve entries for.

    Returns:
      Optional[int]: The category ID with the longest duration, or None if not found.
    """
    formatted_date = date.strftime("%Y-%m-%d")
    query = """
      SELECT category_id
      FROM activity_log
      WHERE strftime('%Y-%m-%d', time_start) = strftime('%Y-%m-%d', ?)
        AND window_class = ?
      GROUP BY category_id
      ORDER BY SUM(strftime('%s', time_stop, 'utc') - strftime('%s', time_start, 'utc')) DESC
      LIMIT 1
    """
    params = (formatted_date, window_class)

    try:
      result = self._db_conn.execute_query(query, params)
      return result[0][0] if result else None
    except Exception as e:
      logger.error(f"Failed to retrieve longest duration category for window class {
                   window_class} on date {formatted_date}: {e}")
      return None

  def get_longest_duration_category_id_for_window_class_in_period(self, period_start: datetime, window_class: str, period_end: Optional[datetime] = None) -> Optional[int]:
    """Return the category with the longest duration for a given window class in a given period.

    Args:
      period_start: The start date of the period.
      window_class: The window class to retrieve entries for.
      period_end: The end date of the period. If None, only period_start is considered.

    Returns:
      Optional[int]: The category ID with the longest duration, or None if not found.
    """
    if period_end:
      query = """
        SELECT category_id
        FROM activity_log
        WHERE time_start BETWEEN ? AND ?
          AND window_class = ?
        GROUP BY category_id
        ORDER BY SUM(strftime('%s', time_stop, 'utc') - strftime('%s', time_start, 'utc')) DESC
        LIMIT 1
      """
      params = (period_start.isoformat(), period_end.isoformat(), window_class)
    else:
      query = """
        SELECT category_id
        FROM activity_log
        WHERE strftime('%Y-%m-%d', time_start) = strftime('%Y-%m-%d', ?)
          AND window_class = ?
        GROUP BY category_id
        ORDER BY SUM(strftime('%s', time_stop, 'utc') - strftime('%s', time_start, 'utc')) DESC
        LIMIT 1
      """
      params = (period_start.strftime("%Y-%m-%d"), window_class)

    try:
      result = self._db_conn.execute_query(query, params)
      return result[0][0] if result else None
    except Exception as e:
      logger.error(f"Failed to retrieve longest duration category for window class {
                   window_class} in period: {e}")
      return None

  def get_top_uncategorized_window_classes(self, limit: int = 10, offset: int = 0) -> List[Tuple[str, int]]:
    """ Return the top uncategorized window classes sorted by total time spent. """
    query = """
      SELECT window_class,
      SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
      FROM activity_log
      WHERE category_id IS NULL OR category_id = (SELECT id FROM categories WHERE name = 'Uncategorized')
      GROUP BY window_class
      ORDER BY total_time_seconds DESC
      LIMIT ? OFFSET ?
    """
    params = (limit, offset)
    try:
      return self._db_conn.execute_query(query, params)
    except Exception as e:
      logger.error(f"Failed to retrieve top uncategorized window classes: {e}")
      return []

  def get_top_uncategorized_window_names(self, limit: int = 10, offset: int = 0) -> List[Tuple[str, int]]:
    """ Return the top uncategorized window names sorted by total time spent. """
    query = """
      SELECT window_name,
      SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
      FROM activity_log
      WHERE category_id IS NULL OR category_id = (SELECT id FROM categories WHERE name = 'Uncategorized')
      GROUP BY window_name
      ORDER BY total_time_seconds DESC
      LIMIT ? OFFSET ?
    """
    params = (limit, offset)
    try:
      return self._db_conn.execute_query(query, params)
    except Exception as e:
      logger.error(f"Failed to retrieve top uncategorized window names: {e}")
      return []

  def get_top_uncategorized_entries(self, limit: int = 10, offset: int = 0) -> List[Tuple[str, str, int]]:
    """ Return the top uncategorized entries sorted by total time spent. """
    query = """
        SELECT window_class, window_name,
              SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
        FROM activity_log
        WHERE category_id IS NULL OR category_id = (SELECT id FROM categories WHERE name = 'Uncategorized')
        GROUP BY window_class, window_name
        ORDER BY total_time_seconds DESC
        LIMIT ? OFFSET ?
      """
    params = (limit, offset)
    try:
      rows = self._db_conn.execute_query(query, params)
      return [(row[0], row[1], row[2]) for row in rows]
    except Exception as e:
      logger.error(f"Failed to retrieve top uncategorized entries: {e}")
      return []
