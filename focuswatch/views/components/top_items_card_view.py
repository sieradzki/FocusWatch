""" Generalized view for displaying a card with a list of items with progress bars and a chart. """


import logging
from typing import List, Optional, Tuple

from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QBrush, QColor, QCursor, QIcon, QPainter
from PySide6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QProgressBar,
                               QPushButton, QSizePolicy, QSpacerItem, QToolTip,
                               QWidget)

from focuswatch.utils.resource_utils import (apply_combined_stylesheet,
                                             apply_stylesheet)
from focuswatch.views.components.card_widget import CardWidget
from focuswatch.views.components.scrollable_legend import ScrollableLegend

logger = logging.getLogger(__name__)


class TopItemsCardView(CardWidget):
  """ Base class for Top Items card views (Categories, Applications, Names). """

  def __init__(self, title: str, viewmodel, parent: Optional[QWidget] = None):
    super().__init__(title, parent)
    self._viewmodel = viewmodel
    self._setup_ui()
    self._connect_signals()
    self.show_event_connected = False
    self.slice_tooltips = {}

  def _setup_ui(self) -> None:
    """ Set up the UI components. """
    self.stacked_widget.setMinimumSize(QSize(300, 300))

    # Create the view for list items
    self.list_container = QWidget()
    self.list_layout = QGridLayout(self.list_container)
    self.list_container.setSizePolicy(
        QSizePolicy.Expanding, QSizePolicy.Expanding)

    # Create the view for the chart
    self.chart_container = QWidget()
    self.chart_layout = QHBoxLayout(self.chart_container)
    self.chart_layout.setContentsMargins(0, 5, 0, 0)
    self.chart_layout.setSpacing(0)

    self.chart_view = QChartView()
    self.chart_view.setRenderHint(QPainter.Antialiasing)
    self.chart_view.setMinimumSize(200, 200)
    self.chart_view.setSizePolicy(
        QSizePolicy.Expanding, QSizePolicy.Expanding)

    # Create the legend for the chart
    self.scrollable_legend = ScrollableLegend()

    self.chart_layout.addWidget(self.chart_view, 3)
    self.chart_layout.addWidget(self.scrollable_legend, 1)

    # Add both views to the CardWidget
    self.add_content_view(self.list_container)
    self.add_content_view(self.chart_container)

    # apply_stylesheet(self, "components/top_items_card.qss")  # TODO

  def showEvent(self, event) -> None:
    super().showEvent(event)
    if not self.show_event_connected:  # only update view once on window show
      self._update_view()
      self.show_event_connected = True

  def _connect_signals(self) -> None:
    """ Connect signals from the ViewModel to the View. """
    raise NotImplementedError(
        "This method should be implemented in derived classes.")

  def on_property_changed(self, property_name: str) -> None:
    """ Handle property changes from the ViewModel. """
    raise NotImplementedError(
        "This method should be implemented in derived classes.")

  def _update_view(self) -> None:
    """ Update the view with the latest data. """
    self._update_list()
    self._update_chart()

  def _update_chart(self) -> None:
    """ Update the pie chart with the given items. """
    series = QPieSeries()
    items = self._viewmodel.top_items
    total_value = sum(value for _, value, _ in items)
    self.slice_tooltips.clear()

    # CLear previous legend items
    for i in reversed(range(self.scrollable_legend.layout.count())):
      self.scrollable_legend.layout.itemAt(
        i).widget().deleteLater()  # TODO test this

    for name, value, color in items:
      slice = QPieSlice(name, value)
      if color:
        slice.setColor(color)
      slice.setLabelVisible(False)
      slice.setExploded(False)
      slice.setPen(Qt.NoPen)  # Remove border
      slice.setLabelColor(QColor("#F9F9F9"))
      series.append(slice)

      percentage = (value / total_value) * 100
      tooltip = f"{name}\n{self._format_time(value)} ({percentage:.1f}%)"
      self.slice_tooltips[slice] = tooltip

      self.scrollable_legend.add_item(
          color, f"{name} ({percentage:.1f}%)")

      slice.hovered.connect(self._on_slice_hover)

    # series.setPieSize(0.8)
    # series.setHoleSize(0.45)

    chart = QChart()
    chart.addSeries(series)
    chart.setAnimationOptions(QChart.SeriesAnimations)
    chart.setAnimationDuration(500)
    chart.setBackgroundVisible(False)
    # Set chart background to transparent
    chart.setBackgroundBrush(QBrush(Qt.transparent))
    chart.layout().setContentsMargins(0, 0, 0, 0)  # Remove margins
    # Hide default chart legend
    chart.legend().hide()

    self.chart_view.setChart(chart)
    self.chart_view.setRenderHint(QPainter.Antialiasing)

    self.chart_view.setStyleSheet("background: transparent;")

  def _on_slice_hover(self, state: bool) -> None:
    """ Handle hover events for pie slices. """
    slice = self.sender()
    if state:
      slice.setExploded(True)
      tooltip_text = self.slice_tooltips.get(slice, "")
      QToolTip.showText(QCursor.pos(), tooltip_text)
    else:
      slice.setExploded(False)
      QToolTip.hideText()

  def mouseMoveEvent(self, event):  # TODO test this
    super().mouseMoveEvent(event)
    # ensure we are on the chart view
    if not self.stacked_widget.currentWidget() == self.chart_view:
      return
    # Find the slice under the cursor
    pos = self.chart_view.mapFromParent(event.pos())
    try:
      slice = self.chart_view.chart().series()[0].sliceAt(pos)
    except AttributeError:
      logger.error("No slices found in the chart. Ignoring hover event.")
      return
    if slice:
      self._on_slice_hover(True)
    else:
      QToolTip.hideText()

  def _update_list(self) -> None:
    """ Update the list of items with progress bars and optional icons/toggles. """
    self._clear_list_layout()
    items = self._viewmodel.top_items
    total_value = sum(value for _, value, _, _ in items)

    row = 0
    for item_data in items:
      logger.info(f"[TOPITEMSCARDVIEW] Adding item to layout: {item_data}")
      row = self._add_item_to_layout(item_data, row, total_value)

    # Add a spacer to push the content to the top
    spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.list_layout.addItem(spacer, row, 0, 1, 4)


  def _add_item_to_layout(self) -> int:
    """ Add an item (with optional children) to the layout. """
    raise NotImplementedError(
        "This method should be implemented in derived classes.")

  def _clear_list_layout(self) -> None:
    """ Clear all items from the list layout. """
    while self.list_layout.count():
      item = self.list_layout.takeAt(0)
      if item.widget():
        item.widget().deleteLater()

  @staticmethod
  def _format_time(seconds: int) -> str:
    """ Format the given time in seconds to a human-readable string. """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    if hours > 0:
      return f"{hours}h {minutes}m"
    elif minutes > 0:
      return f"{minutes}m {remaining_seconds}s"
    else:
      return f"{remaining_seconds}s"
