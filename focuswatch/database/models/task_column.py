""" Task column model for Trello-like project boards. """

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from focuswatch.database.models import Base


class TaskColumn(Base):
  """Represents a customizable kanban column in a project."""

  __tablename__ = "task_columns"

  id = Column(Integer, primary_key=True, autoincrement=True)
  project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
  name = Column(String, nullable=False)
  order_index = Column(Integer, nullable=False, default=0)

  tasks = relationship("Task", back_populates="column")

  def __repr__(self) -> str:
    return (f"TaskColumn(id={self.id}, project_id={self.project_id}, "
            f"name='{self.name}', order_index={self.order_index})")
