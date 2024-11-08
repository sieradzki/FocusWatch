import logging
from typing import List, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PySide6.QtCharts import QChart, QChartView, QBarSeries, QStackedBarSeries, QBarCategoryAxis, QValueAxis, QBarSet
from PySide6.QtGui import QPainter

from focuswatch.viewmodels.components.focus_trend_viewmodel import FocusTrendViewModel
from focuswatch.views.components.card_widget import CardWidget

logger = logging.getLogger(__name__)


class FocusTrendView(CardWidget):
  """ View for the Focus Trend card. """

  def __init__(self, viewmodel: FocusTrendViewModel, parent: Optional[QWidget] = None) -> None:
    super().__init__("Focus Trend", parent)
    self._viewmodel = viewmodel

    self._setup_ui()
    self.connect_signals()
    self.update_chart()

  def _setup_ui(self) -> None:
    self.stacked_widget.setMinimumHeight(300)

    # Create the chart
    self.chart = QChart()
    self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

    # Create the chart view
    self.chart_view = QChartView(self.chart, self.stacked_widget)
    self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
    self.stacked_widget.addWidget(self.chart_view)

  def connect_signals(self) -> None:
    self._viewmodel.trend_data_changed.connect(self.update_chart)

  def on_property_changed(self, property_name: str) -> None:
    print(f"property_name: {property_name}")
    if property_name == "period_start" or property_name == "period_end" or property_name == "trend_data":
      self.update_chart()

  def update_chart(self) -> None:
    """ Update the chart with new trend data. """
    trend_data: List[Dict[str, float]] = self._viewmodel.trend_data

    # Clear existing series
    self.chart.removeAllSeries()

    # Create sets for focused, distracted, and idle
    focused_set = QBarSet("Focused")
    distracted_set = QBarSet("Distracted")
    idle_set = QBarSet("Idle")

    # Populate the sets
    for entry in trend_data:
      focused_set.append(entry["focused"])
      distracted_set.append(entry["distracted"])
      idle_set.append(entry["idle"])

    # Create the stacked bar series and append sets
    series = QStackedBarSeries()
    series.append(focused_set)
    series.append(distracted_set)
    series.append(idle_set)
    self.chart.addSeries(series)

    # Create categories (hours)
    categories = [str(hour) for hour in range(24)]
    axis_x = QBarCategoryAxis()
    axis_x.append(categories)
    self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    series.attachAxis(axis_x)

    # Create value axis (percentages)
    axis_y = QValueAxis()
    axis_y.setRange(0, 100)
    axis_y.setLabelFormat("%.0f%%")
    axis_y.setTitleText("Percentage of Tracked Time")
    self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    series.attachAxis(axis_y)

    # Customize colors
    focused_set.setColor(Qt.GlobalColor.green)
    distracted_set.setColor(Qt.GlobalColor.red)
    idle_set.setColor(Qt.GlobalColor.gray)

    # Update the chart
    self.chart.legend().setVisible(False)
    # self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
    # logger.info("Focus Trend chart updated.")

    # Set transparent background
    self.chart.setBackgroundVisible(False)
    self.chart_view.setStyleSheet("background-color: transparent;")
    self.chart_view.setContentsMargins(0, 0, 0, 0)
    self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
