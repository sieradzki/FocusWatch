import os

from PySide6.QtCore import QDir, QFile

BASE_STYLES_DIR = "focuswatch/views/styles/"


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
    stylesheet = str(file.readAll(), 'utf-8')
    target.setStyleSheet(stylesheet)
