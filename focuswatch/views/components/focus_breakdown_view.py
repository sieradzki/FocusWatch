import logging
from typing import Dict, List, Optional

from PySide6.QtCharts import (QBarCategoryAxis, QBarSet, QChart, QChartView,
                              QStackedBarSeries, QValueAxis)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QBrush, QColor, QCursor, QPainter, QPen
from PySide6.QtWidgets import QToolTip, QWidget

from focuswatch.views.components.card_widget import CardWidget

logger = logging.getLogger(__name__)


class FocusBreakdownView(CardWidget):
  """ View for the Focus Breakdown card, displaying time spent in each state per hour. """

  def __init__(
      self,
      viewmodel,
      parent: Optional[QWidget] = None
  ) -> None:
    super().__init__("Focus Breakdown", parent)
    self._viewmodel = viewmodel

    self._setup_content()
    self._connect_signals()
    self.update_chart()

  def _setup_content(self) -> None:
    """ Set up the user interface. """
    self.stacked_widget.setMinimumHeight(200)

    # Create the chart
    self._chart = QChart()
    self._chart.setAnimationOptions(
        QChart.AnimationOption.SeriesAnimations)
    self._chart.setBackgroundVisible(False)
    self._chart.legend().setVisible(False)

    labels_brush = QBrush(QColor("#F9F9F9"))

    # Create axes once
    self._axis_x = QBarCategoryAxis()
    self._axis_y = QValueAxis()
    # Assuming time is displayed in minutes
    self._axis_y.setLabelFormat("%.0fm")
    self._axis_x.setLabelsBrush(labels_brush)
    self._axis_y.setLabelsBrush(labels_brush)

    y_grid_pen = QPen(QColor(128, 128, 128, 128))
    self._axis_y.setGridLinePen(y_grid_pen)

    self._axis_x.setGridLineVisible(False)

    self._axis_x.setLabelsAngle(90)

    self._chart.addAxis(self._axis_x, Qt.AlignmentFlag.AlignBottom)
    self._chart.addAxis(self._axis_y, Qt.AlignmentFlag.AlignLeft)

    # Create the chart view
    self._chart_view = QChartView(self._chart, self.stacked_widget)
    self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
    self._chart_view.setStyleSheet("background-color: transparent;")
    self._chart_view.setContentsMargins(0, 0, 0, 0)
    self.stacked_widget.addWidget(self._chart_view)

  def _connect_signals(self) -> None:
    """ Connect ViewModel signals to view slots. """
    self._viewmodel.breakdown_data_changed.connect(self.update_chart)

  def _show_no_data_view(self) -> None:
    """ Show the no data view. """
    self.show_no_data_view("No data for the selected period")

  def _show_content_view(self):
    """ Show the content view. """
    self.show_content_view()

  @Slot()
  def update_chart(self) -> None:
    """ Update the chart with new breakdown data. """
    breakdown_data: List[Dict[str, float]] = self._viewmodel.breakdown_data

    for entry in breakdown_data:
      if entry["focused"] != 0.0 or entry["distracted"] != 0.0 or entry["idle"] != 0.0:
        break
    else:
      self.show_no_data_view("No data for the selected period")
      return

    self._ensure_content_view_visible()

    # Clear existing series
    self._chart.removeAllSeries()

    # Create sets for focused, distracted, and idle with specific colors
    focused_set = QBarSet("Focused")
    distracted_set = QBarSet("Distracted")
    idle_set = QBarSet("Idle")

    # Determine the maximum time spent in any category for dynamic Y-axis scaling
    max_time = 0.0  # In minutes

    # Populate the sets and calculate max_time
    for entry in breakdown_data:
      # Convert seconds to minutes for display
      focused_minutes = entry["focused"] / 60
      distracted_minutes = entry["distracted"] / 60
      idle_minutes = entry["idle"] / 60

      focused_set.append(focused_minutes)
      distracted_set.append(distracted_minutes)
      idle_set.append(idle_minutes)

      hour_max = max(focused_minutes, distracted_minutes, idle_minutes)
      if hour_max > max_time:
        max_time = hour_max

    focused_set.hovered.connect(self.on_bar_hovered)
    distracted_set.hovered.connect(self.on_bar_hovered)
    idle_set.hovered.connect(self.on_bar_hovered)

    self._bar_sets = {
      "focused": focused_set,
      "distracted": distracted_set,
      "idle": idle_set
    }

    # Remove borders from bars
    no_border_pen = QPen(Qt.NoPen)
    focused_set.setPen(no_border_pen)
    distracted_set.setPen(no_border_pen)
    idle_set.setPen(no_border_pen)

    # Set specific colors
    focused_set.setColor(QColor("#25A266"))
    distracted_set.setColor(QColor("#FF0000"))
    idle_set.setColor(QColor("#9E9E9E"))

    # Create the stacked bar series and append sets
    series = QStackedBarSeries()
    series.append(focused_set)
    series.append(distracted_set)
    series.append(idle_set)

    series.setBarWidth(0.9)

    self._chart.addSeries(series)

    # Update categories (hours)
    categories = [f"{hour}:00" for hour in range(24)]
    self._axis_x.clear()
    self._axis_x.append(categories)

    # Attach axes to series
    series.attachAxis(self._axis_x)
    series.attachAxis(self._axis_y)

    self._axis_y.setRange(0, 60)
    # Add some padding to the maximum value for better visualization
    self._axis_y.setLabelFormat("%.0fm")

    # Add legend below
    self._chart.legend().setVisible(True)
    self._chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
    for marker in self._chart.legend().markers():
      marker.setLabelBrush(QBrush(QColor("#F9F9F9")))

  def on_bar_hovered(self, status: bool, index: int):
    """ Handle hover events over bar segments. """
    if status:
      sender_set = self.sender()
      category = None
      for key, bar_set in self._bar_sets.items():
        if bar_set == sender_set:
          category = key
          break

      if category:
        hour = index
        activities = self._viewmodel.get_activities_for_hour_and_category(
          hour, category)
        tooltip_text = f"{category.capitalize()}\nTop Activities:\n"
        for activity in activities[:5]:  # config? maybe not
          window_class = activity.window_class
          window_name = activity.window_name
          duration = self._viewmodel.get_activity_duration_in_hour(
            activity, hour)
          tooltip_text += f"- {window_class} | {
            window_name} ({duration:.1f} min)\n"

        QToolTip.showText(
          QCursor.pos(), tooltip_text, self._chart_view)
    else:
      QToolTip.hideText()
