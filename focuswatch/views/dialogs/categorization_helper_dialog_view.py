import logging
from functools import partial
from typing import TYPE_CHECKING, List, Tuple

from PySide6.QtCore import Qt, Slot, QCoreApplication
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
                               QDialogButtonBox, QFrame, QGroupBox,
                               QHBoxLayout, QLabel, QLayout, QLineEdit,
                               QMessageBox, QPushButton, QScrollArea,
                               QSizePolicy, QSpacerItem, QTabWidget,
                               QVBoxLayout, QWidget, QWidgetItem, QGridLayout, QProgressDialog)

from focuswatch.utils.resource_utils import apply_stylesheet
from focuswatch.viewmodels.dialogs.categorization_helper_dialog_viewmodel import \
    CategorizationHelperDialogViewModel
from focuswatch.views.dialogs.category_dialog_view import CategoryDialogView

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.classifier_service import ClassifierService
  from focuswatch.services.keyword_service import KeywordService

logger = logging.getLogger(__name__)


class CategorizationHelperDialogView(QDialog):
  """ Dialog for helping with categorization of uncategorized entries. """

  def __init__(self,
               parent,
               activity_service: "ActivityService",
               category_service: "CategoryService",
               keyword_service: "KeywordService",
               classifier: "ClassifierService"
               ):
    super().__init__(parent)
    self._activity_service = activity_service
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._classifier = classifier

    self._viewmodel = CategorizationHelperDialogViewModel(
        self._activity_service, self._category_service, self._keyword_service, self._classifier)

    self.category_combos = []

    self.setup_ui()
    self.connect_signals()
    self._viewmodel.load_categories()
    self._viewmodel.load_window_classes()
    self._viewmodel.load_window_names()

    apply_stylesheet(self, "dialogs/categorization_helper_dialog.qss")

  def setup_ui(self):
    self.resize(800, 600)
    self.setWindowTitle("Categorization Helper")
    self.main_layout = QVBoxLayout(self)
    self.main_layout.setContentsMargins(10, 10, 10, 10)
    self.main_layout.setSpacing(5)

    # Note to user #TODO this looks bad
    # note_label = QLabel(
    #     "Categorize entries or save them as keywords.")
    # note_label.setWordWrap(True)
    # self.main_layout.addWidget(note_label)

    # Tabs for window classes and window names
    self.tab_widget = QTabWidget(self)
    self.main_layout.addWidget(self.tab_widget)

    # Window Classes Tab
    self.classes_tab = QWidget()
    self.classes_tab_layout = QVBoxLayout(self.classes_tab)
    self.classes_tab_layout.setContentsMargins(0, 0, 0, 0)
    self.classes_tab_layout.setSpacing(0)
    self.tab_widget.addTab(self.classes_tab, "Window Classes")

    # Add header to classes tab
    self.add_header(self.classes_tab_layout)

    self.classes_scroll_area = QScrollArea()
    self.classes_scroll_area.setWidgetResizable(True)
    self.classes_scroll_area.setObjectName("classesScrollArea")
    self.classes_scroll_area.setFrameShape(QFrame.NoFrame)  # Remove frame
    self.classes_tab_layout.addWidget(self.classes_scroll_area)

    self.classes_scroll_content = QWidget()
    self.classes_scroll_content.setObjectName("scrollContent")
    self.classes_scroll_layout = QVBoxLayout(self.classes_scroll_content)
    self.classes_scroll_layout.setContentsMargins(0, 0, 0, 0)
    self.classes_scroll_layout.setSpacing(0)
    self.classes_scroll_area.setWidget(self.classes_scroll_content)

    # Load More button for window classes
    if self._viewmodel.has_more_classes:
      self.load_more_classes_button = QPushButton(
        "Load More Window Classes", self)
      self.load_more_classes_button.clicked.connect(
        self.load_more_window_classes)
      self.classes_tab_layout.addWidget(self.load_more_classes_button)

    # Window Names Tab
    self.names_tab = QWidget()
    self.names_tab_layout = QVBoxLayout(self.names_tab)
    self.names_tab_layout.setContentsMargins(0, 0, 0, 0)
    self.names_tab_layout.setSpacing(0)
    self.tab_widget.addTab(self.names_tab, "Window Names")

    # Add header to names tab
    self.add_header(self.names_tab_layout)

    self.names_scroll_area = QScrollArea()
    self.names_scroll_area.setWidgetResizable(True)
    self.names_scroll_area.setObjectName("namesScrollArea")
    self.names_scroll_area.setFrameShape(QFrame.NoFrame)
    self.names_tab_layout.addWidget(self.names_scroll_area)

    self.names_scroll_content = QWidget()
    self.names_scroll_content.setObjectName("scrollContent")
    self.names_scroll_layout = QVBoxLayout(self.names_scroll_content)
    self.names_scroll_layout.setContentsMargins(0, 0, 0, 0)
    self.names_scroll_layout.setSpacing(0)
    self.names_scroll_area.setWidget(self.names_scroll_content)

    # Load More button for window names
    if self._viewmodel.has_more_names:
      self.load_more_names_button = QPushButton(
        "Load More Window Names", self)
      self.load_more_names_button.clicked.connect(
        self.load_more_window_names)
    self.names_tab_layout.addWidget(self.load_more_names_button)

    # Button box
    self.button_box = QDialogButtonBox(
        QDialogButtonBox.Apply | QDialogButtonBox.Cancel)
    self.main_layout.addWidget(self.button_box)

    self.setLayout(self.main_layout)

  def connect_signals(self):
    self._viewmodel.property_changed.connect(
      self.on_viewmodel_property_changed)
    self._viewmodel.retroactive_categorization_progress.connect(
      self._update_progress_dialog)
    self.button_box.clicked.connect(self.apply_changes)
    self.button_box.rejected.connect(self.reject)

  @Slot(str)
  def on_viewmodel_property_changed(self, property_name: str):
    if property_name == "uncategorized_window_classes":
      # Clear existing items before adding new ones
      self.clear_layout(self.classes_scroll_layout)
      self.populate_entries(self.classes_scroll_layout,
                            self._viewmodel.uncategorized_window_classes, is_window_class=True)
      # If no entries are loaded, hide the 'Load More' button
      if not self._viewmodel.has_more_classes or not self._viewmodel.uncategorized_window_classes:
        self.load_more_classes_button.hide()
      else:
        self.load_more_classes_button.show()
    elif property_name == "uncategorized_window_names":  # TODO method?
      # Clear existing items before adding new ones
      self.clear_layout(self.names_scroll_layout)
      self.populate_entries(self.names_scroll_layout,
                            self._viewmodel.uncategorized_window_names, is_window_class=False)
      # If no entries are loaded, hide the 'Load More' button
      if not self._viewmodel.has_more_names or not self._viewmodel.uncategorized_window_names:
        self.load_more_names_button.hide()
      else:
        self.load_more_names_button.show()
    elif property_name == "categories":
      self.update_categories()
    elif property_name == "no_more_window_classes":
      self.load_more_classes_button.hide()
    elif property_name == "no_more_window_names":
      self.load_more_names_button.hide()

  def add_header(self, layout: QVBoxLayout):
    """ Add a header row to the provided layout. """
    header_widget = QWidget()
    header_layout = QHBoxLayout(header_widget)
    header_layout.setContentsMargins(5, 0, 5, 0)
    header_layout.setSpacing(10)

    # Keyword column
    name_label = QLabel("Name")
    name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    name_label.setObjectName("headerLabel")
    header_layout.addWidget(name_label, stretch=3)

    # Match Case column
    match_case_label = QLabel("Match Case")
    match_case_label.setAlignment(Qt.AlignCenter)
    match_case_label.setFixedWidth(100)
    match_case_label.setFixedHeight(30)
    match_case_label.setObjectName("headerLabel")
    header_layout.addWidget(match_case_label)

    # Time Spent column
    time_label = QLabel("Time Spent")
    time_label.setAlignment(Qt.AlignCenter)
    time_label.setFixedWidth(100)
    time_label.setObjectName("headerLabel")
    header_layout.addWidget(time_label)

    # Category column
    category_label = QLabel("Category")
    category_label.setAlignment(Qt.AlignCenter)
    category_label.setFixedWidth(150)
    category_label.setObjectName("headerLabel")
    header_layout.addWidget(category_label)

    # Empty space for '+' button
    plus_label = QLabel("")
    plus_label.setFixedWidth(30)
    header_layout.addWidget(plus_label)

    # Save as keyword checkbox
    save_as_keyword_label = QLabel("Save keyword")
    save_as_keyword_label.setAlignment(Qt.AlignCenter)
    save_as_keyword_label.setFixedWidth(120)
    save_as_keyword_label.setObjectName("headerLabel")
    header_layout.addWidget(save_as_keyword_label)

    layout.addWidget(header_widget)

    # Add a separator below the header
    separator = QFrame()
    separator.setObjectName("headerSeparator")
    separator.setFrameShape(QFrame.HLine)
    separator.setFrameShadow(QFrame.Plain)
    separator.setFixedHeight(1)
    separator.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(separator)

  def clear_layout(self, layout):
    """ Clear all widgets from a layout. """
    if layout is not None:
      while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
          widget.deleteLater()
        else:
          child_layout = item.layout()
          if child_layout is not None:
            self.clear_layout(child_layout)
          else:
            pass

  def populate_entries(self, layout: QVBoxLayout, entries: List[Tuple[str, int]], is_window_class: bool):
    """ Populate the entries into the provided layout. """
    for index, (keyword, total_time_seconds) in enumerate(entries):
      if keyword == "None":
        continue

      row_widget = QWidget()
      row_layout = QHBoxLayout(row_widget)
      row_layout.setContentsMargins(5, 0, 5, 0)
      row_layout.setSpacing(10)

      # Assign an object name to the row_widget for styling
      row_widget.setObjectName("rowWidget")
      # Set a property for alternating row colors # TODO
      row_widget.setProperty("alt", index % 2 == 0)

      # Keyword input field
      name_edit = QLineEdit(keyword)
      name_edit.setAlignment(Qt.AlignLeft)
      name_edit.setCursorPosition(0)  # Move cursor to the start
      row_layout.addWidget(name_edit, stretch=3)

      # Match Case checkbox
      match_case_checkbox = QCheckBox()
      match_case_checkbox.setChecked(False)
      match_case_checkbox.setFixedWidth(100)
      match_case_checkbox.setFixedHeight(30)
      # Center align the checkbox
      match_case_checkbox.setStyleSheet(
        "QCheckBox { margin-left:auto; margin-right:auto; }")
      row_layout.addWidget(match_case_checkbox)

      # Time Spent label
      time_label = QLabel(
        f"{total_time_seconds // 3600}h {(total_time_seconds % 3600) // 60}m")
      time_label.setFixedWidth(100)
      time_label.setAlignment(Qt.AlignCenter)
      row_layout.addWidget(time_label)

      # Category combo box
      category_combo = QComboBox()
      self.populate_category_combo(category_combo)
      category_combo.setFixedWidth(150)
      category_combo.setFixedHeight(30)
      row_layout.addWidget(category_combo)
      self.category_combos.append(category_combo)  # Store reference

      # '+' button
      new_category_btn = QPushButton("+")
      new_category_btn.setToolTip("Create new category")
      new_category_btn.clicked.connect(
          partial(self.create_new_category, category_combo))
      new_category_btn.setFixedSize(30, 30)
      row_layout.addWidget(new_category_btn)

      # Save as keyword checkbox
      save_as_keyword_checkbox = QCheckBox()
      save_as_keyword_checkbox.setChecked(False)
      save_as_keyword_checkbox.setFixedWidth(120)
      save_as_keyword_checkbox.setStyleSheet(
        "QCheckBox { margin-left:auto; margin-right:auto;}")
      row_layout.addWidget(save_as_keyword_checkbox)

      # Store is_window_class flag
      row_widget.setProperty("is_window_class", is_window_class)

      # Add the row widget to the main layout
      layout.addWidget(row_widget)

      # add a separator between rows
      separator = QFrame()
      separator.setObjectName("separator")
      separator.setFrameShape(QFrame.HLine)
      separator.setFrameShadow(QFrame.Plain)
      separator.setFixedHeight(1)
      separator.setContentsMargins(0, 0, 0, 0)
      layout.addWidget(separator)

    # Add a spacer at the bottom to push entries to the top without stretching them
    spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
    layout.addItem(spacer)

  def populate_category_combo(self, combo_box: QComboBox):
    """ Populate the category combo box with categories. """
    combo_box.clear()
    for category in self._viewmodel.categories:
      combo_box.addItem(category.name, category.id)
      if category.name == "Uncategorized":
        combo_box.setCurrentIndex(combo_box.count() - 1)

  def update_categories(self):
    """ Update categories in all combo boxes. """
    for category_combo in self.category_combos:
      # Save the current selection
      current_category_id = category_combo.currentData()
      self.populate_category_combo(category_combo)
      # Restore the selection if it still exists
      index = category_combo.findData(current_category_id)
      if index != -1:
        category_combo.setCurrentIndex(index)
      else:
        # If the previously selected category was deleted, default to 'Uncategorized'
        index = category_combo.findText("Uncategorized")
        if index != -1:
          category_combo.setCurrentIndex(index)

  @Slot()
  def apply_changes(self):
    print("Applying changes")
    """ Apply the changes and save categorizations. """
    for layout in [self.classes_scroll_layout, self.names_scroll_layout]:
      for i in range(layout.count()):
        item = layout.itemAt(i)
        if isinstance(item, QWidgetItem) and item.widget().objectName() == "rowWidget":
          row_widget = item.widget()
          if row_widget and isinstance(row_widget, QWidget):
            self.save_categorization(row_widget)
        elif isinstance(item.widget(), QFrame):
          # It's a separator, skip
          continue

    reply = QMessageBox.question(self, "Retroactive Categorization",
                                 "Do you want to retroactively categorize the activities with the new rules?",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if reply == QMessageBox.Yes:  # TODO this is repeated with categories view
      self.progress_dialog = self._show_progress_dialog(
          "Progress", "Categorizing entries..."
      )

      # Connect the progress signal before starting the categorization
      self._viewmodel.retroactive_categorization_progress.connect(
          self._update_progress_dialog
      )

      # Start the categorization process
      success = self._viewmodel.perform_retroactive_categorization()

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

    self.accept()

  def save_categorization(self, row_widget: QWidget):
    """ Save categorization for an entry. """
    row_layout = row_widget.layout()

    # TODO better way of getting widgets
    name_edit = row_layout.itemAt(0).widget()
    match_case_checkbox = row_layout.itemAt(1).widget()
    category_combo = row_layout.itemAt(3).widget()
    save_keyword_checkbox = row_layout.itemAt(5).widget()

    if isinstance(category_combo, QComboBox) and category_combo.currentText() != "Uncategorized":
      keyword = name_edit.text()
      category_id = category_combo.currentData()
      match_case = match_case_checkbox.isChecked()
      save_keyword = save_keyword_checkbox.isChecked()
      self._viewmodel.save_categorization(
        keyword, category_id, match_case, save_keyword)

  @Slot()
  def load_more_window_classes(self):
    """ Load more window classes. """
    self._viewmodel.load_window_classes()

  @Slot()
  def load_more_window_names(self):
    """ Load more window names. """
    self._viewmodel.load_window_names()

  def create_new_category(self, category_combo: QComboBox):
    """ Create a new category and set it in the provided combo box. """
    dialog = CategoryDialogView(
      self, self._category_service, self._keyword_service)
    if dialog.exec_():
      category_name = dialog._viewmodel.name
      category_id = self._category_service.get_category_id_from_name(
        category_name)
      category = self._category_service.get_category_by_id(category_id)
      logger.info(f"Created new category: {category.name}")

      # Add the new category to the categories list and emit the signal
      self._viewmodel.categories.append(category)
      self._viewmodel.property_changed.emit('categories')

      # Update the UI
      self.update_categories()

      # Set the newly created category in the combo box
      index = category_combo.findData(category.id)
      if index != -1:
        category_combo.setCurrentIndex(index)
      else:
        # If the category is not found, add it to the combo box
        category_combo.addItem(category.name, category.id)
        category_combo.setCurrentIndex(category_combo.count() - 1)

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
