""" Generalized view for displaying a card with a list of items with progress bars and a chart. """


import logging
from typing import List, Optional, Tuple, Dict

from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QBrush, QColor, QCursor, QIcon, QPainter
from PySide6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QProgressBar,
                               QPushButton, QSizePolicy, QSpacerItem, QToolTip,
                               QWidget, QLayout)

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
    raise NotImplementedError(
        "This method should be implemented in derived classes.")

  def _on_slice_hover(self, state: bool, slice: QPieSlice, is_parent: bool = True) -> None:
    """ Handle hover events for pie slices. """
    if state:
      if is_parent:
        slice.setExploded(True)
        slice.setExplodeDistanceFactor(0.1)
      else:
        slice.setExploded(True)
        slice.setExplodeDistanceFactor(0.02)
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
      self._on_slice_hover(True, slice, slice.series() ==
                           self.chart_view.chart().series()[1])
    else:
      QToolTip.hideText()

  def _update_list(self) -> None:
    """ Update the list of items with progress bars and optional icons/toggles. """
    raise NotImplementedError(
        "This method should be implemented in derived classes.")

  def _add_item_to_layout(self) -> int:
    """ Add an item (with optional children) to the layout. """
    raise NotImplementedError(
        "This method should be implemented in derived classes.")

  def _create_category_label(self, name: str, time: int, color: str) -> QLabel:
    """ Create a label for a category with the given name and time. """
    label = QLabel(f"{name} - {self._format_time(time)}")
    font = label.font()
    label.setStyleSheet(f"color: {color};")
    font.setBold(True)
    label.setFont(font)
    label.setWordWrap(True)
    return label

  def _create_progress_bar(self, time: int, total_time: int, color: str) -> QProgressBar:
    """ Create a progress bar for the given time and total time. """
    progress = QProgressBar()
    progress.setFixedWidth(120)
    progress.setFixedHeight(15)
    progress.setTextVisible(False)
    progress_value = int((time / total_time) * 100) if total_time > 0 else 0
    progress.setValue(progress_value)

    # Apply gradient styling
    base_color = QColor(color)
    stops = [
      f"stop: 0 {base_color.name()},",
      f"stop: 0.3 {base_color.darker(90).name()},",
      f"stop: 0.7 {base_color.darker(80).name()},",
      f"stop: 1 {base_color.darker(70).name()}"
    ]
    chunk_style = f"""
      QProgressBar::chunk {{
        background: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 0,
          {' '.join(stops)}
        );
      }}
    """
    apply_combined_stylesheet(progress, ['progress_bar.qss'], chunk_style)
    return progress

  def _create_percentage_label(self, time: int, total_time: int) -> QLabel:
    """ Create a label for the percentage of the given time compared to the total time. """
    progress_value = int((time / total_time) * 100) if total_time > 0 else 0
    percentage_label = QLabel(f"{progress_value}%")
    percentage_label.setFixedWidth(30)
    percentage_label.setStyleSheet("color: #626262;")
    percentage_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return percentage_label

  def _clear_list_layout(self) -> None:
    """ Clear all items from the list layout, including widgets and sub-layouts. """
    while self.list_layout.count():
      item = self.list_layout.takeAt(0)
      if item.widget():
        item.widget().deleteLater()
      elif item.layout():
        self._clear_layout(item.layout())

  def _clear_layout(self, layout: QLayout) -> None:
    """ Recursively clear a layout and delete all items. """
    while layout.count():
      item = layout.takeAt(0)
      if item.widget():
        item.widget().deleteLater()
      elif item.layout():
        self._clear_layout(item.layout())

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
