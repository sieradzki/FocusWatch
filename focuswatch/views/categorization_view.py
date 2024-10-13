import logging

from PySide6.QtCore import QCoreApplication, QRect, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLayout, QLineEdit,
                               QMessageBox, QProgressDialog, QPushButton,
                               QScrollArea, QSizePolicy, QSpacerItem,
                               QVBoxLayout, QWidget)

from focuswatch.ui.categorization_helper_dialog import \
    CategorizationHelperDialog
from focuswatch.ui.utils import (get_category_color_or_parent,
                                 get_contrasting_text_color)
from focuswatch.viewmodels.categories_viewmodel import \
    CategorizationViewModel
from focuswatch.views.dialogs.categorization_helper_dialog_view import \
    CategorizationHelperView
from focuswatch.views.dialogs.category_dialog_view import CategoryDialogView

logger = logging.getLogger(__name__)


class CategorizationView(QWidget):
  def __init__(self, viewmodel: CategorizationViewModel, parent=None):
    super().__init__(parent)
    self._viewmodel = viewmodel
    self.setupUi()
    self.connect_signals()

  def setupUi(self):
    self.setObjectName(u"categorization_view")

    # Main layout for the CategorizationView
    self.verticalLayout_5 = QVBoxLayout(self)
    self.verticalLayout_5.setObjectName(u"verticalLayout_5")

    # Categorization main frame
    self.categorization_main_frame = QFrame(self)
    self.categorization_main_frame.setObjectName(u"categorization_main_frame")
    self.categorization_main_frame.setFrameShape(QFrame.StyledPanel)
    self.categorization_main_frame.setFrameShadow(QFrame.Raised)

    # Categorization main frame layout
    self.verticalLayout_12 = QVBoxLayout(self.categorization_main_frame)
    self.verticalLayout_12.setObjectName(u"verticalLayout_12")

    # Categorization info label
    self.categorization_info_label = QLabel(self.categorization_main_frame)
    self.categorization_info_label.setObjectName(u"categorization_info_label")
    font1 = QFont()
    font1.setPointSize(12)
    self.categorization_info_label.setFont(font1)
    self.categorization_info_label.setScaledContents(False)
    self.categorization_info_label.setWordWrap(True)

    self.verticalLayout_12.addWidget(self.categorization_info_label)

    # Categorization scroll area
    self.categorization_scrollArea = QScrollArea(
      self.categorization_main_frame)
    self.categorization_scrollArea.setObjectName(u"categorization_scrollArea")
    sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    sizePolicy3.setHorizontalStretch(0)
    sizePolicy3.setVerticalStretch(0)
    sizePolicy3.setHeightForWidth(
      self.categorization_scrollArea.sizePolicy().hasHeightForWidth())
    self.categorization_scrollArea.setSizePolicy(sizePolicy3)
    self.categorization_scrollArea.setWidgetResizable(True)
    self.categorization_scrollAreaWidgetContents = QWidget()
    self.categorization_scrollAreaWidgetContents.setObjectName(
      u"categorization_scrollAreaWidgetContents")
    self.categorization_scrollAreaWidgetContents.setGeometry(
      QRect(0, 0, 1536, 737))
    self.verticalLayout_13 = QVBoxLayout(
      self.categorization_scrollAreaWidgetContents)
    self.verticalLayout_13.setObjectName(u"verticalLayout_13")
    self.categorization_verticalLayout = QVBoxLayout()
    self.categorization_verticalLayout.setObjectName(
      u"categorization_verticalLayout")
    self.categorization_content_horizontalLayout = QHBoxLayout()
    self.categorization_content_horizontalLayout.setObjectName(
      u"categorization_content_horizontalLayout")

    self.categorization_verticalLayout.addLayout(
      self.categorization_content_horizontalLayout)

    self.verticalSpacer_2 = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    self.categorization_verticalLayout.addItem(self.verticalSpacer_2)

    self.categorization_button_horizontalLayout = QHBoxLayout()
    self.categorization_button_horizontalLayout.setObjectName(
      u"categorization_button_horizontalLayout")
    self.categorization_addCategory = QPushButton(
      self.categorization_scrollAreaWidgetContents)
    self.categorization_addCategory.setObjectName(
      u"categorization_addCategory")

    self.categorization_button_horizontalLayout.addWidget(
      self.categorization_addCategory)

    self.horizontalSpacer_4 = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.categorization_button_horizontalLayout.addItem(
      self.horizontalSpacer_4)

    # Categorization helper button
    self.categorization_helper_button = QPushButton(
      self.categorization_scrollAreaWidgetContents)
    self.categorization_helper_button.setObjectName(
      u"categorization_helper_button")
    self.categorization_button_horizontalLayout.addWidget(
      self.categorization_helper_button)

    # Retroactive categorization button
    self.retroactive_categorization_button = QPushButton(
      self.categorization_scrollAreaWidgetContents)
    self.retroactive_categorization_button.setObjectName(
      u"retroactive_categorization_button")

    self.categorization_button_horizontalLayout.addWidget(
      self.retroactive_categorization_button)

    # Restore defaults button
    self.categorization_restoreDefaults = QPushButton(
      self.categorization_scrollAreaWidgetContents)
    self.categorization_restoreDefaults.setObjectName(
      u"categorization_restoreDefaults")
    self.categorization_button_horizontalLayout.addWidget(
      self.categorization_restoreDefaults)

    self.categorization_verticalLayout.addLayout(
      self.categorization_button_horizontalLayout)

    self.verticalLayout_13.addLayout(self.categorization_verticalLayout)

    self.categorization_scrollArea.setWidget(
      self.categorization_scrollAreaWidgetContents)

    self.verticalLayout_12.addWidget(self.categorization_scrollArea)

    self.verticalLayout_5.addWidget(self.categorization_main_frame)

    # Add filter layout
    self.filter_layout = QHBoxLayout()
    self.filter_input = QLineEdit(self.categorization_main_frame)
    self.filter_input.setPlaceholderText(
      "Filter categories and keywords...")

    self.filter_layout.addWidget(self.filter_input)

    # Insert filter layout at the top of the main layout
    self.verticalLayout_12.insertLayout(0, self.filter_layout)

    self.categories_setup()
    self.retranslateUi()

  def retranslateUi(self):
    self.categorization_info_label.setText(QCoreApplication.translate("Home", u"Rules for categorizing events. An event can only have one category. If several categories match, the deepest one will be chosen.\n"
                                                                      "To re-categorize previous entries after adding or updating category, click \"Retroactive categorization\" button", None))
    self.categorization_addCategory.setText(
      QCoreApplication.translate("Home", u"Add category", None))
    self.retroactive_categorization_button.setText(QCoreApplication.translate(
      "Home", u"Retroactive categorization", None))
    self.categorization_restoreDefaults.setText(
      QCoreApplication.translate("Home", u"Restore defaults", None))
    self.categorization_helper_button.setText(
      QCoreApplication.translate("Home", u"Categorization helper", None))

  def connect_signals(self):
    self._viewmodel.property_changed.connect(
      self.on_property_changed)

    self.filter_input.textChanged.connect(self.on_filter_changed)
    self.categorization_addCategory.clicked.connect(self.show_category_dialog)

    self.categorization_helper_button.clicked.connect(
      self.show_categorization_helper)
    self.retroactive_categorization_button.clicked.connect(
      self.retroactive_categorization)
    self.categorization_restoreDefaults.clicked.connect(self.restore_defaults)

  def on_filter_changed(self, text):
    self._viewmodel.filter_text = text

  def on_property_changed(self, property_name):
    if property_name in ['filter_text', 'organized_categories']:
      self.update_categories_display()

  def update_categories_display(self):
    self.clear_layout(self.categorization_content_horizontalLayout)
    self.categories_setup()

  def categories_setup(self):
    category_layout = QVBoxLayout()
    category_layout.setObjectName(u"category_layout")
    category_layout.setSizeConstraint(QLayout.SetDefaultConstraint)
    category_layout.setContentsMargins(-1, 0, 0, -1)

    cat_label_sizePolicy = QSizePolicy(
        QSizePolicy.Maximum, QSizePolicy.Fixed)
    cat_label_sizePolicy.setHorizontalStretch(0)
    cat_label_sizePolicy.setVerticalStretch(0)

    for category_id, category_data in self._viewmodel.organized_categories.items():
      category = category_data['category']
      keywords = category_data['keywords']

      # Skip Uncategorized
      if category.name in ['Uncategorized']:
        continue

      # Apply filter
      if self._viewmodel.filter_text:
        if self._viewmodel.filter_text not in category.name.lower() and not any(self._viewmodel.filter_text in keyword.lower() for keyword in keywords):
          continue

      category_row_layout = QHBoxLayout()
      category_row_layout.setObjectName(
        f"category_row_layout_{category_id}")
      category_row_layout.setSizeConstraint(QLayout.SetMinimumSize)
      category_row_layout.setContentsMargins(-1, 0, 0, -1)
      category_row_layout.setAlignment(Qt.AlignLeft)

      category_button = QPushButton(
        self.categorization_scrollAreaWidgetContents)
      category_button.setObjectName(f"category_button_{category_id}")
      category_button.clicked.connect(
        lambda checked, c_id=category_id: self.show_category_dialog(c_id))
      cat_label_sizePolicy.setHeightForWidth(
        category_button.sizePolicy().hasHeightForWidth())
      category_button.setSizePolicy(cat_label_sizePolicy)

      color = get_category_color_or_parent(category_id)
      font_color = get_contrasting_text_color(color)

      if color:
        category_button.setStyleSheet(
          f"background-color: {color}; color: {font_color};")

      depth = self._viewmodel.get_category_depth(category_id)
      indent = 40 * depth

      horizontalSpacer = QSpacerItem(
        indent, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
      category_row_layout.addItem(horizontalSpacer)

      category_button.setText(category.name)
      font = QFont()
      font.setPointSize(12)
      category_button.setFont(font)

      category_row_layout.addWidget(category_button)

      keywords_label = QLabel(
        self.categorization_scrollAreaWidgetContents)
      keywords_label.setText(' | '.join(keywords))
      keywords_label.setSizePolicy(
        QSizePolicy.Expanding, QSizePolicy.Expanding)
      keywords_label.setWordWrap(True)
      keywords_label.setFont(font)

      category_row_layout.addWidget(keywords_label)

      category_layout.addLayout(category_row_layout)

    self.categorization_content_horizontalLayout.addLayout(category_layout)

  def show_category_dialog(self, category_id):
    dialog = CategoryDialogView(self, self._viewmodel._category_service,
                                self._viewmodel._keyword_service, category_id)
    if dialog.exec_():
      self._viewmodel.load_categories()

  def restore_defaults(self):
    dialog = QMessageBox()
    dialog.setWindowTitle("Restore defaults")
    dialog.setText(
        "Are you sure you want to restore default categories?\nThis action cannot be undone and might take a while.")
    dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    dialog.setDefaultButton(QMessageBox.No)
    result = dialog.exec_()

    if result == QMessageBox.Yes:
      self._viewmodel.restore_defaults()

  def retroactive_categorization(self, skip_confirmation: bool = False):
    if not skip_confirmation:
      dialog = QMessageBox()
      dialog.setWindowTitle("Retroactive Categorization")
      dialog.setText(
        "Are you sure you want to retroactively categorize all entries based on current ruleset?\n"
        "This action cannot be undone and might take a while.")
      dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
      dialog.setDefaultButton(QMessageBox.No)
      result = dialog.exec_()

      if result == QMessageBox.No:
        return

    self.progress_dialog = self.show_progress_dialog(
      "Progress", "Categorizing entries...")

    # Connect the progress signal before starting the categorization
    self._viewmodel.retroactive_categorization_progress.connect(
      self.update_progress_dialog)

    # Start the categorization process
    success = self._viewmodel.retroactive_categorization()

    # Disconnect the signal after the process is complete
    self._viewmodel.retroactive_categorization_progress.disconnect(
      self.update_progress_dialog)

    self.progress_dialog.close()

    if success:
      QMessageBox.information(
        self, "Retroactive Categorization", "Categorization completed successfully.")
    else:
      QMessageBox.critical(
        self, "Retroactive Categorization", "An error occurred during categorization.")

  def update_progress_dialog(self, current: int, total: int):
    if hasattr(self, 'progress_dialog'):
      progress = int((current / total) * 100)
      self.progress_dialog.setValue(progress)
      QCoreApplication.processEvents()

  def show_progress_dialog(self, title, message):
    progress_dialog = QProgressDialog(message, None, 0, 100, self)
    progress_dialog.setWindowTitle(title)
    progress_dialog.setWindowModality(Qt.WindowModal)
    progress_dialog.setMinimumDuration(0)
    progress_dialog.setValue(0)
    progress_dialog.setCancelButton(None)
    progress_dialog.show()
    QCoreApplication.processEvents()
    return progress_dialog

  def show_categorization_helper(self):
    dialog = CategorizationHelperView(self, self._viewmodel._activity_service,
                                      self._viewmodel._category_service, self._viewmodel._keyword_service)
    dialog.exec_()
    self._viewmodel.load_categories()

  def clear_layout(self, layout):
    while layout.count():
      item = layout.takeAt(0)
      widget = item.widget()
      if widget is not None:
        widget.deleteLater()
      else:
        if isinstance(item, QSpacerItem):
          continue
        self.clear_layout(item.layout())

  def update_ui(self):
    self.clear_layout(self.categorization_content_horizontalLayout)
    self.categories_setup()

  def closeEvent(self, event):
    self._viewmodel.property_changed.disconnect(
      self.on_viewmodel_property_changed)
    super().closeEvent(event)
