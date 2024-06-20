""" Dashboard UI """
from PySide6.QtCore import QCoreApplication, QMetaObject, QRect
from PySide6.QtWidgets import (QMainWindow, QMenuBar, QStatusBar, QTabWidget,
                               QVBoxLayout, QWidget)

from focuswatch.database.activity_manager import ActivityManager
from focuswatch.database.category_manager import CategoryManager
from focuswatch.database.keyword_manager import KeywordManager
from focuswatch.ui.categorization_tab import CategorizationTab
from focuswatch.ui.dashboard_tab import DashboardTab
from focuswatch.ui.settings_tab import SettingsTab


class Dashboard(QMainWindow):
  def __init__(self, parent=None):
    super().__init__(parent)
    self._activity_manager = ActivityManager()
    self._category_manager = CategoryManager()
    self._keyword_manager = KeywordManager()
    self.setupUi(self)

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
    self._dashboard_tab = DashboardTab(
        self._activity_manager, self._category_manager, self._keyword_manager, parent=self)
    self.dashboard_tab = self._dashboard_tab.setupUi()
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
  # setupUi

  def retranslateUi(self, Dashboard):
    Dashboard.setWindowTitle(QCoreApplication.translate(
      "Dashboard", u"FocusWatch", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.dashboard_tab), QCoreApplication.translate("Dashboard", u"Dashboard", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.categorization_tab), QCoreApplication.translate("Dashboard", u"Categorization", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.settings_tab), QCoreApplication.translate("Dashboard", u"Settings", None))
  # retranslateUi

  # def onShow(self, event):
    # self.setupUi(self)
