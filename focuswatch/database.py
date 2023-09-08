import sqlite3
import time
from config import load_config


class DatabaseManager:
  def __init__(self):
    self._conn = None
    self._config = load_config()
    self._db_name = self._config['Database']['name']

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
        "duration"      REAL NOT NULL,
        "window_class"  TEXT NOT NULL,
        "window_name"	TEXT NOT NULL,
        "category_id"         INTEGER,
        FOREIGN KEY("category_id") REFERENCES "categories"("id") 
    );''')

    self._cur.execute('''
      CREATE TABLE "categories" (
        "id"	INTEGER NOT NULL UNIQUE,
        "name"	TEXT NOT NULL UNIQUE,
        "parent_category"	INTEGER,
        FOREIGN KEY("parent_category") REFERENCES "categories"("id"),
        PRIMARY KEY("id" AUTOINCREMENT)
      );''')

    self._cur.execute('''
      CREATE TABLE "keywords" (
        "category_id"	INTEGER,
        "name"	TEXT NOT NULL UNIQUE,
        FOREIGN KEY("category_id") REFERENCES "categories"("id")
        ON DELETE CASCADE ON UPDATE CASCADE
      );''')

    self._conn.commit()

    print("Database created successfully")

  def insert_activity(self, window_class, window_name, time_start, time_stop, duration, tags=""):
    if self._conn is not None:
      t = (time_start, time_stop, duration, window_class, window_name, tags)
      self._cur.execute(
          'INSERT INTO activity_log VALUES (?, ?, ?, ?, ?, ?)', t)
      if self._conn.commit():
        return True
      return False

  def create_category(self, category_name, parent_category=None):
    if self._conn is not None:
      t = (category_name, parent_category)
      self._cur.execute(
        'INSERT INTO categories (name, parent_category) VALUES (?, ?)', t)
      if self._conn.commit():
        return True
      return False

  def add_keyword(self, keyword_name, category_id=None, ):
    if self._conn is not None:
      t = (category_id, keyword_name)
      self._cur.execute(
        'INSERT INTO keywords (category_id, name) VALUES (?, ?)', t)
      if self._conn.commit():
        return True
      return False

  def get_all_entries(self):
    if self._conn is not None:
      res = self._cur.execute("SELECT * FROM activity_log")
      if res:
        return res.fetchall()
      else:
        return ""

  """ Get entries from-to (?)"""

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


if __name__ == "__main__":
  db_object = DatabaseManager()
  db_object.create_category("work")
  db_object.create_category("programming", 1)
  db_object.insert_activity('vscodium', 'VSCodium',
                            '19:11', '19:12', 1, 1)
  db_object.add_keyword("vscodium", 1)
  db_object.add_keyword("alacritty")
  entries = db_object.get_all_entries()
  print(entries)
