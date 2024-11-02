""" Watcher service for FocusWatch. 

This module is responsible for monitoring the user's activity and logging it to the database.
"""

import ctypes
import logging
import subprocess
import time
from datetime import datetime
from sys import platform
from typing import Optional, TYPE_CHECKING

import psutil

from focuswatch.config import Config
from focuswatch.models.activity import Activity

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.keyword_service import KeywordService
  from focuswatch.services.classifier_service import ClassifierService


logger = logging.getLogger(__name__)

user32 = None
kernel32 = None
if platform in ["Windows", "win32", "cygwin"]:
  # Constants for Windows API
  GW_HWNDNEXT = 2
  MAX_PATH = 260

  # Define the necessary Windows API functions
  user32 = ctypes.windll.user32
  kernel32 = ctypes.windll.kernel32

  user32.GetWindowTextW.argtypes = [
    ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int
  ]
  user32.GetClassNameW.argtypes = [
    ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int]
  user32.GetForegroundWindow.restype = ctypes.c_int
  user32.GetWindowThreadProcessId.argtypes = [
    ctypes.c_int, ctypes.POINTER(ctypes.c_uint)]

  class LASTINPUTINFO(ctypes.Structure):
    # pylint: disable=invalid-name
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_ulong)]


class WatcherService():
  """ Watcher class for FocusWatch. 

  This class is responsible for monitoring the user's activity and logging it to the database. 
  It uses the Classifier class to classify the activity based on the window class and name.

  Currently, the Watcher class supports Linux with xorg and Windows platforms.
  """

  def __init__(self,
               activity_service: 'ActivityService',
               category_service: 'CategoryService',
               classifier_service: 'ClassifierService',
               watch_interval: Optional[float] = None,
               verbose: Optional[int] = None
               ):
    # Load configuration
    self._config = Config()
    self._watch_interval = float(
      self._config.get_value("General", "watch_interval")) if not watch_interval else watch_interval
    self._verbose = int(self._config.get_value(
      "General", "verbose")) if not verbose else verbose
    self._watch_afk = bool(self._config.get_value("General", "watch_afk"))
    self._afk_timeout = float(
      self._config.get_value("General", "afk_timeout"))

    # Initialize services
    self._activity_service = activity_service
    self._category_service = category_service
    self._classifier_service = classifier_service

    # Initialize activity variables
    self._window_name = self.get_active_window_name()
    self._window_class = self.get_active_window_class()
    self._time_start = time.time()
    self._time_stop = None
    self._category = None

  def __del__(self):
    # Save the last entry before exiting
    self.save_entry()

  def get_active_window_name(self) -> str:
    """ Get the name of the active window. 

    Returns:
      str: The name of the active window.

    Raises:
      NotImplementedError: If the platform is not supported.
      subprocess.CalledProcessError: If the xdotool command fails.
    """
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
      logger.error("This platform is not supported")
      raise NotImplementedError("This platform is not supported")

  def get_active_window_class(self) -> str:
    """ Get the class name of the active window. 

    Returns:
      str: The class name of the active window.

    Raises:
      NotImplementedError: If the platform is not supported.
      subprocess.CalledProcessError: If the xdotool command fails (linux).
      psutil.NoSuchProcess: If the process is not found (windows).
    """
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
        app_name = "None"
      except psutil.AccessDenied:
        app_name = "None"
      return app_name
    else:
      logger.error("This platform is not supported")
      raise NotImplementedError("This platform is not supported")

  def save_entry(self) -> None:
    """Save the current activity entry to the database."""
    if self._verbose:
      print(f"[{self._time_stop - self._time_start:.3f}] [{self._window_class}] {
            self._window_name[:32]} {self._category}")

    # get focused from category.focused
    is_focused = self._category_service.get_category_focused(self._category)

    activity = Activity(
      window_class=self._window_class,
      window_name=self._window_name,
      time_start=datetime.fromtimestamp(self._time_start),
      time_stop=datetime.fromtimestamp(
        self._time_stop) if self._time_stop else None,
      category_id=self._category,
      project_id=None,
      focused=is_focused
    )
    self._activity_service.insert_activity(activity)

  def _get_linux_idle_time(self) -> int:
    """ Get the idle time on Linux using xprintidle. 

    Returns:
      int: The idle time in seconds.

    Raises:
      subprocess.CalledProcessError: If the xprintidle command fails.
    """
    try:
      afk_output = subprocess.check_output(["xprintidle"]).decode().strip()
      return int(afk_output) / 1000  # in seconds
    except subprocess.CalledProcessError as e:
      logger.error(
        f"Error getting idle time: {e}")
      return 0

  def _get_windows_idle_time(self) -> int:
    """ Get the idle time on Windows using the Windows API. 

    Returns:
      int: The idle time in seconds.

    Raises:
      ctypes.ArgumentError: If there is an error in the ctypes arguments.
      OSError: If there is an OS error.
    """
    try:
      # https://stackoverflow.com/a/912223

      last_input_info = LASTINPUTINFO()
      last_input_info.cbSize = ctypes.sizeof(LASTINPUTINFO)

      if not user32.GetLastInputInfo(ctypes.byref(last_input_info)):
        raise ctypes.WinError()

      idle_time_ms = kernel32.GetTickCount() - last_input_info.dwTime
      idle_time_sec = int(idle_time_ms / 1000)

      return idle_time_sec
    except (ctypes.ArgumentError, OSError) as e:
      logger.error(f"Error getting idle time: {e}")
      return 0

  def _check_afk_status(self) -> None:
    """ Check the AFK status of the user. 

    If the user is AFK for more than the AFK timeout, log the AFK status to the database.

    Raises:
      NotImplementedError: If the platform is not supported.
    """
    afk_time = 0
    if platform in ["linux", "linux2"]:
      afk_time = self._get_linux_idle_time()
    elif platform in ["Windows", "win32", "cygwin"]:
      afk_time = self._get_windows_idle_time()
    else:
      logger.error("This platform is not supported")
      raise NotImplementedError("This platform is not supported")

    if afk_time > self._afk_timeout * 60:
      self._time_stop = time.time()
      self._category = self._category_service.get_category_id_from_name(
        "AFK")
      self._window_class = "afk"
      self._window_name = "afk"
      self.save_entry()

      self._time_start = time.time()
      self._window_name = self.get_active_window_name()
      self._window_class = self.get_active_window_class()

  def _reset_activity_state(self) -> None:
    """ Reset the activity state. """
    self._time_start = time.time()
    self._window_name = self.get_active_window_name()
    self._window_class = self.get_active_window_class()

  def _log_activity_change(self) -> None:
    """ Log the activity change to the database. """
    self._time_stop = time.time()
    self._category = self._classifier_service.classify_entry(
        window_class=self._window_class, window_name=self._window_name)
    self.save_entry()

  def monitor(self) -> None:
    """ Monitor the user's activity and log it to the database. 

    This method continuously monitors the user's activity by checking the active window and class. 
    It logs the activity to the database using the Classifier class to classify the activity based on the window class and name. 
    It also logs the time spent on each activity.

    Raises:
      NotImplementedError: If the platform is not supported.
    """
    while True:
      if self._watch_afk:
        self._check_afk_status()

      if self._window_name != self.get_active_window_name():  # log only on activity change
        self._log_activity_change()
        self._reset_activity_state()

      time.sleep(self._watch_interval)


if __name__ == "__main__":
  watcher = WatcherService()
  watcher.monitor()
