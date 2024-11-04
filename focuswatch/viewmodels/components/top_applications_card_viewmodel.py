import logging
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from focuswatch.viewmodels.components.top_items_card_viewmodel import TopItemsCardViewModel

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService

logger = logging.getLogger(__name__)


class TopApplicationsCardViewModel(TopItemsCardViewModel):
  """ ViewModel for the Top Applications Card component """

  def __init__(self,
               activity_service: 'ActivityService',
               period_start: datetime,
               period_end: Optional[datetime] = None):
    super().__init__(period_start, period_end)
    self._activity_service = activity_service

    self._update_top_items()

  def _update_top_items(self) -> None:
    """ Update the list of top items."""
    top_applications = self._activity_service.get_period_entries_class_time_total(
      self._period_start, self._period_end)[:self._top_items_limit]

    # clear top items
    self._top_items.clear()
    for application, category, time, focused in top_applications:
      self._top_items[application] = (
        time, None, None)

    self.property_changed.emit('top_items')

  def get_application_icon(self, application: str) -> Optional[str]:
    """ Get the icon path for an application. """
    return None  # TODO
