import ctypes
import logging
import os
import platform
import sys
import textwrap

from focuswatch.utils import is_frozen, is_linux, is_windows

if platform.system().startswith("win"):
  import winreg as reg

logger = logging.getLogger(__name__)
APP_NAME = "focuswatch"


def get_autostart_path():
  """ Returns the path to the autostart directory for the current OS. """
  if is_windows():  # just in case the registry approach doesn't work, not currently used
    return os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
  elif is_linux():
    return os.path.expanduser("~/.config/autostart")
  else:
    raise OSError("Unsupported operating system")


def is_admin():
  """ Returns True if the current process has admin privileges (Windows). """
  try:
    return ctypes.windll.shell32.IsUserAnAdmin()
  except Exception as e:
    logger.error(f"Failed to check admin status: {e}")
    return False


def run_as_admin(func):
  """ Runs the given function with elevated privileges (Windows). """
  if is_admin():
    return func()
  else:
    try:
      ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    except Exception as e:
      logger.error(f"Failed to elevate privileges: {e}")
      return False


def add_to_autostart_windows():
  """ Adds the application to the Windows autostart by modifying the registry. """
  key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
  try:
    key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_ALL_ACCESS)
    reg.SetValueEx(key, APP_NAME, 0, reg.REG_SZ, sys.executable)
    reg.CloseKey(key)
    logger.info(f"{APP_NAME} added to Windows autostart.")
    return True
  except OSError as e:
    logger.error(f"Failed to add {APP_NAME} to Windows autostart: {e}")
    return False


def add_to_autostart():
  """ Adds the application to the autostart. """
  # Check if the application is frozen (packaged)
  if not is_frozen():
    logger.warning("Autostart can only be set for the packaged application.")
    return False

  if is_windows():
    return run_as_admin(add_to_autostart_windows)
  elif is_linux():
    desktop_entry = textwrap.dedent(f"""
    [Desktop Entry]
    Type=Application
    Name={APP_NAME}
    Exec={sys.executable}
    Terminal=false
    """).strip()
    desktop_file_path = os.path.join(
      get_autostart_path(), f"{APP_NAME}.desktop")
    try:
      with open(desktop_file_path, "w") as f:
        f.write(desktop_entry.strip())
      os.chmod(desktop_file_path, 0o755)
      logger.info(f"{APP_NAME} added to Linux autostart.")
      return True
    except IOError as e:
      logger.error(f"Failed to add {APP_NAME} to Linux autostart: {e}")
      return False
  else:
    raise OSError("Unsupported operating system")


def remove_from_autostart():
  """ Removes the application from the autostart. """
  if is_windows():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
      key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_ALL_ACCESS)
      reg.DeleteValue(key, APP_NAME)
      reg.CloseKey(key)
      logger.info(f"{APP_NAME} removed from Windows autostart.")
      return True
    except OSError as e:
      logger.error(f"Failed to remove {APP_NAME} from Windows autostart: {e}")
      return False
  elif is_linux():
    desktop_file_path = os.path.join(
      get_autostart_path(), f"{APP_NAME}.desktop")
    try:
      os.remove(desktop_file_path)
      logger.info(f"{APP_NAME} removed from Linux autostart.")
      return True
    except OSError as e:
      logger.error(f"Failed to remove {APP_NAME} from Linux autostart: {e}")
      return False
  else:
    raise OSError("Unsupported operating system")


def is_in_autostart():
  """ Returns True if the application is in the autostart. """
  if is_windows():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
      key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_READ)
      reg.QueryValueEx(key, APP_NAME)
      reg.CloseKey(key)
      logger.info(f"{APP_NAME} is in Windows autostart.")
      return True
    except OSError:
      return False
  elif is_linux():
    desktop_file_path = os.path.join(
      get_autostart_path(), f"{APP_NAME}.desktop")
    exists = os.path.exists(desktop_file_path)
    if exists:
      logger.info(f"{APP_NAME} is in Linux autostart.")
    return exists
  else:
    raise OSError("Unsupported operating system")
