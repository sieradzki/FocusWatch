from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class Category:
  """ Represents a category. """
  name: str
  id: Optional[int] = None
  parent_category_id: Optional[int] = None
  color: Optional[str] = None

  def __post_init__(self):
    """ Validate the category data after initialization. """
    if not self.name:
      raise ValueError("name cannot be empty")
    if self.color and not re.match(r'^#[0-9A-Fa-f]{6}$', self.color):
      raise ValueError("color must start with #")
    if self.parent_category_id and self.id and self.parent_category_id == self.id:
      raise ValueError("category cannot be its own parent")

  @property
  def is_root_category(self) -> bool:
    """ Returns True if the category is a root category (no parent). """
    return self.parent_category_id is None
