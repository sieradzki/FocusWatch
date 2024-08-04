from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QPushButton, QGridLayout, QDialogButtonBox,
                               QColorDialog, QMessageBox, QFrame, QSizePolicy, QSpacerItem, QMenu)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, QSize, QCoreApplication
from focuswatch.viewmodels.dialogs.category_dialog_viewmodel import CategoryDialogViewModel
from focuswatch.views.dialogs.keyword_dialog_view import KeywordDialog
from focuswatch.ui.utils import get_category_color
import logging

logger = logging.getLogger(__name__)


class CategoryDialog(QDialog):
  def __init__(self, parent, category_service, keyword_service, category_id=None):
    super().__init__(parent)
    self._viewmodel = CategoryDialogViewModel(
        category_service, keyword_service, category_id)
    self.setupUi()
    self.connectSignals()
    self._viewmodel.add_property_observer('_keywords', self.setup_keyword_grid)

  def setupUi(self):
    if not self.objectName():
      self.setObjectName(u"Dialog")
    self.resize(464, 422)
    self.verticalLayout = QVBoxLayout(self)
    self.verticalLayout.setObjectName(u"verticalLayout")
    self.label = QLabel(self)
    self.label.setObjectName(u"label")
    font = QFont()
    font.setPointSize(16)
    self.label.setFont(font)

    self.verticalLayout.addWidget(self.label)

    self.frame = QFrame(self)
    self.frame.setObjectName(u"frame")
    self.frame.setFrameShape(QFrame.StyledPanel)
    self.frame.setFrameShadow(QFrame.Raised)
    self.verticalLayout_2 = QVBoxLayout(self.frame)
    self.verticalLayout_2.setObjectName(u"verticalLayout_2")

    self.horizontalLayout_2 = QHBoxLayout()
    self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")

    # Name label
    self.nameLabel = QLabel(self.frame)
    self.nameLabel.setObjectName(u"nameLabel")
    sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(
      self.nameLabel.sizePolicy().hasHeightForWidth())
    self.nameLabel.setSizePolicy(sizePolicy)
    self.nameLabel.setMinimumSize(QSize(40, 0))

    self.horizontalLayout_2.addWidget(self.nameLabel)

    # Name line edit
    self.name_lineEdit = QLineEdit(self.frame)
    self.name_lineEdit.setObjectName(u"name_lineEdit")
    sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
    sizePolicy1.setHorizontalStretch(0)
    sizePolicy1.setVerticalStretch(0)
    sizePolicy1.setHeightForWidth(
      self.name_lineEdit.sizePolicy().hasHeightForWidth())
    self.name_lineEdit.setSizePolicy(sizePolicy1)
    self.name_lineEdit.setMaximumSize(QSize(16777215, 30))
    self.name_lineEdit.setText(self._viewmodel.name)

    self.horizontalLayout_2.addWidget(self.name_lineEdit)

    self.horizontalSpacer_2 = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

    self.verticalLayout_2.addLayout(self.horizontalLayout_2)

    # Parent Category
    self.horizontalLayout_4 = QHBoxLayout()
    self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
    self.parentLabel = QLabel(self.frame)
    self.parentLabel.setObjectName(u"parentLabel")
    self.parentLabel.setText("Parent category:")
    self.horizontalLayout_4.addWidget(self.parentLabel)

    self.parent_comboBox = QComboBox(self.frame)
    self.parent_comboBox.setObjectName(u"parent_comboBox")
    self.populate_parent_combo()
    self.parent_comboBox.currentIndexChanged.connect(self.on_parent_changed)
    self.horizontalLayout_4.addWidget(self.parent_comboBox)

    self.horizontalSpacer_3 = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.horizontalLayout_4.addItem(self.horizontalSpacer_3)
    self.verticalLayout_2.addLayout(self.horizontalLayout_4)

    # Color
    self.horizontalLayout = QHBoxLayout()
    self.horizontalLayout.setObjectName(u"horizontalLayout")
    self.colorLabel = QLabel(self.frame)
    self.colorLabel.setObjectName(u"colorLabel")
    self.horizontalLayout.addWidget(self.colorLabel)

    self.selectColor_pushButton = QPushButton(self.frame)
    self.selectColor_pushButton.setObjectName(u"selectColor_pushButton")
    self.selectColor_pushButton.setMinimumSize(QSize(40, 20))
    self.selectColor_pushButton.setMaximumSize(QSize(40, 20))
    self.update_color_button()
    self.selectColor_pushButton.clicked.connect(self.show_color_dialog)
    self.horizontalLayout.addWidget(self.selectColor_pushButton)

    self.horizontalSpacer = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.horizontalLayout.addItem(self.horizontalSpacer)
    self.verticalLayout_2.addLayout(self.horizontalLayout)

    # Keywords
    self.frame_2 = QFrame(self.frame)
    self.frame_2.setObjectName(u"frame_2")
    self.frame_2.setFrameShape(QFrame.StyledPanel)
    self.frame_2.setFrameShadow(QFrame.Raised)
    self.verticalLayout_3 = QVBoxLayout(self.frame_2)
    self.verticalLayout_3.setSpacing(1)
    self.verticalLayout_3.setObjectName(u"verticalLayout_3")
    self.verticalLayout_3.setContentsMargins(1, 1, 1, 1)
    self.horizontalLayout_5 = QHBoxLayout()
    self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
    self.keywordsLabel = QLabel(self.frame_2)
    self.keywordsLabel.setObjectName(u"keywordsLabel")

    self.horizontalLayout_5.addWidget(self.keywordsLabel)

    self.keywords_gridLayout = QGridLayout()
    self.keywords_gridLayout.setObjectName(u"keywords_gridLayout")

    self.setup_keyword_grid()

    self.horizontalLayout_5.addLayout(self.keywords_gridLayout)

    self.horizontalSpacer_5 = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.horizontalLayout_5.addItem(self.horizontalSpacer_5)

    self.verticalLayout_3.addLayout(self.horizontalLayout_5)

    self.verticalSpacer_2 = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    self.verticalLayout_3.addItem(self.verticalSpacer_2)

    # note
    self.noteLabel = QLabel(self.frame_2)
    self.noteLabel.setObjectName(u"noteLabel")

    self.verticalLayout_3.addWidget(self.noteLabel)

    self.verticalLayout_2.addWidget(self.frame_2)

    self.verticalSpacer = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    self.verticalLayout_2.addItem(self.verticalSpacer)

    # Buttons
    self.buttonBox = QDialogButtonBox(self)
    self.buttonBox.setObjectName("buttonBox")
    self.buttonBox.setOrientation(Qt.Horizontal)
    self.buttonBox.setStandardButtons(
      QDialogButtonBox.Cancel | QDialogButtonBox.Save)
    self.buttonBox.accepted.connect(self.accept)
    self.buttonBox.rejected.connect(self.reject)

    if self._viewmodel.can_delete_category():
      self.deleteButton = QPushButton(self.frame)
      self.deleteButton.setObjectName("deleteButton")
      self.deleteButton.setText("Delete category")
      self.deleteButton.setStyleSheet("background-color: red")
      self.deleteButton.clicked.connect(self.delete_category)
      self.verticalLayout_2.addWidget(self.deleteButton)

    self.verticalLayout.addWidget(self.frame)
    self.verticalLayout.addWidget(self.buttonBox)

    self.retranslateUi()

  def retranslateUi(self):
    self.setWindowTitle(QCoreApplication.translate(
      "Dialog", "Edit Category" if self._viewmodel._category else "Add Category", None))
    self.label.setText(QCoreApplication.translate(
      "Dialog", u"Edit Category" if self._viewmodel._category else u"Add a category", None))
    self.nameLabel.setText(QCoreApplication.translate("Dialog", u"Name", None))
    self.parentLabel.setText(QCoreApplication.translate(
      "Dialog", u"Parent category", None))

    self.colorLabel.setText(
      QCoreApplication.translate("Dialog", u"Color", None))
    self.selectColor_pushButton.setText("")
    self.keywordsLabel.setText(
      QCoreApplication.translate("Dialog", u"Keywords", None))
    self.noteLabel.setText(QCoreApplication.translate(
      "Dialog", u"Note: Click on keyword to edit, right-click on keyword to remove it", None))

  def connectSignals(self):
      # Connect ViewModel properties to UI elements
    self._viewmodel.property_changed.connect(self.on_property_changed)

    # Connect UI elements to ViewModel
    self.name_lineEdit.textChanged.connect(self.on_name_changed)
    self.parent_comboBox.currentIndexChanged.connect(
        self.on_parent_changed)
    self.selectColor_pushButton.clicked.connect(self.show_color_dialog)

  def on_property_changed(self, property_name):
    if property_name == '_name':
      self.name_lineEdit.setText(self._viewmodel.name)
    elif property_name == '_parent_category_id':
      self.update_parent_combo()
    elif property_name == '_color':
      self.update_color_button()
    elif property_name == '_keywords':
      self.setup_keyword_grid()

  def on_name_changed(self, text):
    self._viewmodel.name = text

  def populate_parent_combo(self):
    self.parent_comboBox.clear()
    self.parent_comboBox.addItem("None", None)

    for category in self._viewmodel.get_all_categories():
      if (not self._viewmodel._category or category.id != self._viewmodel._category.id) and category.name != "Uncategorized":
        self.parent_comboBox.addItem(category.name, category.id)

    if self._viewmodel.parent_category_id:
      index = self.parent_comboBox.findData(self._viewmodel.parent_category_id)
      if index >= 0:
        self.parent_comboBox.setCurrentIndex(index)

  def update_color_button(self):
    color = QColor(
      self._viewmodel.color) if self._viewmodel.color else QColor(Qt.white)
    self.selectColor_pushButton.setStyleSheet(
      f"background-color: {color.name()};")

  def setup_keyword_grid(self):
    # Clear existing buttons
    for i in reversed(range(self.keywords_gridLayout.count())):
      self.keywords_gridLayout.itemAt(i).widget().setParent(None)
      self.keywords_gridLayout.itemAt(i).widget().deleteLater()

    row, col = 0, 0
    for keyword in self._viewmodel.keywords:
      keywordButton = QPushButton(keyword.name)
      keywordButton.setObjectName(f"keywordButton_{keyword.id}")
      keywordButton.clicked.connect(
        lambda checked, k=keyword: self.edit_keyword(k))
      self.keywords_gridLayout.addWidget(keywordButton, row, col)

      col += 1
      if col >= 4:
        col = 0
        row += 1

    addKeywordButton = QPushButton("+")
    addKeywordButton.clicked.connect(self.show_keyword_dialog)
    self.keywords_gridLayout.addWidget(addKeywordButton, row + 1, 0, 1, 4)

  def show_color_dialog(self):
    color = QColorDialog.getColor(QColor(
      self._viewmodel.color) if self._viewmodel.color else QColor(Qt.white), self)
    if color.isValid():
      self._viewmodel.color = color.name()

  def on_parent_changed(self, index):
    self._viewmodel.parent_category_id = self.parent_comboBox.itemData(index)

  def edit_keyword(self, keyword):
    dialog = KeywordDialog(self, self._viewmodel._keyword_service,
                           self._viewmodel._category.id, keyword.id)
    if dialog.exec_():
      self._viewmodel.update_keyword(
        keyword.id, dialog.nameEdit.text(), dialog.match_case_checkbox.isChecked())

  def show_keyword_dialog(self):
    dialog = KeywordDialog(
      self, self._viewmodel._keyword_service, self._viewmodel._category.id)
    if dialog.exec_():
      self._viewmodel.add_keyword(
        dialog.nameEdit.text(), dialog.match_case_checkbox.isChecked())

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

  def closeEvent(self, event):
    self._viewmodel.property_changed.disconnect(self.on_property_changed)
    super().closeEvent(event)
