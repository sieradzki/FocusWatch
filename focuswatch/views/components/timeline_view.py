import logging
from typing import Dict, List

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLayout,
                               QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from focuswatch.ui.utils import get_contrasting_text_color
from focuswatch.viewmodels.components.timeline_viewmodel import \
    TimelineViewModel

logger = logging.getLogger(__name__)


class TimelineView(QFrame):
  def __init__(self, viewmodel: TimelineViewModel, parent=None):
    super().__init__(parent)
    self._viewmodel = viewmodel
    self._scroll_area = None
    self._main_layout = None
    self._hour_widgets = {}
    self._entry_labels = {}
    self.setupUi()
    self.connect_signals()

  def setupUi(self):
    self.setObjectName("timeline_frame")
    sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
    self.setSizePolicy(sizePolicy)
    self.setMinimumSize(300, 0)
    self.setFrameShape(QFrame.StyledPanel)
    self.setFrameShadow(QFrame.Raised)

    layout = QHBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)

    self._scroll_area = QScrollArea(self)
    self._scroll_area.setWidgetResizable(True)

    scroll_content = QWidget()
    self._scroll_area.setWidget(scroll_content)

    self._main_layout = QVBoxLayout(scroll_content)
    self._main_layout.setSpacing(0)

    # Create layouts and labels for all 24 hours
    for hour in range(24):
      hour_widget = QWidget()
      hour_layout = QHBoxLayout(hour_widget)
      hour_layout.setContentsMargins(0, 0, 0, 0)
      hour_layout.setSizeConstraint(QLayout.SetDefaultConstraint)

      hour_label = QLabel(f"{hour:02d}:00")
      hour_label.setMaximumSize(30, 90)
      hour_label.setMinimumSize(30, 90)
      hour_label.setAlignment(Qt.AlignTop)
      hour_label.setObjectName(f"hour_label_{hour}")
      hour_layout.addWidget(hour_label)

      line = QFrame()
      line.setFrameShape(QFrame.VLine)
      line.setFrameShadow(QFrame.Sunken)
      hour_layout.addWidget(line)

      entries_widget = QWidget()
      entries_layout = QVBoxLayout(entries_widget)
      entries_layout.setContentsMargins(0, 0, 0, 0)
      entries_layout.setSizeConstraint(QLayout.SetDefaultConstraint)

      self._entry_labels[hour] = []
      for _ in range(6):  # 6 quarters per hour
        entry_label = QLabel()
        entry_label.setAlignment(Qt.AlignCenter)
        entry_label.setMaximumHeight(15)  # 90 / 6
        entries_layout.addWidget(entry_label)
        self._entry_labels[hour].append(entry_label)

      hour_layout.addWidget(entries_widget)
      self._hour_widgets[hour] = hour_widget
      self._main_layout.addWidget(hour_widget)

    layout.addWidget(self._scroll_area)

    self.scroll_to_current_hour()

  def connect_signals(self):
    self._viewmodel.data_changed.connect(self.update_timeline)

  @Slot()
  def update_timeline(self):
    self.populate_timeline(self._viewmodel.timeline_data)
    QTimer.singleShot(0, self.scroll_to_current_hour)

  def populate_timeline(self, hour_entries: Dict[int, List[int]]):
    for hour, entries in hour_entries.items():
      hour_widget = self._hour_widgets[hour]
      hour_widget.show()

      for i, entry in enumerate(entries):
        entry_label = self._entry_labels[hour][i]
        entry_label.show()
        style = []

        if entry != 0 and entry is not None:
          category_name = self._viewmodel.get_category_name(entry)
          color = self._viewmodel.get_category_color(entry)

          if i > 0 and entry != entries[i - 1]:
            entry_label.setText(category_name)
          elif i == 0 and (hour == 0 or entry != hour_entries.get(hour - 1, [])[-1]):
            entry_label.setText(category_name)
          else:
            entry_label.setText("")

          if color:
            style.append(f"background-color: {color};")
            text_color = get_contrasting_text_color(color)
            style.append(f"color: {text_color};")
        else:
          style.append("background-color: rgba(0,0,0,0);")
          entry_label.setText("")

        if i == len(entries) - 1:
          style.append("border-bottom: 1px dashed #141414;")

        entry_label.setStyleSheet(''.join(style))

  def scroll_to_current_hour(self):
    current_hour = self._viewmodel.get_current_hour()
    current_hour_widget = self._hour_widgets.get(max(0, current_hour - 2))

    if current_hour_widget:
      y_position = current_hour_widget.pos().y()

      if y_position == 0:
        # If the position is still zero, defer scrolling to allow layout to update
        QTimer.singleShot(100, self.scroll_to_current_hour)
      else:
        self._scroll_area.verticalScrollBar().setValue(y_position)
    else:
      logger.warning(f"Could not find widget for hour {current_hour}")
