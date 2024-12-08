""" View for application settings, with hardcoded sections and updated to work with the new ViewModel. """
import logging
from typing import Optional

from PySide6.QtCore import (QCoreApplication, QEasingCurve, QEvent, QObject,
                            QPropertyAnimation, QSize, Qt, QTimer)
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QDialogButtonBox, QDoubleSpinBox,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QScrollArea, QSizePolicy, QSpinBox,
                               QToolButton, QVBoxLayout, QWidget, QPushButton)

from focuswatch.utils.resource_utils import apply_stylesheet, load_icon

logger = logging.getLogger(__name__)


class WheelEventFilter(QObject):
  """ Ignore wheel events for widgets that do not have focus. """

  def eventFilter(self, obj, event):
    if event.type() == QEvent.Wheel:
      return True
    return super().eventFilter(obj, event)


class SettingsView(QWidget):
  """ Settings view. """

  def __init__(self,
               viewmodel,
               parent: Optional[QObject] = None):
    super().__init__(parent)
    self._viewmodel = viewmodel
    self.current_animation = None
    self._setup_ui()
    self.sections = [
        {"label": self.general_header, "widget": self.general_section},
        {"label": self.watcher_header, "widget": self.watcher_section},
        {"label": self.dashboard_header, "widget": self.dashboard_section},
    ]
    self._connect_signals()

    apply_stylesheet(self, "settings_view.qss")

  def _setup_ui(self) -> None:
    # Main Horizontal Layout
    self.main_layout = QHBoxLayout(self)
    self.main_layout.setContentsMargins(0, 0, 0, 0)
    self.main_layout.setSpacing(0)

    # Navigation Panel
    self.navigation_panel = QWidget(self)
    self.navigation_panel.setObjectName("navigation_panel")
    self.navigation_layout = QVBoxLayout(self.navigation_panel)
    self.navigation_layout.setContentsMargins(0, 0, 0, 0)
    self.navigation_layout.setSpacing(0)

    # Navigation Buttons
    self.nav_general_button = self._create_sidebar_button(
      text="General",
      icon_path="general_icon.png"
    )
    self.nav_general_button.clicked.connect(
      lambda: self.scroll_to_section("general"))

    self.nav_watcher_button = self._create_sidebar_button(
      text="Watcher",
      icon_path="watcher_icon.png"
    )
    self.nav_watcher_button.clicked.connect(
      lambda: self.scroll_to_section("watcher"))

    self.nav_dashboard_button = self._create_sidebar_button(
      text="Dashboard",
      icon_path="dashboard_icon.png"
    )
    self.nav_dashboard_button.clicked.connect(
      lambda: self.scroll_to_section("dashboard"))

    # Add buttons to navigation layout
    self.navigation_layout.addWidget(
      self.nav_general_button, alignment=Qt.AlignCenter)
    self.navigation_layout.addWidget(
      self.nav_watcher_button, alignment=Qt.AlignCenter)
    self.navigation_layout.addWidget(
      self.nav_dashboard_button, alignment=Qt.AlignCenter)
    self.navigation_layout.addStretch()

    # Scroll Area for Settings Content
    self.scroll_area = QScrollArea(self)
    self.scroll_area.setWidgetResizable(True)
    self.scroll_area.setObjectName("settings_scroll_area")

    # Container Widget inside Scroll Area
    self.scroll_content = QWidget()
    self.scroll_content.setObjectName("scroll_content")
    self.scroll_layout = QVBoxLayout(self.scroll_content)
    self.scroll_layout.setContentsMargins(10, 10, 10, 10)
    self.scroll_layout.setSpacing(8)

    # General Settings Section
    self.general_section = self._create_general_section()
    self.scroll_layout.addWidget(self.general_section)

    # Watcher Settings Section
    self.watcher_section = self._create_watcher_section()
    self.scroll_layout.addWidget(self.watcher_section)

    # Dashboard Settings Section
    self.dashboard_section = self._create_dashboard_section()
    self.scroll_layout.addWidget(self.dashboard_section)

    # Spacer at the bottom
    self.scroll_layout.addStretch()

    # Set scroll content
    self.scroll_area.setWidget(self.scroll_content)

    # Right Side Layout
    self.right_layout = QVBoxLayout()
    self.right_layout.setContentsMargins(0, 0, 0, 0)
    self.right_layout.setSpacing(10)

    # Add the filter input
    self.filter_input = QLineEdit(self)
    self.filter_input.setObjectName("filter_input")
    self.filter_input.setPlaceholderText("Filter settings...")
    self.filter_input.setClearButtonEnabled(True)

    # Add the filter input in a container widget with margins
    filter_container = QWidget()
    filter_layout = QHBoxLayout(filter_container)
    filter_layout.setContentsMargins(10, 5, 10, 0)
    filter_layout.addWidget(self.filter_input)
    self.right_layout.addWidget(filter_container)

    # Add a restore button next to the filter input
    self.button_restore_defaults = QPushButton(
        "Restore Defaults", self)
    self.button_restore_defaults.setObjectName("button_restore_defaults")
    filter_layout.addWidget(self.button_restore_defaults)
    self.button_restore_defaults.setFixedHeight(30)

    # Add the scroll area below the filter input
    self.right_layout.addWidget(self.scroll_area)

    # Note Label
    self.label_note = QLabel(self)
    self.label_note.setObjectName("label_note")
    self.label_note.setText(
        QCoreApplication.translate(
            "SettingsView", "Note: Changes will apply on next restart.", None
        )
    )
    self.label_note.setAlignment(Qt.AlignCenter)
    self.right_layout.addWidget(self.label_note)

    # Add Navigation and Right Layout to Main Layout
    self.main_layout.addWidget(self.navigation_panel, 0)
    self.main_layout.addLayout(self.right_layout, 1)

    # Instantiate the event filter
    self.wheel_event_filter = WheelEventFilter()

    # Apply the event filter to all relevant widgets
    widgets_with_wheel = [
      self.watch_interval,
      self.afk_timeout,
      self.daily_focused_goal,
      self.weekly_focused_goal,
      self.monthly_focused_goal,
      self.yearly_focused_goal,
      self.distracted_goal
    ]

    for widget in widgets_with_wheel:
      widget.installEventFilter(self.wheel_event_filter)

    # Initially set General as active
    self.scroll_to_section("general")

  def _connect_signals(self) -> None:
    """ Connect signals between the ViewModel and the View. """
    # Connect ViewModel signals
    self._viewmodel.filter_text_changed.connect(self._apply_filter)

    # Connect UI signals
    self.filter_input.textChanged.connect(self._on_filter_text_changed)
    self.autostart_checkbox.stateChanged.connect(
        self._on_autostart_changed)
    self.watch_interval.valueChanged.connect(
        self._on_watch_interval_changed)
    self.watch_afk.stateChanged.connect(self._on_watch_afk_changed)
    self.afk_timeout.valueChanged.connect(self._on_afk_timeout_changed)
    self.button_restore_defaults.clicked.connect(self._restore_defaults)

    # Connect signals for dashboard settings
    self.daily_focused_goal.valueChanged.connect(
        self._on_daily_focused_goal_changed)
    self.weekly_focused_goal.valueChanged.connect(
        self._on_weekly_focused_goal_changed)
    self.monthly_focused_goal.valueChanged.connect(
        self._on_monthly_focused_goal_changed)
    self.yearly_focused_goal.valueChanged.connect(
        self._on_yearly_focused_goal_changed)
    self.distracted_goal.valueChanged.connect(
        self._on_distracted_goal_changed)
    self.display_cards_idle.stateChanged.connect(
        self._on_display_cards_idle_changed)
    self.display_timeline_idle.stateChanged.connect(
        self._on_display_timeline_idle_changed)

  def _restore_defaults(self):
    """ Restore default categories with confirmation. """
    dialog = QMessageBox(self)
    dialog.setWindowTitle("Restore Defaults")
    dialog.setText(
      "Are you sure you want to restore default settings?\n"
      "This action cannot be undone."
    )
    dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    dialog.setDefaultButton(QMessageBox.No)
    result = dialog.exec_()

    if result == QMessageBox.Yes:
      # Perform restore defaults
      self._viewmodel.restore_defaults()

      QMessageBox.information(
        self, "Restore Defaults", "Default settings restored successfully.\nRestart to apply changes."
      )

  def _on_filter_text_changed(self, text: str) -> None:
    """ Handle changes to the filter text input. """
    self._viewmodel.filter_text = text

  def _apply_filter(self) -> None:
    """ Apply the filter to the settings sections and options. """
    filter_text = self._viewmodel.filter_text.lower().strip()

    # If filter text is empty, show all sections and settings
    if not filter_text:
      for section in self.sections:
        section_widget = section['widget']
        section_widget.setVisible(True)
        for child in section_widget.findChildren(QWidget):
          child.setVisible(True)
      return

    # Filter sections based on the filter text
    for section in self.sections:
      section_widget = section['widget']
      header_label = section['label']

      if filter_text in header_label.text().lower():
        # If section header matches, show entire section
        section_widget.setVisible(True)
        for child in section_widget.findChildren(QWidget):
          child.setVisible(True)
      else:
        # Check if any child setting matches
        section_matches = False
        for child in section_widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
          if child == header_label:
            continue
          matches = self._widget_matches_filter(child, filter_text)
          child.setVisible(matches)
          if matches:
            section_matches = True
        section_widget.setVisible(section_matches)

  def _widget_matches_filter(self, widget: QWidget, filter_text: str) -> bool:
    """ Check if a setting widget matches the filter text. """
    # Check all child widgets within the setting
    for child in widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
      if isinstance(child, QLabel) or isinstance(child, QCheckBox):
        text = child.text().lower()
        if filter_text in text:
          return True
    return False

  def _create_setting_widget(
      self, widget: QWidget, label_text: Optional[str] = None
  ) -> QWidget:
    """ Create a container widget for a setting. """
    setting_widget = QWidget()
    layout = QVBoxLayout(setting_widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)

    if label_text:
      label = QLabel(label_text)
      label.setObjectName(f"{widget.objectName()}_label")
      layout.addWidget(label)
    layout.addWidget(widget)

    return setting_widget

  def _create_sidebar_button(self, text: str, icon_path: str) -> QToolButton:
    """ Helper method to create sidebar buttons using QToolButton. """
    button = QToolButton(self.navigation_panel)
    button.setObjectName(f"sidebar_button_{text.lower()}")
    button.setText(text)
    button.setIcon(load_icon(icon_path))
    button.setIconSize(QSize(16, 18))
    button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    button.setAutoExclusive(True)
    button.setMinimumSize(QSize(30, 40))
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    return button

  def _create_general_section(self) -> QWidget:
    """ Create the General settings section. """
    group_box = QGroupBox()
    group_box.setObjectName("general_group_box")
    group_box.setTitle("")

    group_layout = QVBoxLayout(group_box)
    group_layout.setContentsMargins(10, 15, 10, 10)
    group_layout.setSpacing(10)

    # Section Header
    self.general_header = QLabel(
        QCoreApplication.translate(
            "SettingsView", "General", None), group_box
    )
    header_font = QFont()
    header_font.setPointSize(14)
    header_font.setBold(True)
    self.general_header.setFont(header_font)
    self.general_header.setObjectName("general_header")
    group_layout.addWidget(self.general_header)

    # Autostart Checkbox Setting
    self.autostart_checkbox = QCheckBox(group_box)
    self.autostart_checkbox.setObjectName("autostart_checkbox")
    self.autostart_checkbox.setText(
        QCoreApplication.translate(
            "SettingsView", "Start FocusWatch on system startup", None)
    )
    self.autostart_checkbox.setChecked(self._viewmodel.autostart_enabled)
    self.autostart_checkbox.setEnabled(self._viewmodel.autostart_available)

    # Set custom property if disabled for styling
    if not self._viewmodel.autostart_available:
      self.autostart_checkbox.setProperty("disabled_control", True)

    autostart_setting = self._create_setting_widget(
        self.autostart_checkbox)
    group_layout.addWidget(autostart_setting)

    # Note Label when Autostart is disabled
    self.autostart_note = QLabel(group_box)
    self.autostart_note.setObjectName("autostart_note")
    self.autostart_note.setText(
        QCoreApplication.translate(
            "SettingsView",
            "Autostart cannot be enabled in development mode.",
            None
        )
    )
    self.autostart_note.setVisible(not self._viewmodel.autostart_available)
    # Set custom property for styling
    self.autostart_note.setProperty("disabled_note", True)
    group_layout.addWidget(self.autostart_note)

    return group_box

  def _create_watcher_section(self) -> QWidget:
    """ Create the Watcher settings section. """
    group_box = QGroupBox()
    group_box.setObjectName("watcher_group_box")
    group_box.setTitle("")

    group_layout = QVBoxLayout(group_box)
    group_layout.setContentsMargins(10, 15, 10, 10)
    group_layout.setSpacing(10)

    # Section Header
    self.watcher_header = QLabel(
        QCoreApplication.translate(
            "SettingsView", "Watcher", None), group_box
    )
    header_font = QFont()
    header_font.setPointSize(14)
    header_font.setBold(True)
    self.watcher_header.setFont(header_font)
    self.watcher_header.setObjectName("watcher_header")
    group_layout.addWidget(self.watcher_header)

    # Watch Interval Setting
    self.watch_interval = QDoubleSpinBox(group_box)
    self.watch_interval.setObjectName("watch_interval")
    self.watch_interval.setValue(self._viewmodel.general_watch_interval)
    self.watch_interval.setDecimals(1)
    self.watch_interval.setMinimum(1.0)
    self.watch_interval.setMaximum(60.0)
    self.watch_interval.setSingleStep(0.5)
    self.watch_interval.setSuffix(
        QCoreApplication.translate("SettingsView", " s", None)
    )

    watch_interval_setting = self._create_setting_widget(
        self.watch_interval,
        QCoreApplication.translate("SettingsView", "Watch interval", None)
    )
    group_layout.addWidget(watch_interval_setting)

    # Watch AFK Checkbox
    self.watch_afk = QCheckBox(group_box)
    self.watch_afk.setObjectName("watch_afk")
    self.watch_afk.setChecked(self._viewmodel.general_watch_afk)
    self.watch_afk.setText(
        QCoreApplication.translate("SettingsView", "Watch AFK", None)
    )

    watch_afk_setting = self._create_setting_widget(self.watch_afk)
    group_layout.addWidget(watch_afk_setting)

    # AFK Timeout Setting
    self.afk_timeout = QSpinBox(group_box)
    self.afk_timeout.setObjectName("afk_timeout")
    self.afk_timeout.setMinimum(1)
    self.afk_timeout.setMaximum(60)
    self.afk_timeout.setValue(self._viewmodel.general_afk_timeout)
    self.afk_timeout.setSuffix(
        QCoreApplication.translate("SettingsView", " m", None)
    )

    is_afk_enabled = self._viewmodel.general_watch_afk
    self.afk_timeout.setEnabled(is_afk_enabled)

    if not is_afk_enabled:
      self.afk_timeout.setProperty("disabled_control", True)
    else:
      self.afk_timeout.setProperty("disabled_control", False)

    afk_timeout_setting = self._create_setting_widget(
        self.afk_timeout,
        QCoreApplication.translate("SettingsView", "AFK timeout", None)
    )
    afk_timeout_setting.setObjectName("afk_timeout_setting")
    group_layout.addWidget(afk_timeout_setting)

    return group_box

  def _create_dashboard_section(self) -> QWidget:
    """ Create the Dashboard settings section. """
    group_box = QGroupBox()
    group_box.setObjectName("dashboard_group_box")
    group_box.setTitle("")

    group_layout = QVBoxLayout(group_box)
    group_layout.setContentsMargins(10, 15, 10, 10)
    group_layout.setSpacing(10)

    # Section Header
    self.dashboard_header = QLabel(
        QCoreApplication.translate(
            "SettingsView", "Dashboard", None), group_box
    )
    header_font = QFont()
    header_font.setPointSize(14)
    header_font.setBold(True)
    self.dashboard_header.setFont(header_font)
    self.dashboard_header.setObjectName("dashboard_header")
    group_layout.addWidget(self.dashboard_header)

    # Daily Focused Goal Setting
    self.daily_focused_goal = QDoubleSpinBox(group_box)
    self.daily_focused_goal.setObjectName("daily_focused_goal")
    self.daily_focused_goal.setDecimals(1)
    self.daily_focused_goal.setMinimum(0.0)
    self.daily_focused_goal.setMaximum(24.0)
    self.daily_focused_goal.setSingleStep(0.5)
    self.daily_focused_goal.setSuffix(
        QCoreApplication.translate("SettingsView", " h", None)
    )

    daily_focused_goal_setting = self._create_setting_widget(
        self.daily_focused_goal,
        QCoreApplication.translate(
            "SettingsView", "Daily focused goal", None)
    )
    self.daily_focused_goal.setValue(
        self._viewmodel.dashboard_focused_target_day)
    group_layout.addWidget(daily_focused_goal_setting)

    # Weekly Focused Goal Setting
    self.weekly_focused_goal = QDoubleSpinBox(group_box)
    self.weekly_focused_goal.setObjectName("weekly_focused_goal")
    self.weekly_focused_goal.setDecimals(1)
    self.weekly_focused_goal.setMinimum(0.0)
    self.weekly_focused_goal.setMaximum(168.0)  # 24 * 7
    self.weekly_focused_goal.setSingleStep(1.0)
    self.weekly_focused_goal.setSuffix(
        QCoreApplication.translate("SettingsView", " h", None)
    )

    weekly_focused_goal_setting = self._create_setting_widget(
        self.weekly_focused_goal,
        QCoreApplication.translate(
            "SettingsView", "Weekly focused goal", None)
    )
    self.weekly_focused_goal.setValue(
        self._viewmodel.dashboard_focused_target_week)
    group_layout.addWidget(weekly_focused_goal_setting)

    # Monthly Focused Goal Setting
    self.monthly_focused_goal = QDoubleSpinBox(group_box)
    self.monthly_focused_goal.setObjectName("monthly_focused_goal")
    self.monthly_focused_goal.setDecimals(1)
    self.monthly_focused_goal.setMinimum(0.0)
    # Approximate max hours in a month
    self.monthly_focused_goal.setMaximum(744.0)
    self.monthly_focused_goal.setSingleStep(5.0)
    self.monthly_focused_goal.setSuffix(
        QCoreApplication.translate("SettingsView", " h", None)
    )

    monthly_focused_goal_setting = self._create_setting_widget(
        self.monthly_focused_goal,
        QCoreApplication.translate(
            "SettingsView", "Monthly focused goal", None)
    )
    self.monthly_focused_goal.setValue(
        self._viewmodel.dashboard_focused_target_month)
    group_layout.addWidget(monthly_focused_goal_setting)

    # Yearly Focused Goal Setting
    self.yearly_focused_goal = QDoubleSpinBox(group_box)
    self.yearly_focused_goal.setObjectName("yearly_focused_goal")
    self.yearly_focused_goal.setDecimals(1)
    self.yearly_focused_goal.setMinimum(0.0)
    self.yearly_focused_goal.setMaximum(8760.0)  # 24 * 365
    self.yearly_focused_goal.setSingleStep(10.0)
    self.yearly_focused_goal.setSuffix(
        QCoreApplication.translate("SettingsView", " h", None)
    )

    yearly_focused_goal_setting = self._create_setting_widget(
        self.yearly_focused_goal,
        QCoreApplication.translate(
            "SettingsView", "Yearly focused goal", None)
    )
    self.yearly_focused_goal.setValue(
        self._viewmodel.dashboard_focused_target_year)
    group_layout.addWidget(yearly_focused_goal_setting)

    # Distracted Goal Setting
    self.distracted_goal = QDoubleSpinBox(group_box)
    self.distracted_goal.setObjectName("distracted_goal")
    self.distracted_goal.setDecimals(1)
    self.distracted_goal.setMinimum(0.0)
    self.distracted_goal.setMaximum(100.0)
    self.distracted_goal.setSingleStep(1.0)
    self.distracted_goal.setSuffix(
        QCoreApplication.translate("SettingsView", " %", None)
    )

    distracted_goal_setting = self._create_setting_widget(
        self.distracted_goal,
        QCoreApplication.translate("SettingsView", "Distracted goal", None)
    )
    self.distracted_goal.setValue(
        self._viewmodel.dashboard_distracted_goal)
    group_layout.addWidget(distracted_goal_setting)

    # Display Cards Idle Checkbox
    self.display_cards_idle = QCheckBox(group_box)
    self.display_cards_idle.setObjectName("display_cards_idle")
    self.display_cards_idle.setChecked(
        self._viewmodel.dashboard_display_cards_idle)
    self.display_cards_idle.setText(
        QCoreApplication.translate(
            "SettingsView", "Display idle cards", None)
    )

    display_cards_idle_setting = self._create_setting_widget(
        self.display_cards_idle)
    group_layout.addWidget(display_cards_idle_setting)

    # Display Timeline Idle Checkbox
    self.display_timeline_idle = QCheckBox(group_box)
    self.display_timeline_idle.setObjectName("display_timeline_idle")
    self.display_timeline_idle.setChecked(
        self._viewmodel.dashboard_display_timeline_idle)
    self.display_timeline_idle.setText(
        QCoreApplication.translate(
            "SettingsView", "Display idle in timeline", None)
    )

    display_timeline_idle_setting = self._create_setting_widget(
        self.display_timeline_idle)
    group_layout.addWidget(display_timeline_idle_setting)

    return group_box

  def scroll_to_section(self, section_name: str) -> None:
    """ Scroll the scroll area to the specified section. """
    if section_name == "general":
      target_widget = self.general_header
    elif section_name == "watcher":
      target_widget = self.watcher_header
    elif section_name == "dashboard":
      target_widget = self.dashboard_header
    else:
      logger.warning(f"Unknown section name: {section_name}")
      return

    target_pos = target_widget.pos().y()

    # Animate the scrolling
    scroll_bar = self.scroll_area.verticalScrollBar()
    scroll_animation = QPropertyAnimation(scroll_bar, b"value")
    scroll_animation.setDuration(500)
    scroll_animation.setStartValue(scroll_bar.value())
    scroll_animation.setEndValue(target_pos)
    scroll_animation.setEasingCurve(QEasingCurve.InOutQuad)

    # Highlight the header after scrolling
    def on_scroll_finished():
      self.highlight_header(target_widget)

    scroll_animation.finished.connect(on_scroll_finished)
    scroll_animation.start()

    # Keep a reference to the animation to prevent garbage collection
    self.current_animation = scroll_animation

  def highlight_header(self, header_widget: QLabel) -> None:
    """ Highlight the header widget by changing its background color briefly. """
    original_style = header_widget.styleSheet()
    highlight_style = "background-color: #44475a; border-radius: 3px; padding-left: 1px;"

    header_widget.setStyleSheet(highlight_style)

    QTimer.singleShot(
        500, lambda: header_widget.setStyleSheet(original_style))

  def _on_autostart_changed(self, state: int) -> None:
    """ Handle changes to the autostart checkbox. """
    self._viewmodel.autostart_enabled = state == 2

  def _on_watch_interval_changed(self, value: float) -> None:
    """ Handle changes to the watch interval spin box. """
    self._viewmodel.general_watch_interval = value

  def _on_watch_afk_changed(self, state: int) -> None:
    """ Handle changes to the watch AFK checkbox. """
    is_checked = state == 2
    self._viewmodel.general_watch_afk = is_checked
    self.afk_timeout.setEnabled(is_checked)

    # Update the custom property for styling
    self.afk_timeout.setProperty("disabled_control", not is_checked)
    self.afk_timeout.style().unpolish(self.afk_timeout)
    self.afk_timeout.style().polish(self.afk_timeout)

  def _on_afk_timeout_changed(self, value: int) -> None:
    """ Handle changes to the AFK timeout spin box. """
    self._viewmodel.general_afk_timeout = value

  def _on_daily_focused_goal_changed(self, value: float) -> None:
    """ Handle changes to the daily focused goal setting. """
    self._viewmodel.dashboard_focused_target_day = value

  def _on_weekly_focused_goal_changed(self, value: float) -> None:
    """ Handle changes to the weekly focused goal setting. """
    self._viewmodel.dashboard_focused_target_week = value

  def _on_monthly_focused_goal_changed(self, value: float) -> None:
    """ Handle changes to the monthly focused goal setting. """
    self._viewmodel.dashboard_focused_target_month = value

  def _on_yearly_focused_goal_changed(self, value: float) -> None:
    """ Handle changes to the yearly focused goal setting. """
    self._viewmodel.dashboard_focused_target_year = value

  def _on_distracted_goal_changed(self, value: float) -> None:
    """ Handle changes to the distracted goal setting. """
    self._viewmodel.dashboard_distracted_goal = value

  def _on_display_cards_idle_changed(self, state: int) -> None:
    """ Handle changes to the display cards idle checkbox. """
    is_checked = state == 2
    self._viewmodel.dashboard_display_cards_idle = is_checked

  def _on_display_timeline_idle_changed(self, state: int) -> None:
    """ Handle changes to the display timeline idle checkbox. """
    is_checked = state == 2
    self._viewmodel.dashboard_display_timeline_idle = is_checked
