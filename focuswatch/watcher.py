import subprocess
import time
from sys import platform

from config import load_config
from database import DatabaseManager


class Watcher():
  def __init__(self):
    self._window_name = self.get_active_window_name()
    self._window_class = self.get_active_window_class()
    self._time_start = time.time()
    self._time_stop = None
    self._duration = 0
    self._database = DatabaseManager()

  def get_active_window_name(self):
    if platform in ['linux', 'linux2']:
      cmd = ['xdotool', 'getactivewindow', 'getwindowname']
      try:
        name = subprocess.check_output(
          cmd, encoding='utf-8', stderr=subprocess.STDOUT).strip()
      except subprocess.CalledProcessError:
        name = "None"
      return name
    # TODO Windows support
    else:
      print("Platform currently not supported.")
      exit()

  def get_active_window_class(self):
    if platform in ['linux', 'linux2']:
      cmd = ['xdotool', 'getactivewindow', 'getwindowclassname']
      try:
        class_name = subprocess.check_output(
          cmd, encoding='utf-8', stderr=subprocess.STDOUT).strip()
      except subprocess.CalledProcessError:
        class_name = "None"
      return class_name
    # TODO Windows support
    else:
      print("Platform currently not supported.")
      exit()

  def save_entry(self):
    print(
        f"[{self._duration :.3f}] [{self._window_class}] {self._window_name[:32]}")
    self._database.insert_activity(
      self._window_class,
      self._window_name,
      time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(self._time_start)),
      time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(self._time_stop)),
      self._duration
      # TODO tags
    )

  def monitor(self):
    config = load_config()
    watch_interval = int(config['General']['watch_interval'])
    while (True):
      if self._window_name != self.get_active_window_name():
        self._time_stop = time.time()
        self._duration = round(self._time_stop - self._time_start, 3)
        self.save_entry()
        self._time_start = time.time()
        self._window_name = self.get_active_window_name()
        self._window_class = self.get_active_window_class()

      time.sleep(watch_interval)


if __name__ == '__main__':
  watcher = Watcher()
  watcher.monitor()
