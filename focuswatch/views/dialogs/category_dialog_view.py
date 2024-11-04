import logging
from functools import partial
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (QColorDialog, QComboBox, QDialog,
                               QDialogButtonBox, QFormLayout, QFrame,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QMenu, QMessageBox, QPushButton, QScrollArea,
                               QSizePolicy, QSpacerItem, QVBoxLayout, QWidget, QCheckBox)

from focuswatch.utils.resource_utils import apply_stylesheet
from focuswatch.viewmodels.dialogs.category_dialog_viewmodel import \
    CategoryDialogViewModel
from focuswatch.views.dialogs.keyword_dialog_view import KeywordDialogView

if TYPE_CHECKING:
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.keyword_service import KeywordService

logger = logging.getLogger(__name__)


class CategoryDialogView(QDialog):
  def __init__(self,
               parent: QWidget,
               category_service: 'CategoryService',
               keyword_service: 'KeywordService',
               category_id: Optional[int] = None):
    super().__init__(parent)
    self._viewmodel = CategoryDialogViewModel(
        category_service, keyword_service, category_id)
    self._setup_ui()
    self._connect_signals()

    apply_stylesheet(self, "dialogs/category_dialog.qss")

  def _setup_ui(self):
    self.setWindowTitle(
      "Edit Category" if self._viewmodel._category.id else "Add Category")
    self.setMinimumSize(500, 500)

    # Main layout
    mainLayout = QVBoxLayout(self)
    mainLayout.setSpacing(10)
    mainLayout.setContentsMargins(20, 20, 20, 20)

    # Title label
    self.titleLabel = QLabel(self)
    self.titleLabel.setObjectName("titleLabel")
    self.titleLabel.setText(
      "Edit Category" if self._viewmodel._category.id else "Add Category")
    mainLayout.addWidget(self.titleLabel)

    # Form layout for inputs
    formLayout = QFormLayout()
    formLayout.setLabelAlignment(Qt.AlignRight)
    formLayout.setSpacing(10)

    # Name input
    self.nameLineEdit = QLineEdit(self)
    self.nameLineEdit.setObjectName("nameLineEdit")
    self.nameLineEdit.setText(self._viewmodel.name)
    formLayout.addRow("Name:", self.nameLineEdit)

    # Parent Category combo box
    self.parentComboBox = QComboBox(self)
    self.parentComboBox.setObjectName("parentComboBox")
    self.populate_parent_combo()
    formLayout.addRow("Parent Category:", self.parentComboBox)

    # Color selection
    colorLayout = QHBoxLayout()
    self.selectColorButton = QPushButton(self)
    self.selectColorButton.setObjectName("selectColorButton")
    self.selectColorButton.setFixedSize(40, 20)
    self.update_color_button()
    colorLayout.addWidget(self.selectColorButton)
    colorLayout.addStretch()
    formLayout.addRow("Color:", colorLayout)

    # Focused checkbox
    self.focusedCheckBox = QCheckBox("", self)
    self.focusedCheckBox.setObjectName("focusedCheckBox")
    self.focusedCheckBox.setChecked(self._viewmodel.focused)
    formLayout.addRow("Focused:", self.focusedCheckBox)

    mainLayout.addLayout(formLayout)

    # Keywords Section
    keywordsLabel = QLabel("Keywords:", self)
    keywordsLabel.setObjectName("keywordsLabel")
    mainLayout.addWidget(keywordsLabel)

    # Keywords Frame
    keywordsFrame = QFrame(self)
    keywordsFrame.setObjectName("keywordFrame")
    keywordsFrameLayout = QVBoxLayout(keywordsFrame)
    keywordsFrameLayout.setContentsMargins(5, 5, 5, 5)

    # Scroll area for keywords
    scrollArea = QScrollArea(self)
    scrollArea.setWidgetResizable(True)
    scrollArea.setFixedHeight(150)

    scrollContent = QWidget()
    scrollContent.setObjectName("scrollContent")
    self.keywordsGridLayout = QGridLayout(scrollContent)
    self.keywordsGridLayout.setSpacing(5)
    self.setup_keyword_grid()

    scrollArea.setWidget(scrollContent)
    keywordsFrameLayout.addWidget(scrollArea)

    mainLayout.addWidget(keywordsFrame)

    # Note label
    noteLabel = QLabel(
      "Note: Click on a keyword to edit, right-click to remove.", self)
    noteLabel.setObjectName("noteLabel")
    mainLayout.addWidget(noteLabel)

    # Spacer
    mainLayout.addStretch()

    # Delete button (if applicable)
    if self._viewmodel.can_delete_category():
      self.deleteButton = QPushButton("Delete Category", self)
      self.deleteButton.setObjectName("deleteButton")
      mainLayout.addWidget(self.deleteButton)

    # Dialog buttons
    self.buttonBox = QDialogButtonBox(
      QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
    mainLayout.addWidget(self.buttonBox)

    # Set main layout
    self.setLayout(mainLayout)

  def _connect_signals(self):
    # Connect ViewModel property changes to UI updates
    self._viewmodel.property_changed.connect(self.on_property_changed)

    # Connect UI elements to ViewModel properties and methods
    self.nameLineEdit.textChanged.connect(self.on_name_changed)
    self.parentComboBox.currentIndexChanged.connect(self.on_parent_changed)
    self.selectColorButton.clicked.connect(self.show_color_dialog)
    self.focusedCheckBox.stateChanged.connect(
      self.on_focused_changed)

    self.buttonBox.accepted.connect(self.accept)
    self.buttonBox.rejected.connect(self.reject)

    if hasattr(self, 'deleteButton'):
      self.deleteButton.clicked.connect(self.delete_category)

  @Slot(str)
  def on_property_changed(self, property_name):
    if property_name == 'name':
      self.nameLineEdit.setText(self._viewmodel.name)
    elif property_name == 'parent_category_id':
      self.populate_parent_combo()
    elif property_name == 'color':
      self.update_color_button()
    elif property_name == 'focused':
      self.focusedCheckBox.setChecked(self._viewmodel.focused)
    elif property_name == 'keywords':
      self.setup_keyword_grid()

  @Slot(str)
  def on_name_changed(self, text):
    self._viewmodel.name = text

  @Slot(int)
  def on_parent_changed(self, index):
    self._viewmodel.parent_category_id = self.parentComboBox.itemData(index)

  @Slot(int)
  def on_focused_changed(self, state):
    self._viewmodel.focused = state == 2

  def populate_parent_combo(self):
    self.parentComboBox.blockSignals(True)
    self.parentComboBox.clear()
    self.parentComboBox.addItem("None", None)

    for category in self._viewmodel.get_all_categories():
      if category.id != self._viewmodel._category.id and category.name != "Uncategorized":
        self.parentComboBox.addItem(category.name, category.id)

    current_id = self._viewmodel.parent_category_id
    if current_id:
      index = self.parentComboBox.findData(current_id)
      if index >= 0:
        self.parentComboBox.setCurrentIndex(index)
    else:
      self.parentComboBox.setCurrentIndex(0)
    self.parentComboBox.blockSignals(False)

  def update_color_button(self):
    color = QColor(
      self._viewmodel.color) if self._viewmodel.color else QColor(Qt.white)
    self.selectColorButton.setStyleSheet(f"background-color: {color.name()};")

  def setup_keyword_grid(self):
    # Clear existing buttons
    while self.keywordsGridLayout.count():
      item = self.keywordsGridLayout.takeAt(0)
      widget = item.widget()
      if widget is not None:
        widget.deleteLater()
      else:
        del item

    self.keywordsGridLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    max_columns = 4
    for i in range(max_columns):
      self.keywordsGridLayout.setColumnStretch(i, 1)

    row = 0
    col = 0
    for index, keyword in enumerate(self._viewmodel.keywords):
      keywordButton = QPushButton(keyword.name, self)
      keywordButton.setObjectName(f"keywordButton_{index}")
      keywordButton.setProperty("class", "keywordButton")
      keywordButton.setCursor(Qt.PointingHandCursor)

      keywordButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
      keywordButton.setFixedHeight(30)

      keywordButton.clicked.connect(partial(self.edit_keyword, index))
      keywordButton.setContextMenuPolicy(Qt.CustomContextMenu)
      keywordButton.customContextMenuRequested.connect(
          partial(self.show_keyword_context_menu, index, keywordButton))
      self.keywordsGridLayout.addWidget(keywordButton, row, col)

      col += 1
      if col >= max_columns:
        col = 0
        row += 1

    # Place the '+' button in a new row, spanning all columns
    row += 1
    self.keywordsGridLayout.addItem(QSpacerItem(
      0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum), row, 0)

    addKeywordButton = QPushButton("+", self)
    addKeywordButton.setObjectName("addKeywordButton")
    addKeywordButton.setCursor(Qt.PointingHandCursor)
    addKeywordButton.setFixedHeight(30)
    addKeywordButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    addKeywordButton.clicked.connect(self.show_keyword_dialog)
    self.keywordsGridLayout.addWidget(addKeywordButton, row, 0, 1, max_columns)

  def show_keyword_context_menu(self, index, button, pos):
    menu = QMenu()
    delete_action = QAction('Delete', self)
    delete_action.triggered.connect(partial(self.delete_keyword, index))
    menu.addAction(delete_action)
    menu.exec_(button.mapToGlobal(pos))

  def edit_keyword(self, index):
    keyword = self._viewmodel.keywords[index]
    dialog = KeywordDialogView(self, keyword=keyword)
    dialog.keyword_deleted.connect(partial(self.delete_keyword, index))
    if dialog.exec_() == QDialog.Accepted:
      updated_keyword = dialog.keyword_data
      self._viewmodel.update_keyword(
          index, updated_keyword.name, updated_keyword.match_case)
      self.setup_keyword_grid()

  def delete_keyword(self, index):
    self._viewmodel.remove_keyword(index)
    self.setup_keyword_grid()

  def show_keyword_dialog(self):
    dialog = KeywordDialogView(self)
    if dialog.exec_() == QDialog.Accepted:
      new_keyword = dialog.keyword_data
      self._viewmodel.add_keyword(new_keyword.name, new_keyword.match_case)
      self.setup_keyword_grid()

  def accept(self):
    if self._viewmodel.save_category():
      super().accept()
    else:
      QMessageBox.warning(self, "Error", "Failed to save category")

  def delete_category(self):
    reply = QMessageBox.question(self, 'Delete Category',
                                 'Are you sure you want to delete this category?',
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if reply == QMessageBox.Yes:
      if self._viewmodel.delete_category():
        self.accept()
      else:
        QMessageBox.warning(self, "Error", "Failed to delete category")

  def show_color_dialog(self):
    color = QColorDialog.getColor(QColor(
        self._viewmodel.color) if self._viewmodel.color else QColor(Qt.white), self)
    if color.isValid():
      self._viewmodel.color = color.name()
