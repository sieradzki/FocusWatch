""" Category model for FocusWatch. """

import re
from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from focuswatch.database.models import Base


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

    if color:
      if color.startswith("#"):
        if not re.match(r"^#[0-9A-Fa-f]{6}$", color):
          raise ValueError(
            "color must start with # and follow the format #RRGGBB")
      elif color.startswith("rgb("):
        match = re.match(r"^rgb\((\d{1,3}),(\d{1,3}),(\d{1,3})\)$", color)
        if not match or not all(0 <= int(value) <= 255 for value in match.groups()):
          raise ValueError(
            "color must be in the format rgb(r,g,b) with values 0-255")
      else:
        raise ValueError(
          "color must start with # or be in the format rgb(r,g,b)")
    if parent_category_id and id and parent_category_id == id:
      raise ValueError("category cannot be its own parent")
    self.color = color

  @property
  def is_root_category(self) -> bool:
    """ Returns True if the category is a root category (no parent). """
    return self.parent_category_id is None

  def __repr__(self):
    return f"Category(id={self.id}, name='{self.name}', parent_category_id={self.parent_category_id})"
