""" Database manager for FocusWatch.

This module provides a class for managing the database for FocusWatch.
"""

import logging
import sqlite3

from focuswatch.database.category_manager import CategoryManager
from focuswatch.database.database_connection import DatabaseConnection
from focuswatch.database.keyword_manager import KeywordManager


class DatabaseManager:
  """ Class for managing the database for FocusWatch. """

  def __init__(self):
    """ Initialize the database manager. """

    self._db_conn = DatabaseConnection()
    self._db_conn.connect_or_create()

    if not self.database_exists():
      self._create_db()

      self._category_manager = CategoryManager()
      self._keyword_manager = KeywordManager()

      self._category_manager.insert_default_categories()
      self._keyword_manager.insert_default_keywords()

  def database_exists(self) -> bool:
    """ Check if the database and tables exist. 

    Returns:
      bool: True if the database and tables exist, False otherwise.
    """
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name='activity_log';"
    result = self._db_conn.execute_query(query)
    if result:
      logging.info("Database and tables exist.")
      return True
    else:
      logging.info("Database and tables do not exist.")
      return False

  def _create_db(self):
    """ Create the database. """
    create_table_queries = [
      '''
      CREATE TABLE "activity_log" (
          "time_start" TEXT NOT NULL,
          "time_stop" TEXT NOT NULL,
          "window_class" TEXT NOT NULL,
          "window_name" TEXT NOT NULL,
          "category_id" INTEGER,
          "project_id" INTEGER,
          FOREIGN KEY("category_id") REFERENCES "categories"("id")
      );''',
      '''
      CREATE TABLE "categories" (
          "id" INTEGER NOT NULL UNIQUE,
          "name" TEXT NOT NULL,
          "parent_category" INTEGER,
          "color" TEXT,
          FOREIGN KEY("parent_category") REFERENCES "categories"("id"),
          PRIMARY KEY("id" AUTOINCREMENT)
      );''',
      '''
      CREATE TABLE "keywords" (
          "id" INTEGER NOT NULL UNIQUE,
          "name" TEXT NOT NULL,
          "category_id" INTEGER,
          FOREIGN KEY("category_id") REFERENCES "categories"("id")
          ON DELETE CASCADE ON UPDATE CASCADE,
          PRIMARY KEY("id" AUTOINCREMENT)
      );''',
      '''
      CREATE TABLE "projects" (
          "id" INTEGER NOT NULL UNIQUE,
          "name" TEXT NOT NULL,
          "color" TEXT NOT NULL,
          PRIMARY KEY("id" AUTOINCREMENT)
      );''',
      '''
      CREATE TABLE "tasks" (
          "id" INTEGER NOT NULL UNIQUE,
          "name" TEXT NOT NULL,
          "project_id" INTEGER,
          "completed" INTEGER,
          FOREIGN KEY("project_id") REFERENCES "projects"("id")
          ON DELETE CASCADE ON UPDATE CASCADE,
          PRIMARY KEY("id" AUTOINCREMENT)
      );'''
    ]

    try:
      for query in create_table_queries:
        self._db_conn.execute_update(query)
      logging.info("Database created successfully")
    except sqlite3.DatabaseError as e:
      logging.error(f"Error creating database: {e}")
