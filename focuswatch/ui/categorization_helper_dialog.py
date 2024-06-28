
from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFrame,
                               QGroupBox, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QSizePolicy, QSpacerItem,
                               QVBoxLayout, QWidget)

from focuswatch.ui.category_dialog import CategoryDialog


class CategorizationHelperDialog(QDialog):
  def __init__(self, parent):
    super().__init__(parent)
    self.setupUi(self)

  def setupUi(self, Dialog):
    if not Dialog.objectName():
      Dialog.setObjectName(u"Dialog")
    Dialog.resize(710, 394)
    self.verticalLayout = QVBoxLayout(Dialog)
    self.verticalLayout.setObjectName(u"verticalLayout")
    self.frame = QFrame(Dialog)
    self.frame.setObjectName(u"frame")
    self.frame.setFrameShape(QFrame.Shape.NoFrame)
    self.frame.setFrameShadow(QFrame.Shadow.Raised)
    self.verticalLayout_2 = QVBoxLayout(self.frame)
    self.verticalLayout_2.setObjectName(u"verticalLayout_2")
    self.applications_groupBox = QGroupBox(self.frame)
    self.applications_groupBox.setObjectName(u"applications_groupBox")
    font = QFont()
    font.setPointSize(10)
    self.applications_groupBox.setFont(font)
    self.applications_groupBox.setAutoFillBackground(True)
    self.applications_groupBox.setFlat(False)
    self.verticalLayout_3 = QVBoxLayout(self.applications_groupBox)
    self.verticalLayout_3.setObjectName(u"verticalLayout_3")
    self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
    self.applications_scrollArea = QScrollArea(self.applications_groupBox)
    self.applications_scrollArea.setObjectName(u"applications_scrollArea")
    self.applications_scrollArea.setFrameShape(QFrame.Shape.NoFrame)
    self.applications_scrollArea.setWidgetResizable(True)
    self.applications_scrollAreaWidgetContents = QWidget()
    self.applications_scrollAreaWidgetContents.setObjectName(
        u"applications_scrollAreaWidgetContents")
    self.applications_scrollAreaWidgetContents.setGeometry(
        QRect(0, 0, 668, 111))
    self.verticalLayout_4 = QVBoxLayout(
        self.applications_scrollAreaWidgetContents)
    self.verticalLayout_4.setObjectName(u"verticalLayout_4")
    self.applications_verticalLayout = QVBoxLayout()
    self.applications_verticalLayout.setObjectName(
        u"applications_verticalLayout")
    self.applications_verticalLayout.setContentsMargins(-1, -1, -1, 0)
    self.applications_horizontalLayout = QHBoxLayout()
    self.applications_horizontalLayout.setObjectName(
        u"applications_horizontalLayout")
    self.applications_name_label = QLabel(
        self.applications_scrollAreaWidgetContents)
    self.applications_name_label.setObjectName(u"applications_name_label")

    self.applications_horizontalLayout.addWidget(
        self.applications_name_label)

    self.applications_time_label = QLabel(
        self.applications_scrollAreaWidgetContents)
    self.applications_time_label.setObjectName(u"applications_time_label")

    self.applications_horizontalLayout.addWidget(
        self.applications_time_label)

    self.applications_comboBox = QComboBox(
        self.applications_scrollAreaWidgetContents)
    self.applications_comboBox.setObjectName(u"applications_comboBox")

    self.applications_horizontalLayout.addWidget(
        self.applications_comboBox)

    self.applications_new_category = QPushButton(
        self.applications_scrollAreaWidgetContents)
    self.applications_new_category.setObjectName(
        u"applications_new_category")

    self.applications_horizontalLayout.addWidget(
        self.applications_new_category)

    self.applications_verticalLayout.addLayout(
        self.applications_horizontalLayout)

    self.line = QFrame(self.applications_scrollAreaWidgetContents)
    self.line.setObjectName(u"line")
    self.line.setFrameShape(QFrame.Shape.HLine)
    self.line.setFrameShadow(QFrame.Shadow.Sunken)

    self.applications_verticalLayout.addWidget(self.line)

    self.verticalSpacer_2 = QSpacerItem(
        20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

    self.applications_verticalLayout.addItem(self.verticalSpacer_2)

    self.verticalLayout_4.addLayout(self.applications_verticalLayout)

    self.applications_scrollArea.setWidget(
        self.applications_scrollAreaWidgetContents)

    self.verticalLayout_3.addWidget(self.applications_scrollArea)

    self.verticalLayout_2.addWidget(self.applications_groupBox)

    self.titles_groupBox = QGroupBox(self.frame)
    self.titles_groupBox.setObjectName(u"titles_groupBox")
    self.titles_groupBox.setFont(font)
    self.verticalLayout_5 = QVBoxLayout(self.titles_groupBox)
    self.verticalLayout_5.setObjectName(u"verticalLayout_5")
    self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
    self.titles_scrollArea = QScrollArea(self.titles_groupBox)
    self.titles_scrollArea.setObjectName(u"titles_scrollArea")
    self.titles_scrollArea.setFrameShape(QFrame.Shape.NoFrame)
    self.titles_scrollArea.setWidgetResizable(True)
    self.titles_scrollAreaWidgetContents = QWidget()
    self.titles_scrollAreaWidgetContents.setObjectName(
        u"titles_scrollAreaWidgetContents")
    self.titles_scrollAreaWidgetContents.setGeometry(QRect(0, 0, 668, 110))
    self.verticalLayout_6 = QVBoxLayout(
        self.titles_scrollAreaWidgetContents)
    self.verticalLayout_6.setObjectName(u"verticalLayout_6")
    self.titles_verticalLayout = QVBoxLayout()
    self.titles_verticalLayout.setObjectName(u"titles_verticalLayout")
    self.titles_verticalLayout.setContentsMargins(-1, -1, -1, 0)
    self.titles_horizontalLayout = QHBoxLayout()
    self.titles_horizontalLayout.setObjectName(u"titles_horizontalLayout")
    self.titles_name_label = QLabel(self.titles_scrollAreaWidgetContents)
    self.titles_name_label.setObjectName(u"titles_name_label")

    self.titles_horizontalLayout.addWidget(self.titles_name_label)

    self.titles_time_label = QLabel(self.titles_scrollAreaWidgetContents)
    self.titles_time_label.setObjectName(u"titles_time_label")

    self.titles_horizontalLayout.addWidget(self.titles_time_label)

    self.titles_comboBox = QComboBox(self.titles_scrollAreaWidgetContents)
    self.titles_comboBox.setObjectName(u"titles_comboBox")

    self.titles_horizontalLayout.addWidget(self.titles_comboBox)

    self.titles_new_category = QPushButton(
        self.titles_scrollAreaWidgetContents)
    self.titles_new_category.setObjectName(u"titles_new_category")

    self.titles_horizontalLayout.addWidget(self.titles_new_category)

    self.titles_verticalLayout.addLayout(self.titles_horizontalLayout)

    self.line_2 = QFrame(self.titles_scrollAreaWidgetContents)
    self.line_2.setObjectName(u"line_2")
    self.line_2.setFrameShape(QFrame.Shape.HLine)
    self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

    self.titles_verticalLayout.addWidget(self.line_2)

    self.verticalSpacer_3 = QSpacerItem(
        20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

    self.titles_verticalLayout.addItem(self.verticalSpacer_3)

    self.verticalLayout_6.addLayout(self.titles_verticalLayout)

    self.titles_scrollArea.setWidget(self.titles_scrollAreaWidgetContents)

    self.verticalLayout_5.addWidget(self.titles_scrollArea)

    self.verticalLayout_2.addWidget(self.titles_groupBox)

    self.verticalLayout.addWidget(self.frame)

    self.verticalSpacer = QSpacerItem(
        20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

    self.verticalLayout.addItem(self.verticalSpacer)

    self.buttonBox = QDialogButtonBox(Dialog)
    self.buttonBox.setObjectName(u"buttonBox")
    self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
    self.buttonBox.setStandardButtons(
        QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel)
    self.buttonBox.setCenterButtons(False)

    self.verticalLayout.addWidget(self.buttonBox)

    self.retranslateUi(Dialog)
    self.buttonBox.accepted.connect(Dialog.accept)
    self.buttonBox.rejected.connect(Dialog.reject)

    QMetaObject.connectSlotsByName(Dialog)
# setupUi

  def retranslateUi(self, Dialog):
    Dialog.setWindowTitle(
        QCoreApplication.translate("Dialog", u"Dialog", None))
    self.applications_groupBox.setTitle(QCoreApplication.translate(
        "Dialog", u"Top uncategorized applications", None))
    self.applications_name_label.setText(
        QCoreApplication.translate("Dialog", u"TextLabel", None))
    self.applications_time_label.setText(
        QCoreApplication.translate("Dialog", u"TextLabel", None))
    self.applications_new_category.setText(
        QCoreApplication.translate("Dialog", u"Create new category", None))
    self.titles_groupBox.setTitle(QCoreApplication.translate(
        "Dialog", u"Top uncategorized window titles", None))
    self.titles_name_label.setText(
        QCoreApplication.translate("Dialog", u"TextLabel", None))
    self.titles_time_label.setText(
        QCoreApplication.translate("Dialog", u"TextLabel", None))
    self.titles_new_category.setText(QCoreApplication.translate(
        "Dialog", u"Create new category", None))
# retranslateUi
