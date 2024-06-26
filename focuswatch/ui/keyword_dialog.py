from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect, QSize, Qt,
                            QTime, QUrl)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
                           QFontDatabase, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette,
                           QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox,
                               QDialog, QDialogButtonBox, QFrame, QHBoxLayout,
                               QLabel, QLineEdit, QSizePolicy, QSpacerItem,
                               QTextEdit, QVBoxLayout, QWidget)

from typing import Optional


class KeywordDialog(QDialog):
  def __init__(self, parent, keyword_manager, keyword_id: Optional[int] = None, keyword: Optional[list]=None):
    super().__init__(parent)
    self._keyword_manager = keyword_manager
    if keyword_id:
      self._keyword = self._keyword_manager.get_keyword(keyword_id)
    else:
      self._keyword = keyword
    self.setupUi(self)

  def setupUi(self, Dialog):
    if not Dialog.objectName():
      Dialog.setObjectName(u"Dialog")
    Dialog.resize(395, 142)
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
    self.horizontalLayout = QHBoxLayout()
    self.horizontalLayout.setObjectName(u"horizontalLayout")
    self.nameLabel = QLabel(self.frame)
    self.nameLabel.setObjectName(u"nameLabel")

    self.horizontalLayout.addWidget(self.nameLabel)

    self.nameEdit = QLineEdit(self.frame)
    self.nameEdit.setObjectName(u"nameEdit")
    self.nameEdit.setMaximumSize(QSize(16777215, 30))

    # Set the text of the QLineEdit to the keyword name
    if self._keyword:
      self.nameEdit.setText(self._keyword[1])

    self.horizontalLayout.addWidget(self.nameEdit)

    self.verticalLayout_2.addLayout(self.horizontalLayout)

    self.horizontalLayout2 = QHBoxLayout()
    self.horizontalLayout2.setObjectName(u"horizontalLayout2")

    self.match_case_label = QLabel(self.frame)
    self.match_case_label.setObjectName(u"match_case_label")
    self.horizontalLayout2.addWidget(self.match_case_label)

    self.match_case_checkbox = QCheckBox(self.frame)
    self.match_case_checkbox.setObjectName(u"match_case_checkbox")
    # Add spacer so that the checkbox is next to the label
    self.horizontalLayout2.addWidget(self.match_case_checkbox)

    # Set the state of the checkbox to the match_case value
    if self._keyword:
      self.match_case_checkbox.setChecked(self._keyword[3])

    spacerItem = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.horizontalLayout2.addItem(spacerItem)

    self.verticalLayout_2.addLayout(self.horizontalLayout2)

    self.verticalLayout.addWidget(self.frame)

    self.buttonBox = QDialogButtonBox(Dialog)
    self.buttonBox.setObjectName(u"buttonBox")
    self.buttonBox.setOrientation(Qt.Horizontal)
    self.buttonBox.setStandardButtons(
      QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

    self.verticalLayout.addWidget(self.buttonBox)

    self.retranslateUi(Dialog)
    self.buttonBox.accepted.connect(Dialog.accept)
    self.buttonBox.rejected.connect(Dialog.reject)

    QMetaObject.connectSlotsByName(Dialog)
  # setupUi

  def retranslateUi(self, Dialog):
    Dialog.setWindowTitle(
      QCoreApplication.translate("Dialog", u"Dialog", None))
    if self._keyword:
      self.label.setText(QCoreApplication.translate(
        "Dialog", u"Edit keyword", None))
    else:
      self.label.setText(QCoreApplication.translate(
        "Dialog", u"Add a keyword", None))
    self.nameLabel.setText(QCoreApplication.translate("Dialog", u"Name", None))
    self.match_case_label.setText(
      QCoreApplication.translate("Dialog", u"Match case", None))
  # retranslateUi
