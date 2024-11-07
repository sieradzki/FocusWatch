import logging

from focuswatch.views.components.top_items_card_view import TopItemsCardView
from PySide6.QtCore import Slot

logger = logging.getLogger(__name__)


class TopTitlesCardView(TopItemsCardView):
  def __init__(self,
               viewmodel,
               parent=None):
    super().__init__("Top Titles", viewmodel, parent)

  def _connect_signals(self):
    """ Connect signals from the ViewModel to the View. """
    self._viewmodel.top_items_changed.connect(self.on_top_items_changed)

  @Slot()
  def on_top_items_changed(self):
    self._update_view()
