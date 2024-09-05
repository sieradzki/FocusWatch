import logging
from typing import List, Tuple

from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLayout, QProgressBar,
                               QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from focuswatch.viewmodels.components.top_categories_card_viewmodel import \
    TopCategoriesCardViewModel
from focuswatch.views.components.card_widget import CardWidget

logger = logging.getLogger(__name__)


class TopCategoriesCardView(CardWidget):
  """View for the Top Categories Card component."""

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
    self.categories_layout = QVBoxLayout(self.categories_container)

    # Create the view for the chart
    self.chart_view = QChartView()
    self.chart_view.setRenderHint(QPainter.Antialiasing)
    self.chart_view.setMinimumSize(300, 300)

    # Add both views to the CardWidget using add_content_view
    self.add_content_view(self.categories_container)
    # self.add_content_view(self.chart_view)

  def _connect_signals(self) -> None:
    """ Connect signals from the ViewModel to the View. """
    self._viewmodel.add_property_observer('top_categories', self._update_view)

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
    for category_id, time in self._viewmodel.top_categories:
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
    """ Update the list of categories with progress bars. """
    total_time = sum(time for _, time in self._viewmodel.top_categories)

    for category_id, time in self._viewmodel.top_categories:
      category = self._viewmodel._category_service.get_category_by_id(
        category_id)
      if category:
        category_layout = QHBoxLayout()

        label = QLabel(f"{category.name} - {self._format_time(time)}")
        # label.setStyleSheet(
        #   f"color: {self._viewmodel.get_category_color(category_id)};")
        # set font to bold
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        category_layout.addWidget(label)

        progress = QProgressBar()
        progress.setValue(int((time / total_time) * 100))
        progress.setTextVisible(False)
        category_layout.addWidget(progress)

        self.categories_layout.addLayout(category_layout)

    # Add a spacer to push the content to the top
    spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding,
                         QSizePolicy.Policy.Expanding)
    self.categories_layout.addItem(spacer)

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
