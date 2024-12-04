import logging
import os
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QCoreApplication, QObject, QRect, QSize, Qt, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFileDialog, QFrame, QHBoxLayout, QLabel,
                               QLayout, QLineEdit, QMessageBox,
                               QProgressDialog, QPushButton, QScrollArea,
                               QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from focuswatch.utils.resource_utils import apply_stylesheet
from focuswatch.utils.ui_utils import get_category_color_or_parent
from focuswatch.views.dialogs.categorization_helper_dialog_view import \
    CategorizationHelperDialogView
from focuswatch.views.dialogs.category_dialog_view import CategoryDialogView

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
  from focuswatch.viewmodels.categories_viewmodel import CategoriesViewModel


class CategoriesView(QWidget):
  def __init__(self, viewmodel: "CategoriesViewModel",
               parent: Optional[QObject] = None):
    super().__init__(parent)
    self._viewmodel = viewmodel
    self._max_keywords_display = 10
    self._setup_ui()
    self._connect_signals()

    apply_stylesheet(self, "categories_view.qss")

  def _setup_ui(self):
    """ Set up the UI components. """
    self.setObjectName("categories_view")

    # Main vertical layout
    self.main_layout = QVBoxLayout(self)
    self.main_layout.setObjectName("main_layout")

    # Top bar with filter and buttons
    self._create_top_bar()

    # Divider line TODO is it worth to create a asepate class for this?
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
    """ Create the top bar with filter, import, export, and restore defaults buttons. """
    self.top_bar = QFrame(self)
    self.top_bar.setObjectName("top_bar")
    self.top_bar_layout = QHBoxLayout(self.top_bar)
    self.top_bar_layout.setContentsMargins(0, 0, 0, 0)
    self.top_bar_layout.setSpacing(10)

    # Filter input
    self.filter_input = QLineEdit(self.top_bar)
    self.filter_input.setObjectName("filter_input")
    self.filter_input.setPlaceholderText(
        "Filter categories and keywords...")
    self.filter_input.setClearButtonEnabled(True)
    self.top_bar_layout.addWidget(self.filter_input)

    # Spacer
    self.top_bar_spacer = QSpacerItem(
        40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.top_bar_layout.addItem(self.top_bar_spacer)

    # Import button
    self.button_import = QPushButton("Import", self.top_bar)
    self.button_import.setObjectName("button_import")
    self.button_import.setEnabled(False)
    self.top_bar_layout.addWidget(self.button_import)

    # Export button
    self.button_export = QPushButton("Export", self.top_bar)
    self.button_export.setObjectName("button_export")
    self.top_bar_layout.addWidget(self.button_export)

    # Restore defaults button
    self.button_restore_defaults = QPushButton(
        "Restore Defaults", self.top_bar)
    self.button_restore_defaults.setObjectName("button_restore_defaults")
    self.top_bar_layout.addWidget(self.button_restore_defaults)

    self.main_layout.addWidget(self.top_bar)

  def _create_main_content_area(self):
    """ Create the main content area similar to the original implementation. """
    # Scroll area
    self.scroll_area = QScrollArea(self)
    self.scroll_area.setObjectName("scroll_area")
    self.scroll_area.setWidgetResizable(True)
    self.scroll_area_widget = QWidget()
    self.scroll_area_widget.setObjectName("scroll_area_widget")
    self.scroll_area_layout = QVBoxLayout(self.scroll_area_widget)
    self.scroll_area_layout.setObjectName("scroll_area_layout")

    # Categories layout
    self.categories_layout = QVBoxLayout()
    self.categories_layout.setObjectName("categories_layout")
    self.scroll_area_layout.addLayout(self.categories_layout)

    self.scroll_area.setWidget(self.scroll_area_widget)
    self.main_layout.addWidget(self.scroll_area)

    # Populate categories
    self._populate_categories()

  def _create_bottom_bar(self):
    """ Create the bottom bar with add category, helper, and retroactive categorization buttons. """
    self.bottom_bar = QFrame(self)
    self.bottom_bar.setObjectName("bottom_bar")
    self.bottom_bar_layout = QHBoxLayout(self.bottom_bar)
    self.bottom_bar_layout.setContentsMargins(0, 0, 0, 0)
    self.bottom_bar_layout.setSpacing(10)

    # Add category button
    self.button_add_category = QPushButton("Add Category", self.bottom_bar)
    self.button_add_category.setObjectName("button_add_category")
    self.bottom_bar_layout.addWidget(self.button_add_category)

    # Spacer
    self.bottom_bar_spacer = QSpacerItem(
        40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.bottom_bar_layout.addItem(self.bottom_bar_spacer)

    # Categorization helper button
    self.button_helper = QPushButton(
        "Categorization Helper", self.bottom_bar)
    self.button_helper.setObjectName("button_helper")
    self.bottom_bar_layout.addWidget(self.button_helper)

    # Retroactive categorization button
    self.button_retroactive = QPushButton(
        "Retroactive Categorization", self.bottom_bar)
    self.button_retroactive.setObjectName("button_retroactive")
    self.bottom_bar_layout.addWidget(self.button_retroactive)

    self.main_layout.addWidget(self.bottom_bar)

  def _connect_signals(self):
    """Connect signals and slots."""
    # Connect ViewModel signals
    self._viewmodel.categories_changed.connect(self._on_categories_changed)
    self._viewmodel.filter_text_changed.connect(self._on_filter_text_changed)
    self._viewmodel.organized_categories_changed.connect(
      self._on_organized_categories_changed)

    # Connect UI signals
    self.filter_input.textChanged.connect(self._on_filter_changed)
    self.button_add_category.clicked.connect(self._show_category_dialog)
    self.button_helper.clicked.connect(self._show_categorization_helper)
    self.button_retroactive.clicked.connect(self._retroactive_categorization)
    self.button_restore_defaults.clicked.connect(self._restore_defaults)
    self.button_export.clicked.connect(self._export_categories)

  @Slot()
  def _on_categories_changed(self):
    """ Handle categories_changed signal from the ViewModel. """
    self._populate_categories()

  @Slot()
  def _on_filter_text_changed(self):
    """ Handle filter_text_changed signal from the ViewModel. """
    self._populate_categories()

  @Slot()
  def _on_organized_categories_changed(self):
    """ Handle organized_categories_changed signal from the ViewModel. """
    self._populate_categories()

  @Slot(str)
  def _on_filter_changed(self, text):
    """ Handle filter text changes. """
    self._viewmodel.filter_text = text

  def _populate_categories(self):
    """ Populate the categories in the main content area. """
    # Clear existing content
    self._clear_layout(self.categories_layout)

    def add_categories(categories, depth=0):
      for category_id, category_data in categories.items():
        category = category_data['category']
        keywords = category_data['keywords']
        children_ids = category_data.get('children', [])

        # Check if category or its descendants match the filter
        matches_filter = self._category_matches_filter(category_data)

        if not matches_filter:
          continue  # Skip this category and its children

        # Skip Uncategorized
        if category.name == 'Uncategorized':
          continue

        # Create category row widget
        category_row_widget = QWidget()
        category_row_widget.setObjectName("category_row_widget")
        category_row_widget.setAutoFillBackground(True)
        category_row_layout = QHBoxLayout(category_row_widget)
        category_row_layout.setContentsMargins(0, 0, 0, 0)
        category_row_layout.setSpacing(10)

        # Indentation based on depth
        indent = 20 * depth
        category_row_layout.addSpacing(indent)

        # Toggle Button for Categories with Children
        if children_ids:
          toggle_button = QPushButton()
          toggle_button.setCheckable(True)
          toggle_button.setChecked(category_data.get('expanded', True))
          toggle_button.setFixedSize(16, 16)
          toggle_button.setObjectName('toggle_button')
          # Set icon based on expanded state
          self._update_toggle_button_icon(
            toggle_button, category_data['expanded'])
          toggle_button.clicked.connect(
              lambda checked, cid=category_id: self._toggle_category(cid)
          )
          category_row_layout.addWidget(toggle_button)
        else:
          # Align with toggle button space
          category_row_layout.addSpacing(16)

        # Color Indicator
        color_indicator = QLabel()
        color_indicator.setFixedSize(16, 16)
        category_color = get_category_color_or_parent(category_id)
        if category_color:
          color_indicator.setStyleSheet(
            f"background-color: {category_color}; border-radius: 8px;")
        else:
          color_indicator.setStyleSheet(
            "background-color: #A0A0A0; border-radius: 8px;")
        category_row_layout.addWidget(color_indicator)

        # Category Button
        category_button = QPushButton(category.name)
        category_button.setObjectName(f"category_button_{category_id}")
        category_button.clicked.connect(
            lambda checked, c_id=category_id: self._show_category_dialog(
              c_id)
        )
        category_button.setFont(QFont('Arial', 12))
        category_button.setStyleSheet(
            "background-color: transparent; color: #F9F9F9; border: none; padding: 5px 0; text-align: left;"
        )
        category_row_layout.addWidget(category_button)

        # Keywords as Chips
        keywords_layout = QHBoxLayout()
        keywords_layout.setSpacing(5)
        displayed_keywords = keywords[:self._max_keywords_display]
        if len(keywords) > self._max_keywords_display:
          displayed_keywords.append('...')
        for keyword in displayed_keywords:
          keyword_label = QLabel(keyword)
          keyword_label.setObjectName("keyword_chip")
          keywords_layout.addWidget(keyword_label)
        category_row_layout.addLayout(keywords_layout)

        # Add the category row to the main layout
        self.categories_layout.addWidget(category_row_widget)

        # If the category is expanded, add its children
        if category_data.get('expanded', True) and children_ids:
          child_categories = {
              child_id: self._viewmodel.organized_categories[child_id]
              for child_id in children_ids
          }
          add_categories(child_categories, depth + 1)

    # Start with root categories
    root_categories = {
        cid: cdata
        for cid, cdata in self._viewmodel.organized_categories.items()
        if cdata['category'].parent_category_id is None
    }
    add_categories(root_categories)

    # Add stretch to push content to the top
    self.categories_layout.addStretch()

  def _category_matches_filter(self, category_data):
    """ Check if a category or any of its descendants match the filter. """
    category = category_data['category']
    keywords = category_data['keywords']
    children_ids = category_data.get('children', [])
    filter_text = self._viewmodel.filter_text.lower()

    # Check if the category itself matches the filter
    if filter_text in category.name.lower() or any(filter_text in kw.lower() for kw in keywords):
      return True

    # Recursively check if any child categories match the filter
    for child_id in children_ids:
      child_data = self._viewmodel.organized_categories[child_id]
      if self._category_matches_filter(child_data):
        return True

    # No match found
    return False

  def _toggle_category(self, category_id):
    # Toggle the expanded state
    category_data = self._viewmodel.organized_categories[category_id]
    category_data['expanded'] = not category_data.get('expanded', True)
    # Refresh the category display
    self._populate_categories()

  def _update_toggle_button_icon(self, button, expanded):
    if expanded:
      # button.setIcon(QIcon(':/icons/arrow_down.png'))
      button.setText('▼')
    else:
      # button.setIcon(QIcon(':/icons/arrow_right.png'))
      button.setText('►')
    button.setStyleSheet("background-color: transparent; border: none;")

  def _clear_layout(self, layout):
    """ Clear all widgets from a layout. """
    while layout.count():
      item = layout.takeAt(0)
      widget = item.widget()
      if widget is not None:
        widget.deleteLater()
      elif item.layout():
        self._clear_layout(item.layout())

  def _show_category_dialog(self, category_id=None):
    """ Show the category dialog to add or edit a category. """
    dialog = CategoryDialogView(
        self, self._viewmodel._category_service, self._viewmodel._keyword_service, category_id)
    if dialog.exec_():
      self._viewmodel._load_categories()

  def _show_categorization_helper(self):
    """ Show the categorization helper dialog. """
    dialog = CategorizationHelperDialogView(self, self._viewmodel._activity_service,
                                            self._viewmodel._category_service, self._viewmodel._keyword_service, self._viewmodel._classifier)
    dialog.exec_()
    self._viewmodel._load_categories()

  def _retroactive_categorization(self):
    """ Perform retroactive categorization with confirmation and progress dialog. """
    dialog = QMessageBox()
    dialog.setWindowTitle("Retroactive Categorization")
    dialog.setText(
        "Are you sure you want to retroactively categorize all entries based on the current ruleset?\n"
        "This action cannot be undone and might take a while."
    )
    dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    dialog.setDefaultButton(QMessageBox.No)
    result = dialog.exec_()

    if result == QMessageBox.No:
      return

    self.progress_dialog = self._show_progress_dialog(
        "Progress", "Categorizing entries..."
    )

    # Connect the progress signal before starting the categorization
    self._viewmodel.retroactive_categorization_progress.connect(
        self._update_progress_dialog
    )

    # Start the categorization process
    success = self._viewmodel.retroactive_categorization()

    # Disconnect the signal after the process is complete
    self._viewmodel.retroactive_categorization_progress.disconnect(
        self._update_progress_dialog
    )

    self.progress_dialog.close()

    if success:
      QMessageBox.information(
          self, "Retroactive Categorization", "Categorization completed successfully."
      )
    else:
      QMessageBox.critical(
          self, "Retroactive Categorization", "An error occurred during categorization."
      )

  def _update_progress_dialog(self, current: int, total: int):
    """ Update the progress dialog during retroactive categorization. """
    if hasattr(self, 'progress_dialog'):
      progress = int((current / total) * 100)
      self.progress_dialog.setValue(progress)
      QCoreApplication.processEvents()

  def _show_progress_dialog(self, title: str, message: str) -> QProgressDialog:
    """ Show a progress dialog. """
    progress_dialog = QProgressDialog(message, None, 0, 100, self)
    progress_dialog.setWindowTitle(title)
    progress_dialog.setWindowModality(Qt.WindowModal)
    progress_dialog.setMinimumDuration(0)
    progress_dialog.setValue(0)
    progress_dialog.setCancelButton(None)
    progress_dialog.show()
    QCoreApplication.processEvents()
    return progress_dialog

  def _restore_defaults(self):
    """ Restore default categories with confirmation. """
    dialog = QMessageBox(self)
    dialog.setWindowTitle("Restore Defaults")
    dialog.setText(
      "Are you sure you want to restore default categories?\n"
      "This action cannot be undone and might take a while."
    )
    dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    dialog.setDefaultButton(QMessageBox.No)
    result = dialog.exec_()

    if result == QMessageBox.Yes:
      self.progress_dialog = self._show_progress_dialog(
        "Progress", "Restoring defaults and categorizing entries..."
      )

      # Connect the progress signal
      self._viewmodel.retroactive_categorization_progress.connect(
        self._update_progress_dialog
      )

      # Perform restore defaults and retroactive categorization
      self._viewmodel.restore_defaults()

      # Disconnect the signal
      self._viewmodel.retroactive_categorization_progress.disconnect(
        self._update_progress_dialog
      )

      self.progress_dialog.close()
      QMessageBox.information(
        self, "Restore Defaults", "Default categories restored successfully."
      )

  def closeEvent(self, event):
    """ Handle the close event. """
    self._viewmodel.property_changed.disconnect(self.on_property_changed)
    super().closeEvent(event)

  def _export_categories(self):
    """ Export categories to a file. """
    file_dialog = QFileDialog(self,
                              "Export Categories", "", "YAML Files (*.yml *.yaml);;All Files (*)")

    if file_dialog.exec_() == QFileDialog.Accepted:
      file_path = file_dialog.selectedFiles()[0]
      if os.path.exists(file_path):
        reply = QMessageBox.question(
            self,
            "Overwrite Confirmation",
            f"The file '{
              file_path}' already exists.\nDo you want to overwrite it?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
          return

      try:
        self._viewmodel.export_categories(file_path)
      except Exception as e:
        QMessageBox.critical(
            self,
            "Export Failed",
            f"An error occurred while exporting categories:\n{str(e)}"
        )
