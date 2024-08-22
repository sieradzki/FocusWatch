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

  def __post_init__(self):
    """ Validate the category data after initialization. """
    if self.color and not (re.match(r'^#[0-9A-Fa-f]{6}$', self.color) or re.match(r'^rgb\(\d{1,3},\d{1,3},\d{1,3}\)$', self.color)):
      raise ValueError(
        "color must start with # or be in the format rgb(r,g,b)")
    if self.parent_category_id and self.id and self.parent_category_id == self.id:
      raise ValueError("category cannot be its own parent")

  @property
  def is_root_category(self) -> bool:
    """ Returns True if the category is a root category (no parent). """
    return self.parent_category_id is None
