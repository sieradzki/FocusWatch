""" Top applications component for the FocusWatch Ui. """
from datetime import datetime
from typing import Optional

from PySide6 import QtCharts
from PySide6.QtCharts import QChart
from PySide6.QtCore import QCoreApplication, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLayout,
                               QProgressBar, QScrollArea, QSizePolicy,
                               QSpacerItem, QVBoxLayout, QWidget)

from focuswatch.ui.utils import get_category_color_or_parent, get_contrasting_text_color


class TopApplicationsComponent(QFrame):
  def __init__(self, parent, activity_manager, category_manager, period_start: datetime, period_end: Optional[datetime] = None):
    super().__init__(parent)
    self._parent = parent
    self._activity_manager = activity_manager
    self._category_manager = category_manager
    self.period_start = period_start
    self.period_end = period_end

  def setupUi(self):
    font = QFont()
    font.setPointSize(12)
    font.setBold(False)
    self.top_applications_frame = QFrame(self._parent)
    self.top_applications_frame.setObjectName(u"top_applications_frame")
    self.top_applications_frame.setMinimumSize(QSize(50, 0))
    self.top_applications_frame.setFrameShape(QFrame.StyledPanel)
    self.top_applications_frame.setFrameShadow(QFrame.Raised)
    self.verticalLayout_8 = QVBoxLayout(self.top_applications_frame)
    self.verticalLayout_8.setSpacing(0)
    self.verticalLayout_8.setObjectName(u"verticalLayout_8")
    self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
    self.top_applications_label = QLabel(self.top_applications_frame)
    self.top_applications_label.setObjectName(u"top_applications_label")
    self.top_applications_label.setFont(font)
    self.top_applications_label.setAutoFillBackground(False)
    self.top_applications_label.setAlignment(
      Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
    self.top_applications_label.setMargin(4)

    self.verticalLayout_8.addWidget(self.top_applications_label)

    self.top_applications_scrollArea = QScrollArea(self.top_applications_frame)
    self.top_applications_scrollArea.setObjectName(
      u"top_applications_scrollArea")
    self.top_applications_scrollArea.setWidgetResizable(True)
    self.top_applications_scrollAreaWidgetContents = QWidget()
    self.top_applications_scrollAreaWidgetContents.setObjectName(
      u"top_applications_scrollAreaWidgetContents")
    self.top_applications_scrollAreaWidgetContents.setGeometry(
      QRect(0, 0, 610, 693))
    self.verticalLayout_7 = QVBoxLayout(
      self.top_applications_scrollAreaWidgetContents)
    self.verticalLayout_7.setObjectName(u"verticalLayout_7")
    self.top_applications_main_layout = QVBoxLayout()
    self.top_applications_main_layout.setSpacing(0)
    self.top_applications_main_layout.setObjectName(
      u"top_applications_main_layout")

    self.verticalLayout_7.addLayout(self.top_applications_main_layout)

    self.top_applications_scrollArea.setWidget(
      self.top_applications_scrollAreaWidgetContents)

    self.verticalLayout_8.addWidget(self.top_applications_scrollArea)

    self.top_application_setup()

    self.retranslateUi()

    return self.top_applications_frame

  def retranslateUi(self):
    self.top_applications_label.setText(QCoreApplication.translate(
      "TopApplicationsComponent", u"Top applications", None))

  def top_application_setup(self):
    """ Setup the top application component for the selected date. """
    window_class_by_total_time = self._activity_manager.get_period_entries_class_time_total(
        self.period_start, self.period_end)

    breakdown_verticalLayout = QVBoxLayout()
    breakdown_verticalLayout.setSizeConstraint(
        QLayout.SetDefaultConstraint)

    if not window_class_by_total_time:
      info_label = QLabel(self.top_applications_scrollAreaWidgetContents)
      info_label.setText("No data for the selected period")

      font = QFont()
      font.setPointSize(16)

      info_label.setFont(font)
      info_label.setAlignment(Qt.AlignCenter)

      breakdown_verticalLayout.addWidget(info_label)
      self.top_applications_main_layout.addLayout(breakdown_verticalLayout)
      return

    total_time = 0

    for vals in window_class_by_total_time:
      if vals[0] != 'afk':
        total_time += vals[-1]

    pie_chart = QtCharts.QChartView()
    pie_chart.setRenderHint(QPainter.Antialiasing)
    pie_chart.setMinimumSize(300, 300)
    pie_chart.chart().setAnimationOptions(QChart.AllAnimations)
    pie_chart.chart().setBackgroundVisible(False)

    series = QtCharts.QPieSeries()

    for vals in window_class_by_total_time:
      class_horizontalLayout = QHBoxLayout()
      class_horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)

      window_class, _, time = vals
      if window_class == "afk":
        continue
      if time < 10:
        continue
      category_id = self._activity_manager.get_longest_duration_category_id_for_window_class_in_period(
          self.period_start, window_class, self.period_end)
      category = self._category_manager.get_category_by_id(category_id)
      if not category:
        continue
      id, name, parent_category_id, color = category
      color = get_category_color_or_parent(id)

      text = ""

      text += window_class + ' -'
      hours = time // 3600
      minutes = (time // 60) % 60
      seconds = time % 60
      if hours:
        text += f" {hours}h"
      if minutes:
        text += f" {minutes}m"
      if seconds:
        text += f" {seconds}s"

      class_label = QLabel(self.top_applications_scrollAreaWidgetContents)
      class_label.setText(f"{text}")
      class_label.setStyleSheet(f"color: {color};")
      class_label.setMaximumHeight(20)

      font = QFont()
      font.setBold(True)
      font.setPointSize(10)

      class_label.setFont(font)

      slice = QtCharts.QPieSlice(text, time / 60)

      slice.hovered.connect(slice.setExploded)
      slice.setExplodeDistanceFactor(0.07)
      slice.hovered.connect(slice.setLabelVisible)
      slice.setColor(QColor(color))

      series.append(slice)

      class_progress = QProgressBar(
        self.top_applications_scrollAreaWidgetContents)
      class_progress.setValue((time / total_time) * 100)
      class_progress.setFixedHeight(15)

      base_color = QColor(color)

      # Create gradient stops for smooth transition
      contrasting_color = get_contrasting_text_color(color)
      multiplier = 1 if contrasting_color == 'black' else 2

      stop_1 = f"stop: 0 {base_color.darker(100 - (30 * multiplier)).name()},"
      stop_2 = f"stop: 0.3 {base_color.darker(
        100 - (20 * multiplier)).name()},"
      stop_3 = f"stop: 0.7 {base_color.darker(
        100 - (10 * multiplier)).name()},"
      stop_4 = f"stop: 1 {base_color.name()}"

      class_progress.setStyleSheet(
          f"""
          QProgressBar {{
              text-align: top;
              border-radius: 3px;
              {"color: " + contrasting_color if class_progress.value() > 45 else ''}
          }}
          QProgressBar::chunk {{
              background: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 0,
                  {stop_1}
                  {stop_2}
                  {stop_3}
                  {stop_4}
              );
              border-radius: 3px;
          }}
          """
      )
      class_progress.setFixedWidth(250)

      class_horizontalLayout.addWidget(class_label)
      class_horizontalLayout.addWidget(class_progress)

      breakdown_verticalLayout.addLayout(class_horizontalLayout)

    series.setHoleSize(0.35)
    # series.setLabelsPosition(QtCharts.QPieSlice.LabelInsideNormal)
    pie_chart.chart().addSeries(series)

    legend = pie_chart.chart().legend()
    legend.setVisible(False)
    # legend.setAlignment(Qt.AlignBottom)
    # legend.setFont(QFont("Helvetica", 9))

    verticalSpacer = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    breakdown_verticalLayout.addItem(verticalSpacer)

    self.top_applications_main_layout.addLayout(breakdown_verticalLayout)
    self.top_applications_main_layout.addWidget(pie_chart)
