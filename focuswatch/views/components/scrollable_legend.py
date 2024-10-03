""" Custom widget for a scrollable legend. """
import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QScrollArea, QVBoxLayout,
                               QWidget)

from focuswatch.utils.resource_utils import apply_stylesheet

logger = logging.getLogger(__name__)


class ScrollableLegend(QScrollArea):
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

    # Apply the new stylesheet
    apply_stylesheet(self, "components/scrollable_legend.qss")

  def add_item(self, icon: Optional[QPixmap] = None, label: str = ""):
    item_widget = QWidget()
    item_layout = QHBoxLayout(item_widget)
    item_layout.setContentsMargins(0, 0, 0, 0)

    if icon:  # possible feauture in top applications card
      icon_label = QLabel()
      # icon_label.setPixmap(icon.scaled(
      # 16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
      # item_layout.addWidget(icon_label)
    else:
      color_box = QLabel()
      color_box.setFixedSize(QSize(10, 10))
      color_box.setStyleSheet(
        "background-color: grey; border: none;")
      item_layout.addWidget(color_box)

    label_widget = QLabel(label)
    label_widget.setWordWrap(True)
    item_layout.addWidget(label_widget, 1)

    self.layout.addWidget(item_widget)
