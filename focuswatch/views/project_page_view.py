from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import (
  QDate,
  QDateTime,
  QEvent,
  QMimeData,
  QObject,
  QPoint,
  QRect,
  QSize,
  Qt,
  QTimer,
  Signal,
  Slot,
)
from PySide6.QtGui import QColor, QDrag, QIcon, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
  QApplication,
  QCalendarWidget,
  QCheckBox,
  QColorDialog,
  QComboBox,
  QDateTimeEdit,
  QDialog,
  QDialogButtonBox,
  QFrame,
  QGraphicsOpacityEffect,
  QHBoxLayout,
  QInputDialog,
  QLabel,
  QLayout,
  QLineEdit,
  QMenu,
  QMessageBox,
  QProgressBar,
  QPushButton,
  QScrollArea,
  QSizePolicy,
  QSpacerItem,
  QStyle,
  QTextEdit,
  QVBoxLayout,
  QWidget,
)

from focuswatch.database.models.task import Task, TaskPriority, TaskRecurrence
from focuswatch.database.models.task_column import TaskColumn
from focuswatch.utils.resource_utils import apply_stylesheet
from focuswatch.utils.ui_utils import get_contrasting_text_color

if TYPE_CHECKING:
  from focuswatch.viewmodels.project_page_viewmodel import ProjectPageViewModel


def _format_seconds(total_seconds: int) -> str:
  if total_seconds <= 0:
    return "0m"
  hours = total_seconds // 3600
  minutes = (total_seconds % 3600) // 60
  if hours:
    return f"{hours}h {minutes}m"
  return f"{minutes}m"


def _elide_text(text: str, max_length: int = 96) -> str:
  compact = " ".join(text.split())
  if len(compact) <= max_length:
    return compact
  return f"{compact[:max_length - 1].rstrip()}…"


def _make_priority_icon(color_str: str, size: int = 14) -> QIcon:
  pixmap = QPixmap(size, size)
  pixmap.fill(Qt.GlobalColor.transparent)
  painter = QPainter(pixmap)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  painter.setBrush(QColor(color_str))
  painter.setPen(Qt.PenStyle.NoPen)
  painter.drawRoundedRect(0, 0, size, size, 3, 3)
  painter.end()
  return QIcon(pixmap)


def _make_none_priority_icon(size: int = 14) -> QIcon:
  pixmap = QPixmap(size, size)
  pixmap.fill(Qt.GlobalColor.transparent)
  painter = QPainter(pixmap)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  painter.setPen(QColor("#6b7280"))
  painter.setBrush(Qt.BrushStyle.NoBrush)
  painter.drawRoundedRect(1, 1, size - 2, size - 2, 3, 3)
  painter.end()
  return QIcon(pixmap)


def _make_close_icon(size: int = 14, color: str = "#ef4444", thickness: int = 2) -> QIcon:
  pixmap = QPixmap(size, size)
  pixmap.fill(Qt.GlobalColor.transparent)
  painter = QPainter(pixmap)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  pen = QPen(QColor(color))
  pen.setWidth(thickness)
  painter.setPen(pen)
  margin = 3
  painter.drawLine(margin, margin, size - margin, size - margin)
  painter.drawLine(size - margin, margin, margin, size - margin)
  painter.end()
  return QIcon(pixmap)


def _make_edit_icon(size: int = 14, color: str = "#9CA3AF", thickness: int = 2) -> QIcon:
  pixmap = QPixmap(size, size)
  pixmap.fill(Qt.GlobalColor.transparent)
  painter = QPainter(pixmap)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  pen = QPen(QColor(color))
  pen.setWidth(thickness)
  painter.setPen(pen)
  # Simple pencil: diagonal line + small nib
  m = 2
  painter.drawLine(size - m, m, m, size - m)
  painter.drawLine(m, size - m, m, size - m - 2)
  painter.drawLine(m, size - m, m + 2, size - m)
  painter.end()
  return QIcon(pixmap)


def _theme_icon(names: list[str], fallback: QStyle.StandardPixmap, widget: QWidget) -> QIcon:
  for name in names:
    icon = QIcon.fromTheme(name)
    if not icon.isNull():
      return icon
  return widget.style().standardIcon(fallback)


_PRIORITY_COLORS = {
  TaskPriority.HIGH: "#dc2626",
  TaskPriority.MEDIUM: "#d97706",
  TaskPriority.LOW: "#2563eb",
}

_RECURRENCE_LABELS = {
  TaskRecurrence.DAILY: "Daily",
  TaskRecurrence.WEEKLY: "Weekly",
  TaskRecurrence.MONTHLY: "Monthly",
  TaskRecurrence.YEARLY: "Yearly",
}


# ---------------------------------------------------------------------------
#  Main View
# ---------------------------------------------------------------------------

class ProjectPageView(QWidget):
  """Single project page with Trello-style board interactions."""

  back_requested = Signal()

  def __init__(self,
               viewmodel: "ProjectPageViewModel",
               parent: Optional[QObject] = None):
    super().__init__(parent)
    self._viewmodel = viewmodel

    self._setup_ui()
    self._connect_signals()

    apply_stylesheet(self, "projects_view.qss")

  def _setup_ui(self) -> None:
    self.setObjectName("project_page_view")

    self.main_layout = QVBoxLayout(self)
    self.main_layout.setContentsMargins(0, 0, 0, 0)

    header = QFrame(self)
    header.setObjectName("project_page_header")
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(10, 10, 10, 10)

    self.button_back = QPushButton("\u2190 Back")
    self.button_back.setObjectName("button_back")
    self.button_back.setToolTip("Go back to Projects")
    header_layout.addWidget(self.button_back)

    self.title_label = QLabel("")
    self.title_label.setObjectName("project_page_title")
    header_layout.addWidget(self.title_label)

    header_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

    self.button_add_column = QPushButton("+ Add Column")
    self.button_add_column.setObjectName("button_add_column")
    self.button_add_column.setToolTip("Add a new board column")
    header_layout.addWidget(self.button_add_column)

    self.main_layout.addWidget(header)

    self.board_scroll = _PannableScrollArea(self)
    self.board_scroll.setObjectName("kanban_board_scroll")
    self.board_scroll.setWidgetResizable(True)

    self.board_widget = _BoardDropArea()
    self.board_widget.setObjectName("kanban_board_widget")
    self.board_widget.drop_column_requested.connect(self._on_column_dropped)

    self.board_layout = QHBoxLayout(self.board_widget)
    self.board_layout.setContentsMargins(10, 10, 10, 10)
    self.board_layout.setSpacing(12)

    self.board_scroll.setWidget(self.board_widget)
    self.main_layout.addWidget(self.board_scroll)

  def _connect_signals(self) -> None:
    self.button_back.clicked.connect(self.back_requested.emit)
    self.button_add_column.clicked.connect(self._create_column)

    self._viewmodel.project_changed.connect(self._on_project_changed)
    self._viewmodel.columns_changed.connect(self._schedule_board_update)
    self._viewmodel.tasks_changed.connect(self._schedule_board_update)

    self._column_widgets: dict[int, _TaskColumnWidget] = {}
    self._column_order: list[int] = []
    self._update_scheduled = False

  @Slot()
  def _on_project_changed(self) -> None:
    self.title_label.setText(self._viewmodel.project_name or "Project")

  @Slot()
  def _schedule_board_update(self) -> None:
    """Coalesce columns_changed + tasks_changed into one update."""
    if not self._update_scheduled:
      self._update_scheduled = True
      QTimer.singleShot(0, self._do_board_update)

  def _do_board_update(self) -> None:
    self._update_scheduled = False
    columns = self._viewmodel.columns()
    tasks_by_column = self._viewmodel.tasks_by_column()
    new_col_ids = [c.id for c in columns]

    if new_col_ids != self._column_order:
      # Column structure changed — full rebuild
      self._rebuild_board(columns, tasks_by_column)
    else:
      # Only tasks (or column names) changed — update in-place
      for col in columns:
        cw = self._column_widgets.get(col.id)
        if not cw:
          continue
        if cw.column.name != col.name:
          cw.title_label.setText(col.name)
          cw.column = col
        cw.populate_tasks(
          tasks_by_column.get(col.id, []),
          on_card_click=self._show_edit_task_dialog,
        )

  def _clear_layout(self, layout: QHBoxLayout) -> None:
    while layout.count():
      item = layout.takeAt(0)
      widget = item.widget()
      if widget:
        widget.deleteLater()

  def _rebuild_board(self, columns, tasks_by_column) -> None:
    h_scroll = self.board_scroll.horizontalScrollBar().value()

    self._clear_layout(self.board_layout)
    self.board_widget.clear_indicator()
    self._column_widgets.clear()
    self._column_order.clear()

    for column in columns:
      col_widget = _TaskColumnWidget(column)
      col_widget.add_task_requested.connect(lambda column_id=column.id: self._show_create_task_dialog(column_id))
      col_widget.rename_column_requested.connect(lambda column_id=column.id: self._rename_column(column_id))
      col_widget.delete_column_requested.connect(lambda column_id=column.id: self._delete_column(column_id))
      col_widget.drop_task_requested.connect(self._move_task)

      tasks = tasks_by_column.get(column.id, [])
      col_widget.populate_tasks(tasks, on_card_click=self._show_edit_task_dialog)
      self.board_layout.addWidget(col_widget)
      self._column_widgets[column.id] = col_widget
      self._column_order.append(column.id)

    self.board_layout.addStretch(1)

    # Restore board horizontal scroll only (columns are new, no column scroll to restore)
    QTimer.singleShot(0, lambda: self.board_scroll.horizontalScrollBar().setValue(
      min(h_scroll, self.board_scroll.horizontalScrollBar().maximum())
    ))

  # -- Column CRUD --

  def _create_column(self) -> None:
    text, ok = QInputDialog.getText(self, "Create Column", "Column name:")
    if not ok:
      return
    if not self._viewmodel.create_column(text):
      QMessageBox.warning(self, "Column", "Could not create column (name may already exist).")

  def _rename_column(self, column_id: int) -> None:
    current_name = ""
    for col in self._viewmodel.columns():
      if col.id == column_id:
        current_name = col.name
        break
    text, ok = QInputDialog.getText(self, "Rename Column", "New column name:", text=current_name)
    if not ok:
      return
    if not self._viewmodel.rename_column(column_id, text):
      QMessageBox.warning(self, "Column", "Could not rename column.")

  def _delete_column(self, column_id: int) -> None:
    reply = QMessageBox.question(
      self,
      "Delete Column",
      "Delete this column? Tasks will be moved to another column.",
      QMessageBox.Yes | QMessageBox.No,
      QMessageBox.No,
    )
    if reply != QMessageBox.Yes:
      return
    if not self._viewmodel.delete_column(column_id):
      QMessageBox.warning(self, "Column", "Could not delete column.")

  @Slot(int, int)
  def _on_column_dropped(self, column_id: int, target_index: int) -> None:
    if not self._viewmodel.move_column_to_index(column_id, target_index):
      QMessageBox.warning(self, "Column", "Could not reorder column.")

  # -- Task CRUD --

  def _show_create_task_dialog(self, column_id: int) -> None:
    dialog = _TaskDialog(
      parent=self,
      title="Add Task",
      default_column_id=column_id,
      available_tags=self._viewmodel.get_project_tags(),
      tag_creator=self._viewmodel.create_project_tag,
      tag_deleter=self._viewmodel.delete_project_tag,
      tag_updater=self._viewmodel.update_project_tag,
      tag_fetcher=self._viewmodel.get_project_tags,
      task=None,
    )
    if dialog.exec_() != QDialog.Accepted:
      return

    payload = dialog.payload()
    if not payload["name"]:
      QMessageBox.warning(self, "Task", "Task name cannot be empty.")
      return

    success = self._viewmodel.create_task(
      name=payload["name"],
      priority=payload["priority"],
      tags=payload["tags"],
      description=payload["description"],
      start_date=payload["start_date"],
      due_date=payload["due_date"],
      column_id=payload["column_id"],
      recurrence=payload["recurrence"],
      checklist=payload["checklist"],
    )
    if not success:
      QMessageBox.warning(self, "Task", "Could not create task.")

  def _show_edit_task_dialog(self, task: Task) -> None:
    dialog = _TaskDialog(
      parent=self,
      title="Edit Task",
      task=task,
      default_column_id=task.column_id,
      available_tags=self._viewmodel.get_project_tags(),
      tag_creator=self._viewmodel.create_project_tag,
      tag_deleter=self._viewmodel.delete_project_tag,
      tag_updater=self._viewmodel.update_project_tag,
      tag_fetcher=self._viewmodel.get_project_tags,
    )
    if dialog.exec_() != QDialog.Accepted:
      return

    if dialog.delete_requested:
      self._confirm_delete_task(task.id)
      return

    payload = dialog.payload()
    if not payload["name"]:
      QMessageBox.warning(self, "Task", "Task name cannot be empty.")
      return

    success = self._viewmodel.update_task(
      task_id=task.id,
      name=payload["name"],
      priority=payload["priority"],
      tags=payload["tags"],
      description=payload["description"],
      start_date=payload["start_date"],
      due_date=payload["due_date"],
      column_id=payload["column_id"],
      recurrence=payload["recurrence"],
      checklist=payload["checklist"],
    )
    if not success:
      QMessageBox.warning(self, "Task", "Could not update task.")

  def _confirm_delete_task(self, task_id: int) -> None:
    reply = QMessageBox.question(
      self,
      "Delete Task",
      "Delete this task?",
      QMessageBox.Yes | QMessageBox.No,
      QMessageBox.No,
    )
    if reply != QMessageBox.Yes:
      return
    if not self._viewmodel.delete_task(task_id):
      QMessageBox.warning(self, "Task", "Could not delete task.")

  @Slot(int, int, int)
  def _move_task(self, task_id: int, target_column_id: int, target_index: int) -> None:
    if not self._viewmodel.move_task(task_id, target_column_id, target_index):
      QMessageBox.warning(self, "Task", "Could not move task.")


# ---------------------------------------------------------------------------
#  Pannable scroll area (middle-click or Shift+click drag to scroll)
# ---------------------------------------------------------------------------

class _PannableScrollArea(QScrollArea):
  """Scroll area that supports click-drag horizontal panning."""

  def __init__(self, parent: Optional[QWidget] = None):
    super().__init__(parent)
    self._panning = False
    self._pan_start = QPoint()
    self._h_start = 0
    self._v_start = 0
    self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

  def mousePressEvent(self, event: QMouseEvent) -> None:
    if event.button() == Qt.MouseButton.MiddleButton:
      self._start_pan(event)
    elif event.button() == Qt.MouseButton.LeftButton and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
      self._start_pan(event)
    elif event.button() == Qt.MouseButton.LeftButton and self._can_left_pan(event):
      self._start_pan(event)
    else:
      super().mousePressEvent(event)

  def _can_left_pan(self, event: QMouseEvent) -> bool:
    viewport_pos = self.viewport().mapFrom(self, event.position().toPoint())
    target = self.viewport().childAt(viewport_pos)
    if target is None:
      return True

    blocked_types = (QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox, QDateTimeEdit, _TaskCard, _ColumnDragHandle)
    current = target
    while current is not None:
      if isinstance(current, blocked_types):
        return False
      if current == self.widget():
        return True
      current = current.parentWidget()
    return True

  def _start_pan(self, event: QMouseEvent) -> None:
    self._panning = True
    self._pan_start = event.globalPosition().toPoint()
    self._h_start = self.horizontalScrollBar().value()
    self._v_start = self.verticalScrollBar().value()
    QApplication.setOverrideCursor(Qt.CursorShape.ClosedHandCursor)
    event.accept()

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    if self._panning:
      delta = event.globalPosition().toPoint() - self._pan_start
      self.horizontalScrollBar().setValue(self._h_start - delta.x())
      self.verticalScrollBar().setValue(self._v_start - delta.y())
    else:
      super().mouseMoveEvent(event)

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    if self._panning:
      self._panning = False
      QApplication.restoreOverrideCursor()
    else:
      super().mouseReleaseEvent(event)


# ---------------------------------------------------------------------------
#  Drag auto-scroll helper
# ---------------------------------------------------------------------------

_EDGE_MARGIN = 50   # px from edge to start scrolling
_SCROLL_STEP = 12   # px per tick
_SCROLL_INTERVAL = 30  # ms between ticks


class _DragAutoScroller:
  """Manages auto-scrolling a QScrollArea when a drag is near its edges."""

  def __init__(self):
    self._timer = QTimer()
    self._timer.setInterval(_SCROLL_INTERVAL)
    self._timer.timeout.connect(self._tick)
    self._h_dir = 0  # -1 left, 0 none, +1 right
    self._v_dir = 0  # -1 up, 0 none, +1 down
    self._scroll_area: Optional[QScrollArea] = None

  def update(self, scroll_area: QScrollArea, global_pos: QPoint,
             horizontal: bool = True, vertical: bool = True) -> None:
    """Call from dragMoveEvent. Detects edge proximity and starts/stops timer."""
    self._scroll_area = scroll_area
    vp = scroll_area.viewport()
    local = vp.mapFromGlobal(global_pos)
    vp_w, vp_h = vp.width(), vp.height()

    self._h_dir = 0
    self._v_dir = 0
    if horizontal:
      if local.x() < _EDGE_MARGIN:
        self._h_dir = -1
      elif local.x() > vp_w - _EDGE_MARGIN:
        self._h_dir = 1
    if vertical:
      if local.y() < _EDGE_MARGIN:
        self._v_dir = -1
      elif local.y() > vp_h - _EDGE_MARGIN:
        self._v_dir = 1

    if self._h_dir or self._v_dir:
      if not self._timer.isActive():
        self._timer.start()
    else:
      self._timer.stop()

  def stop(self) -> None:
    self._timer.stop()
    self._h_dir = 0
    self._v_dir = 0
    self._scroll_area = None

  def _tick(self) -> None:
    sa = self._scroll_area
    if sa is None:
      self._timer.stop()
      return
    if self._h_dir:
      hbar = sa.horizontalScrollBar()
      hbar.setValue(hbar.value() + self._h_dir * _SCROLL_STEP)
    if self._v_dir:
      vbar = sa.verticalScrollBar()
      vbar.setValue(vbar.value() + self._v_dir * _SCROLL_STEP)


# ---------------------------------------------------------------------------
#  Board drop area (column reorder)
# ---------------------------------------------------------------------------

class _BoardDropArea(QWidget):
  drop_column_requested = Signal(int, int)

  def __init__(self, parent: Optional[QWidget] = None):
    super().__init__(parent)
    self.setAcceptDrops(True)
    self._indicator: Optional[QFrame] = None
    self._auto_scroller = _DragAutoScroller()

  def _column_widgets(self) -> list[QWidget]:
    result: list[QWidget] = []
    if not self.layout():
      return result
    for i in range(self.layout().count()):
      item = self.layout().itemAt(i)
      widget = item.widget()
      if widget is not None and isinstance(widget, _TaskColumnWidget):
        result.append(widget)
    return result

  def _target_index_from_x(self, x_pos: int) -> int:
    columns = self._column_widgets()
    index = len(columns)
    for i, col in enumerate(columns):
      midpoint = col.x() + (col.width() // 2)
      if x_pos < midpoint:
        index = i
        break
    return index

  def _ensure_indicator(self) -> QFrame:
    if self._indicator is None:
      self._indicator = QFrame(self)
      self._indicator.setObjectName("kanban_column_insertion_indicator")
      self._indicator.setFixedWidth(6)
      self._indicator.setMinimumHeight(280)
      self._indicator.setMaximumHeight(9000)
    return self._indicator

  def _show_indicator(self, index: int) -> None:
    if not self.layout():
      return
    indicator = self._ensure_indicator()
    self.layout().removeWidget(indicator)
    self.layout().insertWidget(index, indicator)
    indicator.show()

  def clear_indicator(self) -> None:
    if self._indicator and self.layout():
      self.layout().removeWidget(self._indicator)
      self._indicator.hide()

  def dragEnterEvent(self, event) -> None:
    text = event.mimeData().text() if event.mimeData() else ""
    if text.startswith("column:"):
      event.acceptProposedAction()
    else:
      event.ignore()

  def _find_scroll_area(self) -> Optional[QScrollArea]:
    p = self.parentWidget()
    while p is not None:
      if isinstance(p, QScrollArea):
        return p
      p = p.parentWidget()
    return None

  def dragMoveEvent(self, event) -> None:
    text = event.mimeData().text() if event.mimeData() else ""
    if not text.startswith("column:"):
      event.ignore()
      return
    target_index = self._target_index_from_x(event.position().toPoint().x())
    self._show_indicator(target_index)
    # Auto-scroll board horizontally when near edge
    sa = self._find_scroll_area()
    if sa:
      self._auto_scroller.update(sa, self.mapToGlobal(event.position().toPoint()), horizontal=True, vertical=False)
    event.acceptProposedAction()

  def dragLeaveEvent(self, event) -> None:
    self.clear_indicator()
    self._auto_scroller.stop()
    super().dragLeaveEvent(event)

  def dropEvent(self, event) -> None:
    self.clear_indicator()
    self._auto_scroller.stop()
    text = event.mimeData().text() if event.mimeData() else ""
    if not text.startswith("column:"):
      event.ignore()
      return
    try:
      column_id = int(text.split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
      event.ignore()
      return
    target_index = self._target_index_from_x(event.position().toPoint().x())
    self.drop_column_requested.emit(column_id, target_index)
    event.acceptProposedAction()


# ---------------------------------------------------------------------------
#  Column widget
# ---------------------------------------------------------------------------

class _TaskColumnWidget(QFrame):
  add_task_requested = Signal()
  rename_column_requested = Signal()
  delete_column_requested = Signal()
  drop_task_requested = Signal(int, int, int)

  def __init__(self, column: TaskColumn, parent: Optional[QWidget] = None):
    super().__init__(parent)
    self.column = column

    self.setObjectName("kanban_column")
    self.setMinimumWidth(320)
    self.setMaximumWidth(320)

    layout = QVBoxLayout(self)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(8)

    header_row = QHBoxLayout()

    self.column_drag_handle = _ColumnDragHandle(column_id=column.id)
    self.column_drag_handle.setObjectName("kanban_column_drag_handle")
    self.column_drag_handle.setToolTip("Drag to reorder column")
    header_row.addWidget(self.column_drag_handle)

    self.title_label = QLabel(column.name)
    self.title_label.setObjectName("kanban_column_title")
    header_row.addWidget(self.title_label)

    header_row.addStretch(1)

    self.button_add_task = QPushButton("+ Add")
    self.button_add_task.setObjectName("kanban_add_task")
    self.button_add_task.setToolTip("Add task to this column")
    self.button_add_task.setVisible(False)
    self.button_add_task.clicked.connect(self.add_task_requested.emit)
    header_row.addWidget(self.button_add_task)

    self.menu_btn = QPushButton("\u22ef")
    self.menu_btn.setObjectName("kanban_column_menu_btn")
    self.menu_btn.setToolTip("Column actions")
    self.menu_btn.setFixedSize(28, 28)
    self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    self.menu_btn.clicked.connect(self._show_column_menu)
    header_row.addWidget(self.menu_btn)

    layout.addLayout(header_row)

    self.scroll = QScrollArea(self)
    self.scroll.setObjectName("kanban_column_scroll")
    self.scroll.setWidgetResizable(True)

    self.content = _DropTasksArea(column_id=column.id)
    self.content.drop_task_requested.connect(self.drop_task_requested.emit)

    self.tasks_layout = QVBoxLayout(self.content)
    self.tasks_layout.setContentsMargins(0, 0, 0, 0)
    self.tasks_layout.setSpacing(8)

    self.scroll.setWidget(self.content)
    layout.addWidget(self.scroll)

  def enterEvent(self, event) -> None:
    self.button_add_task.setVisible(True)
    super().enterEvent(event)

  def leaveEvent(self, event) -> None:
    self.button_add_task.setVisible(False)
    super().leaveEvent(event)

  def _show_column_menu(self) -> None:
    menu = QMenu(self)
    menu.setObjectName("kanban_column_context_menu")
    add_action = menu.addAction("Add card")
    rename_action = menu.addAction("Rename column")
    menu.addSeparator()
    delete_action = menu.addAction("Delete column")
    delete_action.setProperty("destructive", True)

    chosen = menu.exec(self.menu_btn.mapToGlobal(QPoint(0, self.menu_btn.height())))
    if chosen == add_action:
      self.add_task_requested.emit()
    elif chosen == rename_action:
      self.rename_column_requested.emit()
    elif chosen == delete_action:
      self.delete_column_requested.emit()

  def populate_tasks(self, tasks: list[Task], on_card_click) -> None:
    while self.tasks_layout.count():
      item = self.tasks_layout.takeAt(0)
      widget = item.widget()
      if widget:
        widget.deleteLater()
    for task in tasks:
      card = _TaskCard(task)
      card.clicked.connect(lambda t=task: on_card_click(t))
      self.tasks_layout.addWidget(card)
    self.tasks_layout.addStretch(1)


# ---------------------------------------------------------------------------
#  Drop area for tasks
# ---------------------------------------------------------------------------

class _DropTasksArea(QFrame):
  drop_task_requested = Signal(int, int, int)

  def __init__(self, column_id: int, parent: Optional[QWidget] = None):
    super().__init__(parent)
    self.column_id = int(column_id)
    self.setObjectName("kanban_drop_area")
    self.setAcceptDrops(True)
    self._indicator: Optional[QFrame] = None
    self._auto_scroller_v = _DragAutoScroller()  # vertical scroll inside column
    self._auto_scroller_h = _DragAutoScroller()  # horizontal scroll of board

  def _cards(self) -> list[QWidget]:
    cards: list[QWidget] = []
    if not self.layout():
      return cards
    for i in range(self.layout().count()):
      item = self.layout().itemAt(i)
      widget = item.widget()
      if widget is not None and isinstance(widget, _TaskCard):
        cards.append(widget)
    return cards

  def _target_index_from_pos(self, y_pos: int) -> int:
    cards = self._cards()
    index = len(cards)
    for i, card in enumerate(cards):
      midpoint = card.y() + (card.height() // 2)
      if y_pos < midpoint:
        index = i
        break
    return index

  def _ensure_indicator(self) -> QFrame:
    if self._indicator is None:
      self._indicator = QFrame(self)
      self._indicator.setObjectName("kanban_task_insertion_indicator")
      self._indicator.setFixedHeight(10)
    return self._indicator

  def _show_indicator(self, index: int) -> None:
    if not self.layout():
      return
    indicator = self._ensure_indicator()
    self.layout().removeWidget(indicator)
    self.layout().insertWidget(index, indicator)
    indicator.show()

  def _clear_indicator(self) -> None:
    if self._indicator and self.layout():
      self.layout().removeWidget(self._indicator)
      self._indicator.hide()

  def dragEnterEvent(self, event) -> None:
    text = event.mimeData().text() if event.mimeData() else ""
    if text.startswith("task:"):
      self.setProperty("drag_over", True)
      self.style().unpolish(self)
      self.style().polish(self)
      event.acceptProposedAction()
    else:
      event.ignore()

  def _find_scroll_area(self, cls=QScrollArea, exact=False) -> Optional[QScrollArea]:
    """Walk up the tree to find the first scroll area of the given type."""
    p = self.parentWidget()
    while p is not None:
      if exact:
        if type(p) is cls:
          return p
      else:
        if isinstance(p, cls):
          return p
      p = p.parentWidget()
    return None

  def dragMoveEvent(self, event) -> None:
    text = event.mimeData().text() if event.mimeData() else ""
    if not text.startswith("task:"):
      event.ignore()
      return
    target_index = self._target_index_from_pos(event.position().toPoint().y())
    self._show_indicator(target_index)
    global_pos = self.mapToGlobal(event.position().toPoint())
    # Vertical auto-scroll inside column
    col_scroll = self._find_scroll_area(QScrollArea, exact=True)
    if col_scroll:
      self._auto_scroller_v.update(col_scroll, global_pos, horizontal=False, vertical=True)
    # Horizontal auto-scroll of the board
    board_scroll = self._find_scroll_area(_PannableScrollArea)
    if board_scroll:
      self._auto_scroller_h.update(board_scroll, global_pos, horizontal=True, vertical=False)
    event.acceptProposedAction()

  def dragLeaveEvent(self, event) -> None:
    self.setProperty("drag_over", False)
    self.style().unpolish(self)
    self.style().polish(self)
    self._clear_indicator()
    self._auto_scroller_v.stop()
    self._auto_scroller_h.stop()
    super().dragLeaveEvent(event)

  def dropEvent(self, event) -> None:
    self.setProperty("drag_over", False)
    self.style().unpolish(self)
    self.style().polish(self)
    self._auto_scroller_v.stop()
    self._auto_scroller_h.stop()
    text = event.mimeData().text() if event.mimeData() else ""
    if not text.startswith("task:"):
      self._clear_indicator()
      event.ignore()
      return
    try:
      task_id = int(text.split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
      self._clear_indicator()
      event.ignore()
      return
    target_index = self._target_index_from_pos(event.position().toPoint().y())
    self._clear_indicator()
    self.drop_task_requested.emit(task_id, self.column_id, target_index)
    event.acceptProposedAction()


# ---------------------------------------------------------------------------
#  Flow layout (wraps widgets to next row)
# ---------------------------------------------------------------------------

class _FlowLayout(QLayout):
  """Layout that wraps child widgets into multiple rows when width is exceeded."""

  def __init__(self, parent=None, h_spacing=4, v_spacing=4):
    super().__init__(parent)
    self._items: list = []
    self._h_sp = h_spacing
    self._v_sp = v_spacing

  def addItem(self, item):
    self._items.append(item)

  def count(self):
    return len(self._items)

  def itemAt(self, index):
    return self._items[index] if 0 <= index < len(self._items) else None

  def takeAt(self, index):
    return self._items.pop(index) if 0 <= index < len(self._items) else None

  def hasHeightForWidth(self):
    return True

  def heightForWidth(self, width):
    return self._layout(QRect(0, 0, width, 0), False)

  def setGeometry(self, rect):
    super().setGeometry(rect)
    self._layout(rect, True)

  def sizeHint(self):
    return self.minimumSize()

  def minimumSize(self):
    s = QSize()
    for item in self._items:
      s = s.expandedTo(item.minimumSize())
    m = self.contentsMargins()
    return s + QSize(m.left() + m.right(), m.top() + m.bottom())

  def _layout(self, rect, apply):
    m = self.contentsMargins()
    area = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
    x, y, row_h = area.x(), area.y(), 0
    for item in self._items:
      sz = item.sizeHint()
      if x + sz.width() > area.right() + 1 and row_h > 0:
        x = area.x()
        y += row_h + self._v_sp
        row_h = 0
      if apply:
        item.setGeometry(QRect(QPoint(x, y), sz))
      x += sz.width() + self._h_sp
      row_h = max(row_h, sz.height())
    return y + row_h - rect.y() + m.bottom()


# ---------------------------------------------------------------------------
#  Task card (title -> tags -> progress bar -> meta row)
# ---------------------------------------------------------------------------

class _TaskCard(QFrame):
  """Trello-style task card. Drag anywhere; click to open."""

  clicked = Signal()

  def __init__(self, task: Task, parent: Optional[QWidget] = None):
    super().__init__(parent)
    self.task = task
    self._press_pos = QPoint()
    self._click_candidate = False

    self.setObjectName("kanban_task_card")
    self.setCursor(Qt.CursorShape.PointingHandCursor)

    layout = QVBoxLayout(self)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(6)

    # -- Title row (name + tracked time) --
    title_row = QHBoxLayout()
    title_row.setSpacing(6)
    title_label = QLabel(task.name)
    title_label.setObjectName("kanban_task_name")
    title_label.setWordWrap(True)
    title_row.addWidget(title_label, 1)

    tracked_seconds = int(task.total_tracked_time)
    time_str = _format_seconds(tracked_seconds)
    time_label = QLabel(time_str)
    time_label.setObjectName("kanban_task_tracked_time")
    time_label.setToolTip(f"Time tracked: {time_str}")
    title_row.addWidget(time_label, 0, Qt.AlignmentFlag.AlignTop)
    layout.addLayout(title_row)

    if task.description:
      desc_text = _elide_text(task.description)
      desc_label = QLabel(desc_text)
      desc_label.setObjectName("kanban_task_description")
      desc_label.setToolTip(task.description)
      desc_label.setWordWrap(True)
      desc_label.setMaximumHeight(36)
      layout.addWidget(desc_label)

    # -- Tag pills (below title) --
    if task.tags:
      tags_container = QWidget()
      tags_flow = _FlowLayout(tags_container, h_spacing=4, v_spacing=4)
      tags_flow.setContentsMargins(0, 0, 0, 0)
      for tag in task.tags:
        badge = QLabel(tag.name)
        badge.setObjectName("kanban_tag_badge")
        bg = tag.color or "#4B5563"
        fg = get_contrasting_text_color(bg)
        badge.setStyleSheet(
          f"background-color: {bg}; color: {fg}; border-radius: 4px;"
          f" padding: 2px 8px; font-size: 11px; font-weight: bold;"
        )
        tags_flow.addWidget(badge)
      layout.addWidget(tags_container)

    # -- Checklist progress bar --
    checklist = task.checklist if task.checklist else []
    if checklist:
      done = sum(1 for c in checklist if c.get("done"))
      progress = QProgressBar()
      progress.setObjectName("checklist_progress")
      progress.setRange(0, len(checklist))
      progress.setValue(done)
      progress.setTextVisible(True)
      progress.setFormat(f"{done}/{len(checklist)}")
      progress.setFixedHeight(18)
      progress.setToolTip(f"Checklist: {done} of {len(checklist)} done")
      layout.addWidget(progress)

    # -- Compact meta row --
    has_meta = False
    meta_row = QHBoxLayout()
    meta_row.setSpacing(6)

    if task.due_date:
      due_text = task.due_date.strftime("%b %d")
      due_label = QLabel(f"Due {due_text}")
      due_label.setObjectName("kanban_task_meta_icon")
      due_label.setToolTip(f"Due: {task.due_date.strftime('%Y-%m-%d %H:%M')}")
      meta_row.addWidget(due_label)
      has_meta = True

    if task.priority and task.priority != TaskPriority.NONE:
      p_color = _PRIORITY_COLORS.get(task.priority, "#6b7280")
      priority_badge = QLabel(f"\u25cf {task.priority.value.title()}")
      priority_badge.setObjectName("kanban_priority_badge")
      priority_badge.setStyleSheet(f"color: {p_color};")
      meta_row.addWidget(priority_badge)
      has_meta = True

    rec = getattr(task, "recurrence", None)
    if rec and rec != TaskRecurrence.NONE:
      rec_text = _RECURRENCE_LABELS.get(rec, rec.value.title())
      rec_label = QLabel(rec_text)
      rec_label.setObjectName("kanban_task_recurrence")
      meta_row.addWidget(rec_label)
      has_meta = True

    if has_meta:
      meta_row.addStretch(1)
      layout.addLayout(meta_row)

  # -- Drag anywhere on card; short click opens dialog --

  def mousePressEvent(self, event: QMouseEvent) -> None:
    if event.button() == Qt.MouseButton.LeftButton:
      self._press_pos = event.pos()
      self._click_candidate = True
    super().mousePressEvent(event)

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    if not (event.buttons() & Qt.MouseButton.LeftButton) or not self._click_candidate:
      super().mouseMoveEvent(event)
      return
    if (event.pos() - self._press_pos).manhattanLength() < 8:
      super().mouseMoveEvent(event)
      return

    self._click_candidate = False
    pixmap = self.grab()
    self.setVisible(False)

    drag = QDrag(self)
    mime = QMimeData()
    mime.setText(f"task:{self.task.id}")
    drag.setMimeData(mime)
    drag.setPixmap(pixmap)
    drag.setHotSpot(self._press_pos)

    try:
      drag.exec(Qt.DropAction.MoveAction)
    finally:
      self.setVisible(True)

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    if event.button() == Qt.MouseButton.LeftButton and self._click_candidate:
      self.clicked.emit()
    self._click_candidate = False
    super().mouseReleaseEvent(event)


# ---------------------------------------------------------------------------
#  Column drag handle
# ---------------------------------------------------------------------------

class _ColumnDragHandle(QLabel):
  def __init__(self, column_id: int, parent: Optional[QWidget] = None):
    super().__init__("\u22ee", parent)
    self._column_id = int(column_id)
    self._start_pos = QPoint()
    self.setCursor(Qt.CursorShape.OpenHandCursor)

  def _column_widget(self) -> Optional[_TaskColumnWidget]:
    parent = self.parentWidget()
    while parent is not None:
      if isinstance(parent, _TaskColumnWidget):
        return parent
      parent = parent.parentWidget()
    return None

  @staticmethod
  def _set_drag_opacity(widget: Optional[QWidget], opacity: float) -> None:
    if widget is None:
      return
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
      effect = QGraphicsOpacityEffect(widget)
      widget.setGraphicsEffect(effect)
    effect.setOpacity(opacity)

  @staticmethod
  def _clear_drag_opacity(widget: Optional[QWidget]) -> None:
    if widget is None:
      return
    widget.setGraphicsEffect(None)

  def mousePressEvent(self, event: QMouseEvent) -> None:
    if event.button() == Qt.MouseButton.LeftButton:
      self._start_pos = event.pos()
      self.setCursor(Qt.CursorShape.ClosedHandCursor)
      self._set_drag_opacity(self._column_widget(), 0.5)
    super().mousePressEvent(event)

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    self.setCursor(Qt.CursorShape.OpenHandCursor)
    self._clear_drag_opacity(self._column_widget())
    super().mouseReleaseEvent(event)

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    if not (event.buttons() & Qt.MouseButton.LeftButton):
      super().mouseMoveEvent(event)
      return
    if (event.pos() - self._start_pos).manhattanLength() < 6:
      super().mouseMoveEvent(event)
      return
    col = self._column_widget()
    if col is not None:
      col.setVisible(False)
    drag = QDrag(self)
    mime = QMimeData()
    mime.setText(f"column:{self._column_id}")
    drag.setMimeData(mime)
    if col is not None:
      pixmap = col.grab()
      drag.setPixmap(pixmap)
      drag.setHotSpot(QPoint(18, 18))
    try:
      drag.exec(Qt.DropAction.MoveAction)
    finally:
      if col is not None:
        col.setVisible(True)
      self._clear_drag_opacity(col)


# ---------------------------------------------------------------------------
#  Label dialog (create or edit)
# ---------------------------------------------------------------------------

class _LabelDialog(QDialog):
  """Dialog for creating or editing a label with a color picker."""

  def __init__(self, parent: QWidget, name: str = "", color: str = "#4B5563",
               edit_mode: bool = False):
    super().__init__(parent)
    self.setWindowTitle("Edit label" if edit_mode else "Create Label")
    self.setObjectName("task_form_dialog")
    self.setModal(True)
    self.resize(360, 0)

    self._color = color or "#4B5563"
    self._deleted = False

    layout = QVBoxLayout(self)
    layout.setContentsMargins(16, 16, 16, 12)
    layout.setSpacing(10)

    if edit_mode:
      header = QHBoxLayout()
      header.addStretch(1)
      title = QLabel("Edit label")
      title.setStyleSheet("font-size: 14px; font-weight: bold;")
      header.addWidget(title)
      header.addStretch(1)
      close_btn = QPushButton("")
      close_btn.setObjectName("popup_close_btn")
      close_btn.setFixedSize(28, 28)
      close_btn.setIcon(_make_close_icon(color="#9CA3AF"))
      close_btn.setIconSize(QSize(14, 14))
      close_btn.clicked.connect(self.reject)
      header.addWidget(close_btn)
      layout.addLayout(header)

    self.preview_pill = QLabel(name or "Label preview")
    self.preview_pill.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    self.preview_pill.setMinimumHeight(36)
    layout.addWidget(self.preview_pill)

    layout.addWidget(QLabel("Title"))
    self.name_input = QLineEdit()
    self.name_input.setPlaceholderText("e.g. UI/UX, Backend, Bug...")
    self.name_input.setClearButtonEnabled(True)
    self.name_input.setText(name)
    self.name_input.textChanged.connect(self._update_preview)
    layout.addWidget(self.name_input)

    layout.addWidget(QLabel("Color"))
    color_row = QHBoxLayout()
    color_row.setSpacing(8)
    self.color_btn = QPushButton()
    self.color_btn.setFixedSize(42, 28)
    self.color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    self.color_btn.clicked.connect(self._pick_color)
    color_row.addWidget(self.color_btn)

    self.color_hex_label = QLabel(self._color)
    self.color_hex_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
    color_row.addWidget(self.color_hex_label)

    color_row.addStretch(1)

    remove_color_btn = QPushButton("\u2717 Remove")
    remove_color_btn.setObjectName("label_remove_color_btn")
    remove_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    remove_color_btn.setMaximumWidth(110)
    remove_color_btn.clicked.connect(lambda: self._set_color("#4B5563"))
    color_row.addWidget(remove_color_btn)

    layout.addLayout(color_row)

    buttons_row = QHBoxLayout()
    if edit_mode:
      cancel_btn = QPushButton("Cancel")
      cancel_btn.clicked.connect(self.reject)
      buttons_row.addWidget(cancel_btn)

      save_btn = QPushButton("Save")
      save_btn.setObjectName("dialog_ok_btn")
      save_btn.clicked.connect(self.accept)
      buttons_row.addWidget(save_btn)

      delete_btn = QPushButton("Delete")
      delete_btn.setObjectName("dialog_delete_task")
      delete_btn.clicked.connect(self._on_delete)
      buttons_row.addWidget(delete_btn)
    else:
      buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
      ok_btn = buttons.button(QDialogButtonBox.Ok)
      if ok_btn:
        ok_btn.setText("Create")
      buttons.accepted.connect(self.accept)
      buttons.rejected.connect(self.reject)
      buttons_row.addWidget(buttons)
    layout.addLayout(buttons_row)

    self._sync_color_preview()
    self._update_preview()

  def _set_color(self, color: str) -> None:
    self._color = color
    self._sync_color_preview()
    self._update_preview()

  def _pick_color(self) -> None:
    chosen = QColorDialog.getColor(QColor(self._color), self, "Label color")
    if chosen.isValid():
      self._set_color(chosen.name())

  def _sync_color_preview(self) -> None:
    self.color_btn.setStyleSheet(
      f"background-color: {self._color}; border: 1px solid #505052;"
      f" border-radius: 6px;"
    )
    self.color_hex_label.setText(self._color)

  def _update_preview(self) -> None:
    text = self.name_input.text().strip() or "Label preview"
    tc = get_contrasting_text_color(self._color)
    self.preview_pill.setText(text)
    self.preview_pill.setStyleSheet(
      f"background-color: {self._color}; color: {tc};"
      f" border-radius: 6px; padding: 8px 16px; font-size: 13px; font-weight: bold;"
    )

  def _on_delete(self) -> None:
    self._deleted = True
    self.accept()

  @property
  def deleted(self) -> bool:
    return self._deleted

  def label_name(self) -> str:
    return self.name_input.text().strip()

  def label_color(self) -> str:
    return self._color


# ---------------------------------------------------------------------------
#  Labels popup (Trello-style)
# ---------------------------------------------------------------------------

class _LabelsPopup(QDialog):
  """Trello-like floating labels picker."""

  def __init__(self,
               parent: QWidget,
               available_tags: list,
               selected_tag_ids: set,
               tag_creator,
               tag_deleter=None,
               tag_updater=None):
    super().__init__(parent)
    self.setWindowTitle("Labels")
    self.setObjectName("labels_popup")
    self.setModal(True)
    self.resize(380, 0)

    self._tag_creator = tag_creator
    self._tag_deleter = tag_deleter
    self._tag_updater = tag_updater
    self._items: list[tuple[int, str, str, QCheckBox]] = []  # (id, name, color, cb)

    layout = QVBoxLayout(self)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)

    header_row = QHBoxLayout()
    header_row.addStretch(1)
    lbl_title = QLabel("Labels")
    lbl_title.setStyleSheet("font-size: 14px; font-weight: bold;")
    header_row.addWidget(lbl_title)
    header_row.addStretch(1)
    close_btn = QPushButton("")
    close_btn.setObjectName("popup_close_btn")
    close_btn.setFixedSize(28, 28)
    close_btn.setIcon(_make_close_icon(color="#9CA3AF"))
    close_btn.setIconSize(QSize(14, 14))
    close_btn.clicked.connect(self.accept)
    header_row.addWidget(close_btn)
    layout.addLayout(header_row)

    self.search_input = QLineEdit()
    self.search_input.setPlaceholderText("Search labels...")
    self.search_input.setClearButtonEnabled(True)
    self.search_input.textChanged.connect(self._filter)
    layout.addWidget(self.search_input)

    # Label "Labels" sub-header
    sub_header = QLabel("Labels")
    sub_header.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: bold;")
    layout.addWidget(sub_header)

    # "No results" / create suggestion label (hidden by default)
    self.no_results_btn = QPushButton()
    self.no_results_btn.setObjectName("label_create_suggestion")
    self.no_results_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    self.no_results_btn.setVisible(False)
    self.no_results_btn.clicked.connect(self._create_from_search)
    layout.addWidget(self.no_results_btn)

    self.list_widget = QWidget()
    self.list_layout = QVBoxLayout(self.list_widget)
    self.list_layout.setContentsMargins(0, 0, 0, 0)
    self.list_layout.setSpacing(4)
    self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    self.list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    layout.addWidget(self.list_widget)

    for tag in available_tags:
      self._add_row(tag.id, tag.name, tag.color, tag.id in selected_tag_ids)

    # Keep actions at the bottom, content anchored to top
    layout.addStretch(1)

    btn_create = QPushButton("Create a new label")
    btn_create.clicked.connect(self._create_label)
    layout.addWidget(btn_create)

    # Confirm button
    confirm_btn = QPushButton("Done")
    confirm_btn.setObjectName("dialog_ok_btn")
    confirm_btn.clicked.connect(self.accept)
    layout.addWidget(confirm_btn)

  def _add_row(self, tag_id: int, name: str, color: Optional[str], checked: bool) -> None:
    tag_color = color or "#4B5563"
    text_color = get_contrasting_text_color(tag_color)
    row_widget = QWidget()
    row_widget.setObjectName("label_row")
    row_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    row_layout = QHBoxLayout(row_widget)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(6)

    cb = QCheckBox()
    cb.setChecked(checked)
    row_layout.addWidget(cb)

    pill = QPushButton(name)
    pill.setObjectName("label_pill")
    pill.setStyleSheet(
      f"background-color: {tag_color}; color: {text_color}; border-radius: 6px;"
      f" padding: 6px 14px; font-size: 12px; font-weight: bold; text-align: left;"
      f" border: none;"
    )
    pill.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    pill.setCursor(Qt.CursorShape.PointingHandCursor)
    pill.clicked.connect(lambda: cb.setChecked(not cb.isChecked()))
    row_layout.addWidget(pill)

    edit_btn = QPushButton("")
    edit_btn.setObjectName("checklist_remove_btn")
    edit_btn.setFixedSize(24, 24)
    edit_btn.setToolTip("Edit label")
    edit_btn.setIcon(_make_edit_icon(size=14, color="#9CA3AF", thickness=2))
    edit_btn.setIconSize(QSize(14, 14))
    edit_btn.clicked.connect(lambda _, tid=tag_id: self._edit_label(tid))
    row_layout.addWidget(edit_btn)

    self.list_layout.addWidget(row_widget)
    self._items.append((tag_id, name, tag_color, cb))

  def _filter(self, text: str) -> None:
    ft = text.lower()
    any_visible = False
    for i in range(self.list_layout.count()):
      widget = self.list_layout.itemAt(i).widget()
      if widget and i < len(self._items):
        tag_name = self._items[i][1].lower()
        visible = not ft or ft in tag_name
        widget.setMaximumHeight(16777215 if visible else 0)
        widget.setVisible(visible)
        if visible:
          any_visible = True

    # Show create suggestion if search has text and nothing matches
    if ft and not any_visible:
      self.no_results_btn.setText(f'Create label "{text.strip()}"')
      self.no_results_btn.setVisible(True)
    else:
      self.no_results_btn.setVisible(False)

  def _create_from_search(self) -> None:
    """Open create dialog prefilled with the current search text."""
    name = self.search_input.text().strip()
    if not name:
      return

    dialog = _LabelDialog(self, name=name)
    if dialog.exec_() != QDialog.Accepted:
      return

    final_name = dialog.label_name()
    if not final_name:
      return
    final_color = dialog.label_color()

    tag = self._tag_creator(final_name, final_color)
    if not tag:
      QMessageBox.warning(self, "Label", "Could not create label.")
      return
    self._add_row(tag.id, tag.name, tag.color, True)
    self.search_input.clear()

  def _create_label(self) -> None:
    dialog = _LabelDialog(self)
    if dialog.exec_() != QDialog.Accepted:
      return
    name = dialog.label_name()
    if not name:
      return
    color = dialog.label_color()
    tag = self._tag_creator(name, color)
    if not tag:
      QMessageBox.warning(self, "Label", "Could not create label.")
      return
    self._add_row(tag.id, tag.name, tag.color, True)

  def _edit_label(self, tag_id: int) -> None:
    """Open edit dialog for a label. Supports rename, recolor, and delete."""
    idx = next((i for i, (tid, _, _, _) in enumerate(self._items) if tid == tag_id), None)
    if idx is None:
      return
    _, old_name, old_color, cb = self._items[idx]

    dialog = _LabelDialog(self, name=old_name, color=old_color, edit_mode=True)
    if dialog.exec_() != QDialog.Accepted:
      return

    if dialog.deleted:
      # Delete the label
      reply = QMessageBox.question(
        self, "Delete Label",
        "Delete this label? It will be removed from all tasks.",
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
      )
      if reply != QMessageBox.Yes:
        return
      if self._tag_deleter and self._tag_deleter(tag_id):
        item = self.list_layout.takeAt(idx)
        w = item.widget()
        if w:
          w.deleteLater()
        self._items.pop(idx)
      else:
        QMessageBox.warning(self, "Label", "Could not delete label.")
      return

    # Update the label
    new_name = dialog.label_name()
    new_color = dialog.label_color()
    if not new_name:
      return
    if self._tag_updater:
      updated = self._tag_updater(tag_id, new_name, new_color)
      if not updated:
        QMessageBox.warning(self, "Label", "Could not update label.")
        return
    # Rebuild this row in-place
    old_checked = cb.isChecked()
    item = self.list_layout.takeAt(idx)
    w = item.widget()
    if w:
      w.deleteLater()
    self._items.pop(idx)
    # Re-insert at same position
    self._insert_row_at(idx, tag_id, new_name, new_color, old_checked)

  def _insert_row_at(self, index: int, tag_id: int, name: str,
                     color: Optional[str], checked: bool) -> None:
    """Like _add_row but inserts at a specific index."""
    tag_color = color or "#4B5563"
    text_color = get_contrasting_text_color(tag_color)
    row_widget = QWidget()
    row_widget.setObjectName("label_row")
    row_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    row_layout = QHBoxLayout(row_widget)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(6)

    cb = QCheckBox()
    cb.setChecked(checked)
    row_layout.addWidget(cb)

    pill = QPushButton(name)
    pill.setObjectName("label_pill")
    pill.setStyleSheet(
      f"background-color: {tag_color}; color: {text_color}; border-radius: 6px;"
      f" padding: 6px 14px; font-size: 12px; font-weight: bold; text-align: left;"
      f" border: none;"
    )
    pill.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    pill.setCursor(Qt.CursorShape.PointingHandCursor)
    pill.clicked.connect(lambda: cb.setChecked(not cb.isChecked()))
    row_layout.addWidget(pill)

    edit_btn = QPushButton("")
    edit_btn.setObjectName("checklist_remove_btn")
    edit_btn.setFixedSize(24, 24)
    edit_btn.setToolTip("Edit label")
    edit_btn.setIcon(_make_edit_icon(size=14, color="#9CA3AF", thickness=2))
    edit_btn.setIconSize(QSize(14, 14))
    edit_btn.clicked.connect(lambda _, tid=tag_id: self._edit_label(tid))
    row_layout.addWidget(edit_btn)

    self.list_layout.insertWidget(index, row_widget)
    self._items.insert(index, (tag_id, name, tag_color, cb))

  def selected_tag_names(self) -> list[str]:
    return [name for _, name, _, cb in self._items if cb.isChecked()]

  def selected_tag_ids(self) -> set:
    return {tag_id for tag_id, _, _, cb in self._items if cb.isChecked()}


# ---------------------------------------------------------------------------
#  Dates popup (Trello-style: calendar + start/due + recurrence)
# ---------------------------------------------------------------------------

class _DatesPopup(QDialog):
  """Trello-like dates picker with calendar, start/due date and recurrence."""

  def __init__(self,
               parent: QWidget,
               start_date=None,
               due_date=None,
               recurrence: TaskRecurrence = TaskRecurrence.NONE):
    super().__init__(parent)
    self.setWindowTitle("Dates")
    self.setObjectName("dates_popup")
    self.setModal(True)
    self.resize(380, 0)
    self._active_date_target = "due"

    layout = QVBoxLayout(self)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)

    header_row = QHBoxLayout()
    header_row.addStretch(1)
    lbl_title = QLabel("Dates")
    lbl_title.setStyleSheet("font-size: 14px; font-weight: bold;")
    header_row.addWidget(lbl_title)
    header_row.addStretch(1)
    close_btn = QPushButton("")
    close_btn.setObjectName("popup_close_btn")
    close_btn.setFixedSize(28, 28)
    close_btn.setIcon(_make_close_icon(color="#9CA3AF"))
    close_btn.setIconSize(QSize(14, 14))
    close_btn.clicked.connect(self.accept)
    header_row.addWidget(close_btn)
    layout.addLayout(header_row)

    self.calendar = QCalendarWidget()
    self.calendar.setObjectName("dates_popup_calendar")
    self.calendar.setGridVisible(False)
    self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
    if due_date:
      self.calendar.setSelectedDate(QDate(due_date.year, due_date.month, due_date.day))
    else:
      self.calendar.setSelectedDate(QDate.currentDate())
    layout.addWidget(self.calendar)

    # Start date
    self.start_cb = QCheckBox("Start date")
    self.start_cb.setChecked(start_date is not None)
    layout.addWidget(self.start_cb)

    self.start_input = QDateTimeEdit()
    self.start_input.setCalendarPopup(False)
    self.start_input.setDisplayFormat("yyyy-MM-dd HH:mm")
    self.start_input.setDateTime(
      start_date if start_date else QDateTime.currentDateTime()
    )
    self.start_input.setEnabled(self.start_cb.isChecked())
    self.start_cb.toggled.connect(self.start_input.setEnabled)
    self.start_cb.toggled.connect(lambda checked: self._set_active_target("start") if checked else None)
    self.start_input.installEventFilter(self)
    layout.addWidget(self.start_input)

    # Due date
    self.due_cb = QCheckBox("Due date")
    self.due_cb.setChecked(due_date is not None)
    layout.addWidget(self.due_cb)

    self.due_input = QDateTimeEdit()
    self.due_input.setCalendarPopup(False)
    self.due_input.setDisplayFormat("yyyy-MM-dd HH:mm")
    self.due_input.setDateTime(
      due_date if due_date else QDateTime.currentDateTime()
    )
    self.due_input.setEnabled(self.due_cb.isChecked())
    self.due_cb.toggled.connect(self.due_input.setEnabled)
    self.due_cb.toggled.connect(lambda checked: self._set_active_target("due") if checked else None)
    self.due_input.installEventFilter(self)
    layout.addWidget(self.due_input)

    self.calendar.selectionChanged.connect(self._on_calendar_changed)

    # Recurrence
    layout.addWidget(QLabel("Recurring"))
    self.recurrence_combo = QComboBox()
    self.recurrence_combo.addItem("Never", TaskRecurrence.NONE)
    self.recurrence_combo.addItem("Daily", TaskRecurrence.DAILY)
    self.recurrence_combo.addItem("Weekly", TaskRecurrence.WEEKLY)
    self.recurrence_combo.addItem("Monthly", TaskRecurrence.MONTHLY)
    self.recurrence_combo.addItem("Yearly", TaskRecurrence.YEARLY)
    for i in range(self.recurrence_combo.count()):
      if self.recurrence_combo.itemData(i) == recurrence:
        self.recurrence_combo.setCurrentIndex(i)
        break
    layout.addWidget(self.recurrence_combo)

    # Save / Remove buttons
    btn_row = QHBoxLayout()
    save_btn = QPushButton("Save")
    save_btn.clicked.connect(self.accept)
    btn_row.addWidget(save_btn)
    remove_btn = QPushButton("Remove")
    remove_btn.setObjectName("dates_remove_btn")
    remove_btn.clicked.connect(self._on_remove)
    btn_row.addWidget(remove_btn)
    layout.addLayout(btn_row)

    self._removed = False

  def _on_calendar_changed(self) -> None:
    selected = self.calendar.selectedDate()
    target = self.start_input if self._active_date_target == "start" else self.due_input
    target_cb = self.start_cb if self._active_date_target == "start" else self.due_cb
    current_time = target.dateTime().time()
    new_dt = QDateTime(selected, current_time)
    target.setDateTime(new_dt)
    if not target_cb.isChecked():
      target_cb.setChecked(True)

  def _set_active_target(self, target: str) -> None:
    if target in ("start", "due"):
      self._active_date_target = target

  def eventFilter(self, watched: QObject, event: QEvent) -> bool:
    if event.type() == QEvent.Type.FocusIn:
      if watched is self.start_input:
        self._set_active_target("start")
      elif watched is self.due_input:
        self._set_active_target("due")
    return super().eventFilter(watched, event)

  def _on_remove(self) -> None:
    self._removed = True
    self.accept()

  def result_dates(self) -> tuple:
    """Returns (start_str, due_str, recurrence)."""
    if self._removed:
      return ("", "", TaskRecurrence.NONE)
    start = ""
    if self.start_cb.isChecked():
      start = self.start_input.dateTime().toString("yyyy-MM-ddTHH:mm:ss")
    due = ""
    if self.due_cb.isChecked():
      due = self.due_input.dateTime().toString("yyyy-MM-ddTHH:mm:ss")
    return (start, due, self.recurrence_combo.currentData())


# ---------------------------------------------------------------------------
#  Task dialog (single-column layout)
# ---------------------------------------------------------------------------

class _TaskDialog(QDialog):
  def __init__(self,
               parent: QWidget,
               title: str,
               default_column_id: Optional[int],
               available_tags: list,
               tag_creator,
               tag_deleter=None,
               tag_updater=None,
               tag_fetcher=None,
               task: Optional[Task] = None):
    super().__init__(parent)
    self.setWindowTitle(title)
    self.setObjectName("task_form_dialog")
    self.setModal(True)
    self.resize(560, 0)

    self._tag_creator = tag_creator
    self._tag_deleter = tag_deleter
    self._tag_updater = tag_updater
    self._tag_fetcher = tag_fetcher
    self._is_edit_mode = task is not None
    self.delete_requested = False
    self._column_id = default_column_id
    self._available_tags = list(available_tags)

    # State from popups
    self._selected_tag_ids: set = (
      {tag.id for tag in task.tags} if task and task.tags else set()
    )
    self._start_date_str: str = (
      task.start_date.strftime("%Y-%m-%dT%H:%M:%S") if task and task.start_date else ""
    )
    self._due_date_str: str = (
      task.due_date.strftime("%Y-%m-%dT%H:%M:%S") if task and task.due_date else ""
    )
    self._recurrence: TaskRecurrence = (
      getattr(task, "recurrence", TaskRecurrence.NONE) or TaskRecurrence.NONE
    )
    self._checklist: list = (
      deepcopy(task.checklist) if task and task.checklist else []
    )

    layout = QVBoxLayout(self)
    layout.setContentsMargins(20, 20, 20, 16)
    layout.setSpacing(10)

    dialog_title_lbl = QLabel(title)
    dialog_title_lbl.setObjectName("dialog_title")
    layout.addWidget(dialog_title_lbl)

    # Task name
    layout.addWidget(QLabel("Task name:"))
    self.name_input = QLineEdit()
    self.name_input.setPlaceholderText("e.g. Implement board filters")
    self.name_input.setClearButtonEnabled(True)
    self.name_input.setText(task.name if task else "")
    layout.addWidget(self.name_input)

    # Description
    layout.addWidget(QLabel("Description:"))
    self.description_input = QTextEdit()
    self.description_input.setMinimumHeight(80)
    self.description_input.setMaximumHeight(140)
    self.description_input.setPlaceholderText("Add a more detailed description...")
    self.description_input.setPlainText(task.description or "" if task else "")
    layout.addWidget(self.description_input)

    # Priority
    priority_row = QHBoxLayout()
    priority_row.addWidget(QLabel("Priority:"))
    self.priority_combo = QComboBox()
    self.priority_combo.addItem(_make_none_priority_icon(), "None", TaskPriority.NONE)
    self.priority_combo.addItem(
      _make_priority_icon("#dc2626"), "High", TaskPriority.HIGH,
    )
    self.priority_combo.addItem(
      _make_priority_icon("#d97706"), "Medium", TaskPriority.MEDIUM,
    )
    self.priority_combo.addItem(
      _make_priority_icon("#2563eb"), "Low", TaskPriority.LOW,
    )
    self.priority_combo.setMinimumWidth(140)
    priority_row.addWidget(self.priority_combo)
    priority_row.addStretch(1)
    layout.addLayout(priority_row)

    if task:
      self._set_combo_data(self.priority_combo, task.priority)

    # Labels
    self.labels_link = QPushButton("Labels")
    self.labels_link.setObjectName("task_section_link")
    self.labels_link.setCursor(Qt.CursorShape.PointingHandCursor)
    self.labels_link.clicked.connect(self._open_labels_popup)
    layout.addWidget(self.labels_link)

    self.labels_display = QHBoxLayout()
    self.labels_display.setSpacing(4)
    layout.addLayout(self.labels_display)
    self._refresh_label_pills()

    # Dates
    self.dates_link = QPushButton()
    self.dates_link.setObjectName("task_section_link")
    self.dates_link.setCursor(Qt.CursorShape.PointingHandCursor)
    self.dates_link.setIcon(
      _theme_icon(["x-office-calendar", "calendar", "office-calendar"], QStyle.StandardPixmap.SP_FileDialogDetailedView, self)
    )
    self.dates_link.clicked.connect(self._open_dates_popup)
    layout.addWidget(self.dates_link)

    self._refresh_dates_summary()

    # Separator
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet("color: #363739;")
    sep.setFixedHeight(1)
    layout.addWidget(sep)

    # Checklist
    layout.addWidget(QLabel("Checklist:"))
    self.checklist_list = QVBoxLayout()
    self.checklist_list.setSpacing(4)
    layout.addLayout(self.checklist_list)
    self._render_checklist()

    cl_add_row = QHBoxLayout()
    self.checklist_input = QLineEdit()
    self.checklist_input.setPlaceholderText("Add an item...")
    self.checklist_input.returnPressed.connect(self._add_checklist_item)
    self.checklist_input.installEventFilter(self)
    cl_add_row.addWidget(self.checklist_input)
    add_cl_btn = QPushButton("+ Add")
    add_cl_btn.clicked.connect(self._add_checklist_item)
    cl_add_row.addWidget(add_cl_btn)
    layout.addLayout(cl_add_row)

    layout.addStretch(1)

    # Bottom buttons
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    ok_button = buttons.button(QDialogButtonBox.Ok)
    cancel_button = buttons.button(QDialogButtonBox.Cancel)
    if ok_button:
      ok_button.setText("Save Task" if self._is_edit_mode else "Create Task")
    if cancel_button:
      cancel_button.setText("Cancel")
    if self._is_edit_mode:
      self.button_delete = QPushButton("Delete Task")
      self.button_delete.setObjectName("dialog_delete_task")
      self.button_delete.setToolTip("Delete this task")
      buttons.addButton(self.button_delete, QDialogButtonBox.DestructiveRole)
      self.button_delete.clicked.connect(self._on_delete_clicked)

    buttons.accepted.connect(self.accept)
    buttons.rejected.connect(self.reject)
    layout.addWidget(buttons)

  def _on_delete_clicked(self) -> None:
    self.delete_requested = True
    self.accept()

  def eventFilter(self, watched: QObject, event: QEvent) -> bool:
    if watched is self.checklist_input and event.type() == QEvent.Type.KeyPress:
      key = event.key()
      if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        self._add_checklist_item()
        event.accept()
        return True
    return super().eventFilter(watched, event)

  @staticmethod
  def _set_combo_data(combo: QComboBox, value) -> None:
    for index in range(combo.count()):
      if combo.itemData(index) == value:
        combo.setCurrentIndex(index)
        return

  # -- Labels popup --

  def _open_labels_popup(self) -> None:
    popup = _LabelsPopup(
      parent=self,
      available_tags=self._available_tags,
      selected_tag_ids=self._selected_tag_ids,
      tag_creator=self._tag_creator,
      tag_deleter=self._tag_deleter,
      tag_updater=self._tag_updater,
    )
    popup.exec_()
    self._selected_tag_ids = popup.selected_tag_ids()
    # Re-fetch tags so newly created / deleted / edited tags are reflected
    if self._tag_fetcher:
      self._available_tags = list(self._tag_fetcher())
    self._refresh_label_pills()

  def _refresh_label_pills(self) -> None:
    while self.labels_display.count():
      item = self.labels_display.takeAt(0)
      w = item.widget()
      if w:
        w.deleteLater()

    found = False
    for tag in self._available_tags:
      if tag.id in self._selected_tag_ids:
        found = True
        color = tag.color or "#4B5563"
        text_color = get_contrasting_text_color(color)
        pill = QLabel(tag.name)
        pill.setStyleSheet(
          f"background-color: {color}; color: {text_color}; border-radius: 4px;"
          f" padding: 3px 10px; font-size: 11px; font-weight: bold;"
        )
        pill.setCursor(Qt.CursorShape.PointingHandCursor)
        pill.setToolTip("Right-click to remove")
        pill.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        pill.customContextMenuRequested.connect(
          lambda _pos, tid=tag.id: self._unassign_label(tid)
        )
        self.labels_display.addWidget(pill)

    if not found:
      none_label = QLabel("No labels")
      none_label.setStyleSheet("color: #6b7280; font-size: 11px;")
      self.labels_display.addWidget(none_label)

    self.labels_display.addStretch(1)

  def _unassign_label(self, tag_id: int) -> None:
    self._selected_tag_ids.discard(tag_id)
    self._refresh_label_pills()

  # -- Dates popup --

  def _open_dates_popup(self) -> None:
    from datetime import datetime

    start_dt = None
    if self._start_date_str:
      try:
        start_dt = datetime.fromisoformat(self._start_date_str)
      except ValueError:
        pass

    due_dt = None
    if self._due_date_str:
      try:
        due_dt = datetime.fromisoformat(self._due_date_str)
      except ValueError:
        pass

    popup = _DatesPopup(
      parent=self,
      start_date=start_dt,
      due_date=due_dt,
      recurrence=self._recurrence,
    )
    popup.exec_()
    start, due, rec = popup.result_dates()
    self._start_date_str = start
    self._due_date_str = due
    self._recurrence = rec
    self._refresh_dates_summary()

  def _refresh_dates_summary(self) -> None:
    parts = []
    if self._start_date_str:
      parts.append(f"Start: {self._start_date_str[:10]}")
    if self._due_date_str:
      parts.append(f"Due: {self._due_date_str[:10]}")
    if self._recurrence and self._recurrence != TaskRecurrence.NONE:
      parts.append(f"\u21bb {self._recurrence.value.title()}")
    summary = "  \u2022  ".join(parts) if parts else "No dates set"
    self.dates_link.setText(f"Dates  —  {summary}")

  # -- Checklist --

  def _render_checklist(self) -> None:
    while self.checklist_list.count():
      item = self.checklist_list.takeAt(0)
      w = item.widget()
      if w:
        w.deleteLater()
    for idx, entry in enumerate(self._checklist):
      row = QWidget()
      row.setObjectName("checklist_item_row")
      row_layout = QHBoxLayout(row)
      row_layout.setContentsMargins(4, 2, 4, 2)
      row_layout.setSpacing(4)
      cb = QCheckBox(entry.get("text", ""))
      cb.setChecked(entry.get("done", False))
      cb.toggled.connect(lambda checked, i=idx: self._toggle_checklist(i, checked))
      row_layout.addWidget(cb)
      del_btn = QPushButton("")
      del_btn.setObjectName("checklist_remove_btn")
      del_btn.setFixedSize(24, 24)
      del_btn.setToolTip("Remove item")
      del_btn.setIcon(_make_close_icon(size=12, color="#6b7280", thickness=2))
      del_btn.setIconSize(QSize(12, 12))
      del_btn.clicked.connect(lambda _, i=idx: self._remove_checklist(i))
      row_layout.addWidget(del_btn)
      self.checklist_list.addWidget(row)

  def _add_checklist_item(self) -> None:
    text = self.checklist_input.text().strip()
    if not text:
      return
    self._checklist.append({"text": text, "done": False})
    self.checklist_input.clear()
    self._render_checklist()

  def _toggle_checklist(self, idx: int, checked: bool) -> None:
    if 0 <= idx < len(self._checklist):
      self._checklist[idx]["done"] = checked

  def _remove_checklist(self, idx: int) -> None:
    if 0 <= idx < len(self._checklist):
      self._checklist.pop(idx)
      self._render_checklist()

  # -- Payload --

  def payload(self) -> dict:
    tag_names = []
    for tag in self._available_tags:
      if tag.id in self._selected_tag_ids:
        tag_names.append(tag.name)
    return {
      "name": self.name_input.text().strip(),
      "description": self.description_input.toPlainText().strip(),
      "column_id": self._column_id,
      "priority": self.priority_combo.currentData(),
      "start_date": self._start_date_str,
      "due_date": self._due_date_str,
      "tags": tag_names,
      "recurrence": self._recurrence,
      "checklist": deepcopy(self._checklist),
    }
