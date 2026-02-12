import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QScrollArea,
                               QSizePolicy, QSpacerItem, QVBoxLayout, QWidget,
                               QColorDialog, QDialog, QDialogButtonBox)

from focuswatch.utils.resource_utils import apply_stylesheet
from focuswatch.database.models.project import ProjectStatus

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
  from focuswatch.viewmodels.projects_viewmodel import ProjectsViewModel


class ProjectsView(QWidget):
  """ Projects page view. """

  project_open_requested = Signal(int)

  def __init__(self, viewmodel: "ProjectsViewModel",
               parent: Optional[QObject] = None):
    super().__init__(parent)
    self._viewmodel = viewmodel
    self._setup_ui()
    self._connect_signals()

    apply_stylesheet(self, "projects_view.qss")

  def _setup_ui(self):
    """ Set up the UI components. """
    self.setObjectName("projects_view")

    # Main vertical layout
    self.main_layout = QVBoxLayout(self)
    self.main_layout.setObjectName("main_layout")

    # Top bar with filter and buttons
    self._create_top_bar()

    # Divider line
    self.line_divider = QFrame(self)
    self.line_divider.setObjectName("line_divider")
    self.line_divider.setFrameShape(QFrame.Shape.HLine)
    self.line_divider.setFrameShadow(QFrame.Shadow.Sunken)
    self.main_layout.addWidget(self.line_divider)

    # Main content area
    self._create_main_content_area()

    # Bottom bar with buttons
    self._create_bottom_bar()

  def _create_top_bar(self):
    """ Create the top bar with filter input. """
    self.top_bar = QFrame(self)
    self.top_bar.setObjectName("top_bar")
    self.top_bar_layout = QHBoxLayout(self.top_bar)
    self.top_bar_layout.setContentsMargins(0, 0, 0, 0)
    self.top_bar_layout.setSpacing(10)

    # Filter input
    self.filter_input = QLineEdit(self.top_bar)
    self.filter_input.setObjectName("filter_input")
    self.filter_input.setPlaceholderText("Filter projects...")
    self.filter_input.setClearButtonEnabled(True)
    self.top_bar_layout.addWidget(self.filter_input)

    # Spacer
    self.top_bar_spacer = QSpacerItem(
        40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.top_bar_layout.addItem(self.top_bar_spacer)

    self.main_layout.addWidget(self.top_bar)

  def _create_main_content_area(self):
    """ Create the main content area showing projects. """
    # Scroll area
    self.scroll_area = QScrollArea(self)
    self.scroll_area.setObjectName("scroll_area")
    self.scroll_area.setWidgetResizable(True)
    self.scroll_area_widget = QWidget()
    self.scroll_area_widget.setObjectName("scroll_area_widget")
    self.scroll_area_layout = QVBoxLayout(self.scroll_area_widget)
    self.scroll_area_layout.setObjectName("scroll_area_layout")

    # Projects layout
    self.projects_layout = QVBoxLayout()
    self.projects_layout.setObjectName("projects_layout")
    self.scroll_area_layout.addLayout(self.projects_layout)

    self.scroll_area.setWidget(self.scroll_area_widget)
    self.main_layout.addWidget(self.scroll_area)

    # Populate projects
    self._populate_projects()

  def _create_bottom_bar(self):
    """ Create the bottom bar with add project button. """
    self.bottom_bar = QFrame(self)
    self.bottom_bar.setObjectName("bottom_bar")
    self.bottom_bar_layout = QHBoxLayout(self.bottom_bar)
    self.bottom_bar_layout.setContentsMargins(0, 0, 0, 0)
    self.bottom_bar_layout.setSpacing(10)

    # Add project button
    self.button_add_project = QPushButton("Add Project", self.bottom_bar)
    self.button_add_project.setObjectName("button_add_project")
    self.bottom_bar_layout.addWidget(self.button_add_project)

    # Spacer
    self.bottom_bar_spacer = QSpacerItem(
        40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.bottom_bar_layout.addItem(self.bottom_bar_spacer)

    self.main_layout.addWidget(self.bottom_bar)

  def _connect_signals(self):
    """ Connect signals and slots. """
    # Connect ViewModel signals
    self._viewmodel.projects_changed.connect(self._on_projects_changed)
    self._viewmodel.filter_text_changed.connect(self._on_filter_text_changed)

    # Connect UI signals
    self.filter_input.textChanged.connect(self._on_filter_changed)
    self.button_add_project.clicked.connect(self._show_add_project_dialog)

  @Slot()
  def _on_projects_changed(self):
    """ Handle projects_changed signal from the ViewModel. """
    self._populate_projects()

  @Slot()
  def _on_filter_text_changed(self):
    """ Handle filter_text_changed signal from the ViewModel. """
    self._populate_projects()

  @Slot(str)
  def _on_filter_changed(self, text):
    """ Handle filter text changes. """
    self._viewmodel.filter_text = text

  def _populate_projects(self):
    """ Populate the projects in the main content area. """
    # Clear existing content
    self._clear_layout(self.projects_layout)

    # Header row
    header = QFrame()
    header.setObjectName("projects_header")
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(10, 5, 10, 5)
    header_layout.setSpacing(10)

    # Color column placeholder
    header_layout.addSpacing(16)

    name_header = QLabel("Name")
    name_header.setObjectName("projects_header_label")
    header_layout.addWidget(name_header, 2)

    description_header = QLabel("Description")
    description_header.setObjectName("projects_header_label")
    header_layout.addWidget(description_header, 4)

    total_time_header = QLabel("Total time")
    total_time_header.setObjectName("projects_header_label")
    total_time_header.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    header_layout.addWidget(total_time_header, 1)

    actions_header = QLabel("Actions")
    actions_header.setObjectName("projects_header_label")
    actions_header.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    header_layout.addWidget(actions_header, 1)

    self.projects_layout.addWidget(header)

    filter_text = self._viewmodel.filter_text.lower()

    for project in self._viewmodel.projects:
      if project.status != ProjectStatus.ACTIVE:
        continue

      # Check if project matches the filter
      if filter_text and filter_text not in project.name.lower():
        if not project.description or filter_text not in project.description.lower():
          continue

      # Create project row widget
      project_row_widget = QWidget()
      project_row_widget.setObjectName("project_row_widget")
      project_row_widget.setAutoFillBackground(True)
      project_row_widget.setCursor(Qt.CursorShape.PointingHandCursor)
      project_row_widget.mousePressEvent = (  # type: ignore[method-assign]
        lambda event, p_id=project.id: self._open_project(p_id)
      )
      project_row_layout = QHBoxLayout(project_row_widget)
      project_row_layout.setContentsMargins(10, 5, 10, 5)
      project_row_layout.setSpacing(10)

      # Color Indicator
      color_indicator = QLabel()
      color_indicator.setFixedSize(16, 16)
      if project.color:
        color_indicator.setStyleSheet(
            f"background-color: {project.color}; border-radius: 8px;")
      else:
        color_indicator.setStyleSheet(
            "background-color: #A0A0A0; border-radius: 8px;")
      project_row_layout.addWidget(color_indicator)

      # Project Name
      project_name_button = QPushButton(project.name)
      project_name_button.setObjectName("project_name_button")
      project_name_button.setFont(QFont("Arial", 12))
      project_name_button.setFlat(True)
      project_name_button.setCursor(Qt.CursorShape.PointingHandCursor)
      project_name_button.setStyleSheet(
        "background-color: transparent; border: none; text-align: left; padding: 0px;"
      )
      project_name_button.clicked.connect(
        lambda checked=False, p_id=project.id: self._open_project(p_id)
      )
      project_row_layout.addWidget(project_name_button, 2)

      # Description
      description_text = project.description or ""
      description_label = QLabel(description_text)
      description_label.setObjectName("description_label")
      description_label.setStyleSheet("color: #B0B0B0; font-size: 10px;")
      description_label.setWordWrap(False)
      description_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
      project_row_layout.addWidget(description_label, 4)

      # Total time (placeholder, will be computed from task logs later)
      total_time_label = QLabel("—")
      total_time_label.setObjectName("total_time_label")
      total_time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
      project_row_layout.addWidget(total_time_label, 1)

      # Actions
      button_edit = QPushButton("Edit")
      button_edit.setObjectName("button_edit")
      button_edit.setMaximumWidth(80)
      button_edit.clicked.connect(
          lambda checked, p_id=project.id: self._show_edit_project_dialog(p_id)
      )
      button_archive = QPushButton("Archive")
      button_archive.setObjectName("button_archive")
      button_archive.setMaximumWidth(80)
      button_archive.clicked.connect(
          lambda checked, p_id=project.id: self._archive_project(p_id)
      )

      actions_container = QWidget()
      actions_layout = QHBoxLayout(actions_container)
      actions_layout.setContentsMargins(0, 0, 0, 0)
      actions_layout.setSpacing(6)
      actions_layout.addWidget(button_edit)
      actions_layout.addWidget(button_archive)
      actions_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
      project_row_layout.addWidget(actions_container, 1)

      # Add the project row to the main layout
      self.projects_layout.addWidget(project_row_widget)

    # Add stretch to push content to the top
    self.projects_layout.addStretch()

  def _open_project(self, project_id: int):
    self.project_open_requested.emit(project_id)

  def _clear_layout(self, layout):
    """ Clear all widgets from a layout. """
    while layout.count():
      item = layout.takeAt(0)
      widget = item.widget()
      if widget is not None:
        widget.deleteLater()
      elif item.layout():
        self._clear_layout(item.layout())

  def _show_add_project_dialog(self):
    """ Show a dialog to add a new project. """
    dialog = QDialog(self)
    dialog.setWindowTitle("Add New Project")
    dialog.setModal(True)
    
    layout = QVBoxLayout(dialog)
    
    name_label = QLabel("Project Name:")
    name_input = QLineEdit()
    layout.addWidget(name_label)
    layout.addWidget(name_input)
    
    description_label = QLabel("Description (optional):")
    description_input = QLineEdit()
    layout.addWidget(description_label)
    layout.addWidget(description_input)

    # Color picker
    color_row = QWidget()
    color_row_layout = QHBoxLayout(color_row)
    color_row_layout.setContentsMargins(0, 0, 0, 0)

    color_label = QLabel("Color (optional):")
    color_preview = QLabel()
    color_preview.setFixedSize(18, 18)
    color_preview.setObjectName("color_preview")
    color_preview.setStyleSheet("background-color: #A0A0A0; border-radius: 9px;")

    selected_color: str = ""

    def set_preview(hex_color: str):
      nonlocal selected_color
      selected_color = hex_color
      if selected_color:
        color_preview.setStyleSheet(
          f"background-color: {selected_color}; border-radius: 9px;"
        )
      else:
        color_preview.setStyleSheet("background-color: #A0A0A0; border-radius: 9px;")

    button_pick = QPushButton("Pick")
    button_clear = QPushButton("Clear")
    button_pick.clicked.connect(
      lambda: (
        lambda c: set_preview(c.name())
        if c.isValid() else None
      )(QColorDialog.getColor(QColor(selected_color or "#A0A0A0"), self, "Pick a color"))
    )
    button_clear.clicked.connect(lambda: set_preview(""))

    color_row_layout.addWidget(color_label)
    color_row_layout.addSpacing(10)
    color_row_layout.addWidget(color_preview)
    color_row_layout.addSpacing(10)
    color_row_layout.addWidget(button_pick)
    color_row_layout.addWidget(button_clear)
    color_row_layout.addStretch()
    layout.addWidget(color_row)
    
    button_box = QDialogButtonBox(
        QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)
    
    if dialog.exec_() == QDialog.Accepted:
      project_name = name_input.text().strip()
      description = description_input.text().strip()
      
      if project_name:
        result = self._viewmodel.add_project(project_name, selected_color, description)
        if result is None:
          QMessageBox.warning(
              self,
              "Add Project Failed",
              "A project with this name already exists."
          )
      else:
        QMessageBox.warning(
            self,
            "Invalid Input",
            "Project name cannot be empty."
        )

  def _show_edit_project_dialog(self, project_id: int):
    """ Show a dialog to edit a project. """
    project = self._viewmodel._project_service.get_project_by_id(project_id)
    if not project:
      QMessageBox.warning(self, "Error", "Project not found.")
      return

    dialog = QDialog(self)
    dialog.setWindowTitle("Edit Project")
    dialog.setModal(True)
    
    layout = QVBoxLayout(dialog)
    
    name_label = QLabel("Project Name:")
    name_input = QLineEdit()
    name_input.setText(project.name)
    layout.addWidget(name_label)
    layout.addWidget(name_input)
    
    description_label = QLabel("Description (optional):")
    description_input = QLineEdit()
    description_input.setText(project.description or "")
    layout.addWidget(description_label)
    layout.addWidget(description_input)

    # Color picker
    color_row = QWidget()
    color_row_layout = QHBoxLayout(color_row)
    color_row_layout.setContentsMargins(0, 0, 0, 0)

    color_label = QLabel("Color (optional):")
    color_preview = QLabel()
    color_preview.setFixedSize(18, 18)
    color_preview.setObjectName("color_preview")

    selected_color: str = project.color or ""

    def set_preview(hex_color: str):
      nonlocal selected_color
      selected_color = hex_color
      if selected_color:
        color_preview.setStyleSheet(
          f"background-color: {selected_color}; border-radius: 9px;"
        )
      else:
        color_preview.setStyleSheet("background-color: #A0A0A0; border-radius: 9px;")

    set_preview(selected_color)

    button_pick = QPushButton("Pick")
    button_clear = QPushButton("Clear")
    button_pick.clicked.connect(
      lambda: (
        lambda c: set_preview(c.name())
        if c.isValid() else None
      )(QColorDialog.getColor(QColor(selected_color or "#A0A0A0"), self, "Pick a color"))
    )
    button_clear.clicked.connect(lambda: set_preview(""))

    color_row_layout.addWidget(color_label)
    color_row_layout.addSpacing(10)
    color_row_layout.addWidget(color_preview)
    color_row_layout.addSpacing(10)
    color_row_layout.addWidget(button_pick)
    color_row_layout.addWidget(button_clear)
    color_row_layout.addStretch()
    layout.addWidget(color_row)
    
    button_box = QDialogButtonBox(
        QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)
    
    if dialog.exec_() == QDialog.Accepted:
      new_name = name_input.text().strip()
      new_description = description_input.text().strip()
      
      if new_name:
        success = self._viewmodel.update_project(
          project_id,
          new_name,
          selected_color,
          new_description,
        )
        if not success:
          QMessageBox.warning(
            self,
            "Update Failed",
            "A project with this name already exists.",
          )
      else:
        QMessageBox.warning(
          self,
          "Invalid Input",
          "Project name cannot be empty.",
        )

  def _archive_project(self, project_id: int):
    """ Archive a project with confirmation. """
    dialog = QMessageBox(self)
    dialog.setWindowTitle("Archive Project")
    dialog.setText("Are you sure you want to archive this project?")
    dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    dialog.setDefaultButton(QMessageBox.No)
    
    if dialog.exec_() == QMessageBox.Yes:
      self._viewmodel.archive_project(project_id)

  def _activate_project(self, project_id: int):
    """ Activate a project. """
    self._viewmodel.activate_project(project_id)
