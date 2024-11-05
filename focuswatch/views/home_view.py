import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication, QSize, Qt, QTimer, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCalendarWidget, QDialog, QFrame, QGridLayout,
                               QHBoxLayout, QMenu, QPushButton, QSizePolicy,
                               QSpacerItem, QVBoxLayout, QWidget)

from focuswatch.utils.resource_utils import apply_styles, apply_stylesheet
from focuswatch.views.components.card_widget import CardWidget
from focuswatch.views.components.focus_trend_view import FocusTrendView
from focuswatch.views.components.timeline_view import TimelineView
from focuswatch.views.components.top_applications_card_view import \
    TopApplicationsCardView
from focuswatch.views.components.top_categories_card_view import \
    TopCategoriesCardView
from focuswatch.views.components.top_titles_card_view import TopTitlesCardView

if TYPE_CHECKING:
  from focuswatch.viewmodels.home_viewmodel import HomeViewModel

logger = logging.getLogger(__name__)


class HomeView(QWidget):
  def __init__(self,
               viewmodel: "HomeViewModel",
               parent=None):
    super().__init__(parent)
    self._viewmodel = viewmodel
    self._timeline_view = None

    self._setup_ui()
    self._retranslate_ui()
    self._connect_signals()
    apply_styles(self, ["nav_buttons.qss", "period_menu.qss"])

  def _setup_ui(self):
    self.setObjectName("page_home")

    # Main Vertical Layout
    self.verticalLayout_3 = QVBoxLayout(self)
    self.verticalLayout_3.setObjectName("verticalLayout_3")
    self.verticalLayout_3.setContentsMargins(6, 9, 6, 6)

    # Home Layout
    self.home_verticalLayout = QVBoxLayout()
    self.home_verticalLayout.setObjectName("home_verticalLayout")
    self.verticalLayout_3.addLayout(self.home_verticalLayout)

    # Navigation
    self.home_nav_horizontalLayout = QHBoxLayout()
    self.home_nav_horizontalLayout.setSpacing(0)
    self.home_nav_horizontalLayout.setObjectName(
        "home_nav_horizontalLayout")
    self.home_nav_horizontalLayout.setContentsMargins(0, 0, 0, 0)

    # Frame for Navigation
    self.home_nav_frame = QFrame(self)
    self.home_nav_frame.setObjectName("home_nav_frame")
    sizePolicy2 = QSizePolicy(
        QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    sizePolicy2.setHeightForWidth(
        self.home_nav_frame.sizePolicy().hasHeightForWidth())
    self.home_nav_frame.setSizePolicy(sizePolicy2)
    self.home_nav_frame.setFrameShape(QFrame.Shape.NoFrame)
    self.home_nav_frame.setFrameShadow(QFrame.Shadow.Raised)

    self.horizontalLayout_5 = QHBoxLayout(self.home_nav_frame)
    self.horizontalLayout_5.setSpacing(0)
    self.horizontalLayout_5.setObjectName("horizontalLayout_5")
    self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)

    # Navigation Buttons
    self.date_prev_button = QPushButton(self.home_nav_frame)
    self.date_prev_button.setObjectName("date_prev_button")
    self.horizontalLayout_5.addWidget(self.date_prev_button)

    self.date_button = QPushButton(self.home_nav_frame)
    self.date_button.setObjectName("date_button")
    self.date_button.setMinimumSize(QSize(200, 0))
    self.horizontalLayout_5.addWidget(self.date_button)

    self.date_next_button = QPushButton(self.home_nav_frame)
    self.date_next_button.setObjectName("date_next_button")
    self.horizontalLayout_5.addWidget(self.date_next_button)

    self.horizontalSpacer_period = QSpacerItem(
        20, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
    self.horizontalLayout_5.addItem(self.horizontalSpacer_period)

    self.period_type_button = QPushButton(self.home_nav_frame)
    self.period_type_button.setObjectName("period_type_button")
    self.period_type_button.setMinimumSize(QSize(70, 0))
    self.horizontalLayout_5.addWidget(self.period_type_button)

    self.horizontalSpacer_ref = QSpacerItem(
        40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    self.horizontalLayout_5.addItem(self.horizontalSpacer_ref)

    self.refreshButton = QPushButton(self.home_nav_frame)
    self.refreshButton.setObjectName("refreshButton")
    self.horizontalLayout_5.addWidget(self.refreshButton)

    self.home_nav_horizontalLayout.addWidget(self.home_nav_frame)
    self.home_verticalLayout.addLayout(self.home_nav_horizontalLayout)

    # Line Separator
    self.line = QFrame(self)
    self.line.setObjectName("line")
    apply_stylesheet(self.line, "separator.qss")
    self.line.setFrameShadow(QFrame.Shadow.Plain)
    self.line.setFrameShape(QFrame.Shape.HLine)

    self.home_verticalLayout.addWidget(self.line)

    # Main content layout
    self.main_layout = QHBoxLayout()
    self.home_verticalLayout.addLayout(self.main_layout)

    # Timeline frame
    self._timeline_view = TimelineView(
        self._viewmodel.timeline_viewmodel, parent=self)
    self.timeline_frame = self._timeline_view

    self.main_layout.addWidget(self.timeline_frame)

    # Frame for main content
    self.content_frame = QFrame(self)
    self.content_layout = QVBoxLayout(self.content_frame)

    # Grid layout to organize the cards
    self.grid_layout = QGridLayout()
    self.grid_layout.setSpacing(10)

    # Set column and row stretch
    self.grid_layout.setColumnStretch(0, 1)
    self.grid_layout.setColumnStretch(1, 1)
    self.grid_layout.setColumnStretch(2, 1)
    self.grid_layout.setRowStretch(0, 1)
    self.grid_layout.setRowStretch(1, 1)
    self.grid_layout.setRowStretch(2, 1)

    # Top row: Top Categories, Top Applications, Top Titles
    self.top_categories_card = TopCategoriesCardView(
        self._viewmodel.top_categories_card_viewmodel, self)
    self.grid_layout.addWidget(self.top_categories_card, 0, 0)

    self.top_applications_card = TopApplicationsCardView(
        self._viewmodel.top_applications_card_viewmodel, self)
    self.grid_layout.addWidget(self.top_applications_card, 0, 1)

    self.top_titles_card = TopTitlesCardView(
        self._viewmodel.top_titles_card_viewmodel, self)
    self.grid_layout.addWidget(self.top_titles_card, 0, 2)

    # Focus trend
    self.focus_trend_card = FocusTrendView(
        self._viewmodel.focus_trend_viewmodel, self)
    self.grid_layout.addWidget(self.focus_trend_card, 1, 0, 2, 2)

    # Placeholder for Daily Summary
    self.daily_summary_card = CardWidget("Daily Summary", self)
    self.grid_layout.addWidget(self.daily_summary_card, 1, 2, 2, 1)

    # Add the grid layout to the content frame
    self.content_layout.addLayout(self.grid_layout)
    self.main_layout.addWidget(self.content_frame)

  def _retranslate_ui(self):
    self.date_prev_button.setText(
        QCoreApplication.translate("Home", "<", None))
    self.date_next_button.setText(
        QCoreApplication.translate("Home", ">", None))
    self.refreshButton.setText(
        QCoreApplication.translate("Home", "Refresh", None))
    self._update_period_type_button_text()
    self._update_date_button_text()

  def _connect_signals(self):
    """ Connect signals to their respective slots. """
    # Connect ViewModel signals
    self._viewmodel.period_start_changed.connect(self._on_period_changed)
    self._viewmodel.period_end_changed.connect(self._on_period_changed)
    self._viewmodel.period_type_changed.connect(
        self._on_period_type_changed)
    self._viewmodel.period_changed.connect(self._on_period_changed)

    # Connect button signals to slots
    self.date_prev_button.clicked.connect(self._on_date_prev_clicked)
    self.date_next_button.clicked.connect(self._on_date_next_clicked)
    self.date_button.clicked.connect(self._show_calendar)
    self.period_type_button.clicked.connect(self._show_period_menu)
    self.refreshButton.clicked.connect(self._on_refresh_clicked)

  def _update_date_button_text(self):
    """ Update the text of the date button based on the current period. """
    period_start = self._viewmodel.period_start
    period_end = self._viewmodel.period_end
    period_type = self._viewmodel.period_type

    if period_type == "Day":
      if period_start.date() == datetime.today().date():
        self.date_button.setText("Today")
      else:
        self.date_button.setText(period_start.strftime("%d-%m-%Y"))
    elif period_type == "Week":
      self.date_button.setText(f"{period_start.strftime(
          '%b %d')} - {period_end.strftime('%b %d, %Y')}")
    elif period_type == "Month":
      self.date_button.setText(period_start.strftime("%B %Y"))
    elif period_type == "Year":
      self.date_button.setText(period_start.strftime("%Y"))

  def _update_period_type_button_text(self):
    """ Update the text of the period type button. """
    self.period_type_button.setText(self._viewmodel.period_type)

  @Slot()
  def _on_period_changed(self):
    """ Handle changes to the period start or end. """
    self._update_date_button_text()

  @Slot()
  def _on_period_type_changed(self):
    """ Handle changes to the period type. """
    self._update_period_type_button_text()
    self._update_date_button_text()

  def _on_date_prev_clicked(self):
    """ Handle the previous date button click. """
    self._viewmodel.shift_period(-1)

  def _on_date_next_clicked(self):
    """ Handle the next date button click. """
    self._viewmodel.shift_period(1)

  def _show_calendar(self):
    """ Display a calendar dialog to select a date. """
    calendar_dialog = QDialog(self)
    calendar_dialog.setWindowTitle("Select a Date")

    layout = QVBoxLayout()
    calendar = QCalendarWidget()
    layout.addWidget(calendar)
    confirm_button = QPushButton("Confirm Date")
    layout.addWidget(confirm_button)

    def get_selected_date():
      selected_date = calendar.selectedDate().toPython()
      selected_datetime = datetime.combine(selected_date, datetime.min.time())
      self._viewmodel.update_period_from_selected_date(selected_datetime)
      calendar_dialog.accept()

    confirm_button.clicked.connect(get_selected_date)
    calendar_dialog.setLayout(layout)
    calendar_dialog.exec()

  def _show_period_menu(self):
    """ Display a menu to select the period type. """
    menu = QMenu(self)
    actions = {}
    for period in ["Day", "Week", "Month", "Year"]:
      actions[period] = menu.addAction(period)

    action = menu.exec_(self.period_type_button.mapToGlobal(
        self.period_type_button.rect().bottomLeft()))

    if action:
      self._viewmodel.set_period_type(action.text())

  def _on_refresh_clicked(self):
    """ Handle the refresh button click. """
    self._viewmodel.refresh_triggered.emit()
