from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QSizePolicy, QSpacerItem, QStackedWidget,
                               QVBoxLayout, QWidget)

from focuswatch.utils.resource_utils import apply_stylesheet


class CardWidget(QWidget):
  """ Base class for all card-like components in the application. """

  def __init__(self, title: str, parent=None):
    super().__init__(parent)
    self.title = title
    self.current_index = 0
    self.content_views = []
    self.setupUi()
    apply_stylesheet(self, "components/card_widget.qss")

  def setupUi(self):
    layout = QVBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)

    # Create a QFrame to group all elements
    self.frame_container = QFrame(self)
    self.frame_container.setObjectName("frame_container")

    self.verticalLayout = QVBoxLayout(self.frame_container)
    self.verticalLayout.setContentsMargins(0, 0, 0, 0)
    self.verticalLayout.setSpacing(0)

    self.label_title = QLabel(self.title, self.frame_container)
    self.label_title.setObjectName("label_title")
    self.verticalLayout.addWidget(self.label_title)

    self.separator = QFrame(self.frame_container)
    self.separator.setObjectName("separator")
    self.separator.setFrameShape(QFrame.Shape.HLine)
    self.separator.setFrameShadow(QFrame.Shadow.Sunken)
    self.separator.setFixedHeight(2)
    self.verticalLayout.addWidget(self.separator)

    # Main stacked widget to switch between content and no data views
    self.main_stacked_widget = QStackedWidget(self.frame_container)
    self.main_stacked_widget.setObjectName("main_stacked_widget")

    # Content view container
    self.content_container = QWidget()
    self.content_layout = QVBoxLayout(self.content_container)
    self.content_layout.setContentsMargins(0, 0, 0, 0)
    self.content_layout.setSpacing(0)

    # Stacked widget to hold multiple content views
    self.stacked_widget = QStackedWidget(self.content_container)
    self.stacked_widget.setObjectName("stacked_widget")
    self.content_layout.addWidget(self.stacked_widget)

    # Navigation layout for switching content views
    self.navigation_layout = QHBoxLayout()
    self.navigation_layout.setContentsMargins(0, 0, 0, 0)
    self.navigation_layout.setSpacing(10)

    self.prev_button = QPushButton("<", self)
    self.prev_button.setObjectName("prev_button")
    self.prev_button.setFixedSize(24, 24)
    self.prev_button.clicked.connect(self.show_previous_view)
    self.navigation_layout.addWidget(self.prev_button)

    self.next_button = QPushButton(">", self)
    self.next_button.setObjectName("next_button")
    self.next_button.setFixedSize(24, 24)
    self.next_button.clicked.connect(self.show_next_view)
    self.navigation_layout.addWidget(self.next_button)

    # Spacer to push buttons to the right
    spacer = QSpacerItem(
        20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.navigation_layout.addItem(spacer)
    self.content_layout.addLayout(self.navigation_layout)

    # No data view container
    self.no_data_container = QWidget()
    self.no_data_layout = QVBoxLayout(self.no_data_container)
    self.no_data_layout.setContentsMargins(0, 0, 0, 0)
    self.no_data_layout.setSpacing(0)

    # No data label
    self.no_data_label = QLabel(
        "No data available", self.no_data_container)
    self.no_data_label.setObjectName("no_data_label")
    self.no_data_label.setAlignment(Qt.AlignCenter)
    self.no_data_layout.addWidget(self.no_data_label)

    # Add content and no data containers to the main stacked widget
    self.main_stacked_widget.addWidget(self.content_container)
    self.main_stacked_widget.addWidget(self.no_data_container)

    # Add the main stacked widget to the layout
    self.verticalLayout.addWidget(self.main_stacked_widget)

    # Initially show content view
    self.show_content_view()

    layout.addWidget(self.frame_container)

  def add_content_view(self, widget):
    """ Add a new content view to the card. """
    self.stacked_widget.addWidget(widget)
    self.content_views.append(widget)
    self.toggle_navigation_buttons(len(self.content_views) > 1)

  def toggle_navigation_buttons(self, show):
    """ Show or hide the navigation buttons. """
    self.prev_button.setVisible(show)
    self.next_button.setVisible(show)

  def show_next_view(self):
    """ Show the next content view. """
    self.current_index = (self.current_index + 1) % len(self.content_views)
    self.stacked_widget.setCurrentIndex(self.current_index)

  def show_previous_view(self):
    """ Show the previous content view. """
    self.current_index = (self.current_index - 1) % len(self.content_views)
    self.stacked_widget.setCurrentIndex(self.current_index)

  def show_no_data_view(self, message: str = "No data available"):
    """ Display the no data label and hide the content views. """
    self.no_data_label.setText(message)
    self.main_stacked_widget.setCurrentWidget(self.no_data_container)
    self.toggle_navigation_buttons(False)

  def show_content_view(self):
    """ Hide the no data label and show the content views. """
    self.main_stacked_widget.setCurrentWidget(self.content_container)
    self.toggle_navigation_buttons(len(self.content_views) > 1)

  def _ensure_content_view_visible(self):
    """ Ensure the content view is visible. """
    if self.main_stacked_widget.currentWidget() != self.content_container:
      self.show_content_view()
