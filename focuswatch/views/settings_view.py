import logging
from typing import Optional

from PySide6.QtCore import (QCoreApplication, QEasingCurve, QPropertyAnimation,
                            QSize, Qt, QTimer)
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QDialogButtonBox, QDoubleSpinBox,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QScrollArea,
                               QSizePolicy, QSpacerItem, QSpinBox, QTabWidget,
                               QToolButton, QVBoxLayout, QWidget)

from focuswatch.utils.resource_utils import apply_stylesheet, load_icon

logger = logging.getLogger(__name__)


class SettingsView(QWidget):

  def __init__(self, viewmodel, parent=None):
    super().__init__(parent)
    self.viewmodel = viewmodel
    self.current_animation = None
    self.setup_ui()
    self.sections = [  # TODO put it somewhere else maybe?
        {"label": self.general_header, "widget": self.general_section},
        {"label": self.watcher_header, "widget": self.watcher_section},
    ]
    self.connect_signals()

    apply_stylesheet(self, "settings_view.qss")

  def setup_ui(self) -> None:
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

    # Navigation Buttons using QToolButton
    self.nav_general_button = self.create_sidebar_button(
        text="General",
        icon_path="general_icon.png"
    )
    self.nav_general_button.clicked.connect(
        lambda: self.scroll_to_section("general"))

    self.nav_watcher_button = self.create_sidebar_button(
        text="Watcher",
        icon_path="watcher_icon.png"
    )
    self.nav_watcher_button.clicked.connect(
        lambda: self.scroll_to_section("watcher"))

    # Add buttons to navigation layout
    self.navigation_layout.addWidget(self.nav_general_button)
    self.navigation_layout.addWidget(self.nav_watcher_button)
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
    self.general_section = self.create_general_section()
    self.scroll_layout.addWidget(self.general_section)

    # Watcher Settings Section
    self.watcher_section = self.create_watcher_section()
    self.scroll_layout.addWidget(self.watcher_section)

    # Spacer at the bottom
    self.scroll_layout.addStretch()

    # Set scroll content
    self.scroll_area.setWidget(self.scroll_content)

    # Right Side Layout (Scroll Area + Apply Button)
    self.right_layout = QVBoxLayout()
    self.right_layout.setContentsMargins(0, 0, 0, 0)
    self.right_layout.setSpacing(10)
    self.right_layout.addWidget(self.scroll_area)

    # Create a vertical layout for the right side
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

    # Add the scroll area below the filter input
    self.right_layout.addWidget(self.scroll_area)

    # Apply Button Box and Note Label
    self.label_note = QLabel(self)
    self.label_note.setObjectName("label_note")
    self.label_note.setText(
        QCoreApplication.translate(
            "SettingsView", "Note: Changes will apply on next restart.", None
        )
    )
    self.label_note.setAlignment(Qt.AlignCenter)
    self.right_layout.addWidget(self.label_note)

    self.button_box = QDialogButtonBox(self)
    self.button_box.setObjectName("button_box")
    self.button_box.setStandardButtons(QDialogButtonBox.Apply)
    self.right_layout.addWidget(self.button_box)

    # Add Navigation and Right Layout to Main Layout
    self.main_layout.addWidget(self.navigation_panel, 0)
    self.main_layout.addLayout(self.right_layout, 1)

    # Initially set General as active
    self.scroll_to_section("general")

  def connect_signals(self) -> None:
    """ Connect signals between the ViewModel and the View. """
    self.viewmodel.property_changed.connect(self.on_property_changed)
    self.filter_input.textChanged.connect(self.on_filter_text_changed)
    self.autostart_checkbox.stateChanged.connect(self.on_autostart_changed)
    self.watch_interval.valueChanged.connect(self.on_watch_interval_changed)
    self.watch_afk.stateChanged.connect(self.on_watch_afk_changed)
    self.afk_timeout.valueChanged.connect(self.on_afk_timeout_changed)
    self.button_box.button(
      QDialogButtonBox.Apply).clicked.connect(self.apply_settings)

  def on_property_changed(self, property_name: str) -> None:
    """ Handle property changes emitted by the ViewModel.

    Args:
      property_name: The name of the property that changed.
    """
    if property_name == "settings_applied":
      QMessageBox.information(
          self,
          QCoreApplication.translate("SettingsView", "Settings Applied", None),
          QCoreApplication.translate(
              "SettingsView", "Your settings have been applied successfully.", None
          ),
          QMessageBox.Ok,
      )
    elif property_name == "filter_text":
      self.apply_filter()

  def on_filter_text_changed(self, text: str) -> None:
    """ Handle changes to the filter text input.

    Args:
      text: The new filter text.
    """
    self.viewmodel.filter_text = text
    self.apply_filter()

  def apply_filter(self) -> None:
    """ Apply the filter to the settings sections and options."""
    filter_text = self.viewmodel.filter_text.lower().strip()

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
          matches = self.widget_matches_filter(child, filter_text)
          child.setVisible(matches)
          if matches:
            section_matches = True
        section_widget.setVisible(section_matches)

  def section_matches_filter(self, section_widget: QWidget, filter_text: str) -> bool:
    """ Check if a section or any of its child widgets match the filter.

    Args:
      section_widget: The section widget to check.
      filter_text: The filter text to match against.

    Returns:
      True if the section or any child matches; False otherwise.
    """
    # Check the header label
    header_label = section_widget.findChild(
      QLabel, options=Qt.FindDirectChildrenOnly)
    if header_label and filter_text in header_label.text().lower():
      return True

    # Check child widgets
    for child in section_widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
      # Skip the header label
      if child == header_label:
        continue
      if self.widget_matches_filter(child, filter_text):
        child.setVisible(True)
        return True
      else:
        child.setVisible(False)

    return False

  def widget_matches_filter(self, widget: QWidget, filter_text: str) -> bool:
    """ Check if a setting widget matches the filter text.

    Args:
      widget: The setting widget to check.
      filter_text: The filter text to match against.

    Returns:
      True if the setting matches; False otherwise.
    """
    # Check all child widgets within the setting
    for child in widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
      if isinstance(child, QLabel) or isinstance(child, QCheckBox):
        text = child.text().lower()
        if filter_text in text:
          return True
    return False

  def create_setting_widget(
      self, widget: QWidget, label_text: Optional[str] = None
  ) -> QWidget:
    """ Create a container widget for a setting.

    Args:
      widget: The input control widget (e.g., QSpinBox, QCheckBox).
      label_text: The text for the label (optional).

    Returns:
      A QWidget containing the label and control.
    """
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

  def create_sidebar_button(self, text: str, icon_path: str) -> QToolButton:
    """ Helper method to create sidebar buttons using QToolButton. """
    button = QToolButton(self.navigation_panel)
    button.setObjectName(f"sidebar_button_{text.lower()}")
    button.setText(text)
    button.setIcon(load_icon(icon_path))
    button.setIconSize(QSize(16, 18))
    button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    # button.setCheckable(True)
    button.setAutoExclusive(True)
    button.setMinimumSize(QSize(30, 40))
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    return button

  def create_general_section(self) -> QWidget:
    """ Create the General settings section.

    Returns:
      A QWidget containing the general settings section.
    """
    group_box = QGroupBox()
    group_box.setObjectName("general_group_box")
    group_box.setTitle("")

    group_layout = QVBoxLayout(group_box)
    group_layout.setContentsMargins(10, 15, 10, 10)
    group_layout.setSpacing(10)

    # Section Header
    self.general_header = QLabel(
        QCoreApplication.translate("SettingsView", "General", None), group_box
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
    self.autostart_checkbox.setChecked(self.viewmodel.autostart_enabled)
    self.autostart_checkbox.setEnabled(self.viewmodel.is_autostart_available())

    # Set custom property if disabled for styling
    if not self.viewmodel.is_autostart_available():
      self.autostart_checkbox.setProperty("disabled_control", True)

    autostart_setting = self.create_setting_widget(self.autostart_checkbox)
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
    self.autostart_note.setVisible(not self.viewmodel.is_autostart_available())
    # Set custom property for styling
    self.autostart_note.setProperty("disabled_note", True)
    group_layout.addWidget(self.autostart_note)

    return group_box

  def create_watcher_section(self) -> QWidget:
    """ Create the Watcher settings section.

    Returns:
      A QWidget containing the watcher settings section.
    """
    group_box = QGroupBox()
    group_box.setObjectName("watcher_group_box")
    group_box.setTitle("")

    group_layout = QVBoxLayout(group_box)
    group_layout.setContentsMargins(10, 15, 10, 10)
    group_layout.setSpacing(10)

    # Section Header
    self.watcher_header = QLabel(
        QCoreApplication.translate("SettingsView", "Watcher", None), group_box
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
    self.watch_interval.setValue(self.viewmodel.watch_interval)
    self.watch_interval.setDecimals(1)
    self.watch_interval.setMinimum(1.0)
    self.watch_interval.setMaximum(60.0)
    self.watch_interval.setSingleStep(0.5)
    self.watch_interval.setSuffix(
        QCoreApplication.translate("SettingsView", " s", None)
    )

    watch_interval_setting = self.create_setting_widget(
        self.watch_interval,
        QCoreApplication.translate("SettingsView", "Watch interval", None)
    )
    group_layout.addWidget(watch_interval_setting)

    # Watch AFK Checkbox
    self.watch_afk = QCheckBox(group_box)
    self.watch_afk.setObjectName("watch_afk")
    self.watch_afk.setChecked(self.viewmodel.watch_afk)
    self.watch_afk.setText(
        QCoreApplication.translate("SettingsView", "Watch AFK", None)
    )

    watch_afk_setting = self.create_setting_widget(self.watch_afk)
    group_layout.addWidget(watch_afk_setting)

    # AFK Timeout Setting
    self.afk_timeout = QSpinBox(group_box)
    self.afk_timeout.setObjectName("afk_timeout")
    self.afk_timeout.setMinimum(1)
    self.afk_timeout.setMaximum(60)
    self.afk_timeout.setValue(self.viewmodel.afk_timeout)
    self.afk_timeout.setSuffix(
        QCoreApplication.translate("SettingsView", " m", None)
    )

    is_afk_enabled = self.viewmodel.watch_afk
    self.afk_timeout.setEnabled(is_afk_enabled)

    if not is_afk_enabled:
      self.afk_timeout.setProperty("disabled_control", True)
    else:
      self.afk_timeout.setProperty("disabled_control", False)

    afk_timeout_setting = self.create_setting_widget(
        self.afk_timeout,
        QCoreApplication.translate("SettingsView", "AFK timeout", None)
    )
    afk_timeout_setting.setObjectName("afk_timeout_setting")
    group_layout.addWidget(afk_timeout_setting)

    return group_box

  def scroll_to_section(self, section_name: str) -> None:
    """
    Scroll the scroll area to the specified section.

    Args:
        section_name: The name of the section to scroll to ('general' or 'watcher').
    """
    if section_name == "general":
      target_widget = self.general_header
    elif section_name == "watcher":
      target_widget = self.watcher_header
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
    """
    Highlight the header widget by changing its background color briefly.

    Args:
        header_widget: The QLabel widget to highlight.
    """
    original_style = header_widget.styleSheet()
    highlight_style = "background-color: #44475a; border-radius: 3px; padding-left: 1px;"

    header_widget.setStyleSheet(highlight_style)

    QTimer.singleShot(500, lambda: header_widget.setStyleSheet(original_style))

  def on_autostart_changed(self, state: int) -> None:
    """
    Handle changes to the autostart checkbox.

    Args:
        state: The state of the checkbox (Qt.Checked or Qt.Unchecked).
    """
    self.viewmodel.autostart_enabled = state == Qt.Checked

  def on_watch_interval_changed(self, value: float) -> None:
    """
    Handle changes to the watch interval spin box.

    Args:
        value: The new watch interval value.
    """
    self.viewmodel.watch_interval = value

  def on_watch_afk_changed(self, state: int) -> None:
    """ Handle changes to the watch AFK checkbox.

    Args:
      state: The state of the checkbox (Qt.Checked or Qt.Unchecked).
    """
    is_checked = state == 2  # Qt.Checked doesn't work for some reason
    self.viewmodel.watch_afk = is_checked
    self.afk_timeout.setEnabled(is_checked)

    # Update the custom property for styling
    if not is_checked:
      self.afk_timeout.setProperty("disabled_control", True)
    else:
      self.afk_timeout.setProperty("disabled_control", False)

    self.afk_timeout.style().unpolish(self.afk_timeout)
    self.afk_timeout.style().polish(self.afk_timeout)

  def on_afk_timeout_changed(self, value: int) -> None:
    """
    Handle changes to the AFK timeout spin box.

    Args:
        value: The new AFK timeout value.
    """
    self.viewmodel.afk_timeout = value

  def apply_settings(self) -> None:
    """Apply the current settings via the ViewModel."""
    self.viewmodel.apply_settings()
