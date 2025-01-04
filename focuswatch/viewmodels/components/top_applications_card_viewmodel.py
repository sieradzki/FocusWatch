import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from focuswatch.viewmodels.components.top_items_card_viewmodel import \
    TopItemsCardViewModel

if TYPE_CHECKING:
  from focuswatch.config import Config
  from focuswatch.services.activity_service import ActivityService

logger = logging.getLogger(__name__)


class TopApplicationsCardViewModel(TopItemsCardViewModel):
  """ ViewModel for the Top Applications Card component """

  def __init__(self,
               activity_service: "ActivityService",
               config: "Config",
               period_start: datetime,
               period_end: Optional[datetime] = None
               ):
    super().__init__(period_start, period_end)
    self._activity_service = activity_service
    self._config = config

    self.update_top_items()

  def update_top_items(self) -> None:
    """ Update the list of top items."""
    top_applications = self._activity_service.get_period_entries_class_time_total(
      self._period_start, self._period_end)[:self._top_items_limit]

    # clear top items
    self._top_items.clear()
    for application, _, time, _ in top_applications:
      if not self._config["dashboard"]["display_cards_idle"]:
        if application == "afk":
          continue
      self._top_items[application] = (
        time, None, None)

    self.top_items_changed.emit()

  def get_application_icon(self, application: str) -> Optional[str]:
    """ Get the icon path for an application. """
    pass
