from PySide6.QtGui import QColor
from focuswatch.database.category_manager import CategoryManager

def get_contrasting_text_color(background_color):
  """ Returns the contrasting text color for a given background color. """
  background_rgb = QColor(background_color).toRgb()
  brightness = (background_rgb.red() * 299 + background_rgb.green()
                * 587 + background_rgb.blue() * 114) / 1000
  return "black" if brightness > 70 else "white"

def get_category_color(category_id):
  """ Returns the color of a category. If the category does not have a color, return parent category's color. """
  category_manager = CategoryManager()
  current_id = category_id
  category = category_manager.get_category_by_id(current_id)
  color = category[-1]
  while color == None:
    category = category_manager.get_category_by_id(current_id)
    parent_category_id = category[-2]
    if parent_category_id:
      parent_category = category_manager.get_category_by_id(
        parent_category_id)
      color = parent_category[-1]
      current_id = parent_category_id
    else:
      return None
  return color