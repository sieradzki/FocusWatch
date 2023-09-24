import subprocess
import time
from sys import platform

from focuswatch.database import DatabaseManager
from focuswatch.classifier import Classifier
from focuswatch.config import Config


class Watcher():
  def __init__(self, watch_interval=None, verbose=None):
    self._window_name = self.get_active_window_name()
    self._window_class = self.get_active_window_class()
    self._time_start = time.time()
    self._time_stop = None
    self._category = None
    self._database = DatabaseManager()
    self._classifier = Classifier()

    self._config = Config()
    self._watch_interval = float(
      self._config.get_config('General', 'watch_interval')) if not watch_interval else watch_interval
    self._verbose = int(self._config.get_config(
      'General', 'verbose')) if not verbose else verbose

  def __del__(self):
    self.save_entry()

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
    if self._verbose:
      print(
          f"[{self._time_stop - self._time_start :.3f}] [{self._window_class}] {self._window_name[:32]} {self._category}")
    self._database.insert_activity(
      self._window_class,
      self._window_name,
      # YYYY-MM-DD HH:MM:SS.SSS
      time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._time_start)),
      time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._time_stop)),
      self._category,
      None  # TODO add project id when the feature is implemented
    )

  def monitor(self):
    while (True):
      # TODO watch afk
      if self._window_name != self.get_active_window_name():  # log only on activity change
        self._time_stop = time.time()
        self._category = self._classifier.classify_entry(
          window_class=self._window_class, window_name=self._window_name)
        self.save_entry()

        self._time_start = time.time()
        self._window_name = self.get_active_window_name()
        self._window_class = self.get_active_window_class()

      time.sleep(self._watch_interval)


if __name__ == '__main__':
  watcher = Watcher()
  watcher.monitor()
