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


class TopCategoriesCardView(TopItemsCardView):
  def __init__(self, viewmodel, parent=None):
    super().__init__("Top Categories", viewmodel, parent)

  def _connect_signals(self):
    """ Connect signals from the ViewModel to the View. """
    self._viewmodel.property_changed.connect(self.on_property_changed)

  def on_property_changed(self, property_name: str):
    """ Handle property changes from the ViewModel. """
    if property_name in ["top_items", "visible_categories"]:
      self._update_view()

  def _update_list(self) -> None:
    """ Update the list of items with progress bars and optional toggles. """
    self._clear_list_layout()
    organized_categories = self._viewmodel.organized_categories
    total_time = sum([data['time'] for data in organized_categories.values()])

    row = 0

    for item_data in organized_categories.values():
      if not item_data['category'].parent_category_id:
        row = self._add_item_to_layout(item_data, row, total_time)

    # Add a spacer to push the content to the top
    spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.list_layout.addItem(spacer, row, 0, 1, 4)

  def _add_item_to_layout(self, item_data, row, total_value, depth=0) -> int:
    """ Add category item (with toggle buttons) to the layout. """
    category = item_data['category']

    toggle_button = None
    if item_data['children']:
      toggle_button = self._create_toggle_button(item_data)

    label = self._create_category_label(
      category.name, item_data['time'], self._viewmodel.get_category_color(category.id))
    percentage_label = self._create_percentage_label(
      item_data['time'], total_value)
    progress_bar = self._create_progress_bar(
      item_data['time'], total_value, self._viewmodel.get_category_color(category.id))

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
      for child_data in item_data['children']:
        row = self._add_item_to_layout(child_data, row, total_value, depth + 1)

    return row

  def _create_toggle_button(self, category_data: Dict) -> QPushButton:
    """ Create a toggle button for a category with children. """
    toggle_button = QPushButton(
      "+" if not self._viewmodel.is_category_visible(category_data['category'].id) else "-")
    toggle_button.setFixedSize(20, 20)
    toggle_button.clicked.connect(
      lambda _, cat_id=category_data['category'].id: [self._viewmodel.toggle_category_visibility(cat_id)])
    return toggle_button
