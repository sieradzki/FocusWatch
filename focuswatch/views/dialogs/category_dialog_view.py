import logging
from functools import partial
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QColor, QFontMetrics
from PySide6.QtWidgets import (QCheckBox, QColorDialog, QComboBox, QDialog,
                               QDialogButtonBox, QFormLayout, QFrame,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QMenu, QMessageBox, QPushButton, QScrollArea,
                               QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from focuswatch.utils.resource_utils import apply_stylesheet
from focuswatch.viewmodels.dialogs.category_dialog_viewmodel import \
    CategoryDialogViewModel
from focuswatch.views.dialogs.keyword_dialog_view import KeywordDialogView

if TYPE_CHECKING:
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.keyword_service import KeywordService

logger = logging.getLogger(__name__)


class CategoryDialogView(QDialog):
  """ Dialog for adding or editing a category. """

  def __init__(
      self,
      parent: QWidget,
      category_service: "CategoryService",
      keyword_service: "KeywordService",
      category_id: Optional[int] = None
  ):
    super().__init__(parent)
    self._viewmodel = CategoryDialogViewModel(
        category_service, keyword_service, category_id)
    self._setup_ui()
    self._connect_signals()

    apply_stylesheet(self, "dialogs/category_dialog.qss")

  def _setup_ui(self) -> None:
    """ Set up the user interface. """
    is_editing = self._viewmodel.category_id is not None
    self.setWindowTitle("Edit Category" if is_editing else "Add Category")
    self.setMinimumSize(500, 500)

    # Main layout
    main_layout = QVBoxLayout(self)
    main_layout.setSpacing(10)
    main_layout.setContentsMargins(20, 20, 20, 20)

    # Title label
    self._title_label = QLabel(self)
    self._title_label.setObjectName("titleLabel")
    self._title_label.setText(
      "Edit Category" if is_editing else "Add Category")
    main_layout.addWidget(self._title_label)

    # Form layout for inputs
    form_layout = QFormLayout()
    form_layout.setLabelAlignment(Qt.AlignRight)
    form_layout.setSpacing(10)

    # Name input
    self._name_line_edit = QLineEdit(self)
    self._name_line_edit.setObjectName("nameLineEdit")
    self._name_line_edit.setText(self._viewmodel.name)
    form_layout.addRow("Name:", self._name_line_edit)

    # Parent Category combo box
    self._parent_combo_box = QComboBox(self)
    self._parent_combo_box.setObjectName("parentComboBox")
    self._populate_parent_combo()
    form_layout.addRow("Parent Category:", self._parent_combo_box)

    # Color selection
    color_layout = QHBoxLayout()
    self._select_color_button = QPushButton(self)
    self._select_color_button.setObjectName("selectColorButton")
    self._select_color_button.setFixedSize(40, 20)
    self._update_color_button()
    color_layout.addWidget(self._select_color_button)
    color_layout.addStretch()
    form_layout.addRow("Color:", color_layout)

    # Focused checkbox
    self._focused_check_box = QCheckBox("", self)
    self._focused_check_box.setObjectName("focusedCheckBox")
    self._focused_check_box.setChecked(self._viewmodel.focused)
    form_layout.addRow("Focused:", self._focused_check_box)

    main_layout.addLayout(form_layout)

    # Keywords Section
    keywords_label = QLabel("Keywords:", self)
    keywords_label.setObjectName("keywordsLabel")
    main_layout.addWidget(keywords_label)

    # Keywords Frame
    keywords_frame = QFrame(self)
    keywords_frame.setObjectName("keywordFrame")
    keywords_frame_layout = QVBoxLayout(keywords_frame)
    keywords_frame_layout.setContentsMargins(5, 5, 5, 5)

    # Scroll area for keywords
    scroll_area = QScrollArea(self)
    scroll_area.setWidgetResizable(True)
    scroll_area.setFixedHeight(150)

    scroll_content = QWidget()
    scroll_content.setObjectName("scrollContent")
    self._keywords_grid_layout = QGridLayout(scroll_content)
    self._keywords_grid_layout.setSpacing(5)
    self._setup_keyword_grid()

    scroll_area.setWidget(scroll_content)
    keywords_frame_layout.addWidget(scroll_area)

    main_layout.addWidget(keywords_frame)

    # Note label
    note_label = QLabel(
        "Note: Click on a keyword to edit, right-click to remove.", self)
    note_label.setObjectName("noteLabel")
    main_layout.addWidget(note_label)

    # Spacer
    main_layout.addStretch()

    # Delete button (if applicable)
    if self._viewmodel.can_delete_category():
      self._delete_button = QPushButton("Delete Category", self)
      self._delete_button.setObjectName("deleteButton")
      main_layout.addWidget(self._delete_button)

    # Dialog buttons
    self._button_box = QDialogButtonBox(
        QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
    main_layout.addWidget(self._button_box)

    # Set main layout
    self.setLayout(main_layout)

  def _connect_signals(self) -> None:
    """ Connect signals and slots. """
    # Connect ViewModel property changes to UI updates
    self._viewmodel.name_changed.connect(self._on_name_changed)
    self._viewmodel.parent_category_id_changed.connect(
      self._on_parent_category_id_changed)
    self._viewmodel.color_changed.connect(self._on_color_changed)
    self._viewmodel.focused_changed.connect(self._on_focused_changed)
    self._viewmodel.keywords_changed.connect(self._on_keywords_changed)

    # Connect UI elements to ViewModel properties and methods
    self._name_line_edit.textChanged.connect(self._on_name_edit)
    self._parent_combo_box.currentIndexChanged.connect(
      self._on_parent_combo_changed)
    self._select_color_button.clicked.connect(self._show_color_dialog)
    self._focused_check_box.stateChanged.connect(
      self._on_focused_checkbox_changed)

    self._button_box.accepted.connect(self.accept)
    self._button_box.rejected.connect(self.reject)

    if hasattr(self, "_delete_button"):
      self._delete_button.clicked.connect(self._delete_category)

  @Slot()
  def _on_name_changed(self) -> None:
    """ Update the name line edit when the ViewModel name changes. """
    self._name_line_edit.setText(self._viewmodel.name)

  @Slot()
  def _on_parent_category_id_changed(self) -> None:
    """ Update the parent combo box when the ViewModel parent_category_id changes. """
    self._populate_parent_combo()

  @Slot()
  def _on_color_changed(self) -> None:
    """ Update the color button when the ViewModel color changes. """
    self._update_color_button()

  @Slot()
  def _on_focused_changed(self) -> None:
    """ Update the focused checkbox when the ViewModel focused changes. """
    self._focused_check_box.setChecked(self._viewmodel.focused)

  @Slot()
  def _on_keywords_changed(self) -> None:
    """ Update the keywords grid when the ViewModel keywords change. """
    self._setup_keyword_grid()

  @Slot(str)
  def _on_name_edit(self, text: str) -> None:
    """ Handle changes in the name line edit. """
    self._viewmodel.name = text

  @Slot(int)
  def _on_parent_combo_changed(self, index: int) -> None:
    """ Handle changes in the parent category combo box. """
    self._viewmodel.parent_category_id = self._parent_combo_box.itemData(
      index)

  @Slot(int)
  def _on_focused_checkbox_changed(self, state: int) -> None:
    """ Handle changes in the focused checkbox. """
    self._viewmodel.focused = state == 2

  def _populate_parent_combo(self) -> None:
    """ Populate the parent category combo box. """
    self._parent_combo_box.blockSignals(True)
    self._parent_combo_box.clear()
    self._parent_combo_box.addItem("None", None)

    for category in self._viewmodel.get_all_categories():
      if category.id != self._viewmodel.category_id and category.name != "Uncategorized":
        self._parent_combo_box.addItem(category.name, category.id)

    current_id = self._viewmodel.parent_category_id
    if current_id:
      index = self._parent_combo_box.findData(current_id)
      if index >= 0:
        self._parent_combo_box.setCurrentIndex(index)
    else:
      self._parent_combo_box.setCurrentIndex(0)
    self._parent_combo_box.blockSignals(False)

  def _update_color_button(self) -> None:
    """ Update the color button to reflect the selected color. """
    color = QColor(
      self._viewmodel.color) if self._viewmodel.color else QColor(Qt.white)
    self._select_color_button.setStyleSheet(
      f"background-color: {color.name()};")

  def _setup_keyword_grid(self) -> None:
    """ Set up the grid layout for keywords. """
    # Clear existing buttons
    while self._keywords_grid_layout.count():
      item = self._keywords_grid_layout.takeAt(0)
      widget = item.widget()
      if widget is not None:
        widget.deleteLater()

    self._keywords_grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    max_columns = 4
    for i in range(max_columns):
      self._keywords_grid_layout.setColumnStretch(i, 1)

    row = 0
    col = 0
    for index, keyword in enumerate(self._viewmodel.keywords):
      keyword_button = QPushButton(self)
      keyword_button.setObjectName(f"keywordButton_{index}")
      keyword_button.setProperty("class", "keywordButton")
      keyword_button.setCursor(Qt.PointingHandCursor)

      keyword_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
      keyword_button.setFixedHeight(30)
      keyword_button.setMaximumWidth(150)

      # Elide text if it's too long
      font_metrics = QFontMetrics(keyword_button.font())
      elided_text = font_metrics.elidedText(
          keyword.name, Qt.ElideRight, keyword_button.maximumWidth() - 30
      )
      keyword_button.setText(elided_text)

      # Set tooltip if text was elided
      if elided_text != keyword.name:
        keyword_button.setToolTip(keyword.name)

      keyword_button.clicked.connect(partial(self._edit_keyword, index))
      keyword_button.setContextMenuPolicy(Qt.CustomContextMenu)
      keyword_button.customContextMenuRequested.connect(
          partial(self._show_keyword_context_menu, index, keyword_button)
      )
      self._keywords_grid_layout.addWidget(keyword_button, row, col)

      col += 1
      if col >= max_columns:
        col = 0
        row += 1

    # Place the "+" button in a new row, spanning all columns
    row += 1
    self._keywords_grid_layout.addItem(
        QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum), row, 0
    )

    add_keyword_button = QPushButton("+", self)
    add_keyword_button.setObjectName("addKeywordButton")
    add_keyword_button.setCursor(Qt.PointingHandCursor)
    add_keyword_button.setFixedHeight(30)
    add_keyword_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    add_keyword_button.clicked.connect(self._show_keyword_dialog)
    self._keywords_grid_layout.addWidget(
        add_keyword_button, row, 0, 1, max_columns
    )

  def _show_keyword_context_menu(self, index: int, button: QPushButton, pos) -> None:
    """ Show the context menu for a keyword button. """
    menu = QMenu()
    delete_action = QAction("Delete", self)
    delete_action.triggered.connect(partial(self._delete_keyword, index))
    menu.addAction(delete_action)
    menu.exec_(button.mapToGlobal(pos))

  def _edit_keyword(self, index: int) -> None:
    """ Edit a keyword. """
    keyword = self._viewmodel.keywords[index]
    dialog = KeywordDialogView(self, keyword=keyword)
    dialog.keyword_deleted.connect(partial(self._delete_keyword, index))
    if dialog.exec_() == QDialog.Accepted:
      updated_keyword = dialog.keyword_data
      self._viewmodel.update_keyword(
          index, updated_keyword.name, updated_keyword.match_case)
      self._setup_keyword_grid()

  def _delete_keyword(self, index: int) -> None:
    """ Delete a keyword. """
    self._viewmodel.remove_keyword(index)
    self._setup_keyword_grid()

  def _show_keyword_dialog(self) -> None:
    """ Show the dialog to add a new keyword. """
    dialog = KeywordDialogView(self)
    if dialog.exec_() == QDialog.Accepted:
      new_keyword = dialog.keyword_data
      self._viewmodel.add_keyword(
        new_keyword.name, new_keyword.match_case)
      self._setup_keyword_grid()

  def accept(self) -> None:
    """ Handle the accept event. """
    if self._viewmodel.save_category():
      super().accept()
    else:
      QMessageBox.warning(self, "Error", "Failed to save category")

  def _delete_category(self) -> None:
    """ Handle the delete category action. """
    reply = QMessageBox.question(
        self, "Delete Category",
        "Are you sure you want to delete this category?",
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if reply == QMessageBox.Yes:
      if self._viewmodel.delete_category():
        self.accept()
      else:
        QMessageBox.warning(self, "Error", "Failed to delete category")

  def _show_color_dialog(self) -> None:
    """ Show the color selection dialog. """
    initial_color = QColor(
      self._viewmodel.color) if self._viewmodel.color else QColor(Qt.white)
    color = QColorDialog.getColor(initial_color, self)
    if color.isValid():
      self._viewmodel.color = color.name()
