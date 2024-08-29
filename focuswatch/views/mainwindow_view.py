import logging

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMainWindow,
                               QMenuBar, QPushButton, QSizePolicy, QSpacerItem,
                               QStackedWidget, QStatusBar, QTabWidget,
                               QToolButton, QVBoxLayout, QWidget)

from focuswatch.utils.resource_utils import apply_stylesheet, load_icon
from focuswatch.viewmodels.mainwindow_viewmodel import MainWindowViewModel
from focuswatch.views.categorization_view import CategorizationView
from focuswatch.views.dashboard_view import DashboardView
from focuswatch.views.settings_view import SettingsView

logger = logging.getLogger(__name__)


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
    # self.sidebar_button_help = self.create_sidebar_button(
    # "Help", "help.png")
    self.sidebar_button_settings = self.create_sidebar_button(
      "Settings", "settings.png")

    # Add buttons to layout
    self.sidebarLayout.addWidget(
      self.sidebar_button_home, 0, Qt.AlignmentFlag.AlignHCenter)
    self.sidebarLayout.addWidget(
      self.sidebar_button_categories, 0, Qt.AlignmentFlag.AlignHCenter)
    self.sidebarLayout.addSpacerItem(QSpacerItem(
      20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
    # self.sidebarLayout.addWidget(
    # self.sidebar_button_help, 0, Qt.AlignmentFlag.AlignHCenter)
    self.sidebarLayout.addWidget(
      self.sidebar_button_settings, 0, Qt.AlignmentFlag.AlignHCenter)

    # Add Sidebar to Main Layout
    self.horizontalLayout.addWidget(self.sidebar)

    # Main content area
    self.stackedWidget = QStackedWidget(self.centralwidget)
    self.horizontalLayout.addWidget(self.stackedWidget)

    # Mock Pages for testing
    self.page_home = self.create_mock_page("Home Page")
    self.page_categories = self.create_mock_page("Categories Page")
    self.page_settings = self.create_mock_page("Settings Page")

    # Add pages to the stacked widget
    self.stackedWidget.addWidget(self.page_home)
    self.stackedWidget.addWidget(self.page_categories)
    self.stackedWidget.addWidget(self.page_settings)

    # Set the central widget
    self.setCentralWidget(self.centralwidget)
    self.retranslateUi()

    self.update_sidebar_buttons() # TODO Should I just setChecked the home button?

    QMetaObject.connectSlotsByName(self)

  def retranslateUi(self):
    self.logo_label.setText(QCoreApplication.translate(
      "MainWindow", u"focuswatch", None))
    self.sidebar_button_home.setText(
      QCoreApplication.translate("MainWindow", u"Home", None))
    self.sidebar_button_categories.setText(
      QCoreApplication.translate("MainWindow", u"Categories", None))
    # self.sidebar_button_help.setText(
    # QCoreApplication.translate("MainWindow", u"Help", None))
    self.sidebar_button_settings.setText(
      QCoreApplication.translate("MainWindow", u"Settings", None))

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
    apply_stylesheet(button, "sidebar_button.qss")

    return button

  def create_mock_page(self, page_name: str) -> QWidget:
    """ Helper method to create a mock page with a label for distinguishing pages. """
    page = QWidget()
    layout = QVBoxLayout(page)
    label = QLabel(page_name)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)
    return page

  def closeEvent(self, event):
    self._viewmodel.exit_application()
    super().closeEvent(event)

  def connect_signals(self):
    self._viewmodel.property_changed.connect(self.on_property_changed)
    """ Connect button signals to slots for page switching. """
    self.sidebar_button_home.clicked.connect(lambda: self.switch_page("home"))
    self.sidebar_button_categories.clicked.connect(
      lambda: self.switch_page("categories"))
    self.sidebar_button_settings.clicked.connect(
      lambda: self.switch_page("settings"))

  def switch_page(self, name: str):
    """ Switch the page in the stacked widget. """
    self._viewmodel.current_page_index = self._viewmodel.page_index(name)

  def update_sidebar_buttons(self,):
    """ Update the sidebar buttons to reflect the current page. """
    buttons = self.sidebar.findChildren(QToolButton)
    for button in buttons:
      if button.objectName().endswith(self._viewmodel.pages[self._viewmodel.current_page_index]):
        button.setChecked(True)
      else:
        button.setChecked(False)

  def on_property_changed(self, property_name):
    if property_name == '_current_page_index':
      self.stackedWidget.setCurrentIndex(self._viewmodel.current_page_index)
      self.update_sidebar_buttons()
