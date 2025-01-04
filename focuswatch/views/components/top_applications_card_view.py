import logging

from PySide6.QtCore import Slot

from focuswatch.views.components.top_items_card_view import TopItemsCardView

logger = logging.getLogger(__name__)


class TopApplicationsCardView(TopItemsCardView):
  """ View for the Top Applications Card. """
  def __init__(self,
               viewmodel,
               parent=None):
    super().__init__("Top Applications", viewmodel, parent)

  def _connect_signals(self):
    """ Connect signals from the ViewModel to the View. """
    self._viewmodel.top_items_changed.connect(self.on_top_items_changed)

  @Slot()
  def on_top_items_changed(self):
    self._update_view()
