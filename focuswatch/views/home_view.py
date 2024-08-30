import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication, QSize, Qt, QTimer, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCalendarWidget, QDialog, QFrame, QGridLayout,
                               QHBoxLayout, QMenu, QPushButton, QSizePolicy,
                               QSpacerItem, QVBoxLayout, QWidget, QScrollArea)

from focuswatch.ui.top_applications import TopApplicationsComponent
from focuswatch.ui.top_categories import TopCategoriesComponent
from focuswatch.viewmodels.components.timeline_viewmodel import \
    TimelineViewModel
from focuswatch.views.components.timeline_view import TimelineView
from focuswatch.utils.resource_utils import apply_stylesheet, apply_styles

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService
  from focuswatch.viewmodels.home_viewmodel import HomeViewModel

logger = logging.getLogger(__name__)


class HomeView(QWidget):
  def __init__(self, viewmodel: 'HomeViewModel', parent=None):
    super().__init__(parent)
    self._viewmodel = viewmodel
    self._timeline_view = None

    self.setupUi()
    self.retranslateUi()
    self.connect_signals()
    apply_styles(self, ["nav_buttons.qss", "period_menu.qss"])

  def setupUi(self):
    self.setObjectName(u"page_home")
    self.setStyleSheet(u"")

    # Main Vertical Layout
    self.verticalLayout_3 = QVBoxLayout(self)
    self.verticalLayout_3.setObjectName(u"verticalLayout_3")
    self.verticalLayout_3.setContentsMargins(6, 9, 6, 6)

    # Home Layout
    self.home_verticalLayout = QVBoxLayout()
    self.home_verticalLayout.setObjectName(u"home_verticalLayout")
    self.verticalLayout_3.addLayout(self.home_verticalLayout)

    # Navigation
    self.home_nav_horizontalLayout = QHBoxLayout()
    self.home_nav_horizontalLayout.setSpacing(0)
    self.home_nav_horizontalLayout.setObjectName(u"home_nav_horizontalLayout")
    self.home_nav_horizontalLayout.setContentsMargins(0, 0, 0, 0)

    # Frame for Navigation
    self.home_nav_frame = QFrame(self)
    self.home_nav_frame.setObjectName(u"home_nav_frame")
    sizePolicy2 = QSizePolicy(
      QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    sizePolicy2.setHeightForWidth(
      self.home_nav_frame.sizePolicy().hasHeightForWidth())
    self.home_nav_frame.setSizePolicy(sizePolicy2)
    self.home_nav_frame.setFrameShape(QFrame.Shape.NoFrame)
    self.home_nav_frame.setFrameShadow(QFrame.Shadow.Raised)

    self.horizontalLayout_5 = QHBoxLayout(self.home_nav_frame)
    self.horizontalLayout_5.setSpacing(0)
    self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
    self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)

    # Navigation Buttons
    self.date_prev_button = QPushButton(self.home_nav_frame)
    self.date_prev_button.setObjectName(u"date_prev_button")
    self.horizontalLayout_5.addWidget(self.date_prev_button)

    self.date_button = QPushButton(self.home_nav_frame)
    self.date_button.setObjectName(u"date_button")
    # set fixed width to prevent resizing
    self.date_button.setMinimumSize(QSize(200, 0))
    self.horizontalLayout_5.addWidget(self.date_button)

    self.date_next_button = QPushButton(self.home_nav_frame)
    self.date_next_button.setObjectName(u"date_next_button")
    self.horizontalLayout_5.addWidget(self.date_next_button)

    self.horizontalSpacer_period = QSpacerItem(
      20, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
    self.horizontalLayout_5.addItem(self.horizontalSpacer_period)

    self.period_type_button = QPushButton(self.home_nav_frame)
    self.period_type_button.setObjectName(u"period_type_button")
    self.period_type_button.setMinimumSize(QSize(70, 0))
    self.horizontalLayout_5.addWidget(self.period_type_button)

    self.horizontalSpacer_ref = QSpacerItem(
      40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    self.horizontalLayout_5.addItem(self.horizontalSpacer_ref)

    self.refreshButton = QPushButton(self.home_nav_frame)
    self.refreshButton.setObjectName(u"refreshButton")
    self.horizontalLayout_5.addWidget(self.refreshButton)

    self.home_nav_horizontalLayout.addWidget(self.home_nav_frame)
    self.home_verticalLayout.addLayout(self.home_nav_horizontalLayout)

    # Line Separator
    self.line = QFrame(self)
    self.line.setObjectName(u"line")
    apply_stylesheet(self.line, "separator.qss")
    self.line.setFrameShadow(QFrame.Shadow.Plain)
    self.line.setFrameShape(QFrame.Shape.HLine)

    self.home_verticalLayout.addWidget(self.line)

    # Main content layout
    self.main_layout = QHBoxLayout()
    self.home_verticalLayout.addLayout(self.main_layout)

    # Placeholders just for the proper positioning
    # Timeline frame
    self.timeline_frame = QFrame(self)
    self.timeline_frame.setMinimumSize(QSize(300, 400))
    self.timeline_frame.setMaximumSize(QSize(300, 16777215))
    self.timeline_layout = QVBoxLayout(self.timeline_frame)

    self.timeline_frame.setStyleSheet(
      u"background-color: #161616; border: none;")

    # Timeline buttons
    # self.btn_timeline_activity = QPushButton("Activity")
    # self.btn_timeline_projects = QPushButton("Projects")

    # timeline_buttons_layout = QHBoxLayout()
    # timeline_buttons_layout.addWidget(self.btn_timeline_activity)
    # timeline_buttons_layout.addWidget(self.btn_timeline_projects)
    # timeline_buttons_layout.addStretch()

    # self.timeline_layout.addLayout(timeline_buttons_layout)

    # Scroll area for timeline
    self.scroll_timeline = QScrollArea(self.timeline_frame)
    self.scroll_timeline.setWidgetResizable(True)
    self.scroll_area_widget = QWidget()
    self.scroll_timeline.setWidget(self.scroll_area_widget)

    self.timeline_layout.addWidget(self.scroll_timeline)
    self.main_layout.addWidget(self.timeline_frame)

    self.content_frame = QFrame(self)
    self.content_layout = QVBoxLayout(self.content_frame)
    self.main_layout.addWidget(self.content_frame)

  def retranslateUi(self):
    self.date_prev_button.setText(
      QCoreApplication.translate("Home", "<", None))
    self.date_next_button.setText(
      QCoreApplication.translate("Home", ">", None))
    self.period_type_button.setText(QCoreApplication.translate(
      "Home", self._viewmodel.period_type, None))
    self.refreshButton.setText(
      QCoreApplication.translate("Home", "Refresh", None))
    self.update_date_button_text()

  def connect_signals(self):
    self._viewmodel.property_changed.connect(
      self.on_viewmodel_property_changed)
    self.date_prev_button.clicked.connect(self.on_date_prev_clicked)
    self.date_next_button.clicked.connect(self.on_date_next_clicked)
    self.date_button.clicked.connect(self.show_calendar)
    self.period_type_button.clicked.connect(self.show_period_menu)
    # self.refreshButton.clicked.connect(self.refresh_data)

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

    self.period_type_button.setText(period_type)

  @Slot(str)
  def on_viewmodel_property_changed(self, property_name: str):
    if property_name in ['period_updated']:
      self.update_date_button_text()
  #     self.update_components()

  # @Slot(str)
  # def update_timeline_period(self, property_name: str):
  #   if property_name in ['period_start', 'period_end']:
  #     self._timeline_viewmodel.period_start = self._viewmodel.period_start
  #     self._timeline_viewmodel.period_end = self._viewmodel.period_end

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

  # def refresh_data(self):
  #   self.update_components()

  # def update_components(self):
  #   self.clearComponents()
  #   QTimer.singleShot(0, self.component_setup)

  # def component_setup(self):
  #   """ Setup the components """
  #   if self._timeline_view is None or not self._timeline_view.isVisible():
  #     self._timeline_view = TimelineView(self._timeline_viewmodel)
  #     self.gridLayout.addWidget(self._timeline_view, 2, 0, 1, 1)

  #   self._timeline_viewmodel.period_start = self._viewmodel.period_start
  #   self._timeline_viewmodel.period_end = self._viewmodel.period_end
  #   self._timeline_viewmodel.update_timeline_data()

  # def clearComponents(self):
  #   """ Clear the components related to timeline, top categories, and top applications """
  #   if self._timeline_view:
  #     self._timeline_view.setParent(None)
  #     self._timeline_view.deleteLater()
  #     self._timeline_view = None

  # def clearLayout(self, layout):
  #   """ Clear the layout """
  #   if layout is not None:
  #     while layout.count():
  #       item = layout.takeAt(0)
  #       widget = item.widget()
  #       if widget is not None:
  #         widget.deleteLater()
  #       else:
  #         self.clearLayout(item.layout())

  # def showEvent(self, event):
  #   super().showEvent(event)
  #   QTimer.singleShot(0, self.update_components)

  # @Slot(str)
  # def update_timeline_period(self, property_name: str):
  #   if property_name in ['period_start', 'period_end']:
  #     self._timeline_viewmodel.period_start = self._viewmodel.period_start
  #     self._timeline_viewmodel.period_end = self._viewmodel.period_end
  #     self._timeline_viewmodel.update_timeline_data()
