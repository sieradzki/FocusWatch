import logging
from typing import TYPE_CHECKING, Dict, List, Tuple

from PySide6.QtCharts import QChart, QChartView, QLegend, QPieSeries, QPieSlice
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QCursor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QLayout,
                               QProgressBar, QPushButton, QScrollArea,
                               QSizePolicy, QSpacerItem, QToolTip, QVBoxLayout,
                               QWidget)

from focuswatch.utils.resource_utils import (apply_combined_stylesheet,
                                             apply_stylesheet)
from focuswatch.views.components.card_widget import CardWidget
from focuswatch.views.components.scrollable_legend import ScrollableLegend
from focuswatch.views.components.top_items_card_view import TopItemsCardView

if TYPE_CHECKING:
  from focuswatch.viewmodels.components.top_categories_card_viewmodel import \
      TopCategoriesCardViewModel

logger = logging.getLogger(__name__)


class TopApplicationsCardView(TopItemsCardView):
  def __init__(self, viewmodel, parent=None):
    super().__init__("Top Applications", viewmodel, parent)

  def _connect_signals(self):
    """ Connect signals from the ViewModel to the View. """
    self._viewmodel.property_changed.connect(self.on_property_changed)

  def on_property_changed(self, property_name: str):
    """ Handle property changes from the ViewModel. """
    if property_name in ["top_items"]:
      self._update_view()

  def _update_chart(self) -> None:
    """ Update the pie chart with the organized applications in a visually consistent fashion. """
    chart = QChart()
    self.slice_tooltips.clear()
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
      tooltip = f"{application}: {percentage:.1f}%"
      self.slice_tooltips[slice] = tooltip

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
    percentage_label = self._create_percentage_label(time, total_time)

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
