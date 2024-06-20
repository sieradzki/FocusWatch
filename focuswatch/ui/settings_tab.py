""" Settings tab for the FocusWatch Ui. """
from collections import defaultdict

from PySide6.QtCore import QCoreApplication, QRect, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLayout,
                               QPushButton, QScrollArea, QSizePolicy,
                               QSpacerItem, QVBoxLayout, QWidget, QCheckBox, QDoubleSpinBox, QSpinBox, QTabWidget, QDialogButtonBox)

from focuswatch.ui.category_dialog import CategoryDialog
from focuswatch.ui.utils import get_category_color, get_contrasting_text_color


class SettingsTab(QWidget):
  def __init__(self, parent=None):
    super().__init__(parent)
    self._parent = parent
    self.setupUi()

  def setupUi(self):
    self.settings_tab = QWidget()
    self.settings_tab.setObjectName(u"settings_tab")
    self.verticalLayout_9 = QVBoxLayout(self.settings_tab)
    self.verticalLayout_9.setObjectName(u"verticalLayout_9")
    self.tab_settings_watcher = QTabWidget(self.settings_tab)
    self.tab_settings_watcher.setObjectName(u"tab_settings_watcher")
    self.tab = QWidget()
    self.tab.setObjectName(u"tab")
    self.verticalLayout_10 = QVBoxLayout(self.tab)
    self.verticalLayout_10.setObjectName(u"verticalLayout_10")
    self.watcher_tab_layout = QVBoxLayout()
    self.watcher_tab_layout.setObjectName(u"watcher_tab_layout")
    self.watcher_tab_layout.setContentsMargins(2, -1, -1, -1)
    self.watch_label = QLabel(self.tab)
    self.watch_label.setObjectName(u"watch_label")
    font2 = QFont()
    font2.setBold(False)
    self.watch_label.setFont(font2)

    self.watcher_tab_layout.addWidget(self.watch_label)

    self.watch_interval = QDoubleSpinBox(self.tab)
    self.watch_interval.setObjectName(u"watch_interval")
    self.watch_interval.setDecimals(1)
    self.watch_interval.setMinimum(1.000000000000000)
    self.watch_interval.setMaximum(60.000000000000000)
    self.watch_interval.setSingleStep(0.500000000000000)

    self.watcher_tab_layout.addWidget(self.watch_interval)

    self.watch_afk = QCheckBox(self.tab)
    self.watch_afk.setObjectName(u"watch_afk")

    self.watcher_tab_layout.addWidget(self.watch_afk)

    self.afk_label = QLabel(self.tab)
    self.afk_label.setObjectName(u"afk_label")
    self.afk_label.setEnabled(False)

    self.watcher_tab_layout.addWidget(self.afk_label)

    self.afk_timeout = QSpinBox(self.tab)
    self.afk_timeout.setObjectName(u"afk_timeout")
    self.afk_timeout.setEnabled(False)
    self.afk_timeout.setMinimum(1)
    self.afk_timeout.setValue(5)

    self.watcher_tab_layout.addWidget(self.afk_timeout)

    self.label_2 = QLabel(self.tab)
    self.label_2.setObjectName(u"label_2")

    self.watcher_tab_layout.addWidget(self.label_2)

    self.verticalSpacer_3 = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    self.watcher_tab_layout.addItem(self.verticalSpacer_3)

    self.verticalLayout_10.addLayout(self.watcher_tab_layout)

    self.tab_settings_watcher.addTab(self.tab, "")
    self.tab_settings_startup = QWidget()
    self.tab_settings_startup.setObjectName(u"tab_settings_startup")
    self.horizontalLayout_4 = QHBoxLayout(self.tab_settings_startup)
    self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
    self.label = QLabel(self.tab_settings_startup)
    self.label.setObjectName(u"label")
    font3 = QFont()
    font3.setPointSize(16)
    self.label.setFont(font3)
    self.label.setAlignment(Qt.AlignCenter)

    self.horizontalLayout_4.addWidget(self.label)

    self.tab_settings_watcher.addTab(self.tab_settings_startup, "")

    self.verticalLayout_9.addWidget(self.tab_settings_watcher)

    self.buttonBox = QDialogButtonBox(self.settings_tab)
    self.buttonBox.setObjectName(u"buttonBox")
    self.buttonBox.setStandardButtons(
      QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

    self.verticalLayout_9.addWidget(self.buttonBox)

    self.retranslateUi()
    return self.settings_tab

  def retranslateUi(self):
    self.watch_label.setText(QCoreApplication.translate(
      "Dashboard", u"Watch interval", None))
    self.watch_interval.setSuffix(
      QCoreApplication.translate("Dashboard", u" s", None))
    self.watch_afk.setText(QCoreApplication.translate(
      "Dashboard", u"Watch afk", None))
    self.afk_label.setText(QCoreApplication.translate(
      "Dashboard", u"AFK timeout", None))
    self.afk_timeout.setSuffix(
      QCoreApplication.translate("Dashboard", u" m", None))
    self.afk_timeout.setPrefix("")
    self.label_2.setText(QCoreApplication.translate(
      "Dashboard", u"Note: the changes will be applied on next restart", None))

    self.tab_settings_watcher.setTabText(self.tab_settings_watcher.indexOf(
      self.tab), QCoreApplication.translate("Dashboard", u"Watcher", None))
    self.label.setText(QCoreApplication.translate(
      "Dashboard", u"Not implemented", None))
    self.tab_settings_watcher.setTabText(self.tab_settings_watcher.indexOf(
      self.tab_settings_startup), QCoreApplication.translate("Dashboard", u"Startup", None))
    
