from dataclasses import dataclass
from typing import Optional

@dataclass
class Keyword:
  """ Represents a keyword. """
  
  id: Optional[int] = None
  name: str
  category_id: int
  match_case: bool = False

  def __post_init__(self):
    """ Validate the keyword data after initialization. """
    if not self.name:
      raise ValueError("Keyword name cannot be empty")
    if self.category_id is None:
      raise ValueError("Category ID must be provided")

  def matches(self, text: str) -> bool:
    """Check if this keyword matches the given text."""
    if self.match_case:
      return self.name in text
    else:
      return self.name.lower() in text.lower()
