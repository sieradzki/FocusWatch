from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect,
                            QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
                           QFont, QFontDatabase, QGradient, QIcon,
                           QImage, QKeySequence, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
                               QFrame, QHBoxLayout, QLabel, QSizePolicy,
                               QSpacerItem, QTextEdit, QVBoxLayout, QWidget)


class KeywordDialog(QDialog):
  def __init__(self, parent=None, category=None):
    super().__init__(parent)
    self._category = category
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

    self.nameEdit = QTextEdit(self.frame)
    self.nameEdit.setObjectName(u"nameEdit")
    self.nameEdit.setMaximumSize(QSize(16777215, 30))

    self.horizontalLayout.addWidget(self.nameEdit)

    self.verticalLayout_2.addLayout(self.horizontalLayout)

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
    self.label.setText(QCoreApplication.translate(
      "Dialog", u"Add a keyword", None))
    self.nameLabel.setText(QCoreApplication.translate("Dialog", u"Name", None))
  # retranslateUi
