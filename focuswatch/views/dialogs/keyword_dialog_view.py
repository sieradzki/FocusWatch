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
  """ Dialog for adding or editing a keyword. """

  keyword_deleted = Signal()

  def __init__(
      self,
      parent: QWidget,
      keyword: Optional[Keyword] = None
  ):
    super().__init__(parent)
    self._viewmodel = KeywordDialogViewModel(keyword)
    self._setup_ui()
    self._connect_signals()

    apply_stylesheet(self, "dialogs/keyword_dialog.qss")

  def _setup_ui(self) -> None:
    """ Set up the user interface. """
    is_editing = self._viewmodel.get_keyword().id is not None
    self.setWindowTitle("Edit Keyword" if is_editing else "Add Keyword")
    self.setMinimumSize(400, 250)

    # Main layout
    main_layout = QVBoxLayout(self)
    main_layout.setSpacing(10)
    main_layout.setContentsMargins(20, 20, 20, 20)

    # Title label
    self._title_label = QLabel(self)
    self._title_label.setObjectName("titleLabel")
    self._title_label.setText(
        "Edit Keyword" if is_editing else "Add Keyword")
    main_layout.addWidget(self._title_label)

    # Form layout
    form_layout = QFormLayout()
    form_layout.setLabelAlignment(Qt.AlignRight)
    form_layout.setSpacing(10)

    # Name input
    self._name_edit = QLineEdit(self)
    self._name_edit.setText(self._viewmodel.name)
    form_layout.addRow("Name:", self._name_edit)

    # Match case checkbox
    self._match_case_checkbox = QCheckBox("Match case", self)
    self._match_case_checkbox.setChecked(self._viewmodel.match_case)
    form_layout.addRow("", self._match_case_checkbox)

    main_layout.addLayout(form_layout)

    # Spacer
    main_layout.addStretch()

    # Delete button (if applicable)
    if self._viewmodel.can_delete_keyword():
      self._delete_button = QPushButton("Delete Keyword", self)
      self._delete_button.setObjectName("deleteButton")
      main_layout.addWidget(self._delete_button)

    # Dialog buttons
    self._button_box = QDialogButtonBox(
        QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
    main_layout.addWidget(self._button_box)

  def _connect_signals(self) -> None:
    """ Connect signals and slots. """
    # Connect ViewModel property changes to UI updates
    self._viewmodel.name_changed.connect(self._on_name_changed)
    self._viewmodel.match_case_changed.connect(self._on_match_case_changed)

    # Connect UI elements to ViewModel
    self._name_edit.textChanged.connect(self._on_name_edit)
    self._match_case_checkbox.stateChanged.connect(
        self._on_match_case_checkbox_changed)

    self._button_box.accepted.connect(self.accept)
    self._button_box.rejected.connect(self.reject)
    if hasattr(self, '_delete_button'):
      self._delete_button.clicked.connect(self._delete_keyword)

  @Slot()
  def _on_name_changed(self) -> None:
    """ Update the name edit when the ViewModel name changes. """
    self._name_edit.setText(self._viewmodel.name)

  @Slot()
  def _on_match_case_changed(self) -> None:
    """ Update the match case checkbox when the ViewModel match_case changes. """
    self._match_case_checkbox.setChecked(self._viewmodel.match_case)

  @Slot(str)
  def _on_name_edit(self, text: str) -> None:
    """ Handle changes in the name edit. """
    self._viewmodel.name = text

  @Slot(int)
  def _on_match_case_checkbox_changed(self, state: int) -> None:
    """ Handle changes in the match case checkbox. """
    self._viewmodel.match_case = state == 2

  def accept(self) -> None:
    """ Handle the accept event. """
    if not self._viewmodel.is_input_valid():
      QMessageBox.warning(self, "Error", "Keyword name cannot be empty")
      return

    # Return the keyword data to the parent dialog
    self.keyword_data = self._viewmodel.get_keyword()
    super().accept()

  def _delete_keyword(self) -> None:
    """ Handle the delete keyword action. """
    # Emit a signal to inform the parent dialog that the keyword should be deleted
    self.keyword_deleted.emit()
    self.reject()
