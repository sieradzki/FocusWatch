from collections import defaultdict
from datetime import datetime

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect, QSize, Qt,
                            QTime, QUrl)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
                           QFontDatabase, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette,
                           QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDial, QFrame, QGridLayout,
                               QHBoxLayout, QLabel, QLayout, QMainWindow,
                               QMenuBar, QPushButton, QScrollArea, QSizePolicy,
                               QSpacerItem, QStatusBar, QTabWidget,
                               QVBoxLayout, QWidget)

from focuswatch.database import DatabaseManager


class Dashboard(QMainWindow):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setupUi(self)
    self._database = DatabaseManager()
    self.timeline_setup()
    # self.hourSetup()

  def timeline_setup(self):
    # TODO get items based on selected time period
    period_entries = self._database.get_todays_entries()
    quarter_hour_entries = defaultdict(list)
    hour_entries = defaultdict(list)

    for i in range(24):
      hour_entries[i] = [0, 0, 0, 0]

    for entry in period_entries:
      timestamp_start = datetime.strptime(entry[0], "%d-%m-%Y %H:%M:%S")
      timestamp_stop = datetime.strptime(entry[1], "%d-%m-%Y %H:%M:%S")
      category_id = entry[-2]

      hour_start = timestamp_start.hour
      minute_start = timestamp_start.minute // 15
      quarter_hour_start = f"{hour_start:02d}:{minute_start}"

      duration = (timestamp_stop - timestamp_start).total_seconds() / 60

      if quarter_hour_start not in quarter_hour_entries:
        quarter_hour_entries[quarter_hour_start] = {}

      if category_id in quarter_hour_entries[quarter_hour_start]:
        quarter_hour_entries[quarter_hour_start][category_id] += duration
      else:
        quarter_hour_entries[quarter_hour_start][category_id] = duration

    for quarter, entries in quarter_hour_entries.items():
      max_category = max(entries, key=lambda category_id: entries[category_id])
      quarter_hour_entries[quarter] = max_category

    for quarter, max_category in quarter_hour_entries.items():
      hour, index = quarter.split(sep=":")
      hour_entries[int(hour)][int(index)] = max_category

    for hour, entries in hour_entries.items():
      """ Hour label setup """
      hour_horizontalLayout = QHBoxLayout()
      hour_horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)

      hour_label = QLabel(self.scrollAreaWidgetContents)
      hour_label.setMaximumSize(QSize(30, 90))
      hour_label.setMinimumSize(QSize(30, 60))
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
        if entry != 0:
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
        else:
          style.append(f"background-color: rgba(0,0,0,0);")
        if i == 3:
          style.append("border-bottom: 1px dashed #141414;")
        entry_text_label.setStyleSheet(''.join(style))
        entry_text_label.setAlignment(Qt.AlignCenter)

        hour_verticalLayout.addWidget(entry_text_label)

      hour_horizontalLayout.addLayout(hour_verticalLayout)
      self.timeline_main_layout.addLayout(hour_horizontalLayout)

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
    self.tabWidget.setDocumentMode(False)
    self.dashboard_tab = QWidget()
    self.dashboard_tab.setObjectName(u"dashboard_tab")
    self.gridLayout = QGridLayout(self.dashboard_tab)
    self.gridLayout.setObjectName(u"gridLayout")
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

    self.top_apps_frame = QFrame(self.dashboard_tab)
    self.top_apps_frame.setObjectName(u"top_apps_frame")
    self.top_apps_frame.setMinimumSize(QSize(50, 0))
    self.top_apps_frame.setFrameShape(QFrame.StyledPanel)
    self.top_apps_frame.setFrameShadow(QFrame.Raised)

    self.gridLayout.addWidget(self.top_apps_frame, 2, 4, 1, 1)

    self.verticalSpacer = QSpacerItem(
      20, 5, QSizePolicy.Minimum, QSizePolicy.Minimum)

    self.gridLayout.addItem(self.verticalSpacer, 1, 0, 1, 1)

    self.horizontalSpacer_2 = QSpacerItem(
      5, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)

    self.gridLayout.addItem(self.horizontalSpacer_2, 2, 1, 1, 1)

    self.time_breakdown_frame = QFrame(self.dashboard_tab)
    self.time_breakdown_frame.setObjectName(u"time_breakdown_frame")
    self.time_breakdown_frame.setFrameShape(QFrame.StyledPanel)
    self.time_breakdown_frame.setFrameShadow(QFrame.Raised)
    self.verticalLayout_4 = QVBoxLayout(self.time_breakdown_frame)
    self.verticalLayout_4.setSpacing(0)
    self.verticalLayout_4.setObjectName(u"verticalLayout_4")
    self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
    self.label = QLabel(self.time_breakdown_frame)
    self.label.setObjectName(u"label")
    font = QFont()
    font.setPointSize(12)
    font.setBold(False)
    self.label.setFont(font)
    self.label.setAutoFillBackground(False)
    self.label.setMargin(4)

    self.verticalLayout_4.addWidget(self.label)

    self.time_breakdown_scrollArea = QScrollArea(self.time_breakdown_frame)
    self.time_breakdown_scrollArea.setObjectName(u"time_breakdown_scrollArea")
    self.time_breakdown_scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents_2 = QWidget()
    self.scrollAreaWidgetContents_2.setObjectName(
      u"scrollAreaWidgetContents_2")
    self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 1175, 563))
    self.verticalLayout_3 = QVBoxLayout(self.scrollAreaWidgetContents_2)
    self.verticalLayout_3.setObjectName(u"verticalLayout_3")
    self.label_2 = QLabel(self.scrollAreaWidgetContents_2)
    self.label_2.setObjectName(u"label_2")

    self.verticalLayout_3.addWidget(self.label_2)

    self.time_breakdown_scrollArea.setWidget(self.scrollAreaWidgetContents_2)

    self.verticalLayout_4.addWidget(self.time_breakdown_scrollArea)

    self.verticalSpacer_2 = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Minimum)

    self.verticalLayout_4.addItem(self.verticalSpacer_2)

    self.time_chart_frame = QFrame(self.time_breakdown_frame)
    self.time_chart_frame.setObjectName(u"time_chart_frame")
    self.time_chart_frame.setMinimumSize(QSize(0, 50))
    self.time_chart_frame.setFrameShape(QFrame.StyledPanel)
    self.time_chart_frame.setFrameShadow(QFrame.Raised)
    self.dial = QDial(self.time_chart_frame)
    self.dial.setObjectName(u"dial")
    self.dial.setGeometry(QRect(60, -10, 50, 64))
    self.label_3 = QLabel(self.time_chart_frame)
    self.label_3.setObjectName(u"label_3")
    self.label_3.setGeometry(QRect(180, 10, 54, 17))

    self.verticalLayout_4.addWidget(self.time_chart_frame)

    self.verticalSpacer_3 = QSpacerItem(
      20, 40, QSizePolicy.Minimum, QSizePolicy.Minimum)

    self.verticalLayout_4.addItem(self.verticalSpacer_3)

    self.gridLayout.addWidget(self.time_breakdown_frame, 2, 2, 1, 1)

    self.tabWidget.addTab(self.dashboard_tab, "")
    self.tab_2 = QWidget()
    self.tab_2.setObjectName(u"tab_2")
    self.tabWidget.addTab(self.tab_2, "")

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
  # setupUi

  def retranslateUi(self, Dashboard):
    Dashboard.setWindowTitle(
      QCoreApplication.translate("Dashboard", u"Dashboard", None))
    self.date_prev_button.setText(
      QCoreApplication.translate("Dashboard", u"<", None))
    self.date_button.setText(
      QCoreApplication.translate("Dashboard", u"Today", None))
    self.date_next_button.setText(
      QCoreApplication.translate("Dashboard", u">", None))
    self.time_period_button.setText(
      QCoreApplication.translate("Dashboard", u"Day view", None))
    self.label.setText(QCoreApplication.translate(
      "Dashboard", u"Time breakdown (categories)", None))
    self.label_2.setText(QCoreApplication.translate(
      "Dashboard", u"Category - progress bar - time spent ", None))
    self.label_3.setText(QCoreApplication.translate(
      "Dashboard", u"Pie-chart", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.dashboard_tab), QCoreApplication.translate("Dashboard", u"Dashboard", None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(
      self.tab_2), QCoreApplication.translate("Dashboard", u"Categorization", None))
# retranslateUi
