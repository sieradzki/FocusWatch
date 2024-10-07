import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional

from PySide6.QtCore import QObject, QSize, Qt, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QScrollArea,
                               QSpacerItem, QSizePolicy, QVBoxLayout, QWidget)

from focuswatch.utils.resource_utils import apply_stylesheet
from focuswatch.views.components.activity_card import ActivityCard

if TYPE_CHECKING:
  from focuswatch.viewmodels.components.timeline_viewmodel import \
      TimelineViewModel

logger = logging.getLogger(__name__)


class TimelineView(QWidget):
  """ A widget that displays a 24-hour timeline with activity cards. """

  def __init__(
    self,
    viewmodel: 'TimelineViewModel',
    parent: Optional[QWidget] = None,
  ) -> None:
    super().__init__(parent)
    self._viewmodel = viewmodel
    self._hour_height: int = 80  # Pixels per hour
    self._minute_height: float = self._hour_height / 60  # Pixels per minute
    self._quart_duration: int = 10  # Minutes per quart
    self._quarts_per_hour: int = self._hour_height // self._quart_duration
    self._total_quarts: int = 24 * self._quarts_per_hour
    self._setup_ui()
    self._connect_signals()

    self.update_timeline()
    apply_stylesheet(self, "components/timeline.qss")

  def _setup_ui(self) -> None:
    """ Initialize the user interface. """
    self._scroll_area = QScrollArea(self)
    self._scroll_area.setMinimumWidth(300)
    self._scroll_area.setWidgetResizable(True)
    self._scroll_area.setObjectName("timeline_view")

    self._timeline_widget = QWidget()
    self._timeline_widget.setObjectName("timeline_widget")
    self._scroll_area.setWidget(self._timeline_widget)

    self._layout = QVBoxLayout(self)
    self._layout.addWidget(self._scroll_area)
    self._layout.setContentsMargins(0, 0, 0, 0)
    self._layout.setSpacing(0)

    self._timeline_layout = QVBoxLayout(self._timeline_widget)
    self._timeline_layout.setContentsMargins(0, 0, 0, 0)
    self._timeline_layout.setSpacing(0)

    self._create_time_grid()

  def _connect_signals(self) -> None:
    """ Connect signals to slots. """
    self._viewmodel.data_changed.connect(self.update_timeline)
    self._viewmodel.property_changed.connect(self.on_property_changed)

  @Slot()
  def on_property_changed(self, property_name: str) -> None:
    """ Handle property changes in the ViewModel. """
    if property_name in ["period_start", "period_end"]:
      self.update_timeline()

  def _create_time_grid(self) -> None:
    """ Create the time grid representing 24 hours. """
    for hour in range(24):
      hour_widget = QWidget(self._timeline_widget)
      hour_widget.setFixedHeight(self._hour_height)
      hour_widget.setObjectName("hour_widget")
      # hour_widget.setStyleSheet(f"border-bottom: 1px solid red;")

      hour_layout = QHBoxLayout(hour_widget)
      hour_layout.setContentsMargins(0, 0, 0, 0)
      hour_layout.setSpacing(0)

      # Hour label
      hour_label = QLabel(f"{hour:02d}:00", hour_widget)
      hour_label.setObjectName("hour_label")
      hour_label.setFixedWidth(50)
      hour_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      hour_layout.addWidget(hour_label)

      # Hour separator line
      # hour_line = QFrame(hour_widget)
      # hour_line.setFrameShape(QFrame.HLine)
      # hour_layout.addWidget(hour_line)
      hour_spacer = QSpacerItem(
        0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
      hour_layout.addItem(hour_spacer)

      self._timeline_layout.addWidget(hour_widget)

  @Slot()
  def update_timeline(self) -> None:
    """Update the timeline with activity cards based on the ViewModel data."""
    # Clear existing activity cards
    for child in self._timeline_widget.findChildren(QWidget):
      if isinstance(child, ActivityCard):
        child.setParent(None)
        child.deleteLater()

    timeline_data = self._viewmodel.timeline_data

    # Build a flat list of chunks for the entire day
    full_quarts: List[int] = []
    for hour in range(24):
      quarts_in_hour = timeline_data.get(hour, [0] * self._quarts_per_hour)
      full_quarts.extend(quarts_in_hour)

    index = 0
    while index < len(full_quarts):
      category_id = full_quarts[index]
      if not category_id:
        index += 1
        continue 

      # Start of a new activity block
      start_index = index
      duration = self._quart_duration  # Start with 10 minutes
      index += 1

      # Accumulate duration for adjacent quarts with the same category
      while index < len(full_quarts) and full_quarts[index] == category_id:
        duration += self._quart_duration
        index += 1

      # Create the activity card
      activity_card = ActivityCard(
          category_id=category_id,
          category_name=self._viewmodel.get_category_name(category_id),
          color=self._viewmodel.get_category_color(category_id),
          parent=self._timeline_widget,
      )

      # Calculate position and size
      start_minutes = start_index * self._quart_duration
      y_position = start_minutes * self._minute_height

      activity_card.setGeometry(
          50,  # Starting after the hour labels
          int(y_position),
          self.width() - 80,
          int(duration * self._minute_height),
      )

      activity_card.show()

  def resizeEvent(self, event) -> None:
    """ Handle widget resizing to adjust activity cards. """
    super().resizeEvent(event)
    self.update_timeline()
