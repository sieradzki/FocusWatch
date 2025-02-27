""" Metadata model for FocusWatch. """

from sqlalchemy import Column, String
from focuswatch.database.models import Base


class Metadata(Base):
  """ Represents metadata for database state and settings. """

  __tablename__ = "metadata"

  key = Column(String, primary_key=True)
  value = Column(String, nullable=True)

  def __init__(self, key: str, value: str):
    """ Initialize metadata entry.

    Args:
      key: The metadata key
      value: The value as a string
    """
    self.key = key
    self.value = value

  def __repr__(self):
    return f"Metadata(key='{self.key}', value='{self.value}')"
