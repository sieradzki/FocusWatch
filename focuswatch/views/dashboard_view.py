import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication, QSize, Qt, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCalendarWidget, QDialog, QFrame, QGridLayout,
                               QHBoxLayout, QMenu, QPushButton, QSizePolicy,
                               QSpacerItem, QVBoxLayout, QWidget)

from focuswatch.database.activity_manager import ActivityManager
from focuswatch.database.category_manager import CategoryManager
from focuswatch.database.keyword_manager import KeywordManager
from focuswatch.ui.timeline import TimelineComponent
from focuswatch.ui.top_applications import TopApplicationsComponent
from focuswatch.ui.top_categories import TopCategoriesComponent

if TYPE_CHECKING:
  from focuswatch.viewmodels.dashboard_viewmodel import DashboardViewModel

logger = logging.getLogger(__name__)


class DashboardView(QWidget):
  def __init__(self, viewmodel: 'DashboardViewModel', parent=None):
    super().__init__(parent)
    self._viewmodel = viewmodel

    self._activity_manager = ActivityManager()
    self._category_manager = CategoryManager()
    self._keyword_manager = KeywordManager()

    self.setupUi()
    self.retranslateUi()
    self.connect_signals()

  def setupUi(self):
    self.setObjectName("dashboard_view")
    self.gridLayout = QGridLayout(self)
    self.gridLayout.setObjectName("gridLayout")

    # Date navigation frame
    self.date_nav_frame = QFrame(self)
    self.date_nav_frame.setObjectName("date_nav_frame")
    sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
    sizePolicy1.setHorizontalStretch(0)
    sizePolicy1.setVerticalStretch(0)
    sizePolicy1.setHeightForWidth(
      self.date_nav_frame.sizePolicy().hasHeightForWidth())
    self.date_nav_frame.setSizePolicy(sizePolicy1)
    self.date_nav_frame.setMaximumSize(QSize(350, 16777215))
    self.date_nav_frame.setAutoFillBackground(False)
    self.date_nav_frame.setFrameShape(QFrame.NoFrame)
    self.date_nav_frame.setFrameShadow(QFrame.Raised)
    self.date_nav_frame.setLineWidth(0)

    self.horizontalLayout = QHBoxLayout(self.date_nav_frame)
    self.horizontalLayout.setObjectName("horizontalLayout")

    self.date_prev_button = QPushButton(self.date_nav_frame)
    self.date_prev_button.setObjectName("date_prev_button")
    self.date_prev_button.setMaximumSize(20, 16777215)
    self.horizontalLayout.addWidget(self.date_prev_button)

    self.date_button = QPushButton(self.date_nav_frame)
    self.date_button.setObjectName("date_button")
    self.date_button.setMaximumSize(600, 16777215)
    self.horizontalLayout.addWidget(self.date_button)

    self.date_next_button = QPushButton(self.date_nav_frame)
    self.date_next_button.setObjectName("date_next_button")
    self.date_next_button.setMaximumSize(20, 16777215)
    self.horizontalLayout.addWidget(self.date_next_button)

    self.horizontalSpacer_3 = QSpacerItem(
      15, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
    self.horizontalLayout.addItem(self.horizontalSpacer_3)

    self.period_type_button = QPushButton(self.date_nav_frame)
    self.period_type_button.setObjectName("period_type_button")
    self.horizontalLayout.addWidget(self.period_type_button)

    self.gridLayout.addWidget(self.date_nav_frame, 0, 0, 1, 4)

    # Refresh button frame
    self.refresh_frame = QFrame(self)
    self.refresh_frame.setObjectName("refresh_frame")
    self.refresh_frame.setLayoutDirection(Qt.RightToLeft)
    self.refresh_frame.setFrameShape(QFrame.NoFrame)
    self.refresh_frame.setFrameShadow(QFrame.Raised)

    self.horizontalLayout_3 = QHBoxLayout(self.refresh_frame)
    self.horizontalLayout_3.setObjectName("horizontalLayout_3")

    self.refreshButton = QPushButton(self.refresh_frame)
    self.refreshButton.setObjectName("refreshButton")
    self.refreshButton.setMaximumSize(80, 16777215)
    self.horizontalLayout_3.addWidget(self.refreshButton)

    self.horizontalSpacer = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.horizontalLayout_3.addItem(self.horizontalSpacer)

    self.gridLayout.addWidget(self.refresh_frame, 0, 4, 1, 1)

    # Placeholder for timeline, top categories, and top applications
    self.timeline_frame = QFrame(self)
    self.top_categories_frame = QFrame(self)
    self.top_applications_frame = QFrame(self)

    self.gridLayout.addWidget(self.timeline_frame, 2, 0, 1, 1)
    self.gridLayout.addWidget(self.top_categories_frame, 2, 2, 1, 1)
    self.gridLayout.addWidget(self.top_applications_frame, 2, 4, 1, 1)

  def retranslateUi(self):
    self.date_prev_button.setText(
      QCoreApplication.translate("Dashboard", "<", None))
    self.date_next_button.setText(
      QCoreApplication.translate("Dashboard", ">", None))
    self.period_type_button.setText(QCoreApplication.translate(
      "Dashboard", self._viewmodel.period_type, None))
    self.refreshButton.setText(
      QCoreApplication.translate("Dashboard", "Refresh", None))
    self.update_date_button_text()

  def update_date_button_text(self):
    period_start = self._viewmodel.period_start
    period_end = self._viewmodel.period_end
    period_type = self._viewmodel.period_type

    if period_type == "Day":
      if period_start == datetime.today().date():
        self.date_button.setText("Today")
      else:
        self.date_button.setText(period_start.strftime("%d-%m-%Y"))
    elif period_type == "Week":
      self.date_button.setText(f"{period_start.strftime(
        '%b %d')} - {period_end.strftime('%b %d, %Y')}")
    elif period_type == "Month":
      self.date_button.setText(period_start.strftime("%B %Y"))
    elif period_type == "Year":
      self.date_button.setText(period_start.strftime("%Y"))

  def connect_signals(self):
    self._viewmodel.property_changed.connect(
      self.on_viewmodel_property_changed)
    self.date_prev_button.clicked.connect(self.on_date_prev_clicked)
    self.date_next_button.clicked.connect(self.on_date_next_clicked)
    self.date_button.clicked.connect(self.show_calendar)
    self.period_type_button.clicked.connect(self.show_period_menu)
    self.refreshButton.clicked.connect(self.refresh_data)

  @Slot(str)
  def on_viewmodel_property_changed(self, property_name: str):
    logger.debug(f"DashboardView property changed: {property_name}")
    if property_name in ['period_start', 'period_end', 'period_type']:
      self.update_date_button_text()
      self.update_components()

  def on_date_prev_clicked(self):
    self._viewmodel.shift_period(-1)

  def on_date_next_clicked(self):
    self._viewmodel.shift_period(1)

  def show_calendar(self):
    calendar_dialog = QDialog(self)
    calendar_dialog.setWindowTitle("Select a Date")

    layout = QVBoxLayout()
    calendar = QCalendarWidget()
    layout.addWidget(calendar)
    confirm_button = QPushButton("Confirm Date")
    layout.addWidget(confirm_button)

    def get_selected_date():
      selected_date = calendar.selectedDate().toPython()
      self._viewmodel.update_period_from_selected_date(selected_date)
      calendar_dialog.accept()

    confirm_button.clicked.connect(get_selected_date)
    calendar_dialog.setLayout(layout)
    calendar_dialog.exec_()

  def show_period_menu(self):
    menu = QMenu(self)
    actions = {}
    for period in ["Day", "Week", "Month", "Year"]:
      actions[period] = menu.addAction(period)

    action = menu.exec_(self.period_type_button.mapToGlobal(
      self.period_type_button.rect().bottomLeft()))

    if action:
      self._viewmodel.set_period_type(action.text())

  def refresh_data(self):
    self.update_components()

  def update_components(self):
    self.clearComponents()
    self.component_setup()

  def component_setup(self):
    """ Setup the components """
    # Timeline setup
    self._timeline = TimelineComponent(
        self, self._activity_manager, self._category_manager, self._viewmodel.period_start, self._viewmodel.period_end)
    self._timeline_frame = self._timeline.setupUi()

    self.gridLayout.addWidget(self._timeline_frame, 2, 0, 1, 1)

    # Top categories setup
    self._top_categories = TopCategoriesComponent(
        self, self._activity_manager, self._category_manager, self._viewmodel.period_start, self._viewmodel.period_end)
    self._top_categories_frame = self._top_categories.setupUi()

    self.gridLayout.addWidget(self._top_categories_frame, 2, 2, 1, 1)

    # Top applications setup
    self._top_applications = TopApplicationsComponent(
        self, self._activity_manager, self._category_manager, self._viewmodel.period_start, self._viewmodel.period_end)
    self._top_applications_frame = self._top_applications.setupUi()

    self.gridLayout.addWidget(self._top_applications_frame, 2, 4, 1, 1)

  def clearLayout(self, layout):
    """ Clear the layout """
    if layout is not None:
      while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
          widget.deleteLater()
        else:
          self.clearLayout(item.layout())

  def clearComponents(self):
    """ Clear the components related to timeline, top categories, and top applications """
    if hasattr(self, '_timeline_frame') and self._timeline_frame.layout():
      self.clearLayout(self._timeline_frame.layout())

    if hasattr(self, '_top_categories_frame') and self._top_categories_frame.layout():
      self.clearLayout(self._top_categories_frame.layout())

    if hasattr(self, '_top_applications_frame') and self._top_applications_frame.layout():
      self.clearLayout(self._top_applications_frame.layout())

  # def update_components(self):
  #   # Clear existing components
  #   self.clear_layout(self.timeline_frame.layout())
  #   self.clear_layout(self.top_categories_frame.layout())
  #   self.clear_layout(self.top_applications_frame.layout())

  #   # timeline_data = self._viewmodel.get_timeline_data()
  #   # top_categories_data = self._viewmodel.get_top_categories_data()
  #   # top_applications_data = self._viewmodel.get_top_applications_data()

  #   # import old managers

  #   ac = ActivityManager()
  #   cc = CategoryManager()
  #   kc = KeywordManager()

  #   timeline = TimelineComponent(
  #     self, ac, cc, self._viewmodel.period_start, self._viewmodel.period_end)
  #   top_categories = TopCategoriesComponent(
  #     self, ac, cc, self._viewmodel.period_start, self._viewmodel.period_end)
  #   top_applications = TopApplicationsComponent(
  #     self, ac, cc, self._viewmodel.period_start, self._viewmodel.period_end)

  #   self.timeline_frame.setLayout(QVBoxLayout())
  #   self.timeline_frame.layout().addWidget(timeline.setupUi())

  #   self.top_categories_frame.setLayout(QVBoxLayout())
  #   self.top_categories_frame.layout().addWidget(top_categories.setupUi())

  #   self.top_applications_frame.setLayout(QVBoxLayout())
  #   self.top_applications_frame.layout().addWidget(top_applications.setupUi())

  # def clear_layout(self, layout):
  #   if layout is not None:
  #     while layout.count():
  #       item = layout.takeAt(0)
  #       widget = item.widget()
  #       if widget is not None:
  #         widget.deleteLater()
  #       else:
  #         self.clear_layout(item.layout())

  def showEvent(self, event):
    super().showEvent(event)
    self.update_components()
