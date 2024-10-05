import logging

from PySide6.QtCharts import QChart, QPieSeries
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QSpacerItem

from focuswatch.views.components.top_items_card_view import TopItemsCardView

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