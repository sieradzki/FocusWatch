from PySide6.QtCore import QRect, QSize
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QScrollArea,
                               QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from focuswatch.utils.resource_utils import apply_stylesheet


class CardWidget(QWidget):
  """ Base class for all card-like components in the application. """

  def __init__(self, title: str, parent=None):
    super().__init__(parent)
    self.title = title
    self.setupUi()
    apply_stylesheet(self, "components/card_widget.qss")

  def setupUi(self):
    layout = QHBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)

    # Create a QFrame to group all elements
    self.frame_container = QFrame(self)
    self.frame_container.setObjectName("frame_container")

    verticalLayout = QVBoxLayout(self.frame_container)
    verticalLayout.setContentsMargins(0, 0, 0, 0)
    verticalLayout.setSpacing(0)

    self.label_title = QLabel(self.title, self.frame_container)
    self.label_title.setObjectName("label_title")
    self.label_title.setFont(self.font())

    verticalLayout.addWidget(self.label_title)

    self.separator = QFrame(self.frame_container)
    self.separator.setFrameShape(QFrame.Shape.HLine)
    self.separator.setFrameShadow(QFrame.Shadow.Sunken)

    verticalLayout.addWidget(self.separator)

    # Placeholder for content
    self.content_area = QWidget(self.frame_container)
    self.content_area.setObjectName("content_area")
    content_layout = QVBoxLayout(self.content_area)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(0)

    verticalLayout.addWidget(self.content_area)

    # Push the content to the top with spacer
    spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding,
                         QSizePolicy.Policy.Expanding)
    verticalLayout.addItem(spacer)

    layout.addWidget(self.frame_container)

  def add_content(self, widget):
    """ Add a widget to the content area. """
    content_layout = self.content_area.layout()
    content_layout.addWidget(widget)
