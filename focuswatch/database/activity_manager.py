""" Activity Manager Module

This module is responsible for managing the activities in the database.
"""

import time
from datetime import datetime
from typing import List, Optional, Tuple
import logging

from focuswatch.database.database_connection import DatabaseConnection
from focuswatch.database.database_manager import DatabaseManager


logger = logging.getLogger(__name__)


class ActivityManager:
  """ Class for managing activities in the database. """

  def __init__(self) -> None:
    """ Initialize the ActivityManager. """
    self._db_conn = DatabaseConnection()
    self._db_conn.connect()

  def insert_activity(
      self,
      window_class: str,
      window_name: str,
      time_start: datetime,
      time_stop: datetime,
      category_id: Optional[int],
      project_id: Optional[int]
    ) -> bool:
    """ Insert an activity into the database.

    Args:
      window_class: The class of the window.
      window_name: The name of the window.
      time_start: The start time of the activity.
      time_stop: The stop time of the activity.
      category_id: The category id of the activity.
      project_id: The project id of the activity.

    Returns:
      True if the activity was inserted successfully, False otherwise.
    """
    query = 'INSERT INTO activity_log (time_start, time_stop, window_class, window_name, category_id, project_id) VALUES (?, ?, ?, ?, ?, ?)'
    params = (time_start.isoformat(), time_stop.isoformat(), window_class,
              window_name, category_id, project_id)
    result = self._db_conn.execute_update(query, params)
    return result

  def update_category(self, activity_id: int, category_id: int) -> bool:
    """ Update the category id of an activity.

    Args:
      activity_id: The id of the activity to update.
      category_id: The new category id.

    Returns:
      True if the category id was updated successfully, False otherwise.
    """
    query = 'UPDATE activity_log SET category_id = ? WHERE id = ?'
    params = (category_id, activity_id)
    result = self._db_conn.execute_update(query, params)
    return result

  def get_all_activities(self) -> List[Tuple]:
    """ Return all activity entries in the database. """
    query = "SELECT * FROM activity_log"
    result = self._db_conn.execute_query(query)
    return result if result else []

  def get_by_category_id(self, category_id: int) -> List[Tuple]:
    """ Return all activity entries with a given category id.

    Args:
      category_id: The category id to retrieve entries for.
    """
    query = "SELECT * FROM activity_log WHERE category_id = ?"
    params = (category_id,)
    result = self._db_conn.execute_query(query, params)
    return result if result else []

  def get_todays_entries(self) -> List[Tuple]:
    """ Return all entries for today. """
    today = datetime.now().strftime("%Y-%m-%d")
    query = "SELECT * FROM activity_log WHERE time_start LIKE ?"
    params = (f'{today}%',)
    result = self._db_conn.execute_query(query, params)
    return result

  def get_date_entries(self, date: datetime) -> List[Tuple]:
    """ Return all entries for a given date.

    Args:
      date: The date to retrieve entries for.
    """
    formatted_date = date.strftime("%Y-%m-%d")
    query = "SELECT * FROM activity_log WHERE time_start LIKE ?"
    params = (f'{formatted_date}%',)
    result = self._db_conn.execute_query(query, params)
    return result

  def get_period_entries(self, period_start: datetime, period_end: Optional[datetime] = None) -> List[Tuple]:
    """ Return all entries for a given period.

    Args:
      period_start: The start date of the period.
      period_end: The end date of the period. If None, only date_start is considered.
    """
    if period_end:
      query = "SELECT * FROM activity_log WHERE time_start BETWEEN ? AND ?"
      params = (period_start.isoformat(), period_end.isoformat())
    else:
      query = "SELECT * FROM activity_log WHERE date(time_start) = date(?)"
      params = (period_start.isoformat(),)

    result = self._db_conn.execute_query(query, params)
    return result

  def get_weeks_entries(self) -> List[Tuple]:
    """ Return all entries for the past week. """
    query = "SELECT * FROM activity_log WHERE DATETIME(time_start) >= DATETIME('now', 'weekday 0', '-7 days')"
    result = self._db_conn.execute_query(query)
    return result

  def get_date_entries_class_time_total(self, date: datetime) -> List[Tuple]:
    """ Return the total time spent on each window class for a given date.

    Args:
      date: The date to retrieve entries for.
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
    result = self._db_conn.execute_query(query, params)
    return result

  def get_period_entries_class_time_total(self, period_start: datetime, period_end: Optional[datetime] = None) -> List[Tuple]:
    """ Return the total time spent on each window class for a given period.

    Args:
        period_start: The start date of the period.
        period_end: The end date of the period. If None, only period_start is considered.
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

    return self._db_conn.execute_query(query, params)

  def get_longest_duration_category_id_for_window_class_on_date(
      self, date: datetime, window_class: str
    ) -> Optional[int]:
    """ Return the category with the longest duration for a given window class on a given date.

    Args:
      date: The date to retrieve entries for.
      window_class: The window class to retrieve entries for.
    """
    formatted_date = date.strftime("%Y-%m-%d")
    query = """
      SELECT category_id
      FROM activity_log
      WHERE strftime('%Y-%m-%d', time_start) = strftime('%Y-%m-%d', ?)
        AND window_class = ?
      ORDER BY strftime('%s', time_stop, 'utc') - strftime('%s', time_start, 'utc') DESC
      LIMIT 1
    """
    params = (formatted_date, window_class)
    result = self._db_conn.execute_query(query, params)
    return result[0][0] if result else None

  def get_longest_duration_category_id_for_window_class_in_period(
          self, period_start: datetime, window_class: str, period_end: Optional[datetime] = None) -> Optional[int]:
    """ Return the category with the longest duration for a given window class in a given period.

    Args:
        period_start: The start date of the period.
        window_class: The window class to retrieve entries for.
        period_end: The end date of the period. If None, only period_start is considered.
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
      params = (period_start.isoformat(),
                period_end.isoformat(), window_class)
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

    result = self._db_conn.execute_query(query, params)
    return result[0][0] if result else None

  def get_top_uncategorized_window_classes(self, limit: int = 10) -> List[Tuple]:
    """ Return the top uncategorized window classes sorted by total time spent.

    Args:
        limit: The maximum number of window classes to return.

    Returns:
        A list of tuples containing (id, window_class, total_time_seconds).
    """
    query = """
        SELECT id, window_class,
        SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
        FROM activity_log
        WHERE category_id IS NULL OR category_id = (SELECT id FROM categories WHERE name = 'Uncategorized')
        GROUP BY window_class
        ORDER BY total_time_seconds DESC
        LIMIT ?
    """
    params = (limit,)
    result = self._db_conn.execute_query(query, params)
    return result if result else []

  def get_top_uncategorized_window_names(self, limit: int = 10) -> List[Tuple]:
    """ Return the top uncategorized window names sorted by total time spent. 

    Args:
      limit: The maximum number of window names to return.

    Returns:
      A list of tuples containing (id, window_name, total_time_seconds).
    """
    query = """
        SELECT id, window_name,
        SUM(strftime('%s', time_stop) - strftime('%s', time_start)) AS total_time_seconds
        FROM activity_log
        WHERE category_id IS NULL OR category_id = (SELECT id FROM categories WHERE name = 'Uncategorized')
        GROUP BY window_name
        ORDER BY total_time_seconds DESC
        LIMIT ?
    """
    params = (limit,)
    result = self._db_conn.execute_query(query, params)
    return result if result else []
