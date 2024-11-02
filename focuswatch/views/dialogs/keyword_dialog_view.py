import logging
from functools import partial
from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox,
                               QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QVBoxLayout, QWidget)

from focuswatch.models.keyword import Keyword
from focuswatch.utils.resource_utils import apply_stylesheet
from focuswatch.viewmodels.dialogs.keyword_dialog_viewmodel import \
    KeywordDialogViewModel

logger = logging.getLogger(__name__)


class KeywordDialogView(QDialog):

  keyword_deleted = Signal()

  def __init__(self, parent, keyword: Optional[Keyword] = None):
    super().__init__(parent)
    self._viewmodel = KeywordDialogViewModel(keyword)
    self._setup_ui()
    self._connect_signals()

    apply_stylesheet(self, "dialogs/keyword_dialog.qss")

  def _setup_ui(self):
    self.setWindowTitle(
        "Edit Keyword" if self._viewmodel.get_keyword().id else "Add Keyword")
    self.setMinimumSize(400, 250)

    # Main layout
    mainLayout = QVBoxLayout(self)
    mainLayout.setSpacing(10)
    mainLayout.setContentsMargins(20, 20, 20, 20)

    # Title label
    self.titleLabel = QLabel(self)
    self.titleLabel.setObjectName("titleLabel")
    self.titleLabel.setText(
        "Edit Keyword" if self._viewmodel.get_keyword().id else "Add Keyword")
    mainLayout.addWidget(self.titleLabel)

    # Form layout
    formLayout = QFormLayout()
    formLayout.setLabelAlignment(Qt.AlignRight)
    formLayout.setSpacing(10)

    # Name input
    self.nameEdit = QLineEdit(self)
    self.nameEdit.setText(self._viewmodel.name)
    formLayout.addRow("Name:", self.nameEdit)

    # Match case checkbox
    self.match_case_checkbox = QCheckBox("Match case", self)
    self.match_case_checkbox.setChecked(self._viewmodel.match_case)
    formLayout.addRow("", self.match_case_checkbox)

    mainLayout.addLayout(formLayout)

    # Spacer
    mainLayout.addStretch()

    # Delete button (if applicable)
    if self._viewmodel.can_delete_keyword():
      self.deleteButton = QPushButton("Delete Keyword", self)
      self.deleteButton.setObjectName("deleteButton")
      mainLayout.addWidget(self.deleteButton)

    # Dialog buttons
    self.buttonBox = QDialogButtonBox(
        QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
    mainLayout.addWidget(self.buttonBox)

  def _connect_signals(self):
    # Connect ViewModel properties to UI elements
    self._viewmodel.property_changed.connect(self.on_property_changed)

    # Connect UI elements to ViewModel
    self.nameEdit.textChanged.connect(self.on_name_changed)
    self.match_case_checkbox.stateChanged.connect(
        self.on_match_case_changed)

    self.buttonBox.accepted.connect(self.accept)
    self.buttonBox.rejected.connect(self.reject)
    if hasattr(self, 'deleteButton'):
      self.deleteButton.clicked.connect(self.delete_keyword)

  @Slot(str)
  def on_property_changed(self, property_name):
    if property_name == 'name':
      self.nameEdit.setText(self._viewmodel.name)
    elif property_name == 'match_case':
      self.match_case_checkbox.setChecked(self._viewmodel.match_case)

  @Slot(str)
  def on_name_changed(self, text):
    self._viewmodel.name = text

  @Slot(int)
  def on_match_case_changed(self, state):
    self._viewmodel.match_case = bool(state)

  def accept(self):
    if not self._viewmodel.is_input_valid():
      QMessageBox.warning(self, "Error", "Keyword name cannot be empty")
      return

    # Return the keyword data to the parent dialog
    self.keyword_data = self._viewmodel.get_keyword()
    super().accept()

  def delete_keyword(self):
    # Emit a signal to inform the parent dialog that the keyword should be deleted
    self.keyword_deleted.emit()
    self.reject()

  def closeEvent(self, event):
    self._viewmodel.property_changed.disconnect(self.on_property_changed)
    super().closeEvent(event)
