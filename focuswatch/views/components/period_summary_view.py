import logging
from typing import Optional

from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PySide6.QtCore import QSize, Qt, Slot
from PySide6.QtGui import QBrush, QColor, QCursor, QPainter, QPen
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QToolTip,
                               QVBoxLayout, QWidget)

from focuswatch.utils.resource_utils import apply_styles
from focuswatch.views.components.card_widget import CardWidget

logger = logging.getLogger(__name__)


class PeriodSummaryCardView(CardWidget):
  """ View for the Period Summary card. """

  def __init__(self, viewmodel, parent: Optional[QWidget] = None):
    super().__init__("Period Summary", parent)
    self._viewmodel = viewmodel
    self._slice_tooltips = {}
    self._setup_ui()
    self._connect_signals()
    self._show_event_connected = False

    # Apply the stylesheet
    apply_styles(self, ["components/card_widget.qss",
                        "components/period_summary_card.qss"])

  def _setup_ui(self) -> None:
    """ Set up the UI components. """
    self.setMinimumSize(QSize(350, 300))

    # Create the main container
    self.main_container = QWidget()
    self.main_layout = QVBoxLayout(self.main_container)
    self.main_layout.setContentsMargins(15, 15, 15, 15)
    self.main_layout.setSpacing(10)

    # Content widget to hold all the content
    self.content_widget = QWidget()
    self.content_layout = QVBoxLayout(self.content_widget)
    self.content_layout.setSpacing(10)
    self.content_layout.setContentsMargins(0, 0, 0, 0)

    # Focused Time Layout
    self.focused_layout = QHBoxLayout()
    self.focused_layout.setSpacing(5)

    self.focused_time_label = QLabel("Focused time:")
    self.focused_time_label.setObjectName("focused_time_label")
    self.focused_time_value = QLabel("0h 0m")
    self.focused_time_value.setObjectName("focused_time_value")

    # Create separate labels for percentage value and text
    self.focused_percent_value = QLabel("0%")
    self.focused_percent_value.setObjectName("focused_percent_value")
    self.focused_percent_text = QLabel(" of 8h 0m")
    self.focused_percent_text.setObjectName("focused_percent_text")

    # Build a horizontal layout for the percentage, aligned to the right
    self.focused_percent_layout = QHBoxLayout()
    self.focused_percent_layout.setSpacing(0)
    self.focused_percent_layout.addWidget(self.focused_percent_value)
    self.focused_percent_layout.addWidget(self.focused_percent_text)

    # Main focused_layout
    self.focused_layout.addWidget(self.focused_time_label)
    self.focused_layout.addWidget(self.focused_time_value)
    self.focused_layout.addStretch()
    self.focused_layout.addLayout(self.focused_percent_layout)

    # Distracted Time Layout
    self.distracted_layout = QHBoxLayout()
    self.distracted_layout.setSpacing(5)

    self.distracted_time_label = QLabel("Distracted time:")
    self.distracted_time_label.setObjectName("distracted_time_label")
    self.distracted_time_value = QLabel("0h 0m")
    self.distracted_time_value.setObjectName("distracted_time_value")

    # Create separate labels for percentage value and text
    self.distracted_percent_value = QLabel("0%")
    self.distracted_percent_value.setObjectName("distracted_percent_value")
    self.distracted_percent_text = QLabel(" of active time")
    self.distracted_percent_text.setObjectName("distracted_percent_text")

    # Build a horizontal layout for the percentage, aligned to the right
    self.distracted_percent_layout = QHBoxLayout()
    self.distracted_percent_layout.setSpacing(0)
    self.distracted_percent_layout.addWidget(self.distracted_percent_value)
    self.distracted_percent_layout.addWidget(self.distracted_percent_text)

    # Main distracted_layout
    self.distracted_layout.addWidget(self.distracted_time_label)
    self.distracted_layout.addWidget(self.distracted_time_value)
    self.distracted_layout.addStretch()
    self.distracted_layout.addLayout(self.distracted_percent_layout)

    # Add layouts to the content layout
    self.content_layout.addLayout(self.focused_layout)
    self.content_layout.addLayout(self.distracted_layout)

    # Chart area
    self.chart_view = QChartView()
    self.chart_view.setObjectName("chart_view")
    self.chart_view.setRenderHint(QPainter.Antialiasing)
    self.chart_view.setMinimumSize(200, 200)
    self.chart_view.setSizePolicy(
        QSizePolicy.Expanding, QSizePolicy.Expanding)

    self.content_layout.addWidget(self.chart_view)

    # Add the content widget to the main layout
    self.main_layout.addWidget(self.content_widget)

    # Set the main container as the content of the card
    self.add_content_view(self.main_container)

  def showEvent(self, event) -> None:
    """ Handle the show event to update the view initially. """
    super().showEvent(event)
    if not self._show_event_connected:
      self._update_view()
      self._show_event_connected = True

  def _connect_signals(self) -> None:
    """ Connect signals from the ViewModel to the View. """
    self._viewmodel.period_data_changed.connect(self._update_view)

  @Slot()
  def _update_view(self) -> None:
    """ Update the view with the latest data from the ViewModel. """
    period_data = self._viewmodel.period_data

    if not period_data:
      self._show_no_data_view()
      return

    total_active_time = period_data["total_active_time"]

    if total_active_time == 0:
      self._show_no_data_view()
      return
    else:
      # Show the content view
      self.show_content_view()

    # Update focused time value
    self.focused_time_value.setText(period_data["focused_time_str"])

    # Update percent of target
    focused_percent = period_data["focused_percent_of_target"]
    focused_target_str = period_data["focused_target_str"]
    self.focused_percent_value.setText(f"{focused_percent:.0f}%")
    self.focused_percent_text.setText(f" of {focused_target_str}")

    # Update distracted time value
    self.distracted_time_value.setText(period_data["distracted_time_str"])

    # Update distracted percentage
    distracted_percent = period_data["distracted_percent_of_active"]
    self.distracted_percent_value.setText(f"{distracted_percent:.0f}%")
    self.distracted_percent_text.setText(" of active time")

    # Update colors based on percentage thresholds
    # For focused time
    focused_color = self._get_percentage_color(focused_percent)
    self.focused_time_value.setStyleSheet(f"color: {focused_color};")
    self.focused_percent_value.setStyleSheet(f"color: {focused_color};")

    # For distracted time
    distracted_color = self._get_distracted_percentage_color(
        distracted_percent)
    self.distracted_time_value.setStyleSheet(f"color: {distracted_color};")
    self.distracted_percent_value.setStyleSheet(
        f"color: {distracted_color};")

    # Update the chart
    self._update_chart(period_data)

  def _show_no_data_view(self) -> None:
    """ Display the no data label and hide the content. """
    self.show_no_data_view("No data for the selected period")

  def _update_chart(self, period_data) -> None:
    """ Update the pie chart with the given period data. """
    total_time = period_data["total_time"]

    if total_time == 0:
      return

    chart = QChart()
    self._slice_tooltips.clear()

    series = QPieSeries()
    series.setHoleSize(0.4)
    series.setPieSize(0.8)

    state_colors = {
        "focused": "#4CAF50",
        "distracted": "#F44336",
        "idle": "#9E9E9E",
    }

    for state in ["focused", "distracted", "idle"]:
      time = period_data.get(state, 0.0)
      if time > 0:
        percentage = time / total_time * 100
        slice = series.append(state.capitalize(), time)
        slice.setLabelVisible(False)
        slice.setPen(QPen(QColor("#363739"), 1))
        slice.setBrush(
            QBrush(QColor(state_colors.get(state, "#FFFFFF"))))

        tooltip = f"{state.capitalize()}\n{self._format_time(time)} ({
            percentage:.1f}%)"
        self._slice_tooltips[slice] = tooltip

        slice.hovered.connect(
            lambda state, s=slice: self._on_slice_hover(state, s)
        )

    chart.addSeries(series)
    chart.setAnimationOptions(QChart.SeriesAnimations)
    chart.setAnimationDuration(500)
    chart.setBackgroundVisible(False)

    chart.layout().setContentsMargins(0, 0, 0, 0)
    chart.legend().hide()

    self.chart_view.setChart(chart)
    self.chart_view.setRenderHint(QPainter.Antialiasing)

  def _on_slice_hover(self, state: bool, slice: QPieSlice) -> None:
    """ Handle hover events for pie slices. """
    if state:
      slice.setExploded(True)
      slice.setExplodeDistanceFactor(0.1)
      tooltip_text = self._slice_tooltips.get(slice, "")
      QToolTip.showText(QCursor.pos(), tooltip_text)
    else:
      slice.setExploded(False)
      QToolTip.hideText()

  @staticmethod
  def _format_time(seconds: float) -> str:
    """ Format the given time in seconds to a human-readable string. """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours > 0:
      return f"{hours}h {minutes}m"
    elif minutes > 0:
      return f"{minutes}m"
    else:
      return f"{total_seconds % 60}s"

  @staticmethod
  def _get_percentage_color(percent: float) -> str:
    """ Return a color based on the percentage thresholds for focused time. """
    if percent <= 50:
      return "#F44336"
    elif 50 < percent <= 80:
      return "#FFC107"
    else:
      return "#4CAF50"

  @staticmethod
  def _get_distracted_percentage_color(percent: float) -> str:
    """ Return a color based on the percentage thresholds for distracted time. """
    if percent <= 10:
      return "#4CAF50"
    elif 10 < percent <= 20:
      return "#FFC107"
    else:
      return "#F44336"
