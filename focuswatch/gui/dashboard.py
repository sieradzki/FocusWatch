from collections import defaultdict
from datetime import datetime, timedelta

from PySide6 import QtCharts
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect, QSize, Qt,
                            QTime, QUrl)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
                           QFontDatabase, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette,
                           QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDial, QFrame, QGridLayout,
                               QHBoxLayout, QLabel, QLayout, QMainWindow,
                               QMenuBar, QProgressBar, QPushButton,
                               QScrollArea, QSizePolicy, QSpacerItem,
                               QStatusBar, QTabWidget, QVBoxLayout, QWidget)

from focuswatch.database import DatabaseManager


class Dashboard(QMainWindow):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setupUi(self)
    self._database = DatabaseManager()
    self.timeline_setup()
    self.time_breakdown_setup()
    self.top_application_setup()

  def get_contrasting_text_color(self, background_color):
    background_rgb = QColor(background_color).toRgb()
    brightness = (background_rgb.red() * 299 + background_rgb.green()
                  * 587 + background_rgb.blue() * 114) / 1000
    return "black" if brightness > 90 else "white"

  def timeline_setup(self):
    # TODO get items based on selected time period
    period_entries = self._database.get_todays_entries()
    hour_chunk_entries = defaultdict(list)
    hour_entries = defaultdict(list)

    for i in range(24):
      hour_entries[i] = [0, 0, 0, 0, 0, 0]

    for entry in period_entries:
      timestamp_start = datetime.strptime(entry[0], "%Y-%m-%d %H:%M:%S")
      timestamp_stop = datetime.strptime(entry[1], "%Y-%m-%d %H:%M:%S")
      category_id = entry[-2]

      while timestamp_start < timestamp_stop:
        hour_start = timestamp_start.hour
        minute_start = timestamp_start.minute // 10
        quarter_hour_start = f"{hour_start:02d}:{minute_start}"

        duration_in_this_quarter = min(
            10 - (timestamp_start.minute % 10), (timestamp_stop -
                                                 timestamp_start).total_seconds() / 60
        )

        if quarter_hour_start not in hour_chunk_entries:
          hour_chunk_entries[quarter_hour_start] = {}

        if category_id in hour_chunk_entries[quarter_hour_start]:
          hour_chunk_entries[quarter_hour_start][category_id] += duration_in_this_quarter
        else:
          hour_chunk_entries[quarter_hour_start][category_id] = duration_in_this_quarter

        timestamp_start += timedelta(minutes=duration_in_this_quarter)

    for quarter, entries in hour_chunk_entries.items():
      max_category = max(entries, key=lambda category_id: entries[category_id])
      hour_chunk_entries[quarter] = max_category

    for quarter, max_category in hour_chunk_entries.items():
      hour, index = quarter.split(sep=":")
      hour_entries[int(hour)][int(index)] = max_category

    for hour, entries in hour_entries.items():
      """ Hour label setup """
      hour_horizontalLayout = QHBoxLayout()
      hour_horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)

      hour_label = QLabel(self.scrollAreaWidgetContents)
      hour_label.setMaximumSize(QSize(30, 90))
      hour_label.setMinimumSize(QSize(30, 90))
      hour_label.setText(f"{'0' if hour < 10 else ''}{hour}:00")
      hour_label.setAlignment(Qt.AlignTop)

      hour_horizontalLayout.addWidget(hour_label)

      line = QFrame(self.scrollAreaWidgetContents)
      line.setObjectName(u"line")
      line.setFrameShape(QFrame.VLine)
      line.setFrameShadow(QFrame.Sunken)

      hour_horizontalLayout.addWidget(line)

      """ Hour entries setup """
      hour_verticalLayout = QVBoxLayout()
      hour_verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
      for i, entry in enumerate(entries):
        entry_text_label = QLabel(self.scrollAreaWidgetContents)
        style = []
        if entry != 0 and entry != None:  # TODO disallow deleting 'Uncategorized' category or change how it works
          category = self._database.get_category_by_id(entry)
          name = category[1]
          color = category[-1]
          while color == None:
            parent_category_id = category[-2]
            if parent_category_id:
              parent_category = self._database.get_category_by_id(
                parent_category_id)
              color = parent_category[-1]
            else:
              color = "#FFFFFF"  # TODO check if this is ever the case

          if i > 0:
            if entry != entries[i - 1]:
              entry_text_label.setText(name)
          else:
            if entry != hour_entries[hour - 1][-1]:
              entry_text_label.setText(name)
          style.append(f"background-color: {color};")
          text_color = self.get_contrasting_text_color(color)
          style.append(f"color: {text_color};")
        else:
          style.append(f"background-color: rgba(0,0,0,0);")

        if i == len(hour_entries[0]) - 1:
          style.append("border-bottom: 1px dashed #141414;")
        entry_text_label.setStyleSheet(''.join(style))
        entry_text_label.setAlignment(Qt.AlignCenter)
        entry_text_label.setMaximumHeight(90 // len(hour_entries[0]))
        # font = QFont()
        # font.setPointSize(6)

        # entry_text_label.setFont(font)

        hour_verticalLayout.addWidget(entry_text_label)

      hour_horizontalLayout.addLayout(hour_verticalLayout)
      self.timeline_main_layout.addLayout(hour_horizontalLayout)

  def time_breakdown_setup(self):
    categories_by_total_time = self._database.get_daily_category_time_totals()

    breakdown_verticalLayout = QVBoxLayout()
    breakdown_verticalLayout.setSizeConstraint(
        QLayout.SetDefaultConstraint)

    if not categories_by_total_time:
      info_label = QLabel(self.time_breakdown_scrollAreaWidgetContents)
      info_label.setText("No entries for the selected period")

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

    series = QtCharts.QPieSeries()

    for vals in categories_by_total_time:
      category_horizontalLayout = QHBoxLayout()
      category_horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
      cat_id, time = vals
      if time / 60 < 1:  # Don't add really small entries
        continue
      category = self._database.get_category_by_id(cat_id)
      id, name, parent_category_id, color = category

      text = ""
      while color == None:
        if parent_category_id:
          parent_category = self._database.get_category_by_id(
            parent_category_id)
          color = parent_category[-1]
          text += parent_category[1] + " > "
        else:
          color = "#FFFFFF"  # TODO check if this is ever the case

      text += name
      category_label = QLabel(self.time_breakdown_scrollAreaWidgetContents)
      category_label.setText(f"{text} {time/60 :.1f} m")  # TODO if > 60
      category_label.setStyleSheet(f"color: {color};")
      category_label.setMaximumHeight(20)

      font = QFont()
      font.setPointSize(10)

      category_label.setFont(font)

      slice = QtCharts.QPieSlice(text, time / 60)

      slice.setColor(QColor(color))

      slice.hovered.connect(slice.setExploded)
      slice.hovered.connect(slice.setLabelVisible)

      series.append(slice)

      category_horizontalLayout.addWidget(category_label)

      breakdown_verticalLayout.addLayout(category_horizontalLayout)

    series.setHoleSize(0.35)
    # series.setLabelsVisible(True)
    # series.setLabelsPosition(QtCharts.QPieSlice.LabelInsideNormal)
    pie_chart.chart().addSeries(series)
    pie_chart.chart().legend().hide()

    # legend = pie_chart.chart().legend()
    # legend.setAlignment(Qt.AlignBottom)
    # legend.setFont(QFont("Helvetica", 9))

    verticalSpacer = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    breakdown_verticalLayout.addItem(verticalSpacer)
    self.time_breakdown_main_layout.addLayout(breakdown_verticalLayout)
    self.time_breakdown_main_layout.addWidget(pie_chart)

  def top_application_setup(self):
    window_class_by_total_time = self._database.get_daily_entries_class_time_total()

    breakdown_verticalLayout = QVBoxLayout()
    breakdown_verticalLayout.setSizeConstraint(
        QLayout.SetDefaultConstraint)

    if not window_class_by_total_time:
      info_label = QLabel(self.top_apps_scrollAreaWidgetContents)
      info_label.setText("No entries for the selected period")

      font = QFont()
      font.setPointSize(16)

      info_label.setFont(font)
      info_label.setAlignment(Qt.AlignCenter)

      breakdown_verticalLayout.addWidget(info_label)
      self.top_apps_main_layout.addLayout(breakdown_verticalLayout)
      return

    total_time = 0

    for vals in window_class_by_total_time:
      total_time += vals[-1]

    pie_chart = QtCharts.QChartView()
    pie_chart.setRenderHint(QPainter.Antialiasing)
    pie_chart.setMinimumSize(300, 300)

    series = QtCharts.QPieSeries()

    for vals in window_class_by_total_time:
      class_horizontalLayout = QHBoxLayout()
      class_horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)

      window_class, category_id, time = vals
      if time / 60 < 1:
        continue
      category = self._database.get_category_by_id(category_id)
      id, name, parent_category_id, color = category

      text = ""
      while color == None:
        if parent_category_id:
          parent_category = self._database.get_category_by_id(
            parent_category_id)
          color = parent_category[-1]
          # text += parent_category[1] + " > "
        else:
          color = "#FFFFFF"  # TODO check if this is ever the case

      text += window_class
      class_label = QLabel(self.top_apps_scrollAreaWidgetContents)
      class_label.setText(f"{text} {time/60 :.1f} m")  # TODO if > 60
      # class_label.setStyleSheet(f"color: {color};")
      class_label.setMaximumHeight(20)

      font = QFont()
      font.setPointSize(10)

      class_label.setFont(font)

      slice = QtCharts.QPieSlice(text, time / 60)

      # slice.setColor(QColor(color))

      slice.hovered.connect(slice.setExploded)
      slice.hovered.connect(slice.setLabelVisible)

      series.append(slice)

      class_horizontalLayout.addWidget(class_label)

      breakdown_verticalLayout.addLayout(class_horizontalLayout)

    series.setHoleSize(0.35)
    # series.setLabelsVisible(True)
    # series.setLabelsPosition(QtCharts.QPieSlice.LabelInsideNormal)
    pie_chart.chart().addSeries(series)
    pie_chart.chart().legend().hide()

    # legend = pie_chart.chart().legend()
    # legend.setAlignment(Qt.AlignBottom)
    # legend.setFont(QFont("Helvetica", 9))

    verticalSpacer = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

    breakdown_verticalLayout.addItem(verticalSpacer)

    self.top_apps_main_layout.addLayout(breakdown_verticalLayout)
    self.top_apps_main_layout.addWidget(pie_chart)

  def categories_setup(self):
    # Get all categories and keywords
    categories = self._database.get_all_categories()
    keywords = self._database.get_all_keywords()

    # Make a dict category: keywords
    cat_key = defaultdict(list)
    for keyword in keywords:
      cat_key[keyword[-1]].append(keyword[1])

    # for key, value in cat_key.items():
    # print(f"{key} {value}")

    # Organize into parent-cildren
    cat_dict = defaultdict(list)

    for cat_id, name, parent_cat_id, color in categories:
      category = {
        'name': name,
        'color': color,
        'keywords': cat_key[cat_id],
        'children': []
      }

      if parent_cat_id is None:
        cat_dict[cat_id] = category
      else:
        parent_category = cat_dict[parent_cat_id]
        parent_category['children'].append(cat_id)
        cat_dict[cat_id] = category

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

    category_actions_verticalLayout = QVBoxLayout()
    category_actions_verticalLayout.setObjectName(
      u"category_actions_verticalLayout")

    # Size policies
    cat_label_sizePolicy = QSizePolicy(
      QSizePolicy.Maximum, QSizePolicy.Preferred)
    cat_label_sizePolicy.setHorizontalStretch(0)
    cat_label_sizePolicy.setVerticalStretch(0)

    action_sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    action_sizePolicy.setHorizontalStretch(0)
    action_sizePolicy.setVerticalStretch(0)

    for key, vals in cat_dict.items():
      # Name label
      category_label = QLabel(self.categorization_scrollAreaWidgetContents)
      cat_label_sizePolicy.setHeightForWidth(
        category_label.sizePolicy().hasHeightForWidth())
      category_label.setSizePolicy(cat_label_sizePolicy)
      depth = self._database.get_category_depth(key)
      indent = '\t' * depth
      category_label.setText(f"{indent} {key}. {vals['name']}")
      font = QFont()
      font.setPointSize(12)
      category_label.setFont(font)

      category_name_verticalLayout.addWidget(category_label)

      # Keywords label
      keywords_label = QLabel(self.categorization_scrollAreaWidgetContents)
      keywords_label.setText("Keywords: " + '| '.join(vals['keywords']))
      keywords_label.setMinimumSize(QSize(600, 0))
      keywords_label.setWordWrap(True)

      category_keywords_verticalLayout.addWidget(keywords_label)

      # Actions
      # TODO Replace text with icons
      category_action_horizontalLayout = QHBoxLayout()
      category_action_horizontalLayout.setSizeConstraint(
        QLayout.SetMinimumSize)

      edit_button = QPushButton(self.categorization_scrollAreaWidgetContents)
      action_sizePolicy.setHeightForWidth(
        edit_button.sizePolicy().hasHeightForWidth())
      edit_button.setSizePolicy(action_sizePolicy)
      edit_button.setText(
        f"Edit category {key}{' ' if key < 10 else ''}")  # TODO xd

      category_action_horizontalLayout.addWidget(edit_button)

      add_child_button = QPushButton(
        self.categorization_scrollAreaWidgetContents)
      action_sizePolicy.setHeightForWidth(
        add_child_button.sizePolicy().hasHeightForWidth())
      add_child_button.setSizePolicy(action_sizePolicy)
      add_child_button.setText("Add child category")

      category_action_horizontalLayout.addWidget(add_child_button)

      category_actions_verticalLayout.addLayout(
        category_action_horizontalLayout)

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
      category_actions_verticalLayout)

  def dashboard_tab_setup(self):
    self.timeline_setup()
    self.time_breakdown_setup()
    self.top_application_setup()

  def categorization_tab_setup(self):
    self.categories_setup()

  def setupUi(self, Dashboard):
    if not Dashboard.objectName():
      Dashboard.setObjectName(u"Dashboard")
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

    self.timeline_frame = QFrame(self.dashboard_tab)
    self.timeline_frame.setObjectName(u"timeline_frame")
    sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(
      self.timeline_frame.sizePolicy().hasHeightForWidth())
    self.timeline_frame.setSizePolicy(sizePolicy)
    self.timeline_frame.setMinimumSize(QSize(300, 0))
    self.timeline_frame.setFrameShape(QFrame.StyledPanel)
    self.timeline_frame.setFrameShadow(QFrame.Raised)
    self.horizontalLayout_2 = QHBoxLayout(self.timeline_frame)
    self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
    self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
    self.timeline_scrollArea = QScrollArea(self.timeline_frame)
    self.timeline_scrollArea.setObjectName(u"timeline_scrollArea")
    self.timeline_scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QWidget()
    self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
    self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 296, 723))
    self.verticalLayout_6 = QVBoxLayout(self.scrollAreaWidgetContents)
    self.verticalLayout_6.setSpacing(0)
    self.verticalLayout_6.setObjectName(u"verticalLayout_6")
    self.timeline_main_layout = QVBoxLayout()
    self.timeline_main_layout.setObjectName(u"timeline_main_layout")

    self.verticalLayout_6.addLayout(self.timeline_main_layout)

    self.timeline_scrollArea.setWidget(self.scrollAreaWidgetContents)

    self.horizontalLayout_2.addWidget(self.timeline_scrollArea)

    self.gridLayout.addWidget(self.timeline_frame, 2, 0, 1, 1)

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

    self.horizontalLayout.addWidget(self.date_prev_button)

    self.date_button = QPushButton(self.date_nav_frame)
    self.date_button.setObjectName(u"date_button")
    sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    sizePolicy2.setHorizontalStretch(0)
    sizePolicy2.setVerticalStretch(0)
    sizePolicy2.setHeightForWidth(
      self.date_button.sizePolicy().hasHeightForWidth())
    self.date_button.setSizePolicy(sizePolicy2)
    self.date_button.setMaximumSize(QSize(600, 16777215))

    self.horizontalLayout.addWidget(self.date_button)

    self.date_next_button = QPushButton(self.date_nav_frame)
    self.date_next_button.setObjectName(u"date_next_button")
    self.date_next_button.setMaximumSize(QSize(20, 16777215))

    self.horizontalLayout.addWidget(self.date_next_button)

    self.horizontalSpacer_3 = QSpacerItem(
      15, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

    self.horizontalLayout.addItem(self.horizontalSpacer_3)

    self.time_period_button = QPushButton(self.date_nav_frame)
    self.time_period_button.setObjectName(u"time_period_button")

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

    self.categorization_button_horizontalLayout.addWidget(
      self.categorization_addCategory)

    self.horizontalSpacer_4 = QSpacerItem(
      40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    self.categorization_button_horizontalLayout.addItem(
      self.horizontalSpacer_4)

    self.pushButton_4 = QPushButton(
      self.categorization_scrollAreaWidgetContents)
    self.pushButton_4.setObjectName(u"pushButton_4")

    self.categorization_button_horizontalLayout.addWidget(self.pushButton_4)

    self.categorization_save = QPushButton(
      self.categorization_scrollAreaWidgetContents)
    self.categorization_save.setObjectName(u"categorization_save")

    self.categorization_button_horizontalLayout.addWidget(
      self.categorization_save)

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

    self.tabWidget.addTab(self.categorization_tab, "")
    self.settings_tab = QWidget()
    self.settings_tab.setObjectName(u"settings_tab")
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

    self.tabWidget.setCurrentIndex(1)

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
    self.date_button.setText(
      QCoreApplication.translate("Dashboard", u"Today", None))
    self.date_next_button.setText(
      QCoreApplication.translate("Dashboard", u">", None))
    self.time_period_button.setText(
      QCoreApplication.translate("Dashboard", u"Day view", None))
    self.refreshButton.setText(
      QCoreApplication.translate("Dashboard", u"Refresh", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.dashboard_tab), QCoreApplication.translate("Dashboard", u"Dashboard", None))
    self.categorization_info_label.setText(QCoreApplication.translate(
      "Dashboard", u"Rules for categorizing events. An event can only have one category. If several categories match, the deepest one will be chosen.", None))
    self.categorization_addCategory.setText(
      QCoreApplication.translate("Dashboard", u"Add category", None))
    self.pushButton_4.setText(QCoreApplication.translate(
      "Dashboard", u"Retrospective categorization", None))
    self.categorization_save.setText(
      QCoreApplication.translate("Dashboard", u"Save", None))
    self.categorization_restoreDefaults.setText(
      QCoreApplication.translate("Dashboard", u"Restore defaults", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.categorization_tab), QCoreApplication.translate("Dashboard", u"Categorization", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.settings_tab), QCoreApplication.translate("Dashboard", u"Settings", None))
  # retranslateUi

  def onShow(self, event):
    """ This is probably a bad practice """
    # TODO
    self.setupUi(self)
    self.dashboard_tab_setup()
    self.categorization_tab_setup()
