""" Custom widget for a scrollable legend. """
import logging
from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QScrollArea, QVBoxLayout,
                               QWidget, QSpacerItem, QSizePolicy)

from focuswatch.utils.resource_utils import apply_stylesheet
from focuswatch.views.components.elided_label import ElidedLabel

logger = logging.getLogger(__name__)


class ScrollableLegend(QScrollArea):
  """ Custom widget for a scrollable legend. """
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWidgetResizable(True)
    self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    self.setMaximumWidth(150)
    self.setMinimumWidth(100)
    self.setMaximumHeight(300)

    self.content_widget = QWidget()
    self.setWidget(self.content_widget)
    self.layout = QVBoxLayout(self.content_widget)
    self.layout.setContentsMargins(0, 10, 0, 0)

    apply_stylesheet(self, "components/scrollable_legend.qss")

  # or icon path
  def add_item(self, label: str, color: Optional[str] = None, icon: Optional[QPixmap] = None, depth: int = 0):
    item_widget = QWidget()
    item_layout = QHBoxLayout(item_widget)
    item_layout.setContentsMargins(0, 0, 0, 0)

    if depth > 0:
      spacer = QSpacerItem(
        10 * depth, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
      item_layout.addSpacerItem(spacer)
    if icon:  # possible feature in top applications card
      icon_label = QLabel()
      icon_label.setPixmap(icon.scaled(
          16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
      item_layout.addWidget(icon_label)
    else:
      color_box = QLabel()
      color_box.setFixedSize(QSize(10, 10))
      color_box.setStyleSheet(
        f"background-color: {color}; border: none; border-radius: 1px;")
      item_layout.addWidget(color_box)

    label_widget = ElidedLabel(label)
    label_widget.setWordWrap(True)
    item_layout.addWidget(label_widget, 1)

    self.layout.addWidget(item_widget)
