""" Category Dialog UI for FocusWatch """
import logging
from typing import List, Optional, Tuple

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect, QSize, Qt,
                            QTime, QUrl)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
                           QFontDatabase, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette,
                           QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QColorDialog,
                               QComboBox, QDialog, QDialogButtonBox, QFrame,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QSizePolicy, QSpacerItem,
                               QTextEdit, QVBoxLayout, QWidget)

from focuswatch.ui.keyword_dialog import KeywordDialog
from focuswatch.ui.utils import get_category_color

logger = logging.getLogger(__name__)


class CategoryDialog(QDialog):
  def __init__(self, parent, category_manager, keyword_manager, category: Optional[int] = None, keywords: Optional[List[str]] = None):
    super().__init__(parent)
    self._category_manager = category_manager
    self._keyword_manager = keyword_manager

    self._category = category
    self._keywords = keywords
    self.color = None
    self.i, self.j = 0, 0

    # Store new keywords when creating new category
    if not self._category:
      self.new_keywords = []

    self.setupUi(self)

  def show_color_picker(self):
    # TODO move to utils
    current_style = self.selectColor_pushButton.styleSheet()
    if current_style:
      color_name = current_style.split(':')[-1].strip().strip(';')
      initial_color = QColor(color_name)
    else:
      initial_color = QColor(Qt.white)

    color = QColorDialog.getColor(initial_color, self, "Select Color")

    if color.isValid():
      self.color = color.name()
      self.selectColor_pushButton.setStyleSheet(
        f"background-color: {self.color};")

  def delete_keyword(self, sender):
    """ Delete keyword from database and remove from grid. """
    keyword_id = sender.objectName().split(sep='_')[-1]
    if self._category:
      self._keyword_manager.delete_keyword(int(keyword_id))
    else:
      new_keyword_id = self.new_keywords.index(
        [keyword for keyword in self.new_keywords if keyword[0] == int(keyword_id)][0])
      del self.new_keywords[int(new_keyword_id)]
    sender.deleteLater()
    self.setup_keyword_grid()

  def add_keyword_to_grid(self, keyword):
    """ Add keyword to grid layout. """
    keywordButton = QPushButton(self.frame_2)
    keywordButton.setObjectName(f"keywordButton_{keyword[0]}")
    keywordButton.setText(keyword[1])

    # Edit on left-click
    keywordButton.clicked.connect(
      lambda checked, btn=keywordButton: self.edit_keyword(btn))
    # Delete on right-click
    keywordButton.mouseReleaseEvent = lambda event: self.keyword_mouse_release_event(
      event, keywordButton)

    self.keywords_gridLayout.addWidget(keywordButton, self.j, self.i, 1, 1)
    # Update grid position
    self.i += 1
    if self.i == 4:
      self.i = 0
      self.j += 1

  def keyword_mouse_release_event(self, event, button):
    """ Override mouseReleaseEvent to handle right-click. """
    if event.button() == Qt.RightButton:
      self.delete_keyword(button)
    else:
      # Call the original mouseReleaseEvent for other mouse buttons
      QPushButton.mouseReleaseEvent(button, event)

  def setup_keyword_grid(self):
    """ Setup keyword grid layout. """
    # Reset grid position
    self.i = 0
    self.j = 0

    # Clear layout
    for i in reversed(range(self.keywords_gridLayout.count())):
      widget = self.keywords_gridLayout.itemAt(i).widget()
      if widget is not None:
        widget.deleteLater()

    # Get keywords for category
    keywords = []
    if self._category:
      keywords = self._keyword_manager.get_keywords_for_category(
          self._category[0])
    else:
      keywords = self.new_keywords

    # Add keywords to grid
    if keywords:
      for keyword in keywords:
        self.add_keyword_to_grid(keyword)

    # Add '+' button
    self.addKeyword_pushButton = QPushButton(self.frame_2)
    self.addKeyword_pushButton.setObjectName(u"addKeyword_pushButton")
    self.addKeyword_pushButton.setText('+')
    self.addKeyword_pushButton.clicked.connect(self.show_keyword_dialog)

    self.keywords_gridLayout.addWidget(
      self.addKeyword_pushButton, self.j + 1, 0, 4, 4)

  def show_keyword_dialog(self):
    """ Show keyword dialog and return values """
    keyword_dialog = KeywordDialog(self, self._keyword_manager)
    result = keyword_dialog.exec_()

    if result:
      keyword_name = keyword_dialog.nameEdit.text()
      match_case = keyword_dialog.match_case_checkbox.isChecked()
      self.add_keyword(keyword_name, match_case)

  def add_keyword(self, keyword_name, match_case: Optional[bool] = False):
    """ Add keyword to database if category exists, else store in new_keywords. """
    if self._category:
      self._keyword_manager.add_keyword(
        keyword_name, self._category[0], match_case)
    else:
      keyword_id = self.new_keywords[-1][0] + 1 if self.new_keywords else 0
      self.new_keywords.append(
        (keyword_id, keyword_name, None, match_case))

    self.setup_keyword_grid()

  def edit_keyword(self, button):
    """ Edit keyword in database, update grid. """
    keyword_id = button.objectName().split(sep='_')[-1]
    if self._category:
      keyword_dialog = KeywordDialog(self, self._keyword_manager, keyword_id)
    else:
      new_keyword_id = self.new_keywords.index(
        [keyword for keyword in self.new_keywords if keyword[0] == int(keyword_id)][0])
      keyword_dialog = KeywordDialog(
        self, self._keyword_manager, None, self.new_keywords[new_keyword_id])

    result = keyword_dialog.exec_()

    if result:
      keyword_name = keyword_dialog.nameEdit.text()
      if keyword_name:
        match_case = keyword_dialog.match_case_checkbox.isChecked()
        if self._category:
          self._keyword_manager.update_keyword(
            int(keyword_id), keyword_name, self._category[0], match_case)
        else:
          self.new_keywords[new_keyword_id] = (
            int(keyword_id), keyword_name, None, match_case)
        self.setup_keyword_grid()

  def delete_category(self):
    """ Show confirmation dialog before deleting category. """
    category_id = self._category[0]

    confirmation_dialog = QDialog(self)
    confirmation_dialog.setWindowTitle("Confirmation")

    message_label = QLabel("Are you sure you want to delete this category?")

    button_box = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
    button_box.accepted.connect(
      lambda: self.confirm_delete(category_id, confirmation_dialog))
    button_box.rejected.connect(confirmation_dialog.reject)

    layout = QVBoxLayout()
    layout.addWidget(message_label)
    layout.addWidget(button_box)
    confirmation_dialog.setLayout(layout)

    confirmation_dialog.exec_()

  def confirm_delete(self, category_id, confirmation_dialog):
    """ Delete category from database and close dialog. """
    self._category_manager.delete_category(category_id)
    confirmation_dialog.accept()
    self.close()

  def setupUi(self, Dialog):
    if not Dialog.objectName():
      Dialog.setObjectName(u"Dialog")
    Dialog.resize(464, 422)
    self.verticalLayout = QVBoxLayout(Dialog)
    self.verticalLayout.setObjectName(u"verticalLayout")
    self.label = QLabel(Dialog)
    self.label.setObjectName(u"label")
    font = QFont()
    font.setPointSize(16)
    self.label.setFont(font)

    self.verticalLayout.addWidget(self.label)

    self.frame = QFrame(Dialog)
    self.frame.setObjectName(u"frame")
    self.frame.setFrameShape(QFrame.StyledPanel)
    self.frame.setFrameShadow(QFrame.Raised)
    self.verticalLayout_2 = QVBoxLayout(self.frame)
    self.verticalLayout_2.setObjectName(u"verticalLayout_2")

    self.horizontalLayout_2 = QHBoxLayout()
    self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
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

    self.name_lineEdit = QLineEdit(self.frame)
    self.name_lineEdit.setObjectName(u"name_lineEdit")
    sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
    sizePolicy1.setHorizontalStretch(0)
    sizePolicy1.setVerticalStretch(0)
    sizePolicy1.setHeightForWidth(
      self.name_lineEdit.sizePolicy().hasHeightForWidth())
    self.name_lineEdit.setSizePolicy(sizePolicy1)
    self.name_lineEdit.setMaximumSize(QSize(16777215, 30))
    if self._category is not None:
      self.name_lineEdit.setText(self._category[1])

    self.horizontalLayout_2.addWidget(self.name_lineEdit)

    self.horizontalSpacer_2 = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

    self.verticalLayout_2.addLayout(self.horizontalLayout_2)

    self.horizontalLayout_4 = QHBoxLayout()
    self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
    self.parentLabel = QLabel(self.frame)
    self.parentLabel.setObjectName(u"parentLabel")

    self.horizontalLayout_4.addWidget(self.parentLabel)

    # Display all categories except self and Uncategorized in ComboBox
    self.parent_comboBox = QComboBox(self.frame)
    categories = self._category_manager.get_all_categories()
    uncategorized_id = self._category_manager.get_category_id_from_name(
      "Uncategorized")
    self.parent_comboBox.addItem(f"None")
    if self._category is not None:
      cat_id = self._category[0]
    else:
      cat_id = None
    for category in categories:
      if category[0] != cat_id and category[0] != uncategorized_id:
        self.parent_comboBox.addItem(f"{category[1]}")

    parent_category = self._category_manager.get_category_by_id(
        self._category[-2]) if self._category is not None else None

    if parent_category:
      index = self.parent_comboBox.findText(
        parent_category[1], Qt.MatchFixedString)
      if index >= 0:
        self.parent_comboBox.setCurrentIndex(index)
    self.parent_comboBox.setObjectName(u"parent_comboBox")

    self.horizontalLayout_4.addWidget(self.parent_comboBox)

    self.horizontalSpacer_3 = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.horizontalLayout_4.addItem(self.horizontalSpacer_3)

    self.verticalLayout_2.addLayout(self.horizontalLayout_4)

    self.horizontalLayout = QHBoxLayout()
    self.horizontalLayout.setObjectName(u"horizontalLayout")
    self.colorLabel = QLabel(self.frame)
    self.colorLabel.setObjectName(u"colorLabel")

    self.horizontalLayout.addWidget(self.colorLabel)

    self.selectColor_pushButton = QPushButton(self.frame)
    self.selectColor_pushButton.setObjectName(u"selectColor_pushButton")
    sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    sizePolicy2.setHorizontalStretch(0)
    sizePolicy2.setVerticalStretch(0)
    sizePolicy2.setHeightForWidth(
      self.selectColor_pushButton.sizePolicy().hasHeightForWidth())
    self.selectColor_pushButton.setSizePolicy(sizePolicy2)
    self.selectColor_pushButton.setMinimumSize(QSize(20, 0))
    self.selectColor_pushButton.setMaximumSize(QSize(40, 20))
    self.selectColor_pushButton.setBaseSize(QSize(40, 20))

    # Set button color from category or parent if empty
    if self._category is not None:
      color = get_category_color(self._category[0])
      self.selectColor_pushButton.setStyleSheet(
          f"background-color: {color};")
    self.selectColor_pushButton.clicked.connect(self.show_color_picker)

    self.horizontalLayout.addWidget(self.selectColor_pushButton)

    self.horizontalSpacer = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.horizontalLayout.addItem(self.horizontalSpacer)

    self.verticalLayout_2.addLayout(self.horizontalLayout)

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

    # Add category keywords to grid
    self.addKeyword_pushButton = QPushButton()  # dummy
    if self._keywords:
      for keyword in self._keywords:
        self.add_keyword(keyword)
    self.setup_keyword_grid()

    self.horizontalLayout_5.addLayout(self.keywords_gridLayout)

    self.horizontalSpacer_5 = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.horizontalLayout_5.addItem(self.horizontalSpacer_5)

    self.verticalLayout_3.addLayout(self.horizontalLayout_5)

    self.verticalSpacer_2 = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    self.verticalLayout_3.addItem(self.verticalSpacer_2)

    self.noteLabel = QLabel(self.frame_2)
    self.noteLabel.setObjectName(u"noteLabel")

    self.verticalLayout_3.addWidget(self.noteLabel)

    self.verticalLayout_2.addWidget(self.frame_2)

    self.verticalSpacer = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    self.verticalLayout_2.addItem(self.verticalSpacer)

    if self._category:
      if self._category[1] != 'Uncategorized' and self._category[1] != 'AFK':
        self.deleteButton = QPushButton(self.frame)
        self.deleteButton.setObjectName(u"deleteButton")
        self.deleteButton.setStyleSheet(u"background-color: red")

        self.deleteButton.clicked.connect(self.delete_category)

        self.verticalLayout_2.addWidget(self.deleteButton)

    self.verticalLayout.addWidget(self.frame)

    self.buttonBox = QDialogButtonBox(Dialog)
    self.buttonBox.setObjectName(u"buttonBox")
    self.buttonBox.setOrientation(Qt.Horizontal)
    self.buttonBox.setStandardButtons(
      QDialogButtonBox.Cancel | QDialogButtonBox.Save)

    self.verticalLayout.addWidget(self.buttonBox)

    self.retranslateUi(Dialog)
    self.buttonBox.accepted.connect(Dialog.accept)
    self.buttonBox.rejected.connect(Dialog.reject)

    QMetaObject.connectSlotsByName(Dialog)
  # setupUi

  def retranslateUi(self, Dialog):
    Dialog.setWindowTitle(
      QCoreApplication.translate("Dialog", u"Dialog", None))
    if self._category:
      self.label.setText(QCoreApplication.translate(
        "Dialog", u"Edit Category", None))
    else:
      self.label.setText(QCoreApplication.translate(
        "Dialog", u"Add a Category", None))
    self.nameLabel.setText(QCoreApplication.translate("Dialog", u"Name", None))
    self.parentLabel.setText(QCoreApplication.translate(
      "Dialog", u"Parent category", None))

    self.colorLabel.setText(
      QCoreApplication.translate("Dialog", u"Color", None))
    self.selectColor_pushButton.setText("")
    self.keywordsLabel.setText(
      QCoreApplication.translate("Dialog", u"Keywords", None))
    self.addKeyword_pushButton.setText(
      QCoreApplication.translate("Dialog", u"+", None))
    self.noteLabel.setText(QCoreApplication.translate(
      "Dialog", u"Note: Click on keyword to edit, right-click on keyword to remove it", None))
    if self._category is not None and self._category[1] != 'Uncategorized' and self._category[1] != 'AFK':
      self.deleteButton.setText(QCoreApplication.translate(
        "Dialog", u"Delete category", None))
  # retranslateUi
