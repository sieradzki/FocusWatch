import logging
from typing import Dict, List, Tuple

from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLayout, QProgressBar,
                               QSizePolicy, QSpacerItem, QVBoxLayout, QWidget, QPushButton, QGridLayout)

from focuswatch.viewmodels.components.top_categories_card_viewmodel import TopCategoriesCardViewModel
from focuswatch.views.components.card_widget import CardWidget
from focuswatch.utils.resource_utils import apply_stylesheet, apply_combined_stylesheet

logger = logging.getLogger(__name__)


class TopCategoriesCardView(CardWidget):
  """ View for the Top Categories Card component. """

  def __init__(self, viewmodel: TopCategoriesCardViewModel, parent=None):
    super().__init__("Top Categories", parent)
    self._viewmodel = viewmodel
    self._setup_ui()
    self._connect_signals()
    self.show_event_connected = False

  def _setup_ui(self) -> None:
    """ Set up the UI components. """
    # Create the view for progress bars
    self.categories_container = QWidget()
    self.categories_layout = QGridLayout(self.categories_container)

    # Create the view for the chart
    self.chart_view = QChartView()
    self.chart_view.setRenderHint(QPainter.Antialiasing)
    self.chart_view.setMinimumSize(300, 300)

    # Add both views to the CardWidget using add_content_view
    self.add_content_view(self.categories_container)
    self.add_content_view(self.chart_view)

  def _connect_signals(self) -> None:
    """ Connect signals from the ViewModel to the View. """
    self._viewmodel.property_changed.connect(self.on_property_changed)
    self._viewmodel.category_visibility_changed.connect(self._update_view)

  def on_property_changed(self, property_name: str) -> None:
    if property_name == 'organized_categories':
      self._update_view()

  def showEvent(self, event):
    super().showEvent(event)
    if not self.show_event_connected:
      self._update_view()
      self.show_event_connected = True

  def _update_view(self) -> None:
    """ Update the view with the latest data from the ViewModel. """
    self._clear_categories_layout()
    self._update_chart()
    self._update_categories_list()

  def _update_chart(self) -> None:
    """ Update the pie chart with the latest data. """
    series = QPieSeries()
    visible_categories = self._viewmodel.get_visible_categories()

    for category_id, time in visible_categories:
      category = self._viewmodel._category_service.get_category_by_id(
        category_id)
      if category:
        slice = QPieSlice(category.name, time / 60)
        color = self._viewmodel.get_category_color(category_id)
        slice.setColor(QColor(color))
        slice.setLabelVisible(True)
        series.append(slice)

    chart = QChart()
    chart.addSeries(series)
    chart.setTitle("Top Categories")
    chart.legend().hide()
    self.chart_view.setChart(chart)

  def _update_categories_list(self) -> None:
    """Update the list of categories with progress bars."""

    def add_category_to_layout(category_data: Dict, row: int, depth: int = 0) -> int:
      category = category_data['category']
      color = self._viewmodel.get_category_color(category.id)

      # Create the label with category name and time
      label = QLabel(
        f"{category.name} - {self._format_time(category_data['time'])}")
      font = label.font()
      label.setStyleSheet(f"color: {color};")
      font.setBold(True)
      label.setFont(font)
      label.setWordWrap(True)

      # Create toggle button if the category has children
      toggle_button = None
      if category_data['children']:
        toggle_button = QPushButton(
          "+" if not self._viewmodel.is_category_visible(category.id) else "-")
        toggle_button.setFixedSize(20, 20)
        toggle_button.clicked.connect(
          lambda _, cat_id=category.id: self._viewmodel.toggle_category_visibility(cat_id))

      # Style and create the progress bar
      progress = QProgressBar()
      progress.setFixedWidth(120)
      progress.setFixedHeight(15)
      progress.setTextVisible(False)
      total_time = self._get_total_time()
      progress_value = int(
        (category_data['time'] / total_time) * 100) if total_time > 0 else 0
      progress.setValue(progress_value)

      # Apply gradient styling to the progress bar
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

      apply_combined_stylesheet(
        progress, ['progress_bar.qss'], chunk_style)

      # Calculate and create the percentage label
      percentage = QLabel(f"{progress_value}%")
      percentage.setFixedWidth(30)
      percentage.setStyleSheet("color: #626262;")
      percentage.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

      # Combine toggle button and label in a single layout for left alignment
      left_layout = QHBoxLayout()
      left_layout.setAlignment(Qt.AlignLeft)
      if toggle_button:
        left_layout.addWidget(toggle_button)

      # Add indentation based on depth to ensure correct positioning
      if depth > 0:
        spacer = QSpacerItem(
          30 * depth, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
        left_layout.addSpacerItem(spacer)

      left_layout.addWidget(label)

      # Add the combined left layout to the grid in the first column
      grid = self.categories_layout  # Ensure this is QGridLayout
      grid.addLayout(left_layout, row, 0)

      # Combine progress bar and percentage into a layout on the right
      right_layout = QHBoxLayout()
      right_layout.addWidget(progress)
      right_layout.addWidget(percentage)
      right_layout.setAlignment(Qt.AlignRight)
      grid.addLayout(right_layout, row, 1)

      row += 1

      # Recursively add children if the category is visible
      if self._viewmodel.is_category_visible(category.id):
        for child in category_data['children']:
          for child_data in child.values():
            row = add_category_to_layout(child_data, row, depth + 1)

      return row

    # Initialize the row counter and add all top-level categories to the layout
    row = 0
    for category_id, category_data in self._viewmodel.organized_categories.items():
      if not category_data['category'].parent_category_id:
        row = add_category_to_layout(category_data, row)

    # Add a spacer to push the content to the top
    spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.categories_layout.addItem(spacer, row, 0, 1, 2)

  def _clear_categories_layout(self) -> None:
    """ Clear all items from the categories layout. """
    while self.categories_layout.count():
      item = self.categories_layout.takeAt(0)
      if item.widget():
        item.widget().deleteLater()
      elif item.layout():
        self._clear_layout(item.layout())

  @staticmethod
  def _clear_layout(layout: QLayout) -> None:
    """ Clear all items from the given layout. """
    while layout.count():
      item = layout.takeAt(0)
      if item.widget():
        item.widget().deleteLater()
      elif item.layout():
        TopCategoriesCardView._clear_layout(item.layout())

  def _get_total_time(self) -> int:
    """ Get the total time for all root categories. """
    return sum(category_data['time'] for category_data in self._viewmodel.organized_categories.values())

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
