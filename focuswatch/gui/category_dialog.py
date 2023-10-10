
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect,
                            QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
                           QFont, QFontDatabase, QGradient, QIcon,
                           QImage, QKeySequence, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
                               QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QPushButton, QSizePolicy, QSpacerItem,
                               QTextEdit, QVBoxLayout, QWidget, QColorDialog)

from focuswatch.database import DatabaseManager
from focuswatch.gui.keyword_dialog import KeywordDialog


class CategoryDialog(QDialog):
  def __init__(self, parent=None, category=None, keywords=None):
    super().__init__(parent)
    self._database = DatabaseManager()
    self._category = category
    self._keywords = keywords
    self.i, self.j = 0, 0

    self.del_keywords = []
    self.new_keywords = []
    self.color = None

    self.setupUi(self)

  def show_color_picker(self):
    color_dialog = QColorDialog()
    color = color_dialog.getColor()

    if color.isValid():
      self.color = color.name()
      self.selectColor_pushButton.setStyleSheet(
        f"background-color: {self.color};")

  def delete_keyword(self):
    sender_name = self.sender().objectName()
    keyword_id = sender_name.split(sep='_')[-1]
    self.sender().deleteLater()

    for i, keyword in enumerate(self._keywords):
      if keyword[0] == int(keyword_id):
        self.del_keywords.append(keyword)
        del self._keywords[i]

    for i, keyword in enumerate(self.new_keywords):
      if keyword[0] == int(keyword_id):
        del self.new_keywords[i]

    self.setup_keyword_grid()

  def add_keyword_to_grid(self, keyword):
    keywordButton = QPushButton(self.frame_2)
    keywordButton.setObjectName(f"keywordButton_{keyword[0]}")
    keywordButton.clicked.connect(self.delete_keyword)
    keywordButton.setText(keyword[1])
    self.keywords_gridLayout.addWidget(keywordButton, self.j, self.i, 1, 1)
    self.i += 1
    if self.i == 4:
      self.i = 0
      self.j += 1

  def setup_keyword_grid(self):
    self.i = 0
    self.j = 0
    # Clear layout
    for i in reversed(range(self.keywords_gridLayout.count())):
      widget = self.keywords_gridLayout.itemAt(i).widget()
      if widget is not None:
        widget.deleteLater()

    # Add keywords to grid
    if len(self._keywords) > 0:
      for keyword in self._keywords:
        self.add_keyword_to_grid(keyword)

    for keyword in self.new_keywords:
      self.add_keyword_to_grid(keyword)

    # Add '+' button
    self.addKeyword_pushButton = QPushButton(self.frame_2)
    self.addKeyword_pushButton.setObjectName(u"addKeyword_pushButton")
    self.addKeyword_pushButton.setText('+')
    self.addKeyword_pushButton.clicked.connect(self.add_keyword)

    self.keywords_gridLayout.addWidget(
      self.addKeyword_pushButton, self.j + 1, 0, 4, 4)

  def add_keyword(self):
    keyword_dialog = KeywordDialog(self, self._category)
    result = keyword_dialog.exec_()

    if result:
      keyword_name = keyword_dialog.nameEdit.text()
      if len(self.new_keywords) == 0:
        last_new_id = 0
      else:
        last_new_id = int(self.new_keywords[-1][0]) + 1
      if len(self._keywords) == 0:
        last_old_id = 0
      else:
        last_old_id = int(self._keywords[-1][0]) + 1
      key_id = last_new_id if last_new_id > last_old_id else last_old_id
      self.new_keywords.append([key_id, keyword_name])
      self.setup_keyword_grid()

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

    self.name_textEdit = QTextEdit(self.frame)
    self.name_textEdit.setObjectName(u"name_textEdit")
    sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
    sizePolicy1.setHorizontalStretch(0)
    sizePolicy1.setVerticalStretch(0)
    sizePolicy1.setHeightForWidth(
      self.name_textEdit.sizePolicy().hasHeightForWidth())
    self.name_textEdit.setSizePolicy(sizePolicy1)
    self.name_textEdit.setMaximumSize(QSize(16777215, 30))
    if self._category is not None:
      self.name_textEdit.setText(self._category[1])

    self.horizontalLayout_2.addWidget(self.name_textEdit)

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
    categories = self._database.get_all_categories()
    uncategorized_id = self._database.get_category_id_from_name(
      "Uncategorized")
    self.parent_comboBox.addItem(f"None")
    if self._category is not None:
      cat_id = self._category[0]
    else:
      cat_id = None
    for category in categories:
      if category[0] != cat_id and category[0] != uncategorized_id:
        self.parent_comboBox.addItem(f"{category[1]}")

    parent_category = self._database.get_category_by_id(
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
      color = self._category[-1]
      while color == None:
        if self._category[-2]:  # parent_category
          parent_category = self._database.get_category_by_id(
            self._category[-2])
          color = parent_category[-1]
          # text += parent_category[1] + " > "
        else:
          color = "#FFFFFF"

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

    # Add categorie's keywords
    self.addKeyword_pushButton = QPushButton()  # dummy
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
    self.label.setText(QCoreApplication.translate(
      "Dialog", u"Edit Category", None))
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
      "Dialog", u"Note: Click on keyword to remove it", None))
  # retranslateUi
