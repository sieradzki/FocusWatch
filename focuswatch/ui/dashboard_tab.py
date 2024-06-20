""" Dashboard tab for the FocusWatch Ui. """
from datetime import datetime, timedelta
import logging
from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt
from PySide6.QtWidgets import (QCalendarWidget, QDialog, QFrame, QGridLayout,
                               QHBoxLayout, QPushButton, QSizePolicy,
                               QSpacerItem, QVBoxLayout, QWidget)

from focuswatch.ui.timeline import TimelineComponent
from focuswatch.ui.top_applications import TopApplicationsComponent
from focuswatch.ui.top_categories import TopCategoriesComponent


class DashboardTab(QWidget):
  def __init__(self, activity_manager, category_manager, keyword_manager, parent=None):
    super().__init__(parent)
    self._activity_manager = activity_manager
    self._category_manager = category_manager
    self._keyword_manager = keyword_manager
    self._parent = parent

    self.selected_date: datetime = datetime.now()
    # self.setupUi()

  def setupUi(self):
    self.dashboard_tab = QWidget()
    self.dashboard_tab.setObjectName(u"dashboard_tab")
    self.gridLayout = QGridLayout(self.dashboard_tab)
    self.gridLayout.setObjectName(u"gridLayout")

    # Set up the components
    self.component_setup()

    # Date nav
    self.verticalSpacer = QSpacerItem(
      20, 5, QSizePolicy.Minimum, QSizePolicy.Minimum)

    self.gridLayout.addItem(self.verticalSpacer, 1, 0, 1, 1)

    self.date_nav_frame = QFrame(self.dashboard_tab)
    self.date_nav_frame.setObjectName(u"date_nav_frame")
    sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
    sizePolicy1.setHorizontalStretch(0)
    sizePolicy1.setVerticalStretch(0)
    sizePolicy1.setHeightForWidth(
      self.date_nav_frame.sizePolicy().hasHeightForWidth())
    self.date_nav_frame.setSizePolicy(sizePolicy1)
    self.date_nav_frame.setMaximumSize(QSize(250, 16777215))
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
    self.time_period_button.setEnabled(False)

    self.horizontalLayout.addWidget(self.time_period_button)

    self.gridLayout.addWidget(self.date_nav_frame, 0, 0, 1, 4)

    self.horizontalSpacer_2 = QSpacerItem(
      5, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)

    self.gridLayout.addItem(self.horizontalSpacer_2, 2, 1, 1, 1)

    self.frame = QFrame(self.dashboard_tab)
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

    QMetaObject.connectSlotsByName(self.dashboard_tab)

    self.retranslateUi()
    return self.dashboard_tab

  def onShow(self, event):
    self.update_date()
    self.component_setup()

  def component_setup(self):
    """ Setup the components """
    # Timeline setup
    self._timeline = TimelineComponent(
        self.dashboard_tab, self._activity_manager, self._category_manager, self.selected_date)
    self._timeline_frame = self._timeline.setupUi()

    self.gridLayout.addWidget(self._timeline_frame, 2, 0, 1, 1)

    # Top categories setup
    self._top_categories = TopCategoriesComponent(
        self.dashboard_tab, self._activity_manager, self._category_manager, self.selected_date)
    self._top_categories_frame = self._top_categories.setupUi()

    self.gridLayout.addWidget(self._top_categories_frame, 2, 2, 1, 1)

    # Top applications setup
    self._top_applications = TopApplicationsComponent(
        self.dashboard_tab, self._activity_manager, self._category_manager, self.selected_date)
    self._top_applications_frame = self._top_applications.setupUi()

    self.gridLayout.addWidget(self._top_applications_frame, 2, 4, 1, 1)

  def update_date(self):
    """ Update the date displayed on the button. """
    if str(self.selected_date.strftime("%Y-%m-%d")) == str(datetime.today().strftime("%Y-%m-%d")):
      self.date_button.setText("Today")
    else:
      self.date_button.setText(str(self.selected_date.strftime("%Y-%m-%d")))

  def clearLayout(self, layout):
    """ Clear the layout """
    for i in reversed(range(layout.count())):
      item = layout.itemAt(i)

      if isinstance(item, QSpacerItem):
        continue

      widget = item.widget()

      if widget is not None:
        widget.deleteLater()
      else:
        self.clearLayout(item)

  def retranslateUi(self):
    # Date nav
    self.date_prev_button.setText(
      QCoreApplication.translate("Dashboard", u"<", None))
    # self.date_button.setText(
    # QCoreApplication.translate("Dashboard", u"Today", None))
    self.date_next_button.setText(
      QCoreApplication.translate("Dashboard", u">", None))
    self.time_period_button.setText(
      QCoreApplication.translate("Dashboard", u"Day view", None))
    self.refreshButton.setText(
      QCoreApplication.translate("Dashboard", u"Refresh", None))

  def select_date(self):
    """ Select date for dashboard """
    sender_name = self.sender().objectName()

    # Previous day
    if sender_name == 'date_prev_button':
      self.selected_date = self.selected_date - timedelta(days=1)

    # Select date
    elif sender_name == 'date_button':
      # Create a dialog to select a date
      calendar_dialog = QDialog(self)
      calendar_dialog.setWindowTitle("Select a Date")

      layout = QVBoxLayout()
      calendar = QCalendarWidget()
      layout.addWidget(calendar)
      confirm_button = QPushButton("Confirm Date")
      layout.addWidget(confirm_button)

      # Define a slot to capture the selected date
      def get_selected_date():
        calendar_date = calendar.selectedDate().toPython()
        formatted_date = calendar_date.strftime("%Y-%m-%d")
        self.selected_date = datetime.strptime(formatted_date, "%Y-%m-%d")
        calendar_dialog.accept()

      confirm_button.clicked.connect(get_selected_date)
      calendar_dialog.setLayout(layout)
      calendar_dialog.exec_()

    # Next day
    elif sender_name == 'date_next_button':
      self.selected_date = self.selected_date + timedelta(days=1)
      self.date_button.setText(str(self.selected_date))

    # Refresh the dashboard
    self.onShow(self.showEvent)
