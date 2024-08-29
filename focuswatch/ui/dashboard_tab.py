""" Home tab for the FocusWatch Ui. """
from datetime import datetime, timedelta
import logging
from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt
from PySide6.QtWidgets import (QCalendarWidget, QDialog, QFrame, QGridLayout,
                               QHBoxLayout, QPushButton, QSizePolicy,
                               QSpacerItem, QVBoxLayout, QWidget, QMenu)

from focuswatch.ui.timeline import TimelineComponent
from focuswatch.ui.top_applications import TopApplicationsComponent
from focuswatch.ui.top_categories import TopCategoriesComponent

logger = logging.getLogger(__name__)


class HomeTab(QWidget):
  def __init__(self, activity_manager, category_manager, keyword_manager, parent=None):
    super().__init__(parent)
    self._activity_manager = activity_manager
    self._category_manager = category_manager
    self._keyword_manager = keyword_manager
    self._parent = parent

    self.period_start: datetime = datetime.now()
    self.period_end: datetime = None
    self.current_period = "Day"
    # self.setupUi()

  def setupUi(self):
    self.home_tab = QWidget()
    self.home_tab.setObjectName(u"home_tab")
    self.gridLayout = QGridLayout(self.home_tab)
    self.gridLayout.setObjectName(u"gridLayout")

    # Set up the components
    self.component_setup()

    # Date nav
    self.verticalSpacer = QSpacerItem(
      20, 5, QSizePolicy.Minimum, QSizePolicy.Minimum)

    self.gridLayout.addItem(self.verticalSpacer, 1, 0, 1, 1)

    self.date_nav_frame = QFrame(self.home_tab)
    self.date_nav_frame.setObjectName(u"date_nav_frame")
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
    self.horizontalLayout.setObjectName(u"horizontalLayout")
    self.date_prev_button = QPushButton(self.date_nav_frame)
    self.date_prev_button.setObjectName(u"date_prev_button")
    sizePolicy1.setHeightForWidth(
      self.date_prev_button.sizePolicy().hasHeightForWidth())
    self.date_prev_button.setSizePolicy(sizePolicy1)
    self.date_prev_button.setMaximumSize(QSize(20, 16777215))
    self.date_prev_button.clicked.connect(self.select_date)

    self.horizontalLayout.addWidget(self.date_prev_button)

    self.date_button = QPushButton(self.date_nav_frame)
    self.date_button.setObjectName(u"date_button")
    self.date_button.clicked.connect(self.select_date)
    sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    sizePolicy2.setHorizontalStretch(0)
    sizePolicy2.setVerticalStretch(0)
    sizePolicy2.setHeightForWidth(
      self.date_button.sizePolicy().hasHeightForWidth())
    self.date_button.setSizePolicy(sizePolicy2)
    self.date_button.setMaximumSize(QSize(600, 16777215))

    self.horizontalLayout.addWidget(self.date_button)

    self.date_next_button = QPushButton(self.date_nav_frame)
    self.date_next_button.setObjectName(u"date_next_button")
    self.date_next_button.setMaximumSize(QSize(20, 16777215))
    self.date_next_button.clicked.connect(self.select_date)

    self.horizontalLayout.addWidget(self.date_next_button)

    self.update_date()

    self.horizontalSpacer_3 = QSpacerItem(
      15, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

    self.horizontalLayout.addItem(self.horizontalSpacer_3)

    self.time_period_button = QPushButton(self.date_nav_frame)
    self.time_period_button.setObjectName(u"time_period_button")
    self.time_period_button.setEnabled(True)
    self.time_period_button.clicked.connect(self.show_period_menu)

    self.horizontalLayout.addWidget(self.time_period_button)

    self.gridLayout.addWidget(self.date_nav_frame, 0, 0, 1, 4)

    self.horizontalSpacer_2 = QSpacerItem(
      5, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)

    self.gridLayout.addItem(self.horizontalSpacer_2, 2, 1, 1, 1)

    self.frame = QFrame(self.home_tab)
    self.frame.setObjectName(u"frame")
    self.frame.setLayoutDirection(Qt.RightToLeft)
    self.frame.setStyleSheet(u"")
    self.frame.setFrameShape(QFrame.NoFrame)
    self.frame.setFrameShadow(QFrame.Raised)
    self.horizontalLayout_3 = QHBoxLayout(self.frame)
    self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
    self.refreshButton = QPushButton(self.frame)
    self.refreshButton.setObjectName(u"refreshButton")
    self.refreshButton.setMaximumSize(QSize(80, 16777215))

    self.horizontalLayout_3.addWidget(self.refreshButton)

    self.horizontalSpacer = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.horizontalLayout_3.addItem(self.horizontalSpacer)

    self.gridLayout.addWidget(self.frame, 0, 4, 1, 1)

    self.showEvent = self.onShow
    self.refreshButton.clicked.connect(self.showEvent)

    QMetaObject.connectSlotsByName(self.home_tab)

    self.retranslateUi()
    return self.home_tab

  def retranslateUi(self):
    self.date_prev_button.setText(
      QCoreApplication.translate("Home", u"<", None))
    self.date_next_button.setText(
      QCoreApplication.translate("Home", u">", None))
    self.time_period_button.setText(
      QCoreApplication.translate("Home", self.current_period, None))
    self.refreshButton.setText(
      QCoreApplication.translate("Home", u"Refresh", None))

  def onShow(self):
    self.clearComponents()
    self.update_date()
    self.component_setup()

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

  def component_setup(self):
    """ Setup the components """
    # Timeline setup
    self._timeline = TimelineComponent(
        self.home_tab, self._activity_manager, self._category_manager, self.period_start, self.period_end)
    self._timeline_frame = self._timeline.setupUi()

    self.gridLayout.addWidget(self._timeline_frame, 2, 0, 1, 1)

    # Top categories setup
    self._top_categories = TopCategoriesComponent(
        self.home_tab, self._activity_manager, self._category_manager, self.period_start, self.period_end)
    self._top_categories_frame = self._top_categories.setupUi()

    self.gridLayout.addWidget(self._top_categories_frame, 2, 2, 1, 1)

    # Top applications setup
    self._top_applications = TopApplicationsComponent(
        self.home_tab, self._activity_manager, self._category_manager, self.period_start, self.period_end)
    self._top_applications_frame = self._top_applications.setupUi()

    self.gridLayout.addWidget(self._top_applications_frame, 2, 4, 1, 1)

  def update_date(self):
    """ Update the date displayed on the button. """
    if self.current_period == "Day":
      if str(self.period_start.strftime("%Y-%m-%d")) == str(datetime.today().strftime("%Y-%m-%d")):
        self.date_button.setText("Today")
      else:
        self.date_button.setText(str(self.period_start.strftime("%d-%m-%Y")))
    elif self.current_period == "Week":
      self.date_button.setText(f"{self.period_start.strftime(
        '%b %d')} - {self.period_end.strftime('%b %d, %Y')}")
    elif self.current_period == "Month":
      self.date_button.setText(self.period_start.strftime("%B %Y"))
    elif self.current_period == "Year":
      self.date_button.setText(self.period_start.strftime("%Y"))

  def select_date(self):
    """ Select date for home """
    sender_name = self.sender().objectName()

    if sender_name == 'date_prev_button':
      self.change_period(-1)
    elif sender_name == 'date_button':
      self.show_calendar()
    elif sender_name == 'date_next_button':
      self.change_period(1)

    self.update_date()
    self.onShow()

  def change_period(self, direction):
    """ Change the period based on the current view and direction """
    if self.current_period == "Day":
      self.period_start += timedelta(days=direction)
      self.period_end = None
    elif self.current_period == "Week":
      self.period_start += timedelta(weeks=direction)
      self.period_end = self.period_start + timedelta(days=6)
    elif self.current_period == "Month":
      new_month = self.period_start.month + direction
      new_year = self.period_start.year + (new_month - 1) // 12
      new_month = ((new_month - 1) % 12) + 1
      self.period_start = self.period_start.replace(
        year=new_year, month=new_month, day=1)
      self.period_end = (self.period_start +
                         timedelta(days=32).replace(day=1) - timedelta(days=1))
    elif self.current_period == "Year":
      self.period_start = self.period_start.replace(
        year=self.period_start.year + direction, month=1, day=1)
      self.period_end = self.period_start.replace(
        year=self.period_start.year + 1) - timedelta(days=1)

  def show_calendar(self):
    """ Show calendar dialog for date selection """
    calendar_dialog = QDialog(self)
    calendar_dialog.setWindowTitle("Select a Date")

    layout = QVBoxLayout()
    calendar = QCalendarWidget()
    layout.addWidget(calendar)
    confirm_button = QPushButton("Confirm Date")
    layout.addWidget(confirm_button)

    def get_selected_date():
      calendar_date = calendar.selectedDate().toPython()
      self.period_start = calendar_date
      if self.current_period == "Week":
        self.period_start -= timedelta(days=self.period_start.weekday())
      elif self.current_period == "Month":
        self.period_start = self.period_start.replace(day=1)
      elif self.current_period == "Year":
        self.period_start = self.period_start.replace(month=1, day=1)
      calendar_dialog.accept()

    confirm_button.clicked.connect(get_selected_date)
    calendar_dialog.setLayout(layout)
    calendar_dialog.exec_()

  def show_period_menu(self):
    """ Show menu for selecting time period """
    menu = QMenu(self)
    actions = {}
    for period in ["Day", "Week", "Month", "Year"]:
      actions[period] = menu.addAction(period)

    action = menu.exec_(self.time_period_button.mapToGlobal(
      self.time_period_button.rect().bottomLeft()))

    if action:
      self.set_period(action.text())

  def set_period(self, period):
    """ Set the current period and update the view """
    self.current_period = period
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "Day":
      self.period_start = today
      self.period_end = None
    elif period == "Week":
      self.period_start = today - timedelta(days=today.weekday())
      self.period_end = self.period_start + timedelta(days=6)
    elif period == "Month":
      self.period_start = today.replace(day=1)
      self.period_end = (self.period_start + timedelta(days=32)
                         ).replace(day=1) - timedelta(days=1)
    elif period == "Year":
      self.period_start = today.replace(month=1, day=1)
      self.period_end = self.period_start.replace(
        year=self.period_start.year + 1) - timedelta(days=1)

    self.update_date()
    self.time_period_button.setText(self.current_period)
    self.onShow()
