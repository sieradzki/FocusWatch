import platform
import sys


def is_windows():
  return platform.system().lower().startswith("win")


def is_linux():
  return platform.system().lower().startswith("lin")


def is_frozen():
  return getattr(sys, 'frozen', False)
