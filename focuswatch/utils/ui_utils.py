from PySide6.QtGui import QColor
from focuswatch.services.category_service import CategoryService


def get_contrasting_text_color(background_color):
  """ Returns the contrasting text color for a given background color. """
  background_rgb = QColor(background_color).toRgb()
  brightness = (background_rgb.red() * 299 + background_rgb.green()
                * 587 + background_rgb.blue() * 114) / 1000
  return "black" if brightness > 70 else "white"


def get_category_color_or_parent(category_id):
  """ Returns the color of a category. If the category does not have a color, return parent category's color or default (#F9F9F9). """
  category_service = CategoryService()
  current_id = category_id
  category = category_service.get_category_by_id(current_id)
  if category is None:
    return "#F9F9F9"
  color = category.color
  while color is None:
    category = category_service.get_category_by_id(current_id)
    parent_category_id = category.parent_category_id
    if parent_category_id:
      parent_category = category_service.get_category_by_id(
        parent_category_id)
      if not parent_category:
        return "#F9F9F9"
      color = parent_category.color
      current_id = parent_category_id
    else:
      return "#F9F9F9"
  return color


def get_category_color(category_id):
  """ Returns the color of a category. If the category does not have a color, return default (#F9F9F9). """
  category_service = CategoryService()
  category = category_service.get_category_by_id(category_id)
  if category is None:
    return "#F9F9F9"
  color = category.color
  return color if color else "#F9F9F9"
