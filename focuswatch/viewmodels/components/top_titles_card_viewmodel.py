import logging
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from focuswatch.viewmodels.components.top_items_card_viewmodel import TopItemsCardViewModel

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService

logger = logging.getLogger(__name__)


class TopTitlesCardViewModel(TopItemsCardViewModel):
  """ ViewModel for the Top Applications Card component """

  def __init__(self,
               activity_service: 'ActivityService',
               period_start: datetime,
               period_end: Optional[datetime] = None):
    super().__init__(period_start, period_end)
    self._activity_service = activity_service

    self.update_top_items()

  def update_top_items(self) -> None:
    """ Update the list of top items."""
    self._top_items.clear()
    top_titles = self._activity_service.get_period_entries_name_time_total(
      self._period_start, self._period_end)[:self._top_items_limit]

    for name, category, time, focused in top_titles:
      self._top_items[name] = (
        time, None, None)

    self.property_changed.emit('top_items')
