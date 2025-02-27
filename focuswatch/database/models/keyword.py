""" Keyword model for FocusWatch. """

from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from focuswatch.database.models import Base


class Keyword(Base):
  """ Represents a keyword in the database. """

  __tablename__ = "keywords"

  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String, nullable=False)
  category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
  match_case = Column(Boolean, nullable=False, default=False)

  def __init__(self, 
               name: str = "", 
               category_id: int = None,
               match_case: bool = False, 
               id: Optional[int] = None):
    """ Initialize the keyword.

    Args:
      name: Keyword name.
      category_id: ID of the associated category.
      match_case: Whether matching is case-sensitive.
      id: Optional ID if pre-assigned.
    """
    self.id = id
    self.name = name
    self.category_id = category_id
    self.match_case = match_case

  # def __eq__(self, other): # Possibly obsolete
  #   if not isinstance(other, Keyword):
  #     return False
  #   return (self.name == other.name and self.category_id == other.category_id and
  #           self.id == other.id and self.match_case == other.match_case)

  def __repr__(self):
    return f"Keyword(name='{self.name}', category_id={self.category_id}, id={self.id}, match_case={self.match_case})"

  # def __hash__(self): # this as well
  #   return hash((self.name, self.category_id, self.id, self.match_case))

  def matches(self, text: str) -> bool:
    """ Check if this keyword matches the given text.

    Args:
      text: Text to match against.
    Returns:
      bool: True if the keyword matches the text.
    """
    if self.match_case:
      return self.name in text
    return self.name.lower() in text.lower()
