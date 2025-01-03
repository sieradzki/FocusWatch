""" Database manager for FocusWatch.

This module provides a class for managing the database for FocusWatch.
"""

import logging
import sqlite3

from focuswatch.database.database_connection import DatabaseConnection
from focuswatch.services.category_service import CategoryService
from focuswatch.services.keyword_service import KeywordService

logger = logging.getLogger(__name__)


class DatabaseManager:
  """ Class for managing the database for FocusWatch. """

  def __init__(self):
    """ Initialize the database manager. """

    self._db_conn = DatabaseConnection()
    self._db_conn.connect_or_create()

    if not self.database_exists():
      logger.info("Database does not exist. Creating database.")
      self._create_db()

      self._category_service = CategoryService()
      self._keyword_service = KeywordService()

      self._category_service.insert_default_categories()
      self._keyword_service.insert_default_keywords()

  def database_exists(self) -> bool:
    """ Check if the database and tables exist. 

    Returns:
      bool: True if the database and tables exist, False otherwise.
    """
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name='activity';"
    result = self._db_conn.execute_query(query)
    try:
      result = self._db_conn.execute_query(query)
      return bool(result)
    except sqlite3.Error as e:
      logger.error(f"Error checking database existence: {e}")
      return False

  def _create_db(self):
    """ Create the database. """
    create_table_queries = [
      '''
      CREATE TABLE "activity" (
          "id" INTEGER NOT NULL UNIQUE,
          "time_start" TEXT NOT NULL,
          "time_stop" TEXT NOT NULL,
          "window_class" TEXT NOT NULL,
          "window_name" TEXT NOT NULL,
          "category_id" INTEGER,
          "project_id" INTEGER,
          "focused" INTEGER NOT NULL DEFAULT 0,
          FOREIGN KEY("category_id") REFERENCES "categories"("id"),
          PRIMARY KEY("id" AUTOINCREMENT)
      );''',
      '''
      CREATE TABLE "categories" (
          "id" INTEGER NOT NULL UNIQUE,
          "name" TEXT NOT NULL,
          "parent_category" INTEGER,
          "color" TEXT,
          "focused" INTEGER NOT NULL DEFAULT 0,
          FOREIGN KEY("parent_category") REFERENCES "categories"("id"),
          PRIMARY KEY("id" AUTOINCREMENT)
      );''',
      '''
      CREATE TABLE "keywords" (
          "id" INTEGER NOT NULL UNIQUE,
          "name" TEXT NOT NULL,
          "category_id" INTEGER,
          "match_case" INTEGER NOT NULL DEFAULT 0,
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
      logger.info("Database created successfully")
    except sqlite3.DatabaseError as e:
      logger.error(f"Error creating database: {e}")
