""" Tag model for FocusWatch. """

from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from focuswatch.database.models import Base


class Tag(Base):
  """ Represents a tag that can be attached to tasks. """

  __tablename__ = "tags"

  id = Column(Integer, primary_key=True, autoincrement=True)
  project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
  name = Column(String, nullable=False, index=True)
  color = Column(Text, nullable=True)

  tasks = relationship("Task", secondary="task_tags", back_populates="tags")
  project = relationship("Project")

  def __init__(self,
               name: str,
               project_id: Optional[int] = None,
               color: Optional[str] = None):
    self.name = name
    self.project_id = project_id
    self.color = color

  def __repr__(self) -> str:
    return (f"Tag(id={self.id}, name='{self.name}', "
            f"project_id={self.project_id}, color={self.color})")
