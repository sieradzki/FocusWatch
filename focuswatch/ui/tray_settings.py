from PySide6.QtCore import QCoreApplication, QMetaObject
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QDialogButtonBox, QDoubleSpinBox,
                               QLabel, QSizePolicy, QSpacerItem, QSpinBox,
                               QTabWidget, QVBoxLayout, QWidget)

from focuswatch.config import Config


class TraySettings(QWidget):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.config = Config()
    self.setupUi(self)

  def setupUi(self, Settings):
    if not Settings.objectName():
      Settings.setObjectName(u"Settings")
    Settings.resize(260, 300)
    sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(Settings.sizePolicy().hasHeightForWidth())
    Settings.setSizePolicy(sizePolicy)
    self.verticalLayout_2 = QVBoxLayout(Settings)
    self.verticalLayout_2.setObjectName(u"verticalLayout_2")
    self.main_layout = QVBoxLayout()
    self.main_layout.setObjectName(u"main_layout")
    self.tabWidget = QTabWidget(Settings)
    self.tabWidget.setObjectName(u"tabWidget")
    self.tabWidget.setEnabled(True)
    self.tab_watcher = QWidget()
    self.tab_watcher.setObjectName(u"tab_watcher")
    self.verticalLayout_4 = QVBoxLayout(self.tab_watcher)
    self.verticalLayout_4.setObjectName(u"verticalLayout_4")
    self.watcher_tab_layout = QVBoxLayout()
    self.watcher_tab_layout.setObjectName(u"watcher_tab_layout")
    self.watcher_tab_layout.setContentsMargins(2, -1, -1, -1)
    self.watch_label = QLabel(self.tab_watcher)
    self.watch_label.setObjectName(u"watch_label")
    font = QFont()
    font.setBold(False)
    self.watch_label.setFont(font)

    self.watcher_tab_layout.addWidget(self.watch_label)

    self.watch_interval = QDoubleSpinBox(self.tab_watcher)
    self.watch_interval.setObjectName(u"watch_interval")

    self.watch_interval.setValue(
      float(self.config.get_value('General', 'watch_interval')))
    self.watch_interval.setDecimals(1.0)
    self.watch_interval.setMinimum(1.000000000000000)
    self.watch_interval.setMaximum(60.000000000000000)
    self.watch_interval.setSingleStep(0.500000000000000)

    self.watcher_tab_layout.addWidget(self.watch_interval)

    self.watch_afk = QCheckBox(self.tab_watcher)
    self.watch_afk.setChecked(True if (self.config.get_value(
      'General', 'watch_afk') == 'True') else False)
    self.watch_afk.setObjectName(u"watch_afk")

    self.watcher_tab_layout.addWidget(self.watch_afk)

    self.afk_label = QLabel(self.tab_watcher)
    self.afk_label.setObjectName(u"afk_label")
    self.afk_label.setEnabled(self.watch_afk.isChecked())

    self.watcher_tab_layout.addWidget(self.afk_label)

    self.afk_timeout = QSpinBox(self.tab_watcher)
    self.afk_timeout.setObjectName(u"afk_timeout")
    self.afk_timeout.setValue(
      float(self.config.get_value('General', 'afk_timeout'))
    )
    self.afk_timeout.setMinimum(1)
    self.afk_timeout.setEnabled(self.watch_afk.isChecked())

    self.watch_afk.toggled.connect(self.afk_timeout.setEnabled)
    self.watch_afk.toggled.connect(self.afk_label.setEnabled)

    self.watcher_tab_layout.addWidget(self.afk_timeout)

    self.note_label = QLabel(self.tab_watcher)
    self.note_label.setObjectName(u"label_2")
    self.watcher_tab_layout.addWidget(self.note_label)

    self.verticalSpacer = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    self.watcher_tab_layout.addItem(self.verticalSpacer)

    self.verticalLayout_4.addLayout(self.watcher_tab_layout)
    self.dialog_buttons = QDialogButtonBox(self.tab_watcher)
    self.dialog_buttons.setObjectName(u"dialog_buttons")
    self.dialog_buttons.setStandardButtons(
      QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    self.dialog_buttons.setCenterButtons(False)

    self.dialog_buttons.accepted.connect(self.accept)
    self.dialog_buttons.rejected.connect(Settings.close)

    self.verticalLayout_4.addWidget(self.dialog_buttons)

    self.tabWidget.addTab(self.tab_watcher, "")
    self.tab_focused_mode = QWidget()
    self.tab_focused_mode.setObjectName(u"tab_focused_mode")
    # self.tabWidget.addTab(self.tab_focused_mode, "")

    self.main_layout.addWidget(self.tabWidget)

    self.verticalLayout_2.addLayout(self.main_layout)

    self.retranslateUi(Settings)

    self.tabWidget.setCurrentIndex(0)

    QMetaObject.connectSlotsByName(Settings)
  # setupUi

  def accept(self):
    watch_interval = self.watch_interval.value()
    watch_afk = self.watch_afk.isChecked()
    afk_timeout = self.afk_timeout.value()

    # TODO logging
    self.config.update_value(
      section='General', option='watch_interval', value=watch_interval)
    self.config.update_value(
      section='General', option='watch_afk', value=watch_afk
    )
    self.config.update_value(
      section='General', option='afk_timeout', value=afk_timeout
    )
    self.close()

  def retranslateUi(self, Settings):
    Settings.setWindowTitle(
      QCoreApplication.translate("Settings", u"Settings", None))
    self.watch_label.setText(QCoreApplication.translate(
      "Settings", u"Watch interval", None))
    self.watch_interval.setSuffix(
      QCoreApplication.translate("Settings", u" s", None))
    self.watch_afk.setText(QCoreApplication.translate(
      "Settings", u"Watch afk", None))
    self.afk_label.setText(QCoreApplication.translate(
      "Settings", u"AFK timeout", None))
    self.afk_timeout.setSuffix(
      QCoreApplication.translate("Settings", u" m", None))
    self.afk_timeout.setPrefix("")
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.tab_watcher), QCoreApplication.translate("Settings", u"Watcher", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.tab_focused_mode), QCoreApplication.translate("Settings", u"Focused mode", None))
    self.note_label.setText(QCoreApplication.translate(
      "Dashboard", u"Note: the changes will be applied on next restart", None))
  # retranslateUi
