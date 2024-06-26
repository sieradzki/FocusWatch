""" Categorization tab for the FocusWatch Ui. """
from collections import defaultdict

from PySide6.QtCore import QCoreApplication, QRect, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLayout,
                               QPushButton, QScrollArea, QSizePolicy,
                               QSpacerItem, QVBoxLayout, QWidget)

from focuswatch.ui.category_dialog import CategoryDialog
from focuswatch.ui.utils import get_category_color, get_contrasting_text_color


class CategorizationTab(QWidget):
  def __init__(self, category_manager, keyword_manager, parent=None):
    super().__init__(parent)
    self._category_manager = category_manager
    self._keyword_manager = keyword_manager
    self._parent = parent
    # self.setupUi()

  def setupUi(self):
    self.categorization_tab = QWidget()
    self.categorization_tab.setObjectName(u"categorization_tab")

    self.verticalLayout_5 = QVBoxLayout(self.categorization_tab)
    self.verticalLayout_5.setObjectName(u"verticalLayout_5")
    self.categorization_main_frame = QFrame(self.categorization_tab)
    self.categorization_main_frame.setObjectName(u"categorization_main_frame")
    self.categorization_main_frame.setFrameShape(QFrame.StyledPanel)
    self.categorization_main_frame.setFrameShadow(QFrame.Raised)
    self.verticalLayout_12 = QVBoxLayout(self.categorization_main_frame)
    self.verticalLayout_12.setObjectName(u"verticalLayout_12")
    self.categorization_info_label = QLabel(self.categorization_main_frame)
    self.categorization_info_label.setObjectName(u"categorization_info_label")
    font1 = QFont()
    font1.setPointSize(12)
    self.categorization_info_label.setFont(font1)
    self.categorization_info_label.setScaledContents(False)
    self.categorization_info_label.setWordWrap(True)

    self.verticalLayout_12.addWidget(self.categorization_info_label)

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
    self.categorization_addCategory.clicked.connect(self.show_category_dialog)

    self.categorization_button_horizontalLayout.addWidget(
      self.categorization_addCategory)

    self.horizontalSpacer_4 = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.categorization_button_horizontalLayout.addItem(
      self.horizontalSpacer_4)

    self.pushButton_4 = QPushButton(
      self.categorization_scrollAreaWidgetContents)
    self.pushButton_4.setObjectName(u"pushButton_4")
    self.pushButton_4.setEnabled(False)

    self.categorization_button_horizontalLayout.addWidget(self.pushButton_4)

    self.categorization_restoreDefaults = QPushButton(
      self.categorization_scrollAreaWidgetContents)
    self.categorization_restoreDefaults.setObjectName(
      u"categorization_restoreDefaults")
    self.categorization_restoreDefaults.clicked.connect(self.restore_defaults)
    self.categorization_restoreDefaults.setEnabled(False)

    self.categorization_button_horizontalLayout.addWidget(
      self.categorization_restoreDefaults)

    self.categorization_verticalLayout.addLayout(
      self.categorization_button_horizontalLayout)

    self.verticalLayout_13.addLayout(self.categorization_verticalLayout)

    self.categorization_scrollArea.setWidget(
      self.categorization_scrollAreaWidgetContents)

    self.verticalLayout_12.addWidget(self.categorization_scrollArea)

    self.verticalLayout_5.addWidget(self.categorization_main_frame)

    self.showEvent = self.onShow

    self.categories_setup()
    self.retranslateUi()
    return self.categorization_tab

  def onShow(self, event):
    self.clear_layout(self.categorization_content_horizontalLayout)
    self.categories_setup()

  def clear_layout(self, layout):
    while layout.count():
      item = layout.takeAt(0)
      widget = item.widget()
      if widget is not None:
        widget.deleteLater()
      else:
        # If the item is a QSpacerItem, just continue
        if isinstance(item, QSpacerItem):
          continue
        # If the item is a layout, clear it recursively
        sub_layout = item.layout()
        if sub_layout is not None:
          self.clear_layout(sub_layout)

  def retranslateUi(self):
    self.categorization_info_label.setText(QCoreApplication.translate("Dashboard", u"Rules for categorizing events. An event can only have one category. If several categories match, the deepest one will be chosen.\n"
                                                                      "To re-categorize previous entries after adding or updating category, click \"Retrospective categorization\" button. (not yet implemented)", None))
    self.categorization_addCategory.setText(
      QCoreApplication.translate("Dashboard", u"Add category", None))
    self.pushButton_4.setText(QCoreApplication.translate(
      "Dashboard", u"Retrospective categorization", None))
    self.categorization_restoreDefaults.setText(
      QCoreApplication.translate("Dashboard", u"Restore defaults", None))

  def show_category_dialog(self):
    """ This is show edit category, add new dialog for create new? """
    sender_name = self.sender().objectName()
    if sender_name != 'categorization_addCategory':
      category_id = sender_name.split(sep='_')[-1]
      category = self._category_manager.get_category_by_id(category_id)
      keywords = self.get_keywords_for_category(category_id)
    else:
      category = None
      keywords = []
    dialog = CategoryDialog(self, self._category_manager,
                            self._keyword_manager, category)
    result = dialog.exec_()
    if result:
      if not category:
        new_keywords = dialog.new_keywords

      new_color = dialog.color

      if category:
        if new_color and new_color != category[-1]:
          color = new_color
        else:
          color = category[-1]
      else:
        color = new_color

      new_name = dialog.name_lineEdit.text()
      parent = dialog.parent_comboBox.currentText()

      if parent != 'None':
        parent_id = self._category_manager.get_category_id_from_name(parent)
      else:
        parent_id = None

      if category:
        self._category_manager.update_category(
            category_id, new_name, parent_id, color)
      else:
        self._category_manager.create_category(
            new_name, parent_id, color)
        category_id = self._category_manager.get_category_id_from_name(
          new_name)

      if not category:
        for keyw in new_keywords:
          self._keyword_manager.add_keyword(
              keyw[1], category_id, keyw[3])

    # self.onShow(self.showEvent)
    # self.tabWidget.setCurrentIndex(1)

    self.onShow(self.showEvent)

  def get_keywords_for_category(self, category_id):
    keywords = self._keyword_manager.get_all_keywords()
    cat_key = defaultdict(list)
    for keyword in keywords:
      cat_key[str(keyword[-1])].append(keyword)

    return cat_key[category_id]

  def categories_setup(self):
    categories = self._category_manager.get_all_categories()
    cat_key = defaultdict(list)
    for category in categories:
      category_keywords = self._keyword_manager.get_keywords_for_category(
        category[0])
      cat_key[category[0]] = [keyword[1] for keyword in category_keywords]

    temp_cat_dict = defaultdict(list)
    for cat_id, name, parent_cat_id, color in categories:
      category = {
        'name': name,
        'color': color,
        'keywords': cat_key[cat_id],
        'children': []
      }
      if parent_cat_id is None:
        temp_cat_dict[cat_id] = category
      elif parent_cat_id not in temp_cat_dict:
        temp_cat_dict[parent_cat_id] = {
          'name': None,
          'color': None,
          'keywords': [],
          'children': [cat_id],
        }
        temp_cat_dict[cat_id] = category
      else:
        parent_category = temp_cat_dict[int(parent_cat_id)]
        parent_category['children'].append(cat_id)
        temp_cat_dict[cat_id] = category

    cat_dict = defaultdict(list)

    def organize_categories(cat_id):
      category = temp_cat_dict[cat_id]
      cat_dict[cat_id] = category
      for child_id in category['children']:
        organize_categories(child_id)

    root_categories = [cat_id for cat_id, _, parent_cat_id,
                       _ in categories if parent_cat_id is None]
    for root_cat_id in root_categories:
      organize_categories(root_cat_id)

    category_layout = QVBoxLayout()
    category_layout.setObjectName(u"category_layout")
    category_layout.setSizeConstraint(QLayout.SetDefaultConstraint)
    category_layout.setContentsMargins(-1, 0, 0, -1)

    cat_label_sizePolicy = QSizePolicy(
      QSizePolicy.Maximum, QSizePolicy.Preferred)
    cat_label_sizePolicy.setHorizontalStretch(0)
    cat_label_sizePolicy.setVerticalStretch(0)

    for key, vals in cat_dict.items():
      category_row_layout = QHBoxLayout()
      category_row_layout.setObjectName(u"category_row_layout")
      category_row_layout.setSizeConstraint(QLayout.SetMinimumSize)
      category_row_layout.setContentsMargins(-1, 0, 0, -1)
      category_row_layout.setAlignment(Qt.AlignLeft)

      category_button = QPushButton(
        self.categorization_scrollAreaWidgetContents)
      category_button.setObjectName(f"category_button_{key}")
      category_button.clicked.connect(self.show_category_dialog)
      cat_label_sizePolicy.setHeightForWidth(
        category_button.sizePolicy().hasHeightForWidth())
      category_button.setSizePolicy(cat_label_sizePolicy)

      color = get_category_color(key)
      font_color = get_contrasting_text_color(color)

      if color:
        category_button.setStyleSheet(
          f"background-color: {color}; color: {font_color};")

      depth = self._category_manager.get_category_depth(key)
      indent = 40 * depth

      horizontalSpacer = QSpacerItem(
        indent, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
      category_row_layout.addItem(horizontalSpacer)

      category_button.setText(f"{vals['name']}")
      font = QFont()
      font.setPointSize(12)
      category_button.setFont(font)

      category_row_layout.addWidget(category_button)

      keywords_label = QLabel(self.categorization_scrollAreaWidgetContents)
      keywords_label.setText("Keywords: " + ' | '.join(vals['keywords']))
      keywords_label.setSizePolicy(
        QSizePolicy.Expanding, QSizePolicy.Expanding)
      keywords_label.setWordWrap(True)
      font = QFont()
      font.setPointSize(12)
      keywords_label.setFont(font)

      category_row_layout.addWidget(keywords_label)

      category_layout.addLayout(category_row_layout)

    self.categorization_content_horizontalLayout.addLayout(category_layout)

  def restore_defaults(self):
    self._category_manager.insert_default_categories()
    self.onShow(self.showEvent)
    # self.tabWidget.setCurrentIndex(1)
