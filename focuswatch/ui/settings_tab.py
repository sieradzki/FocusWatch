from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QDialogButtonBox, QDoubleSpinBox,
                               QGroupBox, QHBoxLayout, QLabel, QSizePolicy,
                               QSpacerItem, QSpinBox, QTabWidget, QVBoxLayout,
                               QWidget)

from focuswatch.autostart_manager import (add_to_autostart, is_frozen,
                                          is_in_autostart, remove_from_autostart)
from focuswatch.config import Config


class SettingsTab(QWidget):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.config = Config()
    self.setupUi()

  def setupUi(self):
    self.settings_tab = QWidget()
    self.settings_tab.setObjectName(u"settings_tab")
    self.verticalLayout_9 = QVBoxLayout(self.settings_tab)
    self.verticalLayout_9.setObjectName(u"verticalLayout_9")

    self.tab_settings_watcher = QTabWidget(self.settings_tab)
    self.tab_settings_watcher.setObjectName(u"tab_settings_watcher")

    # General tab
    self.general_tab = QWidget()
    self.general_tab.setObjectName(u"general_tab")
    self.verticalLayout_general = QVBoxLayout(self.general_tab)
    self.verticalLayout_general.setObjectName(u"verticalLayout_general")

    # Autostart groupbox
    self.autostart_groupbox = QGroupBox(self.general_tab)
    self.autostart_groupbox.setObjectName(u"autostart_groupbox")
    self.autostart_groupbox.setTitle(QCoreApplication.translate(
        "Dashboard", u"Autostart", None))
    self.verticalLayout_autostart = QVBoxLayout(self.autostart_groupbox)
    self.verticalLayout_autostart.setObjectName(
        u"verticalLayout_autostart")

    self.autostart_checkbox = QCheckBox(self.autostart_groupbox)
    self.autostart_checkbox.setObjectName(u"autostart_checkbox")
    self.autostart_checkbox.setText(QCoreApplication.translate(
        "Dashboard", u"Start FocusWatch on system startup", None))
    self.autostart_checkbox.setChecked(is_in_autostart())
    self.autostart_checkbox.setEnabled(
        is_frozen())  # Disable if not packaged
    self.verticalLayout_autostart.addWidget(self.autostart_checkbox)

    self.verticalLayout_general.addWidget(self.autostart_groupbox)

    # Add spacer at the bottom
    self.verticalLayout_general.addItem(QSpacerItem(
        20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    self.tab_settings_watcher.addTab(self.general_tab, QCoreApplication.translate(
        "Dashboard", u"General", None))

    # Watcher tab
    self.watcher_tab = QWidget()
    self.watcher_tab.setObjectName(u"watcher_tab")
    self.verticalLayout_watcher = QVBoxLayout(self.watcher_tab)
    self.verticalLayout_watcher.setObjectName(u"verticalLayout_watcher")

    self.watch_label = QLabel(self.watcher_tab)
    self.watch_label.setObjectName(u"watch_label")
    font2 = QFont()
    font2.setBold(False)
    self.watch_label.setFont(font2)
    self.watch_label.setText(QCoreApplication.translate(
        "Dashboard", u"Watch interval", None))
    self.verticalLayout_watcher.addWidget(self.watch_label)

    self.watch_interval = QDoubleSpinBox(self.watcher_tab)
    self.watch_interval.setValue(
        float(self.config.get_value('General', 'watch_interval')))
    self.watch_interval.setObjectName(u"watch_interval")
    self.watch_interval.setDecimals(1)
    self.watch_interval.setMinimum(1.0)
    self.watch_interval.setMaximum(60.0)
    self.watch_interval.setSingleStep(0.5)
    self.watch_interval.setSuffix(QCoreApplication.translate(
        "Dashboard", u" s", None))
    self.verticalLayout_watcher.addWidget(self.watch_interval)

    self.watch_afk = QCheckBox(self.watcher_tab)
    self.watch_afk.setChecked(
        self.config.get_value('General', 'watch_afk') == 'True')
    self.watch_afk.setObjectName(u"watch_afk")
    self.watch_afk.setText(QCoreApplication.translate(
        "Dashboard", u"Watch AFK", None))
    self.verticalLayout_watcher.addWidget(self.watch_afk)

    self.afk_label = QLabel(self.watcher_tab)
    self.afk_label.setObjectName(u"afk_label")
    self.afk_label.setEnabled(self.watch_afk.isChecked())
    self.afk_label.setText(QCoreApplication.translate(
        "Dashboard", u"AFK timeout", None))
    self.verticalLayout_watcher.addWidget(self.afk_label)

    self.afk_timeout = QSpinBox(self.watcher_tab)
    self.afk_timeout.setObjectName(u"afk_timeout")
    self.afk_timeout.setEnabled(self.watch_afk.isChecked())
    self.afk_timeout.setMinimum(1)
    self.afk_timeout.setMaximum(60)
    self.afk_timeout.setValue(
        float(self.config.get_value('General', 'afk_timeout')))
    self.afk_timeout.setSuffix(QCoreApplication.translate(
        "Dashboard", u" m", None))
    self.verticalLayout_watcher.addWidget(self.afk_timeout)

    self.label_note = QLabel(self.watcher_tab)
    self.label_note.setObjectName(u"label_note")
    self.label_note.setText(QCoreApplication.translate(
        "Dashboard", u"Note: Changes will apply on next restart", None))
    self.verticalLayout_watcher.addWidget(self.label_note)

    self.verticalLayout_watcher.addItem(QSpacerItem(
        20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    self.tab_settings_watcher.addTab(self.watcher_tab, QCoreApplication.translate(
        "Dashboard", u"Watcher", None))

    self.verticalLayout_9.addWidget(self.tab_settings_watcher)

    self.buttonBox = QDialogButtonBox(self.settings_tab)
    self.buttonBox.setObjectName(u"buttonBox")
    self.buttonBox.setStandardButtons(QDialogButtonBox.Apply)
    self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(
        self.apply_settings)
    self.verticalLayout_9.addWidget(self.buttonBox)

    self.retranslateUi()
    return self.settings_tab

  def retranslateUi(self):
    self.watch_label.setText(QCoreApplication.translate(
        "Dashboard", u"Watch interval", None))
    self.watch_afk.setText(QCoreApplication.translate(
        "Dashboard", u"Watch AFK", None))
    self.afk_label.setText(QCoreApplication.translate(
        "Dashboard", u"AFK timeout", None))
    self.label_note.setText(QCoreApplication.translate(
        "Dashboard", u"Note: Changes will apply on next restart", None))

  def apply_settings(self):
    watch_interval = self.watch_interval.value()
    watch_afk = self.watch_afk.isChecked()
    afk_timeout = self.afk_timeout.value()
    autostart_enabled = self.autostart_checkbox.isChecked()

    self.config.set_value(
        section='General', option='watch_interval', value=watch_interval)
    self.config.set_value(
        section='General', option='watch_afk', value=watch_afk)
    self.config.set_value(
        section='General', option='afk_timeout', value=afk_timeout)

    if autostart_enabled:
      add_to_autostart()
    else:
      remove_from_autostart()
