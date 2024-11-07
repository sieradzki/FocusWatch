""" Generalized view for displaying a card with a list of items with progress bars and a chart. """


import logging
from typing import Optional

from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PySide6.QtCore import QSize, Qt, Slot
from PySide6.QtGui import QBrush, QColor, QCursor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QLayout,
                               QProgressBar, QSizePolicy, QSpacerItem,
                               QToolTip, QWidget)

from focuswatch.utils.resource_utils import apply_combined_stylesheet
from focuswatch.views.components.card_widget import CardWidget
from focuswatch.views.components.elided_label import ElidedLabel
from focuswatch.views.components.scrollable_legend import ScrollableLegend

logger = logging.getLogger(__name__)


class TopItemsCardView(CardWidget):
  """ Base class for Top Items card views (Categories, Applications, Names). """

  def __init__(self,
               title: str,
               viewmodel,
               parent: Optional[QWidget] = None):
    super().__init__(title, parent)
    self._viewmodel = viewmodel
    self._setup_ui()
    self._connect_signals()
    self._show_event_connected = False
    self._slice_tooltips = {}

  def _setup_ui(self) -> None:
    """ Set up the UI components. """
    self.stacked_widget.setMinimumSize(QSize(350, 300))

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
    if not self._show_event_connected:  # only update view once on window show
      self._update_view()
      self._show_event_connected = True

  def _connect_signals(self) -> None:
    """ Connect signals from the ViewModel to the View. """
    raise NotImplementedError(
        "This method should be implemented in derived classes.")

  # @Slot()
  # def _on_period_changed(self):
  #   """ Handle changes to the period start or end. """
  #   raise NotImplementedError(
  #       "This method should be implemented in derived classes.")

  def _update_view(self) -> None:
    """ Update the view with the latest data. """
    self._update_list()
    self._update_chart()

  def _update_chart(self) -> None:
    """ Update the pie chart with the given items. """
    chart = QChart()
    self._slice_tooltips.clear()
    items = self._viewmodel.top_items
    total_time = sum(data[0] for data in items.values())

    # Clear the legend before adding new items
    while self.scrollable_legend.layout.count() > 0:
      item = self.scrollable_legend.layout.takeAt(0)
      if item.widget():
        item.widget().deleteLater()

    series = QPieSeries()
    series.setHoleSize(0.6)
    series.setPieSize(0.85)

    base_color = QColor("#817DF3")
    variation_step = 100

    for index, (application, (time, color, icon)) in enumerate(items.items()):
      slice = series.append(application, time)
      slice.setLabelVisible(False)
      slice.setPen(QPen(QColor("#363739"), 1))

      # Create a color variation based on the base color
      variation_color = base_color.lighter(variation_step + index * 5)
      slice.setBrush(QBrush(variation_color))

      if not color:
        color = slice.brush().color().name()

      percentage = time / total_time * 100
      tooltip = f"{application}\n{self._format_time(time)} ({percentage:.1f}%)"
      self._slice_tooltips[slice] = tooltip

      slice.hovered.connect(
        lambda state, s=slice: self._on_slice_hover(state, s))

      self.scrollable_legend.add_item(
        application, color, depth=0)  # TODO application icons?

    chart.addSeries(series)

    chart.setAnimationOptions(QChart.SeriesAnimations)
    chart.setAnimationDuration(500)
    chart.setBackgroundVisible(False)
    chart.setBackgroundBrush(QBrush(Qt.transparent))
    chart.layout().setContentsMargins(0, 0, 0, 0)
    chart.legend().hide()

    self.chart_view.setChart(chart)
    self.chart_view.setRenderHint(QPainter.Antialiasing)
    self.chart_view.setStyleSheet("background: transparent;")

    # Push items to the top
    spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.scrollable_legend.layout.addItem(spacer)

  def _on_slice_hover(self, state: bool, slice: QPieSlice, is_parent: bool = True) -> None:
    """ Handle hover events for pie slices. """
    if state:
      if is_parent:
        slice.setExploded(True)
        slice.setExplodeDistanceFactor(0.1)
      else:
        slice.setExploded(True)
        slice.setExplodeDistanceFactor(0.02)
      tooltip_text = self._slice_tooltips.get(slice, "")
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
    """ Update the list of top items. """
    items = self._viewmodel.top_items
    total_time = sum(data[0] for data in items.values())

    row = 0
    # Clear the list before adding new items
    self._clear_list_layout()

    for item_key, item_data in items.items():
      row = self._add_item_to_layout((item_key, item_data), row, total_time)

    # Add a spacer to push the content to the top
    spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.list_layout.addItem(spacer)

  def _add_item_to_layout(self, item_data, row, total_time) -> int:
    """ Add an item to the layout and return the row index. """
    name, (time, color, icon) = item_data

    # Create label, progress bar, and percentage label for the item
    label = self._create_category_label(
      name, time, color if color else "#817DF3")
    progress_bar = self._create_progress_bar(
      time, total_time, color if color else "#817DF3")
    percentage_label = self._create_duration_label(time, total_time)

    # Create left layout with label and icon if available
    left_layout = QHBoxLayout()
    left_layout.setAlignment(Qt.AlignLeft)
    if icon:
      icon_label = QLabel()
      icon_label.setPixmap(icon.scaled(
        16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
      left_layout.addWidget(icon_label)
    left_layout.addWidget(label)

    # Add the combined left layout to the grid in the first column
    self.list_layout.addLayout(left_layout, row, 0)

    # Combine progress bar and percentage into a layout on the right
    right_layout = QHBoxLayout()
    right_layout.addSpacerItem(QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
    right_layout.addWidget(progress_bar)
    right_layout.addWidget(percentage_label)
    right_layout.setAlignment(Qt.AlignRight)
    self.list_layout.addLayout(right_layout, row, 1)

    return row + 1

  def _create_category_label(self, name: str, time: int, color: str) -> QLabel:
    full_text = f"{name}"
    label = ElidedLabel(full_text)
    font = label.font()
    font.setBold(True)
    label.setFont(font)
    label.setStyleSheet(f"color: {color};")
    return label

  def _create_progress_bar(self, time: int, total_time: int, color: str) -> QProgressBar:
    """ Create a progress bar for the given time and total time. """
    progress = QProgressBar()
    # progress.setFixedWidth(120)
    progress.setMinimumWidth(120)
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

    progress.setToolTip(
      f"{int((time / total_time) * 100) if total_time > 0 else 0}%")
    apply_combined_stylesheet(progress, ['progress_bar.qss'], chunk_style)
    return progress

  def _create_duration_label(self, time: int, total_time: int) -> QLabel:
    """ Create a label for the percentage of the given time compared to the total time. """
    progress_value = self._format_time(time)
    percentage_label = QLabel(f"{progress_value}")
    percentage_label.setFixedWidth(50)
    percentage_label.setStyleSheet("color: #626262;")
    percentage_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
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
