""" Dashboard UI """
from datetime import datetime, timedelta

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCalendarWidget, QCheckBox, QDialog,
                               QDialogButtonBox, QDoubleSpinBox, QFrame,
                               QGridLayout, QHBoxLayout, QLabel,
                               QMainWindow, QMenuBar, QPushButton,
                               QSizePolicy, QSpacerItem, QSpinBox, QStatusBar,
                               QTabWidget, QVBoxLayout, QWidget)

from focuswatch.database.activity_manager import ActivityManager
from focuswatch.database.category_manager import CategoryManager
from focuswatch.database.keyword_manager import KeywordManager
from focuswatch.ui.categorization_tab import CategorizationTab
from focuswatch.ui.timeline import TimelineComponent
from focuswatch.ui.top_categories import TopCategoriesComponent
from focuswatch.ui.top_applications import TopApplicationsComponent
from focuswatch.ui.settings_tab import SettingsTab


class Dashboard(QMainWindow):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.selected_date = datetime.now()
    # TODO date_start date_end when selected time period > 1 day ?

    self._activity_manager = ActivityManager()
    self._category_manager = CategoryManager()
    self._keyword_manager = KeywordManager()
    self.setupUi(self)

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
        self.selected_date = calendar.selectedDate().toPython()
        calendar_dialog.accept()

      confirm_button.clicked.connect(get_selected_date)
      calendar_dialog.setLayout(layout)
      calendar_dialog.exec_()
      self.onShow(self.showEvent)

    # Next day
    elif sender_name == 'date_next_button':
      self.selected_date = self.selected_date + timedelta(days=1)
      self.date_button.setText(str(self.selected_date))

    # Refresh the dashboard
    self.onShow(self.showEvent)

  def setupUi(self, Dashboard):
    if not Dashboard.objectName():
      Dashboard.setObjectName(u"Dashboard")
      # Resize only on first run
      if not Dashboard.isVisible():
        Dashboard.resize(1600, 900)
    Dashboard.setTabShape(QTabWidget.Rounded)
    self.centralwidget = QWidget(Dashboard)
    self.centralwidget.setObjectName(u"centralwidget")
    self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
    self.verticalLayout_2.setObjectName(u"verticalLayout_2")
    self.verticalLayout = QVBoxLayout()
    self.verticalLayout.setObjectName(u"verticalLayout")
    self.tabWidget = QTabWidget(self.centralwidget)
    self.tabWidget.setObjectName(u"tabWidget")
    self.tabWidget.setTabShape(QTabWidget.Rounded)
    self.tabWidget.setDocumentMode(False)
    self.tabWidget.setTabBarAutoHide(False)

    # Dashboard tab
    self.dashboard_tab = QWidget()
    self.dashboard_tab.setObjectName(u"dashboard_tab")
    self.gridLayout = QGridLayout(self.dashboard_tab)
    self.gridLayout.setObjectName(u"gridLayout")

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
    if str(self.selected_date.strftime("%Y-%m-%d")) == str(datetime.today().strftime("%Y-%m-%d")):
      self.date_button.setText("Today")
    else:
      self.date_button.setText(str(self.selected_date.strftime("%Y-%m-%d")))

    self.horizontalLayout.addWidget(self.date_button)

    self.date_next_button = QPushButton(self.date_nav_frame)
    self.date_next_button.setObjectName(u"date_next_button")
    self.date_next_button.setMaximumSize(QSize(20, 16777215))
    self.date_next_button.clicked.connect(self.select_date)

    self.horizontalLayout.addWidget(self.date_next_button)

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

    self.tabWidget.addTab(self.dashboard_tab, "")

    # Categorization tab
    self._categorization_tab = CategorizationTab(
        self._category_manager, self._keyword_manager, parent=self)
    self.categorization_tab = self._categorization_tab.setupUi()

    self.tabWidget.addTab(self.categorization_tab, "")

    # Settings tab
    self._settings_tab = SettingsTab(parent=self)
    self.settings_tab = self._settings_tab.setupUi()
    self.tabWidget.addTab(self.settings_tab, "")

    self.verticalLayout.addWidget(self.tabWidget)

    self.verticalLayout_2.addLayout(self.verticalLayout)
    Dashboard.setCentralWidget(self.centralwidget)
    self.menubar = QMenuBar(Dashboard)
    self.menubar.setObjectName(u"menubar")
    self.menubar.setGeometry(QRect(0, 0, 1600, 22))
    Dashboard.setMenuBar(self.menubar)
    self.statusbar = QStatusBar(Dashboard)
    self.statusbar.setObjectName(u"statusbar")
    Dashboard.setStatusBar(self.statusbar)

    self.retranslateUi(Dashboard)

    self.tabWidget.setCurrentIndex(0)

    QMetaObject.connectSlotsByName(Dashboard)

    self.showEvent = self.onShow
    self.refreshButton.clicked.connect(self.showEvent)
  # setupUi

  def retranslateUi(self, Dashboard):
    Dashboard.setWindowTitle(QCoreApplication.translate(
      "Dashboard", u"FocusWatch", None))
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

    # Tabs
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.dashboard_tab), QCoreApplication.translate("Dashboard", u"Dashboard", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.categorization_tab), QCoreApplication.translate("Dashboard", u"Categorization", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.settings_tab), QCoreApplication.translate("Dashboard", u"Settings", None))
  # retranslateUi

  def onShow(self, event):
    self.setupUi(self)
