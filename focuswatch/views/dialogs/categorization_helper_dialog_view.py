import logging
from functools import partial
from typing import TYPE_CHECKING, List, Tuple

from PySide6.QtCore import QCoreApplication, Qt, Slot
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
                               QDialogButtonBox, QFrame, QGridLayout,
                               QGroupBox, QHBoxLayout, QLabel, QLayout,
                               QLineEdit, QMessageBox, QProgressDialog,
                               QPushButton, QScrollArea, QSizePolicy,
                               QSpacerItem, QTabWidget, QVBoxLayout, QWidget,
                               QWidgetItem)

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

  def __init__(
      self,
      parent: QWidget,
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

    self._category_combos = []

    self._setup_ui()
    self._connect_signals()
    self._viewmodel.load_categories()
    self._viewmodel.load_window_classes()
    self._viewmodel.load_window_names()

    apply_stylesheet(self, "dialogs/categorization_helper_dialog.qss")

  def _setup_ui(self):
    """ Set up the user interface. """
    self.resize(800, 600)
    self.setWindowTitle("Categorization Helper")
    self._main_layout = QVBoxLayout(self)
    self._main_layout.setContentsMargins(10, 10, 10, 10)
    self._main_layout.setSpacing(5)

    # Tabs for window classes and window names
    self._tab_widget = QTabWidget(self)
    self._main_layout.addWidget(self._tab_widget)

    # Window Classes Tab
    self._classes_tab = QWidget()
    self._classes_tab_layout = QVBoxLayout(self._classes_tab)
    self._classes_tab_layout.setContentsMargins(0, 0, 0, 0)
    self._classes_tab_layout.setSpacing(0)
    self._tab_widget.addTab(self._classes_tab, "Window Classes")

    # Add header to classes tab
    self._add_header(self._classes_tab_layout)

    self._classes_scroll_area = QScrollArea()
    self._classes_scroll_area.setWidgetResizable(True)
    self._classes_scroll_area.setObjectName("classesScrollArea")
    self._classes_scroll_area.setFrameShape(QFrame.NoFrame)  # Remove frame
    self._classes_tab_layout.addWidget(self._classes_scroll_area)

    self._classes_scroll_content = QWidget()
    self._classes_scroll_content.setObjectName("scrollContent")
    self._classes_scroll_layout = QVBoxLayout(self._classes_scroll_content)
    self._classes_scroll_layout.setContentsMargins(0, 0, 0, 0)
    self._classes_scroll_layout.setSpacing(0)
    self._classes_scroll_area.setWidget(self._classes_scroll_content)

    # Load More button for window classes
    self._load_more_classes_button = QPushButton(
      "Load More Window Classes", self)
    self._load_more_classes_button.clicked.connect(
      self._load_more_window_classes)
    self._classes_tab_layout.addWidget(self._load_more_classes_button)

    # Window Names Tab
    self._names_tab = QWidget()
    self._names_tab_layout = QVBoxLayout(self._names_tab)
    self._names_tab_layout.setContentsMargins(0, 0, 0, 0)
    self._names_tab_layout.setSpacing(0)
    self._tab_widget.addTab(self._names_tab, "Window Names")

    # Add header to names tab
    self._add_header(self._names_tab_layout)

    self._names_scroll_area = QScrollArea()
    self._names_scroll_area.setWidgetResizable(True)
    self._names_scroll_area.setObjectName("namesScrollArea")
    self._names_scroll_area.setFrameShape(QFrame.NoFrame)
    self._names_tab_layout.addWidget(self._names_scroll_area)

    self._names_scroll_content = QWidget()
    self._names_scroll_content.setObjectName("scrollContent")
    self._names_scroll_layout = QVBoxLayout(self._names_scroll_content)
    self._names_scroll_layout.setContentsMargins(0, 0, 0, 0)
    self._names_scroll_layout.setSpacing(0)
    self._names_scroll_area.setWidget(self._names_scroll_content)

    # Load More button for window names
    self._load_more_names_button = QPushButton(
      "Load More Window Names", self)
    self._load_more_names_button.clicked.connect(
      self._load_more_window_names)
    self._names_tab_layout.addWidget(self._load_more_names_button)

    # Button box
    self._button_box = QDialogButtonBox(
      QDialogButtonBox.Apply | QDialogButtonBox.Cancel)
    self._main_layout.addWidget(self._button_box)

    self.setLayout(self._main_layout)

  def _connect_signals(self):
    """ Connect signals from the ViewModel to the View's slots. """
    self._viewmodel.categories_changed.connect(self._on_categories_changed)
    self._viewmodel.uncategorized_window_classes_changed.connect(
      self._on_uncategorized_window_classes_changed)
    self._viewmodel.uncategorized_window_names_changed.connect(
      self._on_uncategorized_window_names_changed)
    self._viewmodel.has_more_classes_changed.connect(
      self._on_has_more_classes_changed)
    self._viewmodel.has_more_names_changed.connect(
      self._on_has_more_names_changed)
    self._viewmodel.retroactive_categorization_progress.connect(
      self._update_progress_dialog)
    apply_button = self._button_box.button(QDialogButtonBox.Apply)
    apply_button.clicked.connect(self._apply_changes)
    self._button_box.rejected.connect(self.reject)

  @Slot()
  def _on_categories_changed(self):
    """ Handle updates when categories change. """
    self._update_categories()

  @Slot()
  def _on_uncategorized_window_classes_changed(self):
    """ Handle updates when uncategorized window classes change. """
    self._clear_layout(self._classes_scroll_layout)
    self._populate_entries(
        self._classes_scroll_layout,
        self._viewmodel.uncategorized_window_classes,
        is_window_class=True
    )
    if not self._viewmodel.has_more_classes:
      self._load_more_classes_button.hide()
    else:
      self._load_more_classes_button.show()

  @Slot()
  def _on_uncategorized_window_names_changed(self):
    """ Handle updates when uncategorized window names change. """
    self._clear_layout(self._names_scroll_layout)
    self._populate_entries(
        self._names_scroll_layout,
        self._viewmodel.uncategorized_window_names,
        is_window_class=False
    )
    if not self._viewmodel.has_more_names:
      self._load_more_names_button.hide()
    else:
      self._load_more_names_button.show()

  @Slot()
  def _on_has_more_classes_changed(self):
    """ Handle updates when has_more_classes property changes. """
    if not self._viewmodel.has_more_classes:
      self._load_more_classes_button.hide()
    else:
      self._load_more_classes_button.show()

  @Slot()
  def _on_has_more_names_changed(self):
    """ Handle updates when has_more_names property changes. """
    if not self._viewmodel.has_more_names:
      self._load_more_names_button.hide()
    else:
      self._load_more_names_button.show()

  def _add_header(self, layout: QVBoxLayout):
    """ Add a header row to the provided layout. """
    header_widget = QWidget()
    header_layout = QHBoxLayout(header_widget)
    header_layout.setContentsMargins(5, 0, 5, 0)
    header_layout.setSpacing(10)

    # Name column
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

    # Empty space for "+" button
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

  def _clear_layout(self, layout: QVBoxLayout):
    """ Clear all widgets from a layout. """
    while layout.count():
      item = layout.takeAt(0)
      widget = item.widget()
      if widget is not None:
        widget.deleteLater()
      else:
        child_layout = item.layout()
        if child_layout is not None:
          self._clear_layout(child_layout)

  def _populate_entries(self, layout: QVBoxLayout, entries: List[Tuple[str, int]], is_window_class: bool):
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
      # Set a property for alternating row colors
      row_widget.setProperty("alt", index % 2 == 0)

      # Name input field
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
      self._populate_category_combo(category_combo)
      category_combo.setFixedWidth(150)
      category_combo.setFixedHeight(30)
      row_layout.addWidget(category_combo)
      self._category_combos.append(category_combo)  # Store reference

      # "+" button
      new_category_btn = QPushButton("+")
      new_category_btn.setToolTip("Create new category")
      new_category_btn.clicked.connect(
          partial(self._create_new_category, category_combo))
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

      # Add a separator between rows
      separator = QFrame()
      separator.setObjectName("separator")
      separator.setFrameShape(QFrame.HLine)
      separator.setFrameShadow(QFrame.Plain)
      separator.setFixedHeight(1)
      separator.setContentsMargins(0, 0, 0, 0)
      layout.addWidget(separator)

    # Add a spacer at the bottom to push entries to the top without stretching them
    spacer = QSpacerItem(20, 40, QSizePolicy.Minimum,
                         QSizePolicy.Expanding)
    layout.addItem(spacer)

  def _populate_category_combo(self, combo_box: QComboBox):
    """ Populate the category combo box with categories. """
    combo_box.clear()
    for category in self._viewmodel.categories:
      combo_box.addItem(category.name, category.id)
      if category.name == "Uncategorized":
        combo_box.setCurrentIndex(combo_box.count() - 1)

  def _update_categories(self):
    """ Update categories in all combo boxes. """
    for category_combo in self._category_combos:
      # Save the current selection
      current_category_id = category_combo.currentData()
      self._populate_category_combo(category_combo)
      # Restore the selection if it still exists
      index = category_combo.findData(current_category_id)
      if index != -1:
        category_combo.setCurrentIndex(index)
      else:
        # If the previously selected category was deleted, default to "Uncategorized"
        index = category_combo.findText("Uncategorized")
        if index != -1:
          category_combo.setCurrentIndex(index)

  @Slot()
  def _apply_changes(self):
    """ Apply the changes and save categorizations. """
    print("Applying changes")
    for layout in [self._classes_scroll_layout, self._names_scroll_layout]:
      for i in range(layout.count()):
        item = layout.itemAt(i)
        widget = item.widget()
        if widget and widget.objectName() == "rowWidget":
          self._save_categorization(widget)

    reply = QMessageBox.question(
        self, "Retroactive Categorization",
        "Do you want to retroactively categorize the activities with the new rules?",
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

    if reply == QMessageBox.Yes:
      self._progress_dialog = self._show_progress_dialog(
          "Progress", "Categorizing entries..."
      )

      # Start the categorization process
      self._viewmodel.perform_retroactive_categorization()

      self._progress_dialog.close()
      QMessageBox.information(
          self, "Retroactive Categorization", "Categorization completed successfully."
      )

    self.accept()

  def _save_categorization(self, row_widget: QWidget):
    """ Save categorization for an entry. """
    row_layout = row_widget.layout()

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
  def _load_more_window_classes(self):
    """ Load more window classes. """
    self._viewmodel.load_window_classes()

  @Slot()
  def _load_more_window_names(self):
    """ Load more window names. """
    self._viewmodel.load_window_names()

  def _create_new_category(self, category_combo: QComboBox):
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
      self._viewmodel.categories_changed.emit()

      # Update the UI
      self._update_categories()

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
    if hasattr(self, "_progress_dialog"):
      progress = int((current / total) * 100)
      self._progress_dialog.setValue(progress)
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
