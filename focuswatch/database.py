import sqlite3
import time
from focuswatch.config import Config


class DatabaseManager:
  def __init__(self):
    self._conn = None
    self._config = Config()
    self._db_name = self._config.get_config('Database', 'location')

    try:
      dburi = f"file:{self._db_name}?mode=rw"
      self._conn = sqlite3.connect(dburi, uri=True)
    except sqlite3.OperationalError:
      print("Error connecting to database")
      print("Creating new database")
      self._create_db()

    self._cur = self._conn.cursor()

  def __del__(self):
    if self._conn is not None:
      self._conn.close()

  def _create_db(self):
    self._conn = sqlite3.connect(self._db_name)
    self._cur = self._conn.cursor()

    self._cur.execute('''
    CREATE TABLE "activity_log" (
        "time_start"	TEXT NOT NULL,
        "time_stop" 	TEXT NOT NULL,
        "window_class"  TEXT NOT NULL,
        "window_name"	TEXT NOT NULL,
        "category_id"         INTEGER,
        FOREIGN KEY("category_id") REFERENCES "categories"("id") 
    );''')

    self._cur.execute('''
      CREATE TABLE "categories" (
        "id"	INTEGER NOT NULL UNIQUE,
        "name"	TEXT NOT NULL,
        "parent_category"	INTEGER,
        FOREIGN KEY("parent_category") REFERENCES "categories"("id"),
        PRIMARY KEY("id" AUTOINCREMENT)
      );''')

    self._cur.execute('''
      CREATE TABLE "keywords" (
        "id" INTEGER NOT NULL UNIQUE,
        "name"	TEXT NOT NULL,
        "category_id"	INTEGER,
        FOREIGN KEY("category_id") REFERENCES "categories"("id")
        ON DELETE CASCADE ON UPDATE CASCADE
        PRIMARY KEY("id" AUTOINCREMENT)
      );''')

    self._conn.commit()

    print("Database created successfully")

  """ Activities """

  def insert_activity(self, window_class, window_name, time_start, time_stop, category):
    if self._conn is not None:
      t = (time_start, time_stop, window_class, window_name, category)
      self._cur.execute(
          'INSERT INTO activity_log VALUES (?, ?, ?, ?, ?)', t)
      self._conn.commit()
      if self._conn.total_changes > 0:
        return True
    return False

  def get_all_activities(self):
    if self._conn is not None:
      res = self._cur.execute("SELECT * FROM activity_log")
      if res:
        return res.fetchall()
      else:
        return ""

  # Get entries from-to (?)

  def get_todays_entries(self):
    if self._conn is not None:
      today = time.strftime("%d-%m",
                            time.localtime(time.time()))
      res = self._cur.execute(
          f"SELECT * FROM 'activity_log' WHERE time_start LIKE '%{today}%'")
      return res.fetchall()

  def get_weeks_entries(self):
    if self._conn is not None:
      res = self._cur.execute(
          "SELECT * FROM 'activity_log' WHERE DATETIME(time_start) >= DATETIME('now', 'weekday 0', '-7 days')")
      return res.fetchall()

  """ Categories """

  def create_category(self, category_name, parent_category=None):
    if self._conn is not None:
      t = (category_name, parent_category)
      self._cur.execute(
        'INSERT INTO categories (name, parent_category) VALUES (?, ?)', t)
      self._conn.commit()
      if self._conn.total_changes > 0:
        return True
    return False

  def get_all_categories(self):
    if self._conn is not None:
      res = self._cur.execute("SELECT * FROM categories")
      if res:
        return res.fetchall()
      else:
        return ""

  """ Keywords """

  def add_keyword(self, keyword_name, category_id):
    if self._conn is not None:
      t = (category_id, keyword_name)
      self._cur.execute(
        'INSERT INTO keywords (category_id, name) VALUES (?, ?)', t)
      self._conn.commit()
      if self._conn.total_changes > 0:
        return True
    return False

  def get_all_keywords(self):
    """ Returns all keyword entries in the database """
    if self._conn is not None:
      res = self._cur.execute("SELECT * FROM keywords")
      if res:
        return res.fetchall()
      else:
        return ""

  def get_categories_from_keyword(self, keyword):
    """ Returns categories for given keyword sorted by depth """
    if self._conn is not None:
      t = (f'%{keyword}%',)
      res = self._cur.execute(
          """
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
          """,
          t)
      if res:
        return [row[0] for row in res.fetchall()]
      else:
        return ""


if __name__ == "__main__":
  db_object = DatabaseManager()
  db_object.create_category("work")
  db_object.create_category("programming", 1)
  db_object.create_category("hobby")
  db_object.create_category("programming", 3)
  db_object.create_category("python", 4)
  db_object.add_keyword("code", 1)
  db_object.add_keyword("code", 5)
  db_object.add_keyword("alacritty", 1)
  # entries = db_object.get_all_entries()
  entries = db_object.get_all_keywords()
  print(entries)
  entries = db_object.get_categories_from_keyword('VSCodium')
  print(entries)
