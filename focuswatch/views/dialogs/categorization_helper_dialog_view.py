import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                               QFrame, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QMessageBox, QPushButton,
                               QScrollArea, QSizePolicy, QSpacerItem,
                               QVBoxLayout, QWidget)

from focuswatch.viewmodels.dialogs.categorization_helper_dialog_viewmodel import \
    CategorizationHelperViewModel
from focuswatch.viewmodels.dialogs.category_dialog_viewmodel import \
    CategoryDialogViewModel
from focuswatch.views.dialogs.category_dialog_view import CategoryDialogView

if TYPE_CHECKING:
  from focuswatch.services.activity_service import ActivityService
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.keyword_service import KeywordService

logger = logging.getLogger(__name__)


class CategorizationHelperView(QDialog):
  def __init__(self, parent, activity_service: 'ActivityService', category_service: 'CategoryService', keyword_service: 'KeywordService'):
    super().__init__(parent)
    self._activity_service = activity_service
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._viewmodel = CategorizationHelperViewModel(
        self._activity_service, self._category_service, self._keyword_service)
    self.setup_ui()
    self.connect_signals()

  def setup_ui(self):
    # Resize window
    self.resize(800, 600)
    self.setWindowTitle("Categorization Helper")
    main_layout = QVBoxLayout(self)

    # Note to user
    note_label = QLabel(
        "Create new keywords for the uncategorized activities and assign them to categories.")
    note_label.setWordWrap(True)
    main_layout.addWidget(note_label)

    # Applications group
    self.applications_group = self.create_group(
        "Top uncategorized applications")
    main_layout.addWidget(self.applications_group)

    # Titles group
    self.titles_group = self.create_group(
        "Top uncategorized window titles")
    main_layout.addWidget(self.titles_group)

    # Button box
    self.button_box = QDialogButtonBox(
        QDialogButtonBox.Apply | QDialogButtonBox.Cancel)
    main_layout.addWidget(self.button_box)

    self.update_applications()
    self.update_titles()

    self.setLayout(main_layout)

  def create_group(self, title):
    group = QGroupBox(title)
    layout = QVBoxLayout(group)
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_content = QWidget()
    self.scroll_layout = QVBoxLayout(scroll_content)
    scroll_area.setWidget(scroll_content)
    layout.addWidget(scroll_area)
    return group

  def connect_signals(self):
    self._viewmodel.property_changed.connect(
      self.on_viewmodel_property_changed)

    self.button_box.accepted.connect(self.apply_changes)
    self.button_box.rejected.connect(self.reject)

  def on_viewmodel_property_changed(self, property_name):
    if property_name == "uncategorized_applications":
      self.update_applications()
    elif property_name == "uncategorized_titles":
      self.update_titles()
    elif property_name == "categories":
      self.update_categories()

  def update_applications(self):
    self.populate_group(self.applications_group,
                        self._viewmodel.uncategorized_applications)

  def update_titles(self):
    self.populate_group(self.titles_group,
                        self._viewmodel.uncategorized_titles)

  def update_categories(self):
    for group in [self.applications_group, self.titles_group]:
      scroll_area = group.findChild(QScrollArea)
      if scroll_area:
        content_widget = scroll_area.widget()
        for i in range(content_widget.layout().count()):
          item = content_widget.layout().itemAt(i)
          if isinstance(item, QHBoxLayout):
            combo_box = item.itemAt(3).widget()
            if isinstance(combo_box, QComboBox):
              self.populate_category_combo(combo_box)

  def populate_group(self, group, items):
    scroll_area = group.findChild(QScrollArea)
    if scroll_area:
      content_widget = scroll_area.widget()
      layout = content_widget.layout()
      self.clear_layout(layout)

      for item_id, item_name, total_time_seconds in items:
        if total_time_seconds < 60 or item_name == "None":
          continue

        h_layout = QHBoxLayout()

        name_edit = QLineEdit(item_name)
        name_edit.setMinimumWidth(200)
        h_layout.addWidget(name_edit)

        match_case_checkbox = QCheckBox("Match case")
        match_case_checkbox.setChecked(False)
        h_layout.addWidget(match_case_checkbox)

        time_label = QLabel(
            f"{total_time_seconds // 3600}h {(total_time_seconds % 3600) // 60}m")
        time_label.setFixedWidth(100)
        h_layout.addWidget(time_label)

        category_combo = QComboBox()
        self.populate_category_combo(category_combo)
        h_layout.addWidget(category_combo)

        new_category_btn = QPushButton("+")
        new_category_btn.setToolTip("Create new category")
        new_category_btn.clicked.connect(
            lambda checked, name=item_name: self.create_new_category(name))
        new_category_btn.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed)
        new_category_btn.setFixedWidth(30)
        h_layout.addWidget(new_category_btn)

        layout.addLayout(h_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

      if layout.count() == 0:
        layout.addWidget(
            QLabel("No uncategorized activities found. Good job!"))

      layout.addItem(QSpacerItem(
          20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

  def populate_category_combo(self, combo_box):
    combo_box.clear()
    for category in self._viewmodel.categories:
      combo_box.addItem(category.name, category.id)
      if category.name == "Uncategorized":
        combo_box.setCurrentIndex(combo_box.count() - 1)

  def create_new_category(self, keyword: str):
    dialog = CategoryDialogView(
      self, self._category_service, self._keyword_service)
    if dialog.exec_():
      category_id = self._category_service.get_category_id_from_name(
        dialog._viewmodel.name)
      category = self._category_service.get_category_by_id(category_id)
      logger.info(f"Created new category: {category.name}")

      # Add the new category to the categories list and emit the signal
      self._viewmodel._categories.append(category)
      self._viewmodel.property_changed.emit('categories')

      # self._viewmodel.save_categorization(keyword, category.id, False)

      # Update the UI to reflect the new category immediately
      self.update_categories()

  @Slot()
  def apply_changes(self):
    for group in [self.applications_group, self.titles_group]:
      scroll_area = group.findChild(QScrollArea)
      if scroll_area:
        content_widget = scroll_area.widget()
        for i in range(content_widget.layout().count()):
          item = content_widget.layout().itemAt(i)
          if isinstance(item, QHBoxLayout):
            self.save_categorization(item)

    reply = QMessageBox.question(self, "Retroactive Categorization",
                                 "Do you want to retroactively categorize the activities with the new rules?",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if reply == QMessageBox.Yes:
      self._viewmodel.perform_retroactive_categorization()

    self.accept()

  def save_categorization(self, layout):
    name_edit = layout.itemAt(0).widget()
    match_case_checkbox = layout.itemAt(1).widget()
    category_combo = layout.itemAt(3).widget()

    if isinstance(category_combo, QComboBox) and category_combo.currentText() != "Uncategorized":
      name = name_edit.text()
      category_id = category_combo.currentData()
      match_case = match_case_checkbox.isChecked()
      self._viewmodel.save_categorization(name, category_id, match_case)

  def clear_layout(self, layout):
    while layout.count():
      item = layout.takeAt(0)
      if isinstance(item, QHBoxLayout):
        self.clear_layout(item)
      elif item.widget():
        item.widget().deleteLater()
