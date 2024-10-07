from datetime import datetime, timedelta
from focuswatch.viewmodels.components.timeline_viewmodel import \
    TimelineViewModel
from focuswatch.utils.resource_utils import apply_stylesheet
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QScrollArea,
                               QVBoxLayout, QWidget)
from PySide6.QtGui import QColor
from PySide6.QtCore import QObject, QSize, Qt, Signal, Slot
from typing import Dict, List, Optional

import logging
logger = logging.getLogger(__name__)


# WIP
class ActivityCard(QWidget):
  """A widget representing an activity in the timeline."""

  def __init__(
      self,
      category_id: int,
      category_name: str,
      color: str,
      parent: Optional[QWidget] = None,
  ) -> None:
    super().__init__(parent)
    self._category_id = category_id
    self._category_name = category_name
    self._color = color
    self.setObjectName("activity_card")
    self._init_ui()

  def _init_ui(self) -> None:
    """Initialize the activity card UI."""
    self._layout = QHBoxLayout(self)
    self._layout.setContentsMargins(0, 0, 0, 0)
    self._layout.setSpacing(2)

    self.setStyleSheet(
        f"""
    background-color: #27282C;
    """
    )

    # Color indicator
    self._color_widget = QWidget(self)
    self._color_widget.setFixedWidth(8)
    self._color_widget.setObjectName("activity_card_color")
    self._color_widget.setStyleSheet(
        f"""
        background-color: {self._color};
        border-top-left-radius: 8px;
        border-bottom-left-radius: 8px;
        """
    )
    self._layout.addWidget(self._color_widget)

    # Category name label
    self._label = QLabel(self._category_name, self)
    self._layout.addWidget(self._label)

  def sizeHint(self) -> QSize:
    """Return the recommended size for the widget."""
    return QSize(self.parent().width() - 50, 15)
