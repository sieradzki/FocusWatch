from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, Qt, QSize
from PySide6.QtWidgets import (QMainWindow, QMenuBar, QStatusBar, QTabWidget,
                               QVBoxLayout, QWidget, QHBoxLayout, QFrame, QLabel, QToolButton, QSpacerItem, QSizePolicy, QStackedWidget)
from PySide6.QtGui import QIcon, QFont

from focuswatch.viewmodels.mainwindow_viewmodel import MainWindowViewModel
from focuswatch.views.categorization_view import CategorizationView
from focuswatch.views.dashboard_view import DashboardView
from focuswatch.views.settings_view import SettingsView
from focuswatch.utils.resource_utils import apply_stylesheet, load_icon


class MainWindowView(QMainWindow):
  def __init__(self, viewmodel: MainWindowViewModel, parent=None):
    super().__init__(parent)
    self._viewmodel = viewmodel
    self.setupUi()
    self.connect_signals()

  def setupUi(self):
    if not self.objectName():
      self.setObjectName(u"MainWindow")
    self.resize(*self._viewmodel.window_size)
    self.setWindowTitle(self._viewmodel.window_title)

    # Central widget
    self.centralwidget = QWidget(self)
    self.centralwidget.setObjectName(u"centralwidget")
    self.horizontalLayout = QHBoxLayout(self.centralwidget)
    self.horizontalLayout.setSpacing(0)
    self.horizontalLayout.setObjectName(u"horizontalLayout")
    self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

    # Sidebar
    self.sidebar = QFrame(self.centralwidget)
    self.sidebar.setObjectName(u"sidebar")
    self.sidebar.setFixedWidth(100)
    self.sidebar.setStyleSheet(
      u"background-color: #101010; border: none;")
    self.sidebar.setFrameShape(QFrame.NoFrame)
    self.sidebar.setFrameShadow(QFrame.Raised)

    # Sidebar Layout
    self.sidebarLayout = QVBoxLayout(self.sidebar)
    self.sidebarLayout.setSpacing(6)
    self.sidebarLayout.setObjectName(u"sidebarLayout")
    self.sidebarLayout.setContentsMargins(0, 6, 0, 6)

    # Logo
    self.logo_label = QLabel(self.sidebar)
    self.logo_label.setObjectName(u"logo_label")
    font1 = QFont()
    font1.setPointSize(10)
    font1.setBold(True)
    self.logo_label.setFont(font1)
    self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.sidebarLayout.addWidget(self.logo_label)

    # Sidebar Buttons
    self.sidebar_button_home = self.create_sidebar_button(
      "Home", "home.png")
    self.sidebar_button_categories = self.create_sidebar_button(
      "Categories", "categories.png")
    self.sidebar_button_help = self.create_sidebar_button(
      "Help", "help.png")
    self.sidebar_button_settings = self.create_sidebar_button(
      "Settings", "settings.png")

    # Add buttons to layout
    self.sidebarLayout.addWidget(
      self.sidebar_button_home, 0, Qt.AlignmentFlag.AlignHCenter)
    self.sidebarLayout.addWidget(
      self.sidebar_button_categories, 0, Qt.AlignmentFlag.AlignHCenter)
    self.sidebarLayout.addSpacerItem(QSpacerItem(
      20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
    self.sidebarLayout.addWidget(
      self.sidebar_button_help, 0, Qt.AlignmentFlag.AlignHCenter)
    self.sidebarLayout.addWidget(
      self.sidebar_button_settings, 0, Qt.AlignmentFlag.AlignHCenter)

    # Add Sidebar to Main Layout
    self.horizontalLayout.addWidget(self.sidebar)

    # Main content area
    self.stackedWidget = QStackedWidget(self.centralwidget)
    self.horizontalLayout.addWidget(self.stackedWidget)

    """
    # self.tabWidget = QTabWidget(self.centralwidget)
    # self.tabWidget.setObjectName(u"tabWidget")
    # self.tabWidget.setTabShape(QTabWidget.Rounded)
    # self.tabWidget.setDocumentMode(False)
    # self.tabWidget.setTabBarAutoHide(False)

    # # Dashboard tab
    # self._dashboard_view = DashboardView(
    #     self._viewmodel.dashboard_viewmodel, self._viewmodel._activity_service, self._viewmodel._category_service)
    # self.tabWidget.addTab(self._dashboard_view, "")

    # # Categorization tab
    # self._categorization_view = CategorizationView(
    #     self._viewmodel.categorization_viewmodel)
    # self.tabWidget.addTab(self._categorization_view, "")

    # # Settings tab
    # self._settings_view = SettingsView(
    #     self._viewmodel.settings_viewmodel)
    # self.settings_tab = self._settings_view.setupUi()
    # self.tabWidget.addTab(self.settings_tab, "")

    # self.verticalLayout.addWidget(self.tabWidget)
    # self.verticalLayout_2.addLayout(self.verticalLayout)
    # self.setCentralWidget(self.centralwidget)

    # self.menubar = QMenuBar(self)
    # self.menubar.setObjectName(u"menubar")
    # self.menubar.setGeometry(QRect(0, 0, 1600, 22))
    # self.setMenuBar(self.menubar)

    # self.statusbar = QStatusBar(self)
    # self.statusbar.setObjectName(u"statusbar")
    # self.setStatusBar(self.statusbar)
    """

    self.setCentralWidget(self.centralwidget)
    self.retranslateUi()
    # self.tabWidget.setCurrentIndex(self._viewmodel.current_tab_index)

    QMetaObject.connectSlotsByName(self)

    # Connect signals
    # self.tabWidget.currentChanged.connect(self._viewmodel.switch_tab)

  def retranslateUi(self):
    self.logo_label.setText(QCoreApplication.translate(
      "MainWindow", u"FocusWatch", None))
    self.sidebar_button_home.setText(
      QCoreApplication.translate("MainWindow", u"Home", None))
    self.sidebar_button_categories.setText(
      QCoreApplication.translate("MainWindow", u"Categories", None))
    self.sidebar_button_help.setText(
      QCoreApplication.translate("MainWindow", u"Help", None))
    self.sidebar_button_settings.setText(
      QCoreApplication.translate("MainWindow", u"Settings", None))
    # for i, name in enumerate(self._viewmodel.tab_names):
    # self.tabWidget.setTabText(
    # i, QCoreApplication.translate("MainWindow", name, None))

  def create_sidebar_button(self, text: str, icon_path: str) -> QToolButton:
    """ Helper method to create sidebar buttons. """
    button = QToolButton(self.sidebar)
    button.setObjectName(f"sidebar_button_{text.lower()}")

    # Set size policy
    button_size_policy = QSizePolicy(
      QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    button.setSizePolicy(button_size_policy)
    button.setMinimumSize(QSize(90, 70))
    button.setMaximumSize(QSize(90, 70))

    button.setText(text)
    button.setIcon(load_icon(icon_path))
    button.setIconSize(QSize(32, 32))
    button.setCheckable(True)
    button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    return button

  def closeEvent(self, event):
    self._viewmodel.exit_application()
    super().closeEvent(event)

  def connect_signals(self):
    self._viewmodel.property_changed.connect(self.on_property_changed)

  def on_property_changed(self, property_name):
    print(f"Property changed: {property_name}")
