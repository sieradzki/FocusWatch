from dataclasses import dataclass
from typing import Optional


@dataclass
class Keyword:
  """ Represents a keyword. """

  name: str = ""
  category_id: int = None
  id: Optional[int] = None
  match_case: bool = False

  # def __post_init__(self):
  #   """ Validate the keyword data after initialization. """
  #   if not self.name:
  #     raise ValueError("Keyword name cannot be empty")
  #   if self.category_id is None:
  #     raise ValueError("Category ID must be provided")

  def __eq__(self, other):
    if not isinstance(other, Keyword):
      return False
    return (self.name == other.name and self.category_id == other.category_id and
            self.id == other.id and self.match_case == other.match_case)

  def __repr__(self):
    return f"Keyword(name='{self.name}', category_id={self.category_id}, id={self.id}, match_case={self.match_case})"

  def __hash__(self):
    return hash((self.name, self.category_id, self.id, self.match_case))

  def matches(self, text: str) -> bool:
    """Check if this keyword matches the given text."""
    if self.match_case:
      return self.name in text
    else:
      return self.name.lower() in text.lower()
