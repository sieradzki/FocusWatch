from dataclasses import dataclass
from typing import Optional


@dataclass
class Keyword:
  """ Represents a keyword. """

  id: Optional[int] = None
  name: str = ""
  category_id: Optional[int] = None
  match_case: bool = False

  def __repr__(self):
    return f"Keyword(name='{self.name}', category_id={self.category_id}, id={self.id}, match_case={self.match_case})"

  def matches(self, text: str) -> bool:
    """Check if this keyword matches the given text."""
    if self.match_case:
      return self.name in text
    else:
      return self.name.lower() in text.lower()
