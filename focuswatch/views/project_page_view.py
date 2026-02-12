from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QSpacerItem, QSizePolicy, QVBoxLayout, QWidget, QHBoxLayout

from focuswatch.utils.resource_utils import apply_stylesheet

if TYPE_CHECKING:
  from focuswatch.viewmodels.project_page_viewmodel import ProjectPageViewModel


class ProjectPageView(QWidget):
  """ Single project page. """

  back_requested = Signal()

  def __init__(self, 
               viewmodel: "ProjectPageViewModel", 
               parent: Optional[QObject] = None):
    super().__init__(parent)
    self._viewmodel = viewmodel

    self._setup_ui()
    self._connect_signals()

    apply_stylesheet(self, "projects_view.qss")

  def _setup_ui(self) -> None:
    self.setObjectName("project_page_view")

    self.main_layout = QVBoxLayout(self)
    self.main_layout.setContentsMargins(0, 0, 0, 0)

    header = QFrame(self)
    header.setObjectName("project_page_header")
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(10, 10, 10, 10)

    self.button_back = QPushButton("← Back")
    self.button_back.setObjectName("button_back")
    header_layout.addWidget(self.button_back)

    self.title_label = QLabel("")
    self.title_label.setObjectName("project_page_title")
    header_layout.addWidget(self.title_label)

    header_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

    self.main_layout.addWidget(header)

    self.body = QWidget(self)
    body_layout = QVBoxLayout(self.body)
    body_layout.setContentsMargins(10, 10, 10, 10)

    self.placeholder_label = QLabel("Project page (coming soon)")
    self.placeholder_label.setObjectName("project_page_placeholder")
    body_layout.addWidget(self.placeholder_label)

    body_layout.addStretch(1)
    self.main_layout.addWidget(self.body)

  def _connect_signals(self) -> None:
    self.button_back.clicked.connect(self.back_requested.emit)
    self._viewmodel.project_changed.connect(self._on_project_changed)

  @Slot()
  def _on_project_changed(self) -> None:
    self.title_label.setText(self._viewmodel.project_name or "Project")
