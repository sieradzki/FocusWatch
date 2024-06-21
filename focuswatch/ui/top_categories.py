""" Top categories component for the FocusWatch Ui. """
from datetime import datetime
from typing import Optional

from PySide6 import QtCharts
from PySide6.QtCharts import QChart
from PySide6.QtCore import QCoreApplication, QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLayout,
                               QProgressBar, QScrollArea, QSizePolicy,
                               QSpacerItem, QVBoxLayout, QWidget)

from focuswatch.ui.utils import get_category_color, get_contrasting_text_color


class TopCategoriesComponent(QFrame):
  def __init__(self, parent, activity_manager, category_manager, period_start: datetime, period_end: Optional[datetime] = None):
    super().__init__(parent)
    self._parent = parent
    self._activity_manager = activity_manager
    self._category_manager = category_manager
    self.period_start = period_start
    self.period_end = period_end

  def setupUi(self):
    self.top_categories_frame = QFrame(self._parent)
    self.top_categories_frame.setObjectName(u"top_categories_frame")
    self.top_categories_frame.setFrameShape(QFrame.StyledPanel)
    self.top_categories_frame.setFrameShadow(QFrame.Raised)
    self.verticalLayout_4 = QVBoxLayout(self.top_categories_frame)
    self.verticalLayout_4.setSpacing(0)
    self.verticalLayout_4.setObjectName(u"verticalLayout_4")
    self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
    self.top_categories_label = QLabel(self.top_categories_frame)
    self.top_categories_label.setObjectName(u"top_categories_label")
    font = QFont()
    font.setPointSize(12)
    font.setBold(False)
    self.top_categories_label.setFont(font)
    self.top_categories_label.setAutoFillBackground(False)
    self.top_categories_label.setAlignment(
      Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
    self.top_categories_label.setMargin(4)

    self.verticalLayout_4.addWidget(self.top_categories_label)

    self.top_categories_scrollArea = QScrollArea(self.top_categories_frame)
    self.top_categories_scrollArea.setObjectName(u"top_categories_scrollArea")
    self.top_categories_scrollArea.setWidgetResizable(True)
    self.top_categories_scrollAreaWidgetContents = QWidget()
    self.top_categories_scrollAreaWidgetContents.setObjectName(
      u"top_categories_scrollAreaWidgetContents")
    self.top_categories_scrollAreaWidgetContents.setGeometry(
      QRect(0, 0, 611, 693))
    self.verticalLayout_3 = QVBoxLayout(
      self.top_categories_scrollAreaWidgetContents)
    self.verticalLayout_3.setObjectName(u"verticalLayout_3")
    self.top_categories_main_layout = QVBoxLayout()
    self.top_categories_main_layout.setObjectName(
      u"top_categories_main_layout")

    self.verticalLayout_3.addLayout(self.top_categories_main_layout)

    self.top_categories_scrollArea.setWidget(
      self.top_categories_scrollAreaWidgetContents)

    self.verticalLayout_4.addWidget(self.top_categories_scrollArea)

    self.setup_top_categories()

    self.retranslateUi()

    return self.top_categories_frame

  def retranslateUi(self):
    self.top_categories_label.setText("Top Categories")
    self.top_categories_label.setText(
      QCoreApplication.translate("TopCategoriesComponent", u"Top categories", None))

  def setup_top_categories(self):
    """ Setup the top categories component for the selected date. """
    categories_by_total_time = self._category_manager.get_period_category_time_totals(
        self.period_start, self.period_end)

    breakdown_verticalLayout = QVBoxLayout()
    breakdown_verticalLayout.setSizeConstraint(
        QLayout.SetDefaultConstraint)

    if not categories_by_total_time:
      info_label = QLabel(self.top_categories_scrollAreaWidgetContents)
      info_label.setText("No data for the selected period")

      font = QFont()
      font.setPointSize(16)

      info_label.setFont(font)
      info_label.setAlignment(Qt.AlignCenter)

      breakdown_verticalLayout.addWidget(info_label)
      self.top_categories_main_layout.addLayout(breakdown_verticalLayout)
      return

    total_time = 0

    for vals in categories_by_total_time:
      total_time += vals[-1]

    pie_chart = QtCharts.QChartView()
    pie_chart.setRenderHint(QPainter.Antialiasing)
    pie_chart.setMinimumSize(300, 300)
    pie_chart.chart().setAnimationOptions(QChart.AllAnimations)
    pie_chart.chart().setBackgroundVisible(False)

    series = QtCharts.QPieSeries()

    for vals in categories_by_total_time:
      category_horizontalLayout = QHBoxLayout()
      category_horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
      cat_id, time = vals
      category = self._category_manager.get_category_by_id(cat_id)
      id, name, parent_category_id, color = category

      text = ""
      color = get_category_color(id)

      text += name + ' -'
      hours = time // 3600
      minutes = (time // 60) % 60
      seconds = time % 60
      if hours:
        text += f" {hours}h"
      if minutes:
        text += f" {minutes}m"
      if seconds:
        text += f" {seconds}s"

      category_label = QLabel(self.top_categories_scrollAreaWidgetContents)
      category_label.setText(
        f"{text}")
      if color:
        category_label.setStyleSheet(f"color: {color};")
      category_label.setMaximumHeight(20)

      font = QFont()
      font.setBold(True)
      font.setPointSize(10)

      category_label.setFont(font)

      slice = QtCharts.QPieSlice(text, time / 60)

      if color:
        slice.setColor(QColor(color))

      slice.hovered.connect(slice.setExploded)
      slice.setExplodeDistanceFactor(0.07)
      slice.hovered.connect(slice.setLabelVisible)

      series.append(slice)

      category_horizontalLayout.addWidget(category_label)

      category_progress = QProgressBar(
        self.top_categories_scrollAreaWidgetContents)
      category_progress.setValue((time / total_time) * 100)
      category_progress.setFixedHeight(15)

      base_color = QColor(color)

      # Create gradient stops for smooth transition
      contrasting_color = get_contrasting_text_color(color)

      # Multiplier is needed for really dark colors
      multiplier = 1 if contrasting_color == 'black' else 2

      stop_1 = f"stop: 0 {base_color.darker(100 - (30 * multiplier)).name()},"
      stop_2 = f"stop: 0.3 {base_color.darker(
        100 - (20 * multiplier)).name()},"
      stop_3 = f"stop: 0.7 {base_color.darker(
        100 - (10 * multiplier)).name()},"
      stop_4 = f"stop: 1 {base_color.name()}"

      category_progress.setStyleSheet(
          f"""
          QProgressBar {{
              text-align: top;
              border-radius: 3px;
              {"color: " + contrasting_color if category_progress.value() >
               45 else ''}
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
      category_progress.setFixedWidth(250)
      category_horizontalLayout.addWidget(category_progress)
      breakdown_verticalLayout.addLayout(category_horizontalLayout)

    series.setHoleSize(0.35)
    pie_chart.chart().addSeries(series)
    # pie_chart.chart().legend().hide()

    legend = pie_chart.chart().legend()
    legend.setVisible(False)
    # legend.setAlignment(Qt.AlignBottom)
    # legend.setFont(QFont("Helvetica", 9))

    verticalSpacer = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    breakdown_verticalLayout.addItem(verticalSpacer)
    self.top_categories_main_layout.addLayout(breakdown_verticalLayout)
    self.top_categories_main_layout.addWidget(pie_chart)
