import logging
from typing import Dict

from PySide6.QtCharts import QChart, QPieSeries, QPieSlice
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (QHBoxLayout, QPushButton, QSizePolicy,
                               QSpacerItem)

from focuswatch.views.components.top_items_card_view import TopItemsCardView

logger = logging.getLogger(__name__)


class TopCategoriesCardView(TopItemsCardView):
  def __init__(self,
               viewmodel,
               parent=None):
    super().__init__("Top Categories", viewmodel, parent)

  def _connect_signals(self):
    """ Connect signals from the ViewModel to the View. """
    self._viewmodel.organized_categories_changed.connect(
      self.on_categories_changed)
    self._viewmodel.visible_categories_changed.connect(
      self.on_categories_changed)

  @Slot()
  def on_categories_changed(self):
    self._update_view()

  def _update_chart(self) -> None:
    """ Update the pie chart with the organized categories in a multi-level fashion. """
    chart = QChart()
    self._slice_tooltips.clear()
    organized_categories = self._viewmodel.organized_categories
    total_time = sum(data["time"] for data in organized_categories.values())

    # Clear the legend before adding new items
    while self.scrollable_legend.layout.count() > 0:
      item = self.scrollable_legend.layout.takeAt(0)
      if item.widget():
        item.widget().deleteLater()

    # Create the main series (first level for children)
    child_series = QPieSeries()
    # Make the hole smaller so children are more visible
    child_series.setHoleSize(0.5)
    child_series.setPieSize(0.6)

    parent_series = QPieSeries()
    parent_series.setHoleSize(0.6)  # Parents start where children end
    parent_series.setPieSize(0.85)

    for category_id, category_data in organized_categories.items():
      category = category_data["category"]
      if category and not category.parent_category_id:
        # Create parent legend item
        self.scrollable_legend.add_item(
          f"{category.name}", self._viewmodel.get_category_color(category.id), depth=0)

        # Create child slices if this parent has children
        if category_data["children"]:
          for child_data in category_data["children"]:
            child_category = child_data["category"]
            if child_category:
              child_slice = QPieSlice(
                child_category.name, child_data["time"])
              child_color = self._viewmodel.get_category_color(
                child_category.id)
              if child_color:
                child_slice.setColor(child_color)
              child_slice.setLabelVisible(False)
              child_slice.setPen(QPen(QColor("#363739"), 2))
              child_series.append(child_slice)

              child_percentage = (
                child_data["time"] / total_time) * 100
              child_tooltip = f"{child_category.name}\n{
                self._format_time(child_data["time"])} ({child_percentage:.1f}%)"
              self._slice_tooltips[child_slice] = child_tooltip

              # Update scrollable legend with nesting for child categories
              self.scrollable_legend.add_item(
                f"{child_category.name}", child_color, depth=1)
              child_slice.hovered.connect(
                lambda state, s=child_slice: self._on_slice_hover(state, s, False))

        # Add parent slice
        parent_slice = QPieSlice(category.name, category_data["time"])
        color = self._viewmodel.get_category_color(category.id)
        if color:
          parent_slice.setColor(color)
        parent_slice.setLabelVisible(False)
        parent_slice.setPen(QPen(QColor("#363739"), 2))
        parent_series.append(parent_slice)

        percentage = (category_data["time"] / total_time) * 100
        tooltip = f"{category.name}\n{self._format_time(
          category_data["time"])} ({percentage:.1f}%)"
        self._slice_tooltips[parent_slice] = tooltip

        parent_slice.hovered.connect(
          lambda state, s=parent_slice: self._on_slice_hover(state, s, True))

    # Add both series to the chart
    chart.addSeries(child_series)
    chart.addSeries(parent_series)

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
    """ Update the list of items with progress bars and optional toggles. """
    self._clear_list_layout()
    organized_categories = self._viewmodel.organized_categories
    total_time = sum([data["time"] for data in organized_categories.values()])

    row = 0

    for item_data in organized_categories.values():
      if not item_data["category"].parent_category_id:
        row = self._add_item_to_layout(item_data, row, total_time)

    # Add a spacer to push the content to the top
    spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.list_layout.addItem(spacer, row, 0, 1, 4)

  def _add_item_to_layout(self, item_data, row, total_value, depth=0) -> int:
    category = item_data["category"]
    toggle_button = None
    if item_data["children"]:
      toggle_button = self._create_toggle_button(item_data)

    label = self._create_category_label(
      category.name, item_data["time"], self._viewmodel.get_category_color(category.id))
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    percentage_label = self._create_duration_label(
      item_data["time"], total_value)
    progress_bar = self._create_progress_bar(
      item_data["time"], total_value, self._viewmodel.get_category_color(category.id))

    # Add indentation based on depth to ensure correct positioning
    left_layout = QHBoxLayout()
    left_layout.setAlignment(Qt.AlignLeft)
    if toggle_button:
      left_layout.addWidget(toggle_button)

    if depth > 0:
      spacer = QSpacerItem(
        30 * depth, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
      left_layout.addSpacerItem(spacer)

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

    row += 1

    # Recursively add children if the category is visible
    if self._viewmodel.is_category_visible(category.id):
      for child_data in item_data["children"]:
        row = self._add_item_to_layout(child_data, row, total_value, depth + 1)

    return row

  def _create_toggle_button(self, category_data: Dict) -> QPushButton:
    """ Create a toggle button for a category with children. """
    toggle_button = QPushButton(
      "+" if not self._viewmodel.is_category_visible(category_data["category"].id) else "-")
    toggle_button.setFixedSize(20, 20)
    toggle_button.clicked.connect(
      lambda _, cat_id=category_data["category"].id: [self._viewmodel.toggle_category_visibility(cat_id)])
    return toggle_button
