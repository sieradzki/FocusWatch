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
      self._conn = sqlite3.connect(dburi, uri=True, check_same_thread=False)
    except sqlite3.OperationalError:
      print("Error connecting to database")
      print("Creating new database")
      self._create_db()
      self.insert_default_categories()

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
        "project_id" INTEGER,
        FOREIGN KEY("category_id") REFERENCES "categories"("id") 
    );''')

    self._cur.execute('''
      CREATE TABLE "categories" (
        "id"	INTEGER NOT NULL UNIQUE,
        "name"	TEXT NOT NULL,
        "parent_category"	INTEGER,
        "color" TEXT,
        FOREIGN KEY("parent_category") REFERENCES "categories"("id"),
        PRIMARY KEY("id" AUTOINCREMENT)
      );''')
    # "ignore_case" INTEGER,

    self._cur.execute('''
      CREATE TABLE "keywords" (
        "id" INTEGER NOT NULL UNIQUE,
        "name"	TEXT NOT NULL,
        "category_id"	INTEGER,
        FOREIGN KEY("category_id") REFERENCES "categories"("id")
        ON DELETE CASCADE ON UPDATE CASCADE
        PRIMARY KEY("id" AUTOINCREMENT)
      );''')

    self._cur.execute('''
      CREATE TABLE "projects" (
        "id" INTEGER NOT NULL UNIQUE,
        "name" TEXT NOT NULL,
        "color" TEXT NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT)
      );''')

    self._cur.execute('''
      CREATE TABLE "tasks" (
        "id" INTEGER NOT NULL UNIQUE,
        "name" TEXT NOT NULL,
        "project_id" INTEGER,
        "completed" INTEGER,
        FOREIGN KEY("project_id") REFERENCES "projects"("id")
        ON DELETE CASCADE ON UPDATE CASCADE
        PRIMARY KEY("id" AUTOINCREMENT)
      );''')

    self._conn.commit()

    print("Database created successfully")

  def insert_default_categories(self):
    """ Default categories based on activity watch """
    self.create_category("Work", None, "#00cc00")
    self.create_category("Programming", 1)
    self.create_category("Documents", 1)
    self.create_category("Image", 1)
    self.create_category("Audio", 1)
    self.create_category("3D", 1)

    self.create_category("Comms", None, "#33ccff")
    self.create_category("IM", 7)
    self.create_category("Email", 7)

    self.create_category("Media", None, "#ff0000")
    self.create_category("Games", 10)
    self.create_category("Video", 10)
    self.create_category("Social media", 10)
    self.create_category("Music", 10)

    self.create_category("Uncategorized", None, "#8c8c8c")

    self.insert_default_keywords()

  def insert_default_keywords(self):
    """ Default keywords based on activity watch """
    self.add_keyword("Google Docs", 1)
    self.add_keyword("libreoffice", 1)

    self.add_keyword("GitHub", 2)
    self.add_keyword("Stack Overflow", 2)
    self.add_keyword("BitBucket", 2)
    self.add_keyword("Gitlab", 2)
    self.add_keyword("vim", 2)
    self.add_keyword("Spyder", 2)
    self.add_keyword("kate", 2)
    self.add_keyword("Visual Studio", 2)
    self.add_keyword("code", 2)

    self.add_keyword("Gimp", 4)
    self.add_keyword("Inkscape", 4)

    self.add_keyword("Audacity", 5)

    self.add_keyword("Blender", 6)

    self.add_keyword("Messenger", 8)
    self.add_keyword("Signal", 8)
    self.add_keyword("WhatsApp", 8)
    self.add_keyword("Slack", 8)
    self.add_keyword("Discord", 8)

    self.add_keyword("Gmail", 9)
    self.add_keyword("Thunderbird", 9)
    self.add_keyword("mutt", 9)
    self.add_keyword("alpine", 9)

    self.add_keyword("Minecraft", 11)
    self.add_keyword("Steam", 11)

    self.add_keyword("YouTube", 12)
    self.add_keyword("mpv", 12)
    self.add_keyword("VLC", 12)
    self.add_keyword("Twitch", 12)

    self.add_keyword("reddit", 13)
    self.add_keyword("Facebook", 13)
    self.add_keyword("Instagram", 13)

    self.add_keyword("Spotify", 14)

  """ Activities """

  def insert_activity(self, window_class, window_name, time_start, time_stop, category, project_id):
    if self._conn is not None:
      t = (time_start, time_stop, window_class,
           window_name, category, project_id)
      self._cur.execute(
          'INSERT INTO activity_log VALUES (?, ?, ?, ?, ?, ?)', t)
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

  # def get_months_entries(self):
    # if self._conn is not None:
      # res = self._cur.execute("SELECT * FROM 'activity_log' WHERE DATETIME(time_start) >= DATETIME('now', 'weekday 0', '-7 days')")

  """ Categories """

  def create_category(self, category_name, parent_category=None, color=None):
    if self._conn is not None:
      t = (category_name, parent_category, color)
      self._cur.execute(
        'INSERT INTO categories (name, parent_category, color) VALUES (?, ?, ?)', t)
      self._conn.commit()
      if self._conn.total_changes > 0:
        return True
    return False

    # TODO Reclassify every entry ?

  def get_all_categories(self):
    if self._conn is not None:
      res = self._cur.execute("SELECT * FROM categories")
      if res:
        return res.fetchall()
      else:
        return ""

  def get_category_by_id(self, id):
    if self._conn is not None:
      t = (id,)
      res = self._cur.execute("SELECT * FROM categories where id=?", t)
      if res:
        result = res.fetchall()
        if len(result) > 0:
          return result[0]
        else:
          return ""
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
    # TODO no longer used
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

  def get_category_depth(self, category_id):
    if self._conn is not None:
      t = (category_id,)
      res = self._cur.execute(
        """
          WITH RECURSIVE CategoryHierarchy(id, depth) AS (
            SELECT id, 0 as depth
            FROM categories
            WHERE parent_category IS NULL
            UNION ALL
            SELECT c.id, ch.depth + 1
            FROM categories c
            JOIN CategoryHierarchy ch ON c.parent_category = ch.id
          )
          SELECT depth
          FROM CategoryHierarchy
          WHERE id = ?;
        """, t
      )
      if res:
        return res.fetchall()[0][0]
      else:
        return ""

  def get_category_id_from_name(self, category_name):
    if self._conn is not None:
      t = (category_name,)
      res = self._cur.execute('SELECT id FROM categories where name=?', t)
      if res:
        return res.fetchall()[0][0]
      else:
        return ""


if __name__ == "__main__":
  db_object = DatabaseManager()
  # db_object.create_category("work")
  # db_object.create_category("programming", 1)
  # db_object.create_category("hobby")
  # db_object.create_category("programming", 3)
  # db_object.create_category("python", 4)
  # db_object.add_keyword("code", 1)
  # db_object.add_keyword("code", 5)
  # db_object.add_keyword("alacritty", 1)
  # entries = db_object.get_all_entries()
  # entries = db_object.get_all_keywords()
  # print(entries)
  # entries = db_object.get_categories_from_keyword('VSCodium')
  # print(entries)
  today = time.strftime("%Y-%m-%d", time.localtime(time.time()))
  time_from = f"{today} 00:00:00"
  time_to = f"{today} 23:59:59"
  entries = db_object.get_entries_from_to(time_from, time_to)
  print(entries)
  entries = db_object.get_todays_entries()
  print(entries)
