""" Dashboard UI """
from collections import defaultdict
from datetime import datetime, timedelta

from PySide6 import QtCharts
from PySide6.QtCharts import QChart
from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect, QSize, Qt)
from PySide6.QtGui import (QColor, QFont, QPainter)
from PySide6.QtWidgets import (QCalendarWidget, QCheckBox,
                               QDialog, QDialogButtonBox, QDoubleSpinBox,
                               QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QLayout, QMainWindow, QMenuBar, QProgressBar,
                               QPushButton, QScrollArea, QSizePolicy,
                               QSpacerItem, QSpinBox, QStatusBar, QTabWidget,
                               QVBoxLayout, QWidget)

from focuswatch.database.activity_manager import ActivityManager
from focuswatch.database.category_manager import CategoryManager
from focuswatch.database.keyword_manager import KeywordManager
from focuswatch.ui.category_dialog import CategoryDialog
from focuswatch.ui.timeline import TimelineComponent
from focuswatch.ui.utils import (get_category_color,
                                 get_contrasting_text_color)


class Dashboard(QMainWindow):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.selected_date = datetime.now()
    # TODO date_start date_end when selected time period > 1 day ?

    self._activity_manager = ActivityManager()
    self._category_manager = CategoryManager()
    self._keyword_manager = KeywordManager()
    self.setupUi(self)
    self.time_breakdown_setup()
    self.top_application_setup()

  def select_date(self):
    """ Select date for dashboard """
    sender_name = self.sender().objectName()

    # Previous day
    if sender_name == 'date_prev_button':
      self.selected_date = self.selected_date - timedelta(days=1)

    # Select date
    elif sender_name == 'date_button':
      # Create a dialog to select a date
      calendar_dialog = QDialog(self)
      calendar_dialog.setWindowTitle("Select a Date")

      layout = QVBoxLayout()
      calendar = QCalendarWidget()
      layout.addWidget(calendar)
      confirm_button = QPushButton("Confirm Date")
      layout.addWidget(confirm_button)

      # Define a slot to capture the selected date
      def get_selected_date():
        self.selected_date = calendar.selectedDate().toPython()
        calendar_dialog.accept()

      confirm_button.clicked.connect(get_selected_date)
      calendar_dialog.setLayout(layout)
      calendar_dialog.exec_()
      self.onShow(self.showEvent)

    # Next day
    elif sender_name == 'date_next_button':
      self.selected_date = self.selected_date + timedelta(days=1)
      self.date_button.setText(str(self.selected_date))

    # Refresh the dashboard
    self.onShow(self.showEvent)

  """ Dashboard tab """

  def time_breakdown_setup(self):
    """ Setup the time breakdown component for the selected date. """
    categories_by_total_time = self._category_manager.get_date_category_time_totals(
      self.selected_date)

    breakdown_verticalLayout = QVBoxLayout()
    breakdown_verticalLayout.setSizeConstraint(
        QLayout.SetDefaultConstraint)

    if not categories_by_total_time:
      info_label = QLabel(self.time_breakdown_scrollAreaWidgetContents)
      info_label.setText("No data for the selected period")

      font = QFont()
      font.setPointSize(16)

      info_label.setFont(font)
      info_label.setAlignment(Qt.AlignCenter)

      breakdown_verticalLayout.addWidget(info_label)
      self.time_breakdown_main_layout.addLayout(breakdown_verticalLayout)
      return

    total_time = 0

    for vals in categories_by_total_time:
      total_time += vals[-1]

    pie_chart = QtCharts.QChartView()
    pie_chart.setRenderHint(QPainter.Antialiasing)
    pie_chart.setMinimumSize(300, 300)
    pie_chart.chart().setAnimationOptions(QChart.AllAnimations)
    pie_chart.chart().setBackgroundVisible(False)

    series = QtCharts.QPieSeries()

    for vals in categories_by_total_time:
      category_horizontalLayout = QHBoxLayout()
      category_horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
      cat_id, time = vals
      category = self._category_manager.get_category_by_id(cat_id)
      id, name, parent_category_id, color = category

      text = ""
      color = get_category_color(id)

      text += name + ' -'
      hours = time // 3600
      minutes = (time // 60) % 60
      seconds = time % 60
      if hours:
        text += f" {hours}h"
      if minutes:
        text += f" {minutes}m"
      if seconds:
        text += f" {seconds}s"

      category_label = QLabel(self.time_breakdown_scrollAreaWidgetContents)
      category_label.setText(
        f"{text}")
      if color:
        category_label.setStyleSheet(f"color: {color};")
      category_label.setMaximumHeight(20)

      font = QFont()
      font.setBold(True)
      font.setPointSize(10)

      category_label.setFont(font)

      slice = QtCharts.QPieSlice(text, time / 60)

      if color:
        slice.setColor(QColor(color))

      slice.hovered.connect(slice.setExploded)
      slice.setExplodeDistanceFactor(0.07)
      slice.hovered.connect(slice.setLabelVisible)

      series.append(slice)

      category_horizontalLayout.addWidget(category_label)

      category_progress = QProgressBar(
        self.time_breakdown_scrollAreaWidgetContents)
      category_progress.setValue((time / total_time) * 100)
      category_progress.setFixedHeight(15)

      base_color = QColor(color)

      # Create gradient stops for smooth transition
      contrasting_color = get_contrasting_text_color(color)

      # Multiplier is needed for really dark colors
      multiplier = 1 if contrasting_color == 'black' else 2

      stop_1 = f"stop: 0 {base_color.darker(100 - (30 * multiplier)).name()},"
      stop_2 = f"stop: 0.3 {base_color.darker(
        100 - (20 * multiplier)).name()},"
      stop_3 = f"stop: 0.7 {base_color.darker(
        100 - (10 * multiplier)).name()},"
      stop_4 = f"stop: 1 {base_color.name()}"

      category_progress.setStyleSheet(
          f"""
          QProgressBar {{
              text-align: top;
              border-radius: 3px;
              {"color: " + contrasting_color if category_progress.value() >
               45 else ''}
          }}
          QProgressBar::chunk {{
              background: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 0,
                  {stop_1}
                  {stop_2}
                  {stop_3}
                  {stop_4}
              );
              border-radius: 3px;
          }}
          """
      )
      category_progress.setFixedWidth(250)
      category_horizontalLayout.addWidget(category_progress)
      breakdown_verticalLayout.addLayout(category_horizontalLayout)

    series.setHoleSize(0.35)
    pie_chart.chart().addSeries(series)
    # pie_chart.chart().legend().hide()

    legend = pie_chart.chart().legend()
    legend.setVisible(False)
    # legend.setAlignment(Qt.AlignBottom)
    # legend.setFont(QFont("Helvetica", 9))

    verticalSpacer = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    breakdown_verticalLayout.addItem(verticalSpacer)
    self.time_breakdown_main_layout.addLayout(breakdown_verticalLayout)
    self.time_breakdown_main_layout.addWidget(pie_chart)

  def top_application_setup(self):
    """ Setup the top application component for the selected date. """
    window_class_by_total_time = self._activity_manager.get_date_entries_class_time_total(
      self.selected_date)

    breakdown_verticalLayout = QVBoxLayout()
    breakdown_verticalLayout.setSizeConstraint(
        QLayout.SetDefaultConstraint)

    if not window_class_by_total_time:
      info_label = QLabel(self.top_apps_scrollAreaWidgetContents)
      info_label.setText("No data for the selected period")

      font = QFont()
      font.setPointSize(16)

      info_label.setFont(font)
      info_label.setAlignment(Qt.AlignCenter)

      breakdown_verticalLayout.addWidget(info_label)
      self.top_apps_main_layout.addLayout(breakdown_verticalLayout)
      return

    total_time = 0

    for vals in window_class_by_total_time:
      if vals[0] != 'afk':
        total_time += vals[-1]

    pie_chart = QtCharts.QChartView()
    pie_chart.setRenderHint(QPainter.Antialiasing)
    pie_chart.setMinimumSize(300, 300)
    pie_chart.chart().setAnimationOptions(QChart.AllAnimations)
    pie_chart.chart().setBackgroundVisible(False)

    series = QtCharts.QPieSeries()

    for vals in window_class_by_total_time:
      class_horizontalLayout = QHBoxLayout()
      class_horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)

      window_class, _, time = vals
      if window_class == "afk":
        continue
      if time < 10:
        continue
      category_id = self._activity_manager.get_longest_duration_category_id_for_window_class_on_date(
        self.selected_date, window_class)
      category = self._category_manager.get_category_by_id(category_id)
      id, name, parent_category_id, color = category
      color = get_category_color(id)

      text = ""

      text += window_class + ' -'
      hours = time // 3600
      minutes = (time // 60) % 60
      seconds = time % 60
      if hours:
        text += f" {hours}h"
      if minutes:
        text += f" {minutes}m"
      if seconds:
        text += f" {seconds}s"

      class_label = QLabel(self.top_apps_scrollAreaWidgetContents)
      class_label.setText(f"{text}")
      class_label.setStyleSheet(f"color: {color};")
      class_label.setMaximumHeight(20)

      font = QFont()
      font.setBold(True)
      font.setPointSize(10)

      class_label.setFont(font)

      slice = QtCharts.QPieSlice(text, time / 60)

      slice.hovered.connect(slice.setExploded)
      slice.setExplodeDistanceFactor(0.07)
      slice.hovered.connect(slice.setLabelVisible)
      slice.setColor(QColor(color))

      series.append(slice)

      class_progress = QProgressBar(
        self.time_breakdown_scrollAreaWidgetContents)
      class_progress.setValue((time / total_time) * 100)
      class_progress.setFixedHeight(15)

      base_color = QColor(color)

      # Create gradient stops for smooth transition
      contrasting_color = get_contrasting_text_color(color)
      multiplier = 1 if contrasting_color == 'black' else 2

      stop_1 = f"stop: 0 {base_color.darker(100 - (30 * multiplier)).name()},"
      stop_2 = f"stop: 0.3 {base_color.darker(
        100 - (20 * multiplier)).name()},"
      stop_3 = f"stop: 0.7 {base_color.darker(
        100 - (10 * multiplier)).name()},"
      stop_4 = f"stop: 1 {base_color.name()}"

      class_progress.setStyleSheet(
          f"""
          QProgressBar {{
              text-align: top;
              border-radius: 3px;
              {"color: " + contrasting_color if class_progress.value() > 45 else ''}
          }}
          QProgressBar::chunk {{
              background: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 0,
                  {stop_1}
                  {stop_2}
                  {stop_3}
                  {stop_4}
              );
              border-radius: 3px;
          }}
          """
      )
      class_progress.setFixedWidth(250)

      class_horizontalLayout.addWidget(class_label)
      class_horizontalLayout.addWidget(class_progress)

      breakdown_verticalLayout.addLayout(class_horizontalLayout)

    series.setHoleSize(0.35)
    # series.setLabelsPosition(QtCharts.QPieSlice.LabelInsideNormal)
    pie_chart.chart().addSeries(series)

    legend = pie_chart.chart().legend()
    legend.setVisible(False)
    # legend.setAlignment(Qt.AlignBottom)
    # legend.setFont(QFont("Helvetica", 9))

    verticalSpacer = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    breakdown_verticalLayout.addItem(verticalSpacer)

    self.top_apps_main_layout.addLayout(breakdown_verticalLayout)
    self.top_apps_main_layout.addWidget(pie_chart)

  """ Categorization tab """

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
    dialog = CategoryDialog(self, category, keywords)
    result = dialog.exec_()
    if result:
      del_keywords = dialog.del_keywords
      new_keywords = dialog.new_keywords
      new_color = dialog.color

      if category is not None:
        color = new_color if new_color != category[-1] and new_color is not None else category[-1]
      else:
        color = new_color
      new_name = dialog.name_lineEdit.text()
      parent = dialog.parent_comboBox.currentText()
      if parent != 'None':
        parent_id = self._category_manager.get_category_id_from_name(parent)
      else:
        parent_id = None

      if category is not None:
        self._category_manager.update_category(
          category_id, new_name, parent_id, color)
      else:
        self._category_manager.create_category(new_name, parent_id, color)
        category_id = self._category_manager.get_category_id_from_name(
          new_name)

      for keyw in del_keywords:
        self._keyword_manager.delete_keyword(keyw[0])
      for keyw in new_keywords:
        self._keyword_manager.add_keyword(keyw[1], category_id)

    self.onShow(self.showEvent)
    self.tabWidget.setCurrentIndex(1)

  def get_keywords_for_category(self, category_id):
    keywords = self._keyword_manager.get_all_keywords()
    cat_key = defaultdict(list)
    for keyword in keywords:
      cat_key[str(keyword[-1])].append(keyword)

    return cat_key[category_id]

  def categories_setup(self):
    # Get all categories and keywords
    categories = self._category_manager.get_all_categories()
    keywords = self._keyword_manager.get_all_keywords()

    # Make a dict category: keywords
    cat_key = defaultdict(list)
    for keyword in keywords:
      cat_key[keyword[-1]].append(keyword[1])

    # Create a temporary dictionary to store categories with parent-child relationships
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

    # Organize cat_dict with children next to parents
    cat_dict = defaultdict(list)

    def organize_categories(cat_id):
      category = temp_cat_dict[cat_id]
      cat_dict[cat_id] = category
      for child_id in category['children']:
        organize_categories(child_id)

    # Start with categories that have no parent
    root_categories = [cat_id for cat_id, _, parent_cat_id,
                       _ in categories if parent_cat_id is None]
    for root_cat_id in root_categories:
      organize_categories(root_cat_id)

    # Create layouts
    category_name_verticalLayout = QVBoxLayout()
    category_name_verticalLayout.setObjectName(
      u"category_name_verticalLayout")
    category_name_verticalLayout.setSizeConstraint(
      QLayout.SetDefaultConstraint)
    category_name_verticalLayout.setContentsMargins(-1, 0, 0, -1)

    category_keywords_verticalLayout = QVBoxLayout()
    category_keywords_verticalLayout.setObjectName(
      u"category_keywords_verticalLayout")
    category_keywords_verticalLayout.setSizeConstraint(
        QLayout.SetDefaultConstraint)

    category_spacer_verticalLayout = QVBoxLayout()
    category_spacer_verticalLayout.setObjectName(
      u"category_spacer_verticalLayout")

    # Size policies
    cat_label_sizePolicy = QSizePolicy(
      QSizePolicy.Maximum, QSizePolicy.Preferred)
    cat_label_sizePolicy.setHorizontalStretch(0)
    cat_label_sizePolicy.setVerticalStretch(0)

    for key, vals in cat_dict.items():
      # Name label
      category_name_horizontalLayout = QHBoxLayout()
      category_name_horizontalLayout.setObjectName(
        u"category_name_horizontalLayout")
      category_name_horizontalLayout.setSizeConstraint(
        QLayout.SetMinimumSize)
      category_name_horizontalLayout.setContentsMargins(-1, 0, 0, -1)
      category_name_horizontalLayout.setAlignment(Qt.AlignLeft)

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
      category_name_horizontalLayout.addItem(horizontalSpacer)
#
      category_button.setText(f"{vals['name']}")
      font = QFont()
      font.setPointSize(12)
      category_button.setFont(font)

      category_name_horizontalLayout.addWidget(category_button)
      category_name_verticalLayout.addLayout(category_name_horizontalLayout)

      # Keywords label
      keywords_label = QLabel(self.categorization_scrollAreaWidgetContents)
      keywords_label.setText("Keywords: " + ' | '.join(vals['keywords']))
      keywords_label.setMinimumSize(QSize(800, 0))
      keywords_label.setWordWrap(True)
      font = QFont()
      font.setPointSize(12)
      keywords_label.setFont(font)
      category_keywords_verticalLayout.addWidget(keywords_label)

      # Spacer
      horizontalSpacer = QSpacerItem(
          60, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
      category_spacer_verticalLayout.addItem(horizontalSpacer)

    horizontalSpacer_1 = QSpacerItem(
      60, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
    horizontalSpacer_2 = QSpacerItem(
      200, 20, QSizePolicy.Maximum, QSizePolicy.Minimum)

    self.categorization_content_horizontalLayout.addLayout(
      category_name_verticalLayout)
    self.categorization_content_horizontalLayout.addItem(
      horizontalSpacer_1)
    self.categorization_content_horizontalLayout.addLayout(
      category_keywords_verticalLayout)
    self.categorization_content_horizontalLayout.addItem(
      horizontalSpacer_2)
    self.categorization_content_horizontalLayout.addLayout(
        category_spacer_verticalLayout)

  def dashboard_tab_setup(self):
    # self._timeline.setup_timeline()
    self.time_breakdown_setup()
    self.top_application_setup()

  def categorization_tab_setup(self):
    self.categories_setup()

  def restore_defaults(self):
    self._category_manager.insert_default_categories()
    self.onShow(self.showEvent)
    self.tabWidget.setCurrentIndex(1)

  def setupUi(self, Dashboard):
    if not Dashboard.objectName():
      Dashboard.setObjectName(u"Dashboard")
      # Resize only on first run
      if not Dashboard.isVisible():
        Dashboard.resize(1600, 900)
    Dashboard.setTabShape(QTabWidget.Rounded)
    self.centralwidget = QWidget(Dashboard)
    self.centralwidget.setObjectName(u"centralwidget")
    self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
    self.verticalLayout_2.setObjectName(u"verticalLayout_2")
    self.verticalLayout = QVBoxLayout()
    self.verticalLayout.setObjectName(u"verticalLayout")
    self.tabWidget = QTabWidget(self.centralwidget)
    self.tabWidget.setObjectName(u"tabWidget")
    self.tabWidget.setTabShape(QTabWidget.Rounded)
    self.tabWidget.setDocumentMode(False)
    self.tabWidget.setTabBarAutoHide(False)
    self.dashboard_tab = QWidget()
    self.dashboard_tab.setObjectName(u"dashboard_tab")
    self.gridLayout = QGridLayout(self.dashboard_tab)
    self.gridLayout.setObjectName(u"gridLayout")
    self.time_breakdown_frame = QFrame(self.dashboard_tab)
    self.time_breakdown_frame.setObjectName(u"time_breakdown_frame")
    self.time_breakdown_frame.setFrameShape(QFrame.StyledPanel)
    self.time_breakdown_frame.setFrameShadow(QFrame.Raised)
    self.verticalLayout_4 = QVBoxLayout(self.time_breakdown_frame)
    self.verticalLayout_4.setSpacing(0)
    self.verticalLayout_4.setObjectName(u"verticalLayout_4")
    self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
    self.time_breakdown_label = QLabel(self.time_breakdown_frame)
    self.time_breakdown_label.setObjectName(u"time_breakdown_label")
    font = QFont()
    font.setPointSize(12)
    font.setBold(False)
    self.time_breakdown_label.setFont(font)
    self.time_breakdown_label.setAutoFillBackground(False)
    self.time_breakdown_label.setAlignment(
      Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
    self.time_breakdown_label.setMargin(4)

    self.verticalLayout_4.addWidget(self.time_breakdown_label)

    self.time_breakdown_scrollArea = QScrollArea(self.time_breakdown_frame)
    self.time_breakdown_scrollArea.setObjectName(u"time_breakdown_scrollArea")
    self.time_breakdown_scrollArea.setWidgetResizable(True)
    self.time_breakdown_scrollAreaWidgetContents = QWidget()
    self.time_breakdown_scrollAreaWidgetContents.setObjectName(
      u"time_breakdown_scrollAreaWidgetContents")
    self.time_breakdown_scrollAreaWidgetContents.setGeometry(
      QRect(0, 0, 611, 693))
    self.verticalLayout_3 = QVBoxLayout(
      self.time_breakdown_scrollAreaWidgetContents)
    self.verticalLayout_3.setObjectName(u"verticalLayout_3")
    self.time_breakdown_main_layout = QVBoxLayout()
    self.time_breakdown_main_layout.setObjectName(
      u"time_breakdown_main_layout")

    self.verticalLayout_3.addLayout(self.time_breakdown_main_layout)

    self.time_breakdown_scrollArea.setWidget(
      self.time_breakdown_scrollAreaWidgetContents)

    self.verticalLayout_4.addWidget(self.time_breakdown_scrollArea)

    self.gridLayout.addWidget(self.time_breakdown_frame, 2, 2, 1, 1)

    """ Timeline setup """
    self._timeline = TimelineComponent(
        self.dashboard_tab, self._activity_manager, self._category_manager, self.selected_date)
    self.timeline_frame = self._timeline.setupUi(self._timeline)

    self.gridLayout.addWidget(self.timeline_frame, 2, 0, 1, 1)

    # Top applications setup
    self.top_apps_frame = QFrame(self.dashboard_tab)
    self.top_apps_frame.setObjectName(u"top_apps_frame")
    self.top_apps_frame.setMinimumSize(QSize(50, 0))
    self.top_apps_frame.setFrameShape(QFrame.StyledPanel)
    self.top_apps_frame.setFrameShadow(QFrame.Raised)
    self.verticalLayout_8 = QVBoxLayout(self.top_apps_frame)
    self.verticalLayout_8.setSpacing(0)
    self.verticalLayout_8.setObjectName(u"verticalLayout_8")
    self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
    self.top_apps_label = QLabel(self.top_apps_frame)
    self.top_apps_label.setObjectName(u"top_apps_label")
    self.top_apps_label.setFont(font)
    self.top_apps_label.setAutoFillBackground(False)
    self.top_apps_label.setAlignment(
      Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
    self.top_apps_label.setMargin(4)

    self.verticalLayout_8.addWidget(self.top_apps_label)

    self.top_apps_scrollArea = QScrollArea(self.top_apps_frame)
    self.top_apps_scrollArea.setObjectName(u"top_apps_scrollArea")
    self.top_apps_scrollArea.setWidgetResizable(True)
    self.top_apps_scrollAreaWidgetContents = QWidget()
    self.top_apps_scrollAreaWidgetContents.setObjectName(
      u"top_apps_scrollAreaWidgetContents")
    self.top_apps_scrollAreaWidgetContents.setGeometry(QRect(0, 0, 610, 693))
    self.verticalLayout_7 = QVBoxLayout(self.top_apps_scrollAreaWidgetContents)
    self.verticalLayout_7.setObjectName(u"verticalLayout_7")
    self.top_apps_main_layout = QVBoxLayout()
    self.top_apps_main_layout.setSpacing(0)
    self.top_apps_main_layout.setObjectName(u"top_apps_main_layout")

    self.verticalLayout_7.addLayout(self.top_apps_main_layout)

    self.top_apps_scrollArea.setWidget(self.top_apps_scrollAreaWidgetContents)

    self.verticalLayout_8.addWidget(self.top_apps_scrollArea)

    self.gridLayout.addWidget(self.top_apps_frame, 2, 4, 1, 1)

    self.verticalSpacer = QSpacerItem(
      20, 5, QSizePolicy.Minimum, QSizePolicy.Minimum)

    self.gridLayout.addItem(self.verticalSpacer, 1, 0, 1, 1)

    self.date_nav_frame = QFrame(self.dashboard_tab)
    self.date_nav_frame.setObjectName(u"date_nav_frame")
    sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
    sizePolicy1.setHorizontalStretch(0)
    sizePolicy1.setVerticalStretch(0)
    sizePolicy1.setHeightForWidth(
      self.date_nav_frame.sizePolicy().hasHeightForWidth())
    self.date_nav_frame.setSizePolicy(sizePolicy1)
    self.date_nav_frame.setMaximumSize(QSize(250, 16777215))
    self.date_nav_frame.setAutoFillBackground(False)
    self.date_nav_frame.setFrameShape(QFrame.NoFrame)
    self.date_nav_frame.setFrameShadow(QFrame.Raised)
    self.date_nav_frame.setLineWidth(0)
    self.horizontalLayout = QHBoxLayout(self.date_nav_frame)
    self.horizontalLayout.setObjectName(u"horizontalLayout")
    self.date_prev_button = QPushButton(self.date_nav_frame)
    self.date_prev_button.setObjectName(u"date_prev_button")
    sizePolicy1.setHeightForWidth(
      self.date_prev_button.sizePolicy().hasHeightForWidth())
    self.date_prev_button.setSizePolicy(sizePolicy1)
    self.date_prev_button.setMaximumSize(QSize(20, 16777215))
    self.date_prev_button.clicked.connect(self.select_date)

    self.horizontalLayout.addWidget(self.date_prev_button)

    self.date_button = QPushButton(self.date_nav_frame)
    self.date_button.setObjectName(u"date_button")
    self.date_button.clicked.connect(self.select_date)
    sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    sizePolicy2.setHorizontalStretch(0)
    sizePolicy2.setVerticalStretch(0)
    sizePolicy2.setHeightForWidth(
      self.date_button.sizePolicy().hasHeightForWidth())
    self.date_button.setSizePolicy(sizePolicy2)
    self.date_button.setMaximumSize(QSize(600, 16777215))
    if str(self.selected_date.strftime("%Y-%m-%d")) == str(datetime.today().strftime("%Y-%m-%d")):
      self.date_button.setText("Today")
    else:
      self.date_button.setText(str(self.selected_date.strftime("%Y-%m-%d")))

    self.horizontalLayout.addWidget(self.date_button)

    self.date_next_button = QPushButton(self.date_nav_frame)
    self.date_next_button.setObjectName(u"date_next_button")
    self.date_next_button.setMaximumSize(QSize(20, 16777215))
    self.date_next_button.clicked.connect(self.select_date)

    self.horizontalLayout.addWidget(self.date_next_button)

    self.horizontalSpacer_3 = QSpacerItem(
      15, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

    self.horizontalLayout.addItem(self.horizontalSpacer_3)

    self.time_period_button = QPushButton(self.date_nav_frame)
    self.time_period_button.setObjectName(u"time_period_button")
    self.time_period_button.setEnabled(False)

    self.horizontalLayout.addWidget(self.time_period_button)

    self.gridLayout.addWidget(self.date_nav_frame, 0, 0, 1, 4)

    self.horizontalSpacer_2 = QSpacerItem(
      5, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)

    self.gridLayout.addItem(self.horizontalSpacer_2, 2, 1, 1, 1)

    self.frame = QFrame(self.dashboard_tab)
    self.frame.setObjectName(u"frame")
    self.frame.setLayoutDirection(Qt.RightToLeft)
    self.frame.setStyleSheet(u"")
    self.frame.setFrameShape(QFrame.NoFrame)
    self.frame.setFrameShadow(QFrame.Raised)
    self.horizontalLayout_3 = QHBoxLayout(self.frame)
    self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
    self.refreshButton = QPushButton(self.frame)
    self.refreshButton.setObjectName(u"refreshButton")
    self.refreshButton.setMaximumSize(QSize(80, 16777215))

    self.horizontalLayout_3.addWidget(self.refreshButton)

    self.horizontalSpacer = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.horizontalLayout_3.addItem(self.horizontalSpacer)

    self.gridLayout.addWidget(self.frame, 0, 4, 1, 1)

    self.tabWidget.addTab(self.dashboard_tab, "")
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

    self.tabWidget.addTab(self.categorization_tab, "")
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
    self.tabWidget.addTab(self.settings_tab, "")

    self.verticalLayout.addWidget(self.tabWidget)

    self.verticalLayout_2.addLayout(self.verticalLayout)

    Dashboard.setCentralWidget(self.centralwidget)
    self.menubar = QMenuBar(Dashboard)
    self.menubar.setObjectName(u"menubar")
    self.menubar.setGeometry(QRect(0, 0, 1600, 22))
    Dashboard.setMenuBar(self.menubar)
    self.statusbar = QStatusBar(Dashboard)
    self.statusbar.setObjectName(u"statusbar")
    Dashboard.setStatusBar(self.statusbar)

    self.retranslateUi(Dashboard)

    self.tabWidget.setCurrentIndex(0)

    QMetaObject.connectSlotsByName(Dashboard)

    self.showEvent = self.onShow
    self.refreshButton.clicked.connect(self.showEvent)
  # setupUi

  def retranslateUi(self, Dashboard):
    Dashboard.setWindowTitle(QCoreApplication.translate(
      "Dashboard", u"FocusWatch", None))
    self.time_breakdown_label.setText(
      QCoreApplication.translate("Dashboard", u"Top categories", None))
    self.top_apps_label.setText(QCoreApplication.translate(
      "Dashboard", u"Top applications", None))
    self.date_prev_button.setText(
      QCoreApplication.translate("Dashboard", u"<", None))
    # self.date_button.setText(
    # QCoreApplication.translate("Dashboard", u"Today", None))
    self.date_next_button.setText(
      QCoreApplication.translate("Dashboard", u">", None))
    self.time_period_button.setText(
      QCoreApplication.translate("Dashboard", u"Day view", None))
    self.refreshButton.setText(
      QCoreApplication.translate("Dashboard", u"Refresh", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.dashboard_tab), QCoreApplication.translate("Dashboard", u"Dashboard", None))
    self.categorization_info_label.setText(QCoreApplication.translate("Dashboard", u"Rules for categorizing events. An event can only have one category. If several categories match, the deepest one will be chosen.\n"
                                                                      "To re-categorize previous entries after adding or updating category, click \"Retrospective categorization\" button. (not yet implemented)", None))
    self.categorization_addCategory.setText(
      QCoreApplication.translate("Dashboard", u"Add category", None))
    self.pushButton_4.setText(QCoreApplication.translate(
      "Dashboard", u"Retrospective categorization", None))
    self.categorization_restoreDefaults.setText(
      QCoreApplication.translate("Dashboard", u"Restore defaults", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.categorization_tab), QCoreApplication.translate("Dashboard", u"Categorization", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.settings_tab), QCoreApplication.translate("Dashboard", u"Settings", None))
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
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.settings_tab), QCoreApplication.translate("Dashboard", u"Settings", None))
  # retranslateUi

  def onShow(self, event):
    """ This is probably a bad practice """
    # TODO
    self.setupUi(self)
    self.dashboard_tab_setup()
    self.categorization_tab_setup()
