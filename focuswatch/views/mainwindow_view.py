from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QTimer
from PySide6.QtWidgets import (QMainWindow, QMenuBar, QStatusBar, QTabWidget,
                               QVBoxLayout, QWidget)

from focuswatch.ui.dashboard_tab import DashboardTab
from focuswatch.viewmodels.mainwindow_viewmodel import MainWindowViewModel
from focuswatch.views.categorization_view import CategorizationView
from focuswatch.views.settings_view import SettingsView


class MainWindowView(QMainWindow):
  def __init__(self, viewmodel: MainWindowViewModel, parent=None):
    super().__init__(parent)
    self._viewmodel = viewmodel
    self.setupUi()

  def setupUi(self):
    if not self.objectName():
      self.setObjectName(u"MainWindow")
    self.resize(*self._viewmodel.window_size)
    self.setWindowTitle(self._viewmodel.window_title)
    self.setTabShape(QTabWidget.Rounded)

    self.centralwidget = QWidget(self)
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
    # Temporarily use managers instead of services # TODO
    from focuswatch.database.activity_manager import ActivityManager
    from focuswatch.database.category_manager import CategoryManager
    from focuswatch.database.keyword_manager import KeywordManager

    acitivity_manager = ActivityManager()
    category_manager = CategoryManager()
    keyword_manager = KeywordManager()

    self._dashboard_tab = DashboardTab(
        acitivity_manager, category_manager, keyword_manager)

    # self._dashboard_tab = DashboardTab(
    #     self._viewmodel.get_activity_service(),
    #     self._viewmodel.get_category_service(),
    #     self._viewmodel.get_keyword_service()
    # )

    self.dashboard_tab = self._dashboard_tab.setupUi()
    self.tabWidget.addTab(self.dashboard_tab, "")

    # Categorization tab
    self._categorization_view = CategorizationView(
      self._viewmodel.get_categorization_viewmodel())
    self.categorization_tab = self._categorization_view.setupUi()
    self.tabWidget.addTab(self.categorization_tab, "")

    # Settings tab
    self._settings_view = SettingsView(
        self._viewmodel.get_settings_viewmodel())
    self.settings_tab = self._settings_view.setupUi()
    self.tabWidget.addTab(self.settings_tab, "")

    self.verticalLayout.addWidget(self.tabWidget)
    self.verticalLayout_2.addLayout(self.verticalLayout)
    self.setCentralWidget(self.centralwidget)

    self.menubar = QMenuBar(self)
    self.menubar.setObjectName(u"menubar")
    self.menubar.setGeometry(QRect(0, 0, 1600, 22))
    self.setMenuBar(self.menubar)

    self.statusbar = QStatusBar(self)
    self.statusbar.setObjectName(u"statusbar")
    self.setStatusBar(self.statusbar)

    self.retranslateUi()
    self.tabWidget.setCurrentIndex(self._viewmodel.current_tab_index)

    QMetaObject.connectSlotsByName(self)

    # Connect signals
    self.tabWidget.currentChanged.connect(self._viewmodel.switch_tab)

  def retranslateUi(self):
    for i, name in enumerate(self._viewmodel.tab_names):
      self.tabWidget.setTabText(
          i, QCoreApplication.translate("MainWindow", name, None))

  def closeEvent(self, event):
    self._viewmodel.exit_application()
    super().closeEvent(event)
