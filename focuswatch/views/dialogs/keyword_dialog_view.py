import logging
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import QCoreApplication, QSize, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                               QPushButton, QSizePolicy, QSpacerItem,
                               QVBoxLayout)

from focuswatch.viewmodels.dialogs.keyword_dialog_viewmodel import \
    KeywordDialogViewModel

if TYPE_CHECKING:
  from focuswatch.services.keyword_service import KeywordService
  from focuswatch.models.keyword import Keyword

logger = logging.getLogger(__name__)


class KeywordDialogView(QDialog):

  def __init__(self, parent, keyword_service: 'KeywordService', keyword_id: Optional[int] = None, keyword: Optional['Keyword'] = None):
    super().__init__(parent)
    self._viewmodel = KeywordDialogViewModel(
      keyword_service, keyword_id, keyword)
    self.setupUi()
    self.connectSignals()

  def setupUi(self):
    self.setObjectName("Dialog")
    self.resize(395, 142)

    # Main layout
    self.verticalLayout = QVBoxLayout(self)
    self.verticalLayout.setObjectName("verticalLayout")

    # Dialog title
    self.label = QLabel(self)
    self.label.setObjectName("label")
    font = QFont()
    font.setPointSize(16)
    self.label.setFont(font)
    self.verticalLayout.addWidget(self.label)

    # Frame
    self.frame = QFrame(self)
    self.frame.setObjectName("frame")
    self.frame.setFrameShape(QFrame.StyledPanel)
    self.frame.setFrameShadow(QFrame.Raised)
    self.verticalLayout_2 = QVBoxLayout(self.frame)
    self.verticalLayout_2.setObjectName("verticalLayout_2")

    # Name label
    self.horizontalLayout = QHBoxLayout()
    self.horizontalLayout.setObjectName("horizontalLayout")
    self.nameLabel = QLabel(self.frame)
    self.nameLabel.setObjectName("nameLabel")
    self.horizontalLayout.addWidget(self.nameLabel)

    # Name input
    self.nameEdit = QLineEdit(self.frame)
    self.nameEdit.setObjectName("nameEdit")
    self.nameEdit.setMaximumSize(QSize(16777215, 30))
    self.nameEdit.setText(self._viewmodel.name)
    self.horizontalLayout.addWidget(self.nameEdit)

    self.verticalLayout_2.addLayout(self.horizontalLayout)

    # Match case label
    self.horizontalLayout2 = QHBoxLayout()
    self.horizontalLayout2.setObjectName("horizontalLayout2")
    self.match_case_label = QLabel(self.frame)
    self.match_case_label.setObjectName("match_case_label")
    self.horizontalLayout2.addWidget(self.match_case_label)

    # Match case checkbox
    self.match_case_checkbox = QCheckBox(self.frame)
    self.match_case_checkbox.setObjectName("match_case_checkbox")
    self.match_case_checkbox.setChecked(self._viewmodel.match_case)
    self.horizontalLayout2.addWidget(self.match_case_checkbox)

    spacerItem = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.horizontalLayout2.addItem(spacerItem)

    self.verticalLayout_2.addLayout(self.horizontalLayout2)

    # Delete button
    if self._viewmodel.can_delete_keyword():
      self.delete_button = QPushButton(self.frame)
      self.delete_button.setObjectName("delete_button")
      self.delete_button.setStyleSheet("background-color: red")
      self.delete_button.setText("Delete")
      self.verticalLayout_2.addWidget(self.delete_button)

    self.verticalLayout.addWidget(self.frame)

    # Dialog buttons
    self.buttonBox = QDialogButtonBox(self)
    self.buttonBox.setObjectName("buttonBox")
    self.buttonBox.setOrientation(Qt.Horizontal)
    self.buttonBox.setStandardButtons(
      QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
    self.verticalLayout.addWidget(self.buttonBox)

    self.retranslateUi()

  def retranslateUi(self):
    self.setWindowTitle(QCoreApplication.translate(
      "Dialog", "Keyword dialog", None))
    if self._viewmodel._keyword.id:
      self.label.setText(QCoreApplication.translate(
        "Dialog", "Edit keyword", None))
    else:
      self.label.setText(QCoreApplication.translate(
        "Dialog", "Add a keyword", None))
    self.nameLabel.setText(QCoreApplication.translate("Dialog", "Name", None))
    self.match_case_label.setText(
      QCoreApplication.translate("Dialog", "Match case", None))

  def connectSignals(self):
    # Connect ViewModel properties to UI elements
    self._viewmodel.property_changed.connect(self.on_property_changed)

    # Connect UI elements to ViewModel
    self.nameEdit.textChanged.connect(self.on_name_changed)
    self.match_case_checkbox.stateChanged.connect(
        self.on_match_case_changed)

    self.buttonBox.accepted.connect(self.accept)
    self.buttonBox.rejected.connect(self.reject)
    if hasattr(self, 'delete_button'):
      self.delete_button.clicked.connect(self.delete_keyword)

  def on_property_changed(self, property_name):
    if property_name == '_name':
      self.nameEdit.setText(self._viewmodel.name)
    elif property_name == '_match_case':
      self.match_case_checkbox.setChecked(self._viewmodel.match_case)

  def on_name_changed(self, text):
    self._viewmodel.name = text

  def on_match_case_changed(self, state):
    self._viewmodel.match_case = state

  def accept(self):
    if not self._viewmodel.is_input_valid():  # TODO return error message and show in the dialog
      QMessageBox.warning(self, "Error", "Keyword name cannot be empty")
      return

    if self._viewmodel.category_id:  # save when category exists
      super().accept()
    else:  # creating new category so save the keyword data for later
      self.keyword_data = self._viewmodel.get_keyword()
      super().accept()

  def delete_keyword(self):
    if self._viewmodel.delete_keyword():
      self.done(KeywordDialogView.Deleted())  # Custom return code
    else:
      QMessageBox.warning(self, "Error", "Failed to delete keyword")

  @staticmethod
  def Deleted():
    return QDialog.Accepted + 1  # Custom return code

  def closeEvent(self, event):
    self._viewmodel.property_changed.disconnect(self.on_property_changed)
    super().closeEvent(event)
