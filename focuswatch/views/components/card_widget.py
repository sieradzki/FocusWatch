from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame,
                               QHBoxLayout, QSizePolicy, QStackedWidget, QPushButton, QSpacerItem)
from PySide6.QtCore import QSize, Qt
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
    self.label_title.setFont(self.font())
    self.verticalLayout.addWidget(self.label_title)

    self.separator = QFrame(self.frame_container)
    self.separator.setObjectName("separator")
    self.separator.setFrameShape(QFrame.Shape.HLine)
    self.separator.setFrameShadow(QFrame.Shadow.Sunken)
    self.separator.setFixedHeight(2)
    self.verticalLayout.addWidget(self.separator)

    # Stacked widget to hold multiple content views
    self.stacked_widget = QStackedWidget(self.frame_container)
    self.stacked_widget.setObjectName("stacked_widget")
    self.verticalLayout.addWidget(self.stacked_widget)

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
    self.navigation_layout.addSpacerItem(QSpacerItem(
      20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
    self.verticalLayout.addLayout(self.navigation_layout)

    # Initially hide the navigation layout
    self.toggle_navigation_buttons(False)

    layout.addWidget(self.frame_container)

  def add_content_view(self, widget):
    """ Add a new content view to the card. """
    self.stacked_widget.addWidget(widget)
    self.content_views.append(widget)
    self.toggle_navigation_buttons(len(self.content_views) > 1)

  def toggle_navigation_buttons(self, show):
    """ Show or hide the navigation layout based on the number of content views. """
    if show:
      # If the navigation layout isn't already in the vertical layout, add it.
      if self.navigation_layout not in [self.verticalLayout.itemAt(i).layout() for i in range(self.verticalLayout.count())]:
        self.verticalLayout.addLayout(self.navigation_layout)
    else:
      # If there's only one view, remove the navigation layout from the vertical layout
      self.verticalLayout.removeItem(self.navigation_layout)

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
