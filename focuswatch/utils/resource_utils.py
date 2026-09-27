import logging
import os
import re
import sys

from PySide6.QtCore import QDir, QFile
from PySide6.QtGui import QIcon

logger = logging.getLogger(__name__)


def get_base_path() -> str:
  """ Get base path for resources, depending on whether the app is frozen.

  Returns:
    The base path as a string.
  """
  if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
  else:
    base_path = os.path.abspath(os.path.join(
      os.path.dirname(__file__), "..", ".."))
  return base_path


BASE_DIR = get_base_path()
BASE_RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
BASE_STYLES_DIR = os.path.join(BASE_RESOURCES_DIR, "styles")
BASE_ICONS_DIR = os.path.join(BASE_RESOURCES_DIR, "icons")


def _resolve_qss_urls(stylesheet: str, stylesheet_path: str) -> str:
  """Resolve relative url(...) paths in QSS to absolute paths."""
  base_dir = os.path.dirname(stylesheet_path)

  def replace_url(match: re.Match) -> str:
    raw_token = match.group(1).strip()
    quote = ""
    if raw_token.startswith(("'", '"')) and raw_token.endswith(("'", '"')) and len(raw_token) >= 2:
      quote = raw_token[0]
      raw_path = raw_token[1:-1]
    else:
      raw_path = raw_token

    if (
      raw_path.startswith((":/", "qrc:/", "http://", "https://", "data:"))
      or os.path.isabs(raw_path)
    ):
      return f"url({raw_token})"

    absolute_path = os.path.normpath(os.path.join(base_dir, raw_path)).replace("\\", "/")
    if quote:
      return f"url({quote}{absolute_path}{quote})"
    return f"url({absolute_path})"

  return re.sub(r"url\(([^)]+)\)", replace_url, stylesheet)


def apply_stylesheet(target, style_path: str) -> None:
  """
  Loads a QSS stylesheet file and applies it to the specified target widget or QApplication instance.

  Args:
    target (QWidget or QApplication): The widget or application instance to apply the stylesheet to.
    style_path (str): The relative path from the base styles directory to the QSS stylesheet file.
  """
  full_path = os.path.join(BASE_STYLES_DIR, style_path)

  app_dir = QDir(QDir.currentPath())
  stylesheet_path = app_dir.filePath(full_path)

  file = QFile(stylesheet_path)
  if file.open(QFile.ReadOnly | QFile.Text):
    stylesheet = str(file.readAll(), "utf-8")
    stylesheet = _resolve_qss_urls(stylesheet, stylesheet_path)
    target.setStyleSheet(stylesheet)
  else:
    logger.error(f"Failed to open stylesheet file: {style_path}")


def apply_styles(target, stylesheet_paths: list[str]) -> None:
  """
  Loads and applies multiple QSS stylesheet files to the specified target widget or QApplication instance.

  Args:
    target (QWidget or QApplication): The widget or application instance to apply the stylesheets to.
    stylesheet_paths (list[str]): A list of relative paths from the base styles directory to the QSS stylesheet files.
  """
  stylesheets = load_stylesheets(stylesheet_paths)
  target.setStyleSheet(stylesheets)


def load_stylesheets(stylesheet_paths: list[str]) -> str:
  """
  Loads and concatenates multiple stylesheets into a single string.

  Args:
    stylesheet_paths (list[str]): A list of relative paths from the base styles directory to the QSS stylesheet files.

  Returns:
    str: The concatenated stylesheets.
  """
  stylesheets = []
  for path in stylesheet_paths:
    full_path = os.path.join(BASE_STYLES_DIR, path)

    app_dir = QDir(QDir.currentPath())
    stylesheet_path = app_dir.filePath(full_path)

    file = QFile(stylesheet_path)
    if file.open(QFile.ReadOnly | QFile.Text):
      stylesheet = str(file.readAll(), "utf-8")
      stylesheet = _resolve_qss_urls(stylesheet, stylesheet_path)
      stylesheets.append(stylesheet)

  return "\n".join(stylesheets)


def apply_combined_stylesheet(target, style_paths: list[str], additional_styles: str = "") -> None:
  """
  Loads multiple QSS stylesheet files, combines them with additional styles,
  and applies them to the specified target widget or QApplication instance.

  Args:
    target (QWidget or QApplication): The widget or application instance to apply the stylesheet to.
    style_paths (list[str]): A list of relative paths from the base styles directory to the QSS stylesheet files.
    additional_styles (str): Additional styles to combine with the loaded stylesheets.
  """
  # Load the stylesheets from file paths
  loaded_styles = load_stylesheets(style_paths)

  # Combine the loaded stylesheets with additional dynamic styles
  combined_styles = f"{loaded_styles}\n{additional_styles}"

  # Apply the combined stylesheet to the target
  target.setStyleSheet(combined_styles)


def load_icon(icon_name: str) -> QIcon:
  """
  Loads an icon from the resources/icons directory.

  Args:
    icon_name (str): The name of the icon file to load.

  Returns:
    QIcon: The loaded icon.
  """
  icon_path = os.path.join(BASE_ICONS_DIR, icon_name)

  try:
    if not os.path.exists(icon_path):
      logger.error(f"Icon file not found: {icon_path}")
      return QIcon()

    icon = QIcon(icon_path)

    if icon.isNull():
      logger.error(f"Failed to load icon (isNull): {icon_path}")
      return QIcon()

    # logger.debug(f"Successfully loaded icon: {icon_path}")
    return icon

  except FileNotFoundError as e:
    logger.error(f"Icon file not found: {icon_path} - {e}")
    return QIcon()
