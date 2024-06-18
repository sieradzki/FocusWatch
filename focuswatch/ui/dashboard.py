""" Dashboard UI """
from collections import defaultdict
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
from focuswatch.ui.category_dialog import CategoryDialog
from focuswatch.ui.timeline import TimelineComponent
from focuswatch.ui.top_categories import TopCategoriesComponent
from focuswatch.ui.top_applications import TopApplicationsComponent
from focuswatch.ui.utils import get_category_color, get_contrasting_text_color


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

  """ Categorization tab """

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

    # Categorization tab
    self.tabWidget.addTab(self.dashboard_tab, "")
    self._categorization_tab = CategorizationTab(
        self._category_manager, self._keyword_manager, parent=self)
    self.categorization_tab = self._categorization_tab.setupUi()

    self.tabWidget.addTab(self.categorization_tab, "")

    # Settings tab
    self.settings_tab = QWidget()
    self.settings_tab.setObjectName(u"settings_tab")
    self.verticalLayout_9 = QVBoxLayout(self.settings_tab)
    self.verticalLayout_9.setObjectName(u"verticalLayout_9")
    self.tab_settings_watcher = QTabWidget(self.settings_tab)
    self.tab_settings_watcher.setObjectName(u"tab_settings_watcher")
    self.tab = QWidget()
    self.tab.setObjectName(u"tab")
    self.verticalLayout_10 = QVBoxLayout(self.tab)
    self.verticalLayout_10.setObjectName(u"verticalLayout_10")
    self.watcher_tab_layout = QVBoxLayout()
    self.watcher_tab_layout.setObjectName(u"watcher_tab_layout")
    self.watcher_tab_layout.setContentsMargins(2, -1, -1, -1)
    self.watch_label = QLabel(self.tab)
    self.watch_label.setObjectName(u"watch_label")
    font2 = QFont()
    font2.setBold(False)
    self.watch_label.setFont(font2)

    self.watcher_tab_layout.addWidget(self.watch_label)

    self.watch_interval = QDoubleSpinBox(self.tab)
    self.watch_interval.setObjectName(u"watch_interval")
    self.watch_interval.setDecimals(1)
    self.watch_interval.setMinimum(1.000000000000000)
    self.watch_interval.setMaximum(60.000000000000000)
    self.watch_interval.setSingleStep(0.500000000000000)

    self.watcher_tab_layout.addWidget(self.watch_interval)

    self.watch_afk = QCheckBox(self.tab)
    self.watch_afk.setObjectName(u"watch_afk")

    self.watcher_tab_layout.addWidget(self.watch_afk)

    self.afk_label = QLabel(self.tab)
    self.afk_label.setObjectName(u"afk_label")
    self.afk_label.setEnabled(False)

    self.watcher_tab_layout.addWidget(self.afk_label)

    self.afk_timeout = QSpinBox(self.tab)
    self.afk_timeout.setObjectName(u"afk_timeout")
    self.afk_timeout.setEnabled(False)
    self.afk_timeout.setMinimum(1)
    self.afk_timeout.setValue(5)

    self.watcher_tab_layout.addWidget(self.afk_timeout)

    self.label_2 = QLabel(self.tab)
    self.label_2.setObjectName(u"label_2")

    self.watcher_tab_layout.addWidget(self.label_2)

    self.verticalSpacer_3 = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    self.watcher_tab_layout.addItem(self.verticalSpacer_3)

    self.verticalLayout_10.addLayout(self.watcher_tab_layout)

    self.tab_settings_watcher.addTab(self.tab, "")
    self.tab_settings_startup = QWidget()
    self.tab_settings_startup.setObjectName(u"tab_settings_startup")
    self.horizontalLayout_4 = QHBoxLayout(self.tab_settings_startup)
    self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
    self.label = QLabel(self.tab_settings_startup)
    self.label.setObjectName(u"label")
    font3 = QFont()
    font3.setPointSize(16)
    self.label.setFont(font3)
    self.label.setAlignment(Qt.AlignCenter)

    self.horizontalLayout_4.addWidget(self.label)

    self.tab_settings_watcher.addTab(self.tab_settings_startup, "")

    self.verticalLayout_9.addWidget(self.tab_settings_watcher)

    self.buttonBox = QDialogButtonBox(self.settings_tab)
    self.buttonBox.setObjectName(u"buttonBox")
    self.buttonBox.setStandardButtons(
      QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

    self.verticalLayout_9.addWidget(self.buttonBox)
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
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.dashboard_tab), QCoreApplication.translate("Dashboard", u"Dashboard", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.categorization_tab), QCoreApplication.translate("Dashboard", u"Categorization", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.settings_tab), QCoreApplication.translate("Dashboard", u"Settings", None))
    self.watch_label.setText(QCoreApplication.translate(
      "Dashboard", u"Watch interval", None))
    self.watch_interval.setSuffix(
      QCoreApplication.translate("Dashboard", u" s", None))
    self.watch_afk.setText(QCoreApplication.translate(
      "Dashboard", u"Watch afk", None))
    self.afk_label.setText(QCoreApplication.translate(
      "Dashboard", u"AFK timeout", None))
    self.afk_timeout.setSuffix(
      QCoreApplication.translate("Dashboard", u" m", None))
    self.afk_timeout.setPrefix("")
    self.label_2.setText(QCoreApplication.translate(
      "Dashboard", u"Note: the changes will be applied on next restart", None))
    self.tab_settings_watcher.setTabText(self.tab_settings_watcher.indexOf(
      self.tab), QCoreApplication.translate("Dashboard", u"Watcher", None))
    self.label.setText(QCoreApplication.translate(
      "Dashboard", u"Not implemented", None))
    self.tab_settings_watcher.setTabText(self.tab_settings_watcher.indexOf(
      self.tab_settings_startup), QCoreApplication.translate("Dashboard", u"Startup", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.settings_tab), QCoreApplication.translate("Dashboard", u"Settings", None))
  # retranslateUi

  def onShow(self, event):
    self.setupUi(self)
