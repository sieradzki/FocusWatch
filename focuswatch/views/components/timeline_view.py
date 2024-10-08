import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional

from PySide6.QtCore import QObject, QSize, Qt, Signal, Slot, QTimer
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
    minutes_per_chunk: int = 10,
    hour_height: int = 120,
    parent: Optional[QWidget] = None,
  ) -> None:
    """
    Initialize the TimelineView.

    Args:
      viewmodel (TimelineViewModel): The ViewModel for the timeline.
      minutes_per_chunk (int): Minutes per time chunk.
      hour_height (int): Height of an hour in pixels.
      parent (QWidget, optional): Parent widget.
    """
    super().__init__(parent)
    self._viewmodel = viewmodel
    self._minutes_per_chunk = minutes_per_chunk
    self._hour_height: int = hour_height  # Pixels per hour
    self._minute_height: float = self._hour_height / 60  # Pixels per minute
    self._chunks_per_hour: int = 60 // self._minutes_per_chunk
    self._total_chunks: int = 24 * self._chunks_per_hour
    self._setup_ui()
    self._connect_signals()

    self.update_timeline()
    self.scroll_to_current_hour()
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
      hour_widget.setObjectName(f"hour_widget_{hour}")
      # Set custom property for styling
      hour_widget.setProperty('cssClass', 'hour_widget')

      hour_layout = QHBoxLayout(hour_widget)
      hour_layout.setContentsMargins(0, 0, 0, 0)
      hour_layout.setSpacing(0)

      # Hour label
      hour_label = QLabel(f"{hour:02d}:00", hour_widget)
      hour_label.setObjectName(f"hour_label_{hour}")
      hour_label.setFixedWidth(50)
      hour_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      hour_layout.addWidget(hour_label)

      hour_label.setProperty('cssClass', 'hour_label')

      # Spacer to fill the rest of the space
      hour_spacer = QSpacerItem(
        0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum
      )
      hour_layout.addItem(hour_spacer)

      self._timeline_layout.addWidget(hour_widget)

  @Slot()
  def update_timeline(self) -> None:
    """ Update the timeline with activity cards based on the ViewModel data. """
    # Clear existing activity cards
    for child in self._timeline_widget.findChildren(QWidget):
      if isinstance(child, ActivityCard):
        child.setParent(None)
        child.deleteLater()

    timeline_data = self._viewmodel.timeline_data

    # Build a flat list of chunks for the entire day
    full_chunks: List[int] = []
    for hour in range(24):
      chunks_in_hour = timeline_data.get(hour, [0] * self._chunks_per_hour)
      full_chunks.extend(chunks_in_hour)

    index = 0
    while index < len(full_chunks):
      category_id = full_chunks[index]
      if not category_id:
        index += 1
        continue  # No activity in this chunk

      # Start of a new activity block
      start_index = index
      duration = self._minutes_per_chunk  # Start with minutes per chunk
      index += 1

      # Accumulate duration for adjacent chunks with the same category
      while index < len(full_chunks) and full_chunks[index] == category_id:
        duration += self._minutes_per_chunk
        index += 1

      # Calculate position and size
      start_minutes = start_index * self._minutes_per_chunk
      y_position = start_minutes * self._minute_height
      height = int(duration * self._minute_height)

      # Create the activity card
      activity_card = ActivityCard(
        category_id=category_id,
        category_name=self._viewmodel.get_category_name(category_id),
        color=self._viewmodel.get_category_color(category_id),
        parent=self._timeline_widget,
      )

      activity_card.setGeometry(
        50,  # Starting after the hour labels
        int(y_position),
        self.width() - 80,
        height,
      )

      activity_card.show()

  def scroll_to_current_hour(self) -> None:
    """ Scroll to the current hour in the timeline. """
    current_hour = datetime.now().hour
    # Scroll 2 hours earlier for context
    y_position = max(0, (current_hour - 2)) * self._hour_height

    # Ensure the scroll area has updated before scrolling
    def set_scroll_position():
      self._scroll_area.verticalScrollBar().setValue(int(y_position))

    QTimer.singleShot(0, set_scroll_position)

  def resizeEvent(self, event) -> None:
    """Handle widget resizing to adjust activity cards."""
    super().resizeEvent(event)
    self.update_timeline()
