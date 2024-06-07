""" Watcher module for FocusWatch. 

This module provides a class for monitoring the active window and logging the activity.
"""
import ctypes
import subprocess
import time
from datetime import datetime
from sys import platform

import psutil

from focuswatch.classifier import Classifier
from focuswatch.config import Config
from focuswatch.database.activity_manager import ActivityManager
from focuswatch.database.category_manager import CategoryManager

if platform in ["Windows", "win32", "cygwin"]:
  # Constants for Windows API
  GW_HWNDNEXT = 2
  MAX_PATH = 260

  # Define the necessary Windows API functions
  user32 = ctypes.windll.user32
  kernel32 = ctypes.windll.kernel32

  user32.GetWindowTextW.argtypes = [
    ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int]
  user32.GetClassNameW.argtypes = [
    ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int]
  user32.GetForegroundWindow.restype = ctypes.c_int
  user32.GetWindowThreadProcessId.argtypes = [
    ctypes.c_int, ctypes.POINTER(ctypes.c_uint)]


class Watcher():
  """ Watcher class for FocusWatch. """

  def __init__(self, watch_interval=None, verbose=None):
    self._config = Config()
    self._watch_interval = float(
      self._config.get_config("General", "watch_interval")) if not watch_interval else watch_interval
    self._verbose = int(self._config.get_config(
      "General", "verbose")) if not verbose else verbose
    self._watch_afk = bool(self._config.get_config("General", "watch_afk"))
    self._afk_timeout = float(
      self._config.get_config("General", "afk_timeout"))

    self._category_manager = CategoryManager()
    self._activity_manager = ActivityManager()
    self._classifier = Classifier()

    self._window_name = self.get_active_window_name()
    self._window_class = self.get_active_window_class()
    self._time_start = time.time()
    self._time_stop = None
    self._category = None

  def __del__(self):
    self.save_entry()

  def get_active_window_name(self):
    if platform in ["linux", "linux2"]:
      cmd = ["xdotool", "getactivewindow", "getwindowname"]
      try:
        name = subprocess.check_output(
          cmd, encoding="utf-8", stderr=subprocess.STDOUT).strip()
      except subprocess.CalledProcessError:
        name = "None"
      return name
    elif platform in ["Windows", "win32", "cygwin"]:
      active_window_handle = user32.GetForegroundWindow()
      # Get the window title (name)
      window_title = ctypes.create_unicode_buffer(MAX_PATH)
      user32.GetWindowTextW(active_window_handle, window_title, MAX_PATH)
      return window_title.value
    else:
      raise NotImplementedError("This platform is not supported")

  def get_active_window_class(self):
    if platform in ["linux", "linux2"]:
      cmd = ["xdotool", "getactivewindow", "getwindowclassname"]
      try:
        class_name = subprocess.check_output(
          cmd, encoding="utf-8", stderr=subprocess.STDOUT).strip()
      except subprocess.CalledProcessError:
        class_name = "None"
      return class_name
    elif platform in ["Windows", "win32", "cygwin"]:
      active_window_handle = user32.GetForegroundWindow()
      # Get PID
      active_window_pid = ctypes.c_uint(0)
      user32.GetWindowThreadProcessId(
        active_window_handle, ctypes.byref(active_window_pid))
      # Get the application name (executable name) using psutil
      try:
        process = psutil.Process(active_window_pid.value)
        app_name = process.exe().split("\\")[-1].split(".")[0]
      except psutil.NoSuchProcess:
        app_name = "Unknown (Process not found)"
      return app_name
    else:
      print("Platform currently not supported.")
      exit()

  def save_entry(self):
    if self._verbose:
      print(
          f"[{self._time_stop - self._time_start:.3f}] [{self._window_class}] {self._window_name[:32]} {self._category}")
    self._activity_manager.insert_activity(
      self._window_class,
      self._window_name,
      # YYYY-MM-DD HH:MM:SS.SSS
      datetime.fromtimestamp(self._time_start),
      datetime.fromtimestamp(self._time_stop),
      self._category,
      None  # TODO add project id when the feature is implemented
    )

  def monitor(self):
    while True:
      if self._watch_afk:
        # Linux afk time
        if platform in ["linux", "linux2"]:
          afk_output = subprocess.check_output(["xprintidle"]).decode().strip()
          afk_time = int(afk_output) / 1000  # in seconds

        # Windows afk time
        elif platform in ["Windows", "win32", "cygwin"]:
          # Get idle time
          last_input_info = ctypes.c_ulong()
          user32.GetLastInputInfo(ctypes.byref(last_input_info))
          idle_time = kernel32.GetTickCount() - last_input_info.value
          afk_time = idle_time / 1000
        else:
          raise NotImplementedError("This platform is not supported")

        if afk_time > self._afk_timeout * 60:
          self._time_stop = time.time()
          self._category = self._category_manager.get_category_id_from_name(
            "AFK")
          self._window_class = "afk"
          self._window_name = "afk"
          self.save_entry()

          self._time_start = time.time()
          self._window_name = self.get_active_window_name()
          self._window_class = self.get_active_window_class()

      if self._window_name != self.get_active_window_name():  # log only on activity change
        self._time_stop = time.time()
        self._category = self._classifier.classify_entry(
          window_class=self._window_class, window_name=self._window_name)
        self.save_entry()

        self._time_start = time.time()
        self._window_name = self.get_active_window_name()
        self._window_class = self.get_active_window_class()

      time.sleep(self._watch_interval)


if __name__ == "__main__":
  watcher = Watcher()
  watcher.monitor()
