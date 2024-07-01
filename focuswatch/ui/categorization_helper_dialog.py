
from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFrame,
                               QGroupBox, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QSizePolicy, QSpacerItem,
                               QVBoxLayout, QWidget, QLineEdit, QCheckBox, QMessageBox)

from focuswatch.ui.category_dialog import CategoryDialog


class CategorizationHelperDialog(QDialog):
  def __init__(self, parent, activity_manager, category_manager, keyword_manager):
    super().__init__(parent)
    self._activity_manager = activity_manager
    self._category_manager = category_manager
    self._keyword_manager = keyword_manager
    self.setupUi(self)
    self.populate_entries()

  def setupUi(self, Dialog):
    if not Dialog.objectName():
      Dialog.setObjectName(u"Dialog")
    # Dialog.resize(512, 864)
    self.verticalLayout = QVBoxLayout(Dialog)
    self.verticalLayout.setObjectName(u"verticalLayout")
    self.frame = QFrame(Dialog)
    self.frame.setObjectName(u"frame")
    self.frame.setFrameShape(QFrame.Shape.NoFrame)
    self.frame.setFrameShadow(QFrame.Shadow.Raised)
    self.verticalLayout_2 = QVBoxLayout(self.frame)
    self.verticalLayout_2.setObjectName(u"verticalLayout_2")

    # Add a note to the user
    self.note_label = QLabel(
      "Craete new keywords for the uncategorized activities and assign them to categories.")
    self.note_label.setWordWrap(True)
    self.verticalLayout_2.addWidget(self.note_label)

    # Applications
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

    self.verticalLayout_4.addLayout(self.applications_verticalLayout)
    self.applications_scrollArea.setWidget(
      self.applications_scrollAreaWidgetContents)
    self.verticalLayout_3.addWidget(self.applications_scrollArea)
    self.verticalLayout_2.addWidget(self.applications_groupBox)

    # Titles
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
    self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.accept)

    self.verticalLayout.addWidget(self.buttonBox)

    self.retranslateUi(Dialog)
    self.buttonBox.accepted.connect(Dialog.accept)
    self.buttonBox.rejected.connect(Dialog.reject)

    QMetaObject.connectSlotsByName(Dialog)

  def retranslateUi(self, Dialog):
    Dialog.setWindowTitle(
        QCoreApplication.translate("Dialog", u"Dialog", None))
    self.applications_groupBox.setTitle(QCoreApplication.translate(
        "Dialog", u"Top uncategorized applications", None))
    self.titles_groupBox.setTitle(QCoreApplication.translate(
        "Dialog", u"Top uncategorized window titles", None))
# retranslateUi

  def populate_entries(self):
    # Get top uncategorized activities
    uncategorized_applications = self._activity_manager.get_top_uncategorized_window_classes(
      10)

    uncategorized_titles = self._activity_manager.get_top_uncategorized_window_names(
      10)

    # Populate applications
    self.populate_group(self.applications_verticalLayout,
                        uncategorized_applications)

    # Populate titles
    self.populate_group(self.titles_verticalLayout,
                        uncategorized_titles)

  def populate_group(self, layout, activities):
    # Clear existing items in the layout
    while layout.count():
      child = layout.takeAt(0)
      if child.widget():
        child.widget().deleteLater()

    for activity in activities:
      activity_id, name, total_time_seconds = activity
      # Don't show None entries # TODO - should we even log this in the watcher?
      if total_time_seconds < 60 or name == "None":
        continue

      # Create horizontal layout for each entry
      h_layout = QHBoxLayout()

      # Add name label
      name_edit = QLineEdit(name)
      name_edit.setMinimumWidth(200)
      h_layout.addWidget(name_edit)

      # Add match_case checkbox
      match_case_checkbox = QCheckBox("Match case")
      match_case_checkbox.setChecked(False)
      h_layout.addWidget(match_case_checkbox)

      # Add time label
      time_label = QLabel(
        f"{total_time_seconds // 3600}h {(total_time_seconds % 3600) // 60}m")
      time_label.setFixedWidth(100)
      h_layout.addWidget(time_label)

      # Add category combo box
      category_combo = QComboBox()
      # TODO this temp, optimize it
      categories = self._category_manager.get_all_categories()
      uncategorized_id = None
      for i, category in enumerate(categories):
        category_combo.addItem(category[1], category[0])  # name, id
        if category[1] == "Uncategorized":
          uncategorized_id = i
          category_combo.setCurrentIndex(i)
      h_layout.addWidget(category_combo)

      # Add "Create new category" button
      new_category_btn = QPushButton("+")
      new_category_btn.setToolTip("Create new category")
      # Connect the button to the create_new_category method and pass the keyword
      new_category_btn.clicked.connect(
        lambda checked, keyword=name: self.create_new_category(keyword))
      new_category_btn.setSizePolicy(
        QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
      new_category_btn.setFixedWidth(30)
      h_layout.addWidget(new_category_btn)

      # Add the horizontal layout to the main vertical layout
      layout.addLayout(h_layout)

      separator = QFrame()
      separator.setFrameShape(QFrame.HLine)
      separator.setFrameShadow(QFrame.Sunken)
      layout.addWidget(separator)

    # Check if there are any entries and if not display a "Good job" message
    if layout.count() == 0:
      layout.addWidget(QLabel("No uncategorized activities found. Good job!"))

    # Add vertical spacer at the end
    layout.addItem(QSpacerItem(
      20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

  def create_new_category(self, keyword):
    dialog = CategoryDialog(
      self, self._category_manager, self._keyword_manager, keywords=[keyword])
    result = dialog.exec_()
    if result:
      new_keywords = dialog.new_keywords
      color = dialog.color

      new_name = dialog.name_lineEdit.text()
      parent = dialog.parent_comboBox.currentText()

      if parent != 'None':
        parent_id = self._category_manager.get_category_id_from_name(parent)
      else:
        parent_id = None

      self._category_manager.create_category(
          new_name, parent_id, color)
      category_id = self._category_manager.get_category_id_from_name(
        new_name)

      for keyw in new_keywords:
        self._keyword_manager.add_keyword(
            keyw[1], category_id, keyw[3])
      # Refresh the combo boxes with the new category
      self.populate_entries()

  def accept(self):
    # Save the categorizations
    for i in range(self.applications_verticalLayout.count()):
      item = self.applications_verticalLayout.itemAt(i)
      if isinstance(item, QHBoxLayout):
        self.save_categorization(item)

    for i in range(self.titles_verticalLayout.count()):
      item = self.titles_verticalLayout.itemAt(i)
      if isinstance(item, QHBoxLayout):
        self.save_categorization(item)

    # Display dialog and ask if the user wants to retroactively categorize
    dialog = QMessageBox()
    dialog.setWindowTitle("Retroactive categorization")
    dialog.setText(
      "Do you want to retroactively categorize the activities with the new rules?")
    dialog.setStandardButtons(QMessageBox.StandardButton.Yes |
                              QMessageBox.StandardButton.No)
    dialog.setDefaultButton(QMessageBox.StandardButton.Yes)
    result = dialog.exec_()
    if result == QMessageBox.StandardButton.Yes:
      self.parent().retroactive_categorization(skip_confirmation=True)

    super().accept()

  def save_categorization(self, layout):
    name_label = layout.itemAt(0).widget()
    match_case_checkbox = layout.itemAt(1).widget()
    category_combo = layout.itemAt(3).widget()
    category_id = category_combo.currentData()
    category_name = category_combo.currentText()

    # no need to update if it's already uncategorized
    if isinstance(category_combo, QComboBox) and category_name != "Uncategorized":
      # Add keyword to the category
      keyword = name_label.text()
      match_case = match_case_checkbox.isChecked()
      self._keyword_manager.add_keyword(
          keyword, category_id, match_case)
