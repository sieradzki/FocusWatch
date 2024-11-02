""" Generalized ViewModel for Top Items cards. """


from datetime import datetime
from typing import List, Optional, Tuple, Dict

from PySide6.QtCore import Property, Slot
from PySide6.QtGui import QColor

from focuswatch.viewmodels.base_viewmodel import BaseViewModel


class TopItemsCardViewModel(BaseViewModel):
  """ Base ViewModel for Top Items cards. """

  def __init__(self,
               period_start: datetime,
               period_end: Optional[datetime] = None,
               item_limit: int = 10):
    super().__init__()
    self._period_start = period_start
    self._period_end = period_end
    self._top_items_limit = item_limit

    # optional for additional context like icon path for applications but i'm not sure if's gonna be used to be honest
    self._top_items: Dict[str, Tuple[float,
                                     Optional[QColor], Optional[str]]] = {}

  @Slot(datetime, datetime)
  def update_period(self, start: datetime, end: Optional[datetime]) -> None:
    """ Update the time period for item analysis. """
    self.period_start = start
    self.period_end = end
    self._update_top_items()

  @Property(datetime, notify=BaseViewModel.property_changed)
  def period_start(self) -> datetime:
    return self._period_start

  @period_start.setter
  def period_start(self, value: datetime) -> None:
    self._set_property('_period_start', value)
    self._update_top_items()

  @Property(datetime, notify=BaseViewModel.property_changed)
  def period_end(self) -> Optional[datetime]:
    return self._period_end

  @period_end.setter
  def period_end(self, value: Optional[datetime]) -> None:
    self._set_property('_period_end', value)
    self._update_top_items()

  @Property(list, notify=BaseViewModel.property_changed)
  def top_items(self) -> List[Tuple[str, float, Optional[QColor], Optional[str]]]:
    return self._top_items

  def _update_top_items(self) -> None:
    """ Update the list of top items. To be implemented in derived classes. """
    raise NotImplementedError(
        "This method should be implemented in derived classes.")
