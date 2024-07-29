from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QDialogButtonBox, QDoubleSpinBox,
                               QGroupBox, QHBoxLayout, QLabel, QSizePolicy,
                               QSpacerItem, QSpinBox, QTabWidget, QVBoxLayout,
                               QWidget)


class SettingsView(QWidget):
  def __init__(self, viewmodel, parent=None):
    super().__init__(parent)
    self.viewmodel = viewmodel
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
    self.autostart_groupbox.setTitle(
        QCoreApplication.translate("Dashboard", u"Autostart", None))
    self.verticalLayout_autostart = QVBoxLayout(self.autostart_groupbox)
    self.verticalLayout_autostart.setObjectName(
        u"verticalLayout_autostart")

    self.autostart_checkbox = QCheckBox(self.autostart_groupbox)
    self.autostart_checkbox.setObjectName(u"autostart_checkbox")
    self.autostart_checkbox.setText(QCoreApplication.translate(
        "Dashboard", u"Start FocusWatch on system startup", None))
    self.autostart_checkbox.setChecked(self.viewmodel.autostart_enabled)
    self.autostart_checkbox.setEnabled(
        self.viewmodel.is_autostart_available())
    self.autostart_checkbox.stateChanged.connect(self.on_autostart_changed)
    self.verticalLayout_autostart.addWidget(self.autostart_checkbox)

    self.verticalLayout_general.addWidget(self.autostart_groupbox)

    # Add spacer at the bottom
    self.verticalLayout_general.addItem(QSpacerItem(
        20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    self.tab_settings_watcher.addTab(
        self.general_tab, QCoreApplication.translate("Dashboard", u"General", None))

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
    self.watch_interval.setValue(self.viewmodel.watch_interval)
    self.watch_interval.setObjectName(u"watch_interval")
    self.watch_interval.setDecimals(1)
    self.watch_interval.setMinimum(1.0)
    self.watch_interval.setMaximum(60.0)
    self.watch_interval.setSingleStep(0.5)
    self.watch_interval.setSuffix(
        QCoreApplication.translate("Dashboard", u" s", None))
    self.watch_interval.valueChanged.connect(
        self.on_watch_interval_changed)
    self.verticalLayout_watcher.addWidget(self.watch_interval)

    self.watch_afk = QCheckBox(self.watcher_tab)
    self.watch_afk.setChecked(self.viewmodel.watch_afk)
    self.watch_afk.setObjectName(u"watch_afk")
    self.watch_afk.setText(QCoreApplication.translate(
        "Dashboard", u"Watch AFK", None))
    self.watch_afk.stateChanged.connect(self.on_watch_afk_changed)
    self.verticalLayout_watcher.addWidget(self.watch_afk)

    self.afk_label = QLabel(self.watcher_tab)
    self.afk_label.setObjectName(u"afk_label")
    self.afk_label.setEnabled(self.viewmodel.watch_afk)
    self.afk_label.setText(QCoreApplication.translate(
        "Dashboard", u"AFK timeout", None))
    self.verticalLayout_watcher.addWidget(self.afk_label)

    self.afk_timeout = QSpinBox(self.watcher_tab)
    self.afk_timeout.setObjectName(u"afk_timeout")
    self.afk_timeout.setEnabled(self.viewmodel.watch_afk)
    self.afk_timeout.setMinimum(1)
    self.afk_timeout.setMaximum(60)
    self.afk_timeout.setValue(self.viewmodel.afk_timeout)
    self.afk_timeout.setSuffix(
        QCoreApplication.translate("Dashboard", u" m", None))
    self.afk_timeout.valueChanged.connect(self.on_afk_timeout_changed)
    self.verticalLayout_watcher.addWidget(self.afk_timeout)

    self.label_note = QLabel(self.watcher_tab)
    self.label_note.setObjectName(u"label_note")
    self.label_note.setText(QCoreApplication.translate(
        "Dashboard", u"Note: Changes will apply on next restart", None))
    self.verticalLayout_watcher.addWidget(self.label_note)

    self.verticalLayout_watcher.addItem(QSpacerItem(
        20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    self.tab_settings_watcher.addTab(
        self.watcher_tab, QCoreApplication.translate("Dashboard", u"Watcher", None))

    self.verticalLayout_9.addWidget(self.tab_settings_watcher)

    self.buttonBox = QDialogButtonBox(self.settings_tab)
    self.buttonBox.setObjectName(u"buttonBox")
    self.buttonBox.setStandardButtons(QDialogButtonBox.Apply)
    self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(
        self.apply_settings)
    self.verticalLayout_9.addWidget(self.buttonBox)

    # Connect ViewModel signals
    self.viewmodel.property_changed.connect(
        self.on_viewmodel_property_changed)

    return self.settings_tab

  def on_autostart_changed(self, state):
    self.viewmodel.autostart_enabled = state == Qt.Checked

  def on_watch_interval_changed(self, value):
    self.viewmodel.watch_interval = value

  def on_watch_afk_changed(self, state):
    self.viewmodel.watch_afk = state == Qt.Checked
    self.afk_timeout.setEnabled(self.viewmodel.watch_afk)
    self.afk_label.setEnabled(self.viewmodel.watch_afk)

  def on_afk_timeout_changed(self, value):
    self.viewmodel.afk_timeout = value

  def apply_settings(self):
    self.viewmodel.apply_settings()

  def on_viewmodel_property_changed(self, property_name):
    if property_name == 'settings_applied':
      # You could show a message box here to inform the user that settings have been applied
      pass
