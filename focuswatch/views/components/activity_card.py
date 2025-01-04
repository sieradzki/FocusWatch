import logging
from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from focuswatch.utils.resource_utils import apply_stylesheet

logger = logging.getLogger(__name__)


class ActivityCard(QWidget):
  """ A widget representing an activity in the timeline. """

  def __init__(
      self,
      category_id: int,
      category_name: str,
      color: str,
      parent_category: Optional[str] = None,
      time_range: Optional[str] = None,
      duration: Optional[int] = None,
      parent: Optional[QWidget] = None,
  ) -> None:
    super().__init__(parent)
    self._category_id = category_id
    self._category_name = category_name
    self._color = color
    self._parent_category = parent_category
    self._time_range = time_range
    self._duration = duration

    self.setObjectName("activity_card")

    self._setup_ui()
    apply_stylesheet(self, "components/activity_card.qss")

  def _setup_ui(self) -> None:
    """ Initialize the activity card UI. """
    self._layout = QHBoxLayout(self)
    self._layout.setContentsMargins(0, 0, 0, 2)
    self._layout.setSpacing(0)

    # Color indicator
    self._color_widget = QWidget(self)
    self._color_widget.setFixedWidth(12)
    self._color_widget.setObjectName("activity_card_color")
    self._color_widget.setStyleSheet(
        f"background-color: {self._color};"
    )
    self._layout.addWidget(self._color_widget)

    # Container for text content
    self._text_container = QWidget(self)
    self._text_container.setObjectName("activity_card_text_container")
    self._text_container_layout = QVBoxLayout(self._text_container)
    self._text_container_layout.setSpacing(0)
    self._text_container_layout.setContentsMargins(3, 0, 3, 0)
    # self._text_container.setStyleSheet(f"background-color: {self._color};")

    if self._duration and self._duration <= 20:
      self.setProperty("durationType", "short")
      # For shorter durations: Combine parent->category and time in one row
      combined_layout = QHBoxLayout()
      combined_layout.setContentsMargins(0, 0, 0, 0)
      combined_layout.setSpacing(0)

      label_text = f"{self._parent_category} -> {
        self._category_name}" if self._parent_category else self._category_name

      # Category label
      self._label_category = QLabel(
          label_text, self._text_container)
      self._label_category.setObjectName("activity_card_label_category")
      self._label_category.setProperty("durationType", "short")
      self._label_category.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
      combined_layout.addWidget(self._label_category)

      # Spacer to push time label to the right
      combined_layout.addStretch()

      # Time label
      if self._time_range:
        self._label_time = QLabel(
            self._time_range, self._text_container)
        self._label_time.setObjectName("activity_card_label_time")
        self._label_time.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        combined_layout.addWidget(self._label_time)

      self._text_container_layout.addLayout(combined_layout)
    else:
      self.setProperty("durationType", "long")
      # For longer durations, display parent and category labels at the top
      if self._parent_category:
        self._label_parent = QLabel(
          self._parent_category, self._text_container)
        self._label_parent.setObjectName("activity_card_label_parent")
        self._label_parent.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._text_container_layout.addWidget(self._label_parent)

      self._label_category = QLabel(self._category_name, self._text_container)
      self._label_category.setObjectName("activity_card_label_category")
      self._label_category.setProperty("durationType", "long")
      self._label_category.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
      self._text_container_layout.addWidget(self._label_category)

      # Add a spacer to push the time label to the bottom
      self._text_container_layout.addStretch()

      # Time label at the bottom right
      if self._time_range:
        self._label_time = QLabel(
            self._time_range, self._text_container)
        self._label_time.setObjectName("activity_card_label_time")
        self._label_time.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        self._text_container_layout.addWidget(self._label_time)

    # Add the text container to the main layout
    self._layout.addWidget(self._text_container)

    self.setMouseTracking(True)

  def sizeHint(self) -> QSize:
    """ Return the recommended size for the widget. """
    return QSize(self.parent().width() - 50, 60)
