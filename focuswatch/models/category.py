from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class Category:
  """ Represents a category. """
  id: Optional[int] = None
  name: str = ""
  parent_category_id: Optional[int] = None
  color: Optional[str] = None
  focused: bool = 0

  def __post_init__(self):
    """ Validate the category data after initialization. """
    if self.color:
      if self.color.startswith("#"):
        if not re.match(r'^#[0-9A-Fa-f]{6}$', self.color):
          raise ValueError(
            "color must start with # and follow the format #RRGGBB")
      elif self.color.startswith("rgb("):
        match = re.match(r'^rgb\((\d{1,3}),(\d{1,3}),(\d{1,3})\)$', self.color)
        if not match or not all(0 <= int(value) <= 255 for value in match.groups()):
          raise ValueError(
            "color must be in the format rgb(r,g,b) where r, g, b are between 0 and 255")
      else:
        raise ValueError(
          "color must start with # or be in the format rgb(r,g,b)")

    if self.parent_category_id and self.id and self.parent_category_id == self.id:
      raise ValueError("category cannot be its own parent")

  @property
  def is_root_category(self) -> bool:
    """ Returns True if the category is a root category (no parent). """
    return self.parent_category_id is None
