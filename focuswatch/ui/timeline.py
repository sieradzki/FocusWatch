""" Timeline component for the FocusWatch Ui. """
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from PySide6.QtCore import QRect, QSize, Qt, QTimer
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLayout,
                               QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from focuswatch.ui.utils import get_category_color_or_parent, get_contrasting_text_color


class TimelineComponent(QFrame):
  def __init__(self, parent, activity_manager, category_manager, period_start: datetime, perdiod_end: Optional[datetime] = None):
    super().__init__(parent)
    self._parent = parent
    self._activity_manager = activity_manager
    self._category_manager = category_manager
    self.period_start = period_start
    self.period_end = perdiod_end

  def setupUi(self):
    self.timeline_frame = QFrame(self._parent)
    self.timeline_frame.setObjectName(u"timeline_frame")
    sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(
      self.timeline_frame.sizePolicy().hasHeightForWidth())
    self.timeline_frame.setSizePolicy(sizePolicy)
    self.timeline_frame.setMinimumSize(QSize(300, 0))
    self.timeline_frame.setFrameShape(QFrame.StyledPanel)
    self.timeline_frame.setFrameShadow(QFrame.Raised)
    self.horizontalLayout_2 = QHBoxLayout(self.timeline_frame)
    self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
    self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
    self.timeline_scrollArea = QScrollArea(self.timeline_frame)
    self.timeline_scrollArea.setObjectName(u"timeline_scrollArea")
    self.timeline_scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QWidget()
    self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
    self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 296, 723))
    self.verticalLayout_6 = QVBoxLayout(self.scrollAreaWidgetContents)
    self.verticalLayout_6.setSpacing(0)
    self.verticalLayout_6.setObjectName(u"verticalLayout_6")
    self.timeline_main_layout = QVBoxLayout()
    self.timeline_main_layout.setObjectName(u"timeline_main_layout")

    self.verticalLayout_6.addLayout(self.timeline_main_layout)
    self.timeline_scrollArea.setWidget(self.scrollAreaWidgetContents)
    self.horizontalLayout_2.addWidget(self.timeline_scrollArea)

    self.setup_timeline()

    return self.timeline_frame

  def scroll_to_current_hour(self):
    """ Scroll to the current hour label. (-2 hours for better visibility) """
    current_hour = datetime.now().hour
    current_hour_label = self.scrollAreaWidgetContents.findChild(
      QLabel, f"hour_label_{max(0, current_hour - 2)}")
    y_position = current_hour_label.y()
    if y_position == 0:
      # If the position is still zero, defer scrolling to allow layout to update
      QTimer.singleShot(0, self.scroll_to_current_hour)
      return
    self.timeline_scrollArea.verticalScrollBar().setValue(y_position)

  def setup_timeline(self):
    """ Setup the timeline component for the selected period. """
    period_entries = self._activity_manager.get_period_entries(
      self.period_start, self.period_end)
    hour_chunk_entries = defaultdict(list)
    hour_entries = defaultdict(list)

    # TODO refactor this: entry density should be calculated dynamically
    for i in range(24):
      hour_entries[i] = [0, 0, 0, 0, 0, 0]  # 6 quarters in an hour

    # Parse the entries into quarters
    for entry in period_entries:
      timestamp_start = datetime.strptime(entry[1], "%Y-%m-%dT%H:%M:%S.%f")
      timestamp_stop = datetime.strptime(entry[2], "%Y-%m-%dT%H:%M:%S.%f")
      category_id = entry[-2]  # TODO named tuple?

      while timestamp_start < timestamp_stop:
        hour_start = timestamp_start.hour
        minute_start = timestamp_start.minute // 10
        quarter_hour_start = f"{hour_start:02d}:{minute_start}"

        duration_in_this_quarter = min(  # Calculate the duration in this quarter - entries can span multiple quarters
            10 - (timestamp_start.minute % 10), (timestamp_stop -
                                                 timestamp_start).total_seconds() / 60
        )

        if quarter_hour_start not in hour_chunk_entries:
          hour_chunk_entries[quarter_hour_start] = {}

        if category_id in hour_chunk_entries[quarter_hour_start]:
          hour_chunk_entries[quarter_hour_start][category_id] += duration_in_this_quarter
        else:
          hour_chunk_entries[quarter_hour_start][category_id] = duration_in_this_quarter

        timestamp_start += timedelta(minutes=duration_in_this_quarter)

    for quarter, entries in hour_chunk_entries.items():
      max_category = max(entries, key=lambda category_id: entries[category_id])
      hour_chunk_entries[quarter] = max_category

    for quarter, max_category in hour_chunk_entries.items():
      hour, index = quarter.split(sep=":")
      hour_entries[int(hour)][int(index)] = max_category

    self.populate_timeline(hour_entries)

  def populate_timeline(self, hour_entries):
    for hour, entries in hour_entries.copy().items():
      """ Hour label setup """
      hour_horizontalLayout = QHBoxLayout()
      hour_horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)

      hour_label = QLabel(self.scrollAreaWidgetContents)
      hour_label.setMaximumSize(QSize(30, 90))
      hour_label.setMinimumSize(QSize(30, 90))
      hour_label.setText(f"{'0' if hour < 10 else ''}{hour}:00")
      hour_label.setAlignment(Qt.AlignTop)
      hour_label.setObjectName(f"hour_label_{hour}")

      hour_horizontalLayout.addWidget(hour_label)

      line = QFrame(self.scrollAreaWidgetContents)
      line.setObjectName(u"line")
      line.setFrameShape(QFrame.VLine)
      line.setFrameShadow(QFrame.Sunken)

      hour_horizontalLayout.addWidget(line)

      """ Hour entries setup """
      hour_verticalLayout = QVBoxLayout()
      hour_verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
      for i, entry in enumerate(entries):
        entry_text_label = QLabel(self.scrollAreaWidgetContents)
        style = []
        if entry != 0 and entry != None:  # TODO disallow deleting 'Uncategorized' category or change how it works
          category = self._category_manager.get_category_by_id(entry)
          if not category:
            continue
          name = category[1]
          color = get_category_color_or_parent(entry)

          if i > 0:
            if entry != entries[i - 1]:
              entry_text_label.setText(name)
          else:
            if len(hour_entries[hour - 1]) > 0 and entry != hour_entries[hour - 1][-1]:
              entry_text_label.setText(name)
          if color:
            style.append(f"background-color: {color};")
          text_color = get_contrasting_text_color(color)
          style.append(f"color: {text_color};")
        else:
          style.append(f"background-color: rgba(0,0,0,0);")

        if i == len(hour_entries[0]) - 1:
          style.append("border-bottom: 1px dashed #141414;")
        entry_text_label.setStyleSheet(''.join(style))
        entry_text_label.setAlignment(Qt.AlignCenter)
        entry_text_label.setMaximumHeight(90 // len(hour_entries[0]))
        # font = QFont()
        # font.setPointSize(6)

        # entry_text_label.setFont(font)

        hour_verticalLayout.addWidget(entry_text_label)

      hour_horizontalLayout.addLayout(hour_verticalLayout)
      self.timeline_main_layout.addLayout(hour_horizontalLayout)

    self.scroll_to_current_hour()
