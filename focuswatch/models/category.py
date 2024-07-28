from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
  """ Represents a category. """
  id: Optional[int] = None
  name: str
  parent_category_id: Optional[int] = None
  color: Optional[str] = None

  def __post_init__(self):
    """ Validate the category data after initialization. """
    if not self.name:
      raise ValueError("name cannot be empty")
    if self.color and not self.color.startswith("#"):
      raise ValueError("color must start with #")
    if self.parent_category_id == self.id:
      raise ValueError("category cannot be its own parent")

  @property
  def is_root_category(self) -> bool:
    """ Returns True if the category is a root category (no parent). """
    return self.parent_category_id is None
