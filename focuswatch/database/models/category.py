""" Category model for FocusWatch. """

from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from focuswatch.database.models import Base
from focuswatch.utils.ui_utils import validate_color_format


class Category(Base):
  """ Represents a category in the database. """

  __tablename__ = "categories"

  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String, nullable=False)
  parent_category_id = Column(
    Integer, ForeignKey("categories.id"), nullable=True)
  color = Column(String, nullable=True)
  focused = Column(Boolean, nullable=False, default=False)

  def __init__(self,
               name: str = "",
               parent_category_id: Optional[int] = None,
               color: Optional[str] = None,
               focused: bool = False,
               id: Optional[int] = None):
    """ Initialize and validate the category.

    Args:
      name: Category name.
      parent_category_id: ID of the parent category.
      color: Color in #RRGGBB or rgb(r,g,b) format.
      focused: Whether the category is focused.
      id: Optional ID if pre-assigned.
    """
    self.id = id
    self.name = name
    self.parent_category_id = parent_category_id
    self.focused = focused
    if color is not None:
      if validate_color_format(color):
        self.color = color
      else:
        raise ValueError(
          f"Invalid color format: {color}. Use #RRGGBB or rgb(r,g,b).")
    else:
      self.color = None

  @property
  def is_root_category(self) -> bool:
    """ Returns True if the category is a root category (no parent). """
    return self.parent_category_id is None

  def __repr__(self):
    return f"Category(id={self.id}, name='{self.name}', parent_category_id={self.parent_category_id})"
