from focuswatch.viewmodels.base_viewmodel import BaseViewModel
from focuswatch.services.activity_service import ActivityService
from focuswatch.services.category_service import CategoryService
from datetime import datetime, timedelta


class DashboardViewModel(BaseViewModel):
  def __init__(self, activity_service: ActivityService, category_service: CategoryService):
    super().__init__()
    self._activity_service = activity_service
    self._category_service = category_service
    self._selected_date = datetime.now().date()
    self._selected_period = "Day"

  @property
  def selected_date(self) -> datetime.date:
    return self._selected_date

  @selected_date.setter
  def selected_date(self, value: datetime.date) -> None:
    self._set_property('_selected_date', value)
    self._update_dashboard_data()

  @property
  def selected_period(self) -> str:
    return self._selected_period

  @selected_period.setter
  def selected_period(self, value: str) -> None:
    self._set_property('_selected_period', value)
    self._update_dashboard_data()

  def _update_dashboard_data(self) -> None:
    # This method will fetch and update all dashboard data based on the selected date and period
    self._update_timeline_data()
    self._update_top_categories()
    self._update_top_applications()

  def _update_timeline_data(self) -> None:
    # Fetch and update timeline data
    # This is a placeholder. Implement the actual logic.
    pass

  def _update_top_categories(self) -> None:
    # Fetch and update top categories data
    # This is a placeholder. Implement the actual logic.
    pass

  def _update_top_applications(self) -> None:
    # Fetch and update top applications data
    # This is a placeholder. Implement the actual logic.
    pass
