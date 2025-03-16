import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QCoreApplication, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMainWindow,
                               QSizePolicy, QSpacerItem,
                               QStackedWidget, QToolButton,
                               QVBoxLayout, QWidget)

from focuswatch.utils.resource_utils import apply_stylesheet, load_icon
from focuswatch.views.categories_view import CategoriesView
from focuswatch.views.home_view import HomeView
from focuswatch.views.settings_view import SettingsView

if TYPE_CHECKING:
  from focuswatch.viewmodels.mainwindow_viewmodel import MainWindowViewModel

logger = logging.getLogger(__name__)


class MainWindowView(QMainWindow):
  """ Main window view. """

  def __init__(self,
               viewmodel: "MainWindowViewModel",
               parent: Optional[QWidget] = None):
    super().__init__(parent)
    self._viewmodel = viewmodel
    self._setup_ui()
    self._retranslate_ui()
    self._connect_signals()

  def _setup_ui(self):
    if not self.objectName():
      self.setObjectName("MainWindow")
    self.resize(*self._viewmodel.window_size)
    self.setWindowTitle(self._viewmodel.window_title)

    # Central widget
    self.central_widget = QWidget(self)
    self.central_widget.setObjectName("central_widget")
    self.horizontal_layout = QHBoxLayout(self.central_widget)
    self.horizontal_layout.setSpacing(0)
    self.horizontal_layout.setObjectName("horizontal_layout")
    self.horizontal_layout.setContentsMargins(0, 0, 0, 0)

    # Sidebar
    self.sidebar = QFrame(self.central_widget)
    self.sidebar.setObjectName("sidebar")
    self.sidebar.setFixedWidth(100)
    self.sidebar.setStyleSheet(
      "background-color: #101010; border: none;")
    self.sidebar.setFrameShape(QFrame.NoFrame)
    self.sidebar.setFrameShadow(QFrame.Raised)

    # Sidebar Layout
    self.sidebar_layout = QVBoxLayout(self.sidebar)
    self.sidebar_layout.setSpacing(6)
    self.sidebar_layout.setObjectName("sidebar_layout")
    self.sidebar_layout.setContentsMargins(0, 6, 0, 6)

    # Logo
    self.logo_label = QLabel(self.sidebar)
    self.logo_label.setObjectName("logo_label")
    font1 = QFont()
    font1.setPointSize(10)
    font1.setBold(True)
    self.logo_label.setFont(font1)
    self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.sidebar_layout.addWidget(self.logo_label)

    # Sidebar Buttons
    self.sidebar_button_home = self._create_sidebar_button(
      "Home", "home.png")
    self.sidebar_button_categories = self._create_sidebar_button(
      "Categories", "categories.png")
    self.sidebar_button_projects = self._create_sidebar_button(
      "Projects", "projects.png"
    )
    # self.sidebar_button_help = self._create_sidebar_button(
    # "Help", "help.png")
    self.sidebar_button_settings = self._create_sidebar_button(
      "Settings", "settings.png")

    # Add buttons to layout
    self.sidebar_layout.addWidget(
      self.sidebar_button_home, 0, Qt.AlignmentFlag.AlignHCenter)
    self.sidebar_layout.addWidget(
      self.sidebar_button_categories, 0, Qt.AlignmentFlag.AlignHCenter)
    self.sidebar_layout.addWidget(
      self.sidebar_button_projects, 0, Qt.AlignmentFlag.AlignHCenter)
    self.sidebar_layout.addSpacerItem(QSpacerItem(
      20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
    # self.sidebar_layout.addWidget(
    # self.sidebar_button_help, 0, Qt.AlignmentFlag.AlignHCenter)
    self.sidebar_layout.addWidget(
      self.sidebar_button_settings, 0, Qt.AlignmentFlag.AlignHCenter)

    # Add Sidebar to Main Layout
    self.horizontal_layout.addWidget(self.sidebar)

    # Main content area
    self.stacked_widget = QStackedWidget(self.central_widget)
    self.horizontal_layout.addWidget(self.stacked_widget)

    # Pages
    self.page_home = HomeView(self._viewmodel.home_viewmodel)
    self.page_categories = CategoriesView(
      self._viewmodel.categories_viewmodel)
    self.page_settings = SettingsView(self._viewmodel.settings_viewmodel)

    # Add pages to the stacked widget
    self.stacked_widget.addWidget(self.page_home)
    self.stacked_widget.addWidget(self.page_categories)
    self.stacked_widget.addWidget(self.page_settings)

    # Set the central widget
    self.setCentralWidget(self.central_widget)

    self._update_sidebar_buttons()

  def _retranslate_ui(self):
    self.logo_label.setText(QCoreApplication.translate(
      "MainWindow", "focuswatch", None))
    self.sidebar_button_home.setText(
      QCoreApplication.translate("MainWindow", "Home", None))
    self.sidebar_button_categories.setText(
      QCoreApplication.translate("MainWindow", "Categories", None))
    # self.sidebar_button_help.setText(
    # QCoreApplication.translate("MainWindow", "Help", None))
    self.sidebar_button_settings.setText(
      QCoreApplication.translate("MainWindow", "Settings", None))

  def _create_sidebar_button(self, text: str, icon_path: str) -> QToolButton:
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

  def _create_mock_page(self, page_name: str) -> QWidget:  # Not needed anymore
    """ Helper method to create a mock page with a label for distinguishing pages. """
    page = QWidget()
    layout = QVBoxLayout(page)
    label = QLabel(page_name)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)
    return page

  def closeEvent(self, event):  # noqa: N802
    self._viewmodel.exit_application()
    super().closeEvent(event)

  def _connect_signals(self):
    """ Connect signals to their respective slots. """
    # Connect ViewModel signals
    self._viewmodel.current_page_index_changed.connect(
        self._on_current_page_index_changed)
    self._viewmodel.window_title_changed.connect(
        self._on_window_title_changed)
    self._viewmodel.window_size_changed.connect(
        self._on_window_size_changed)

    # Connect button signals to slots for page switching
    self.sidebar_button_home.clicked.connect(
        lambda: self._switch_page("home"))
    self.sidebar_button_categories.clicked.connect(
        lambda: self._switch_page("categories"))
    self.sidebar_button_settings.clicked.connect(
        lambda: self._switch_page("settings"))

  def _switch_page(self, name: str):
    """ Switch the page in the stacked widget. """
    self._viewmodel.current_page_index = self._viewmodel.page_index(name)

  def _update_sidebar_buttons(self,):
    """ Update the sidebar buttons to reflect the current page. """
    buttons = self.sidebar.findChildren(QToolButton)
    for button in buttons:
      if button.objectName().endswith(self._viewmodel.pages[self._viewmodel.current_page_index]):
        button.setChecked(True)
      else:
        button.setChecked(False)

  def _on_current_page_index_changed(self):
    """ Handle changes to the current page index. """
    self.stacked_widget.setCurrentIndex(self._viewmodel.current_page_index)
    self._update_sidebar_buttons()

  def _on_window_title_changed(self):
    """ Handle changes to the window title. """
    self.setWindowTitle(self._viewmodel.window_title)

  def _on_window_size_changed(self):
    """ Handle changes to the window size. """
    self.resize(*self._viewmodel.window_size)
