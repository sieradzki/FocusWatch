from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QLabel, QSizePolicy, QToolTip


class ElidedLabel(QLabel):
  """ Custom label that elides text and shows a tooltip when the text is elided. """

  def __init__(self, full_text, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.full_text = full_text
    self.is_elided = False
    self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    self.setMouseTracking(True)

  def resizeEvent(self, event):
    metrics = QFontMetrics(self.font())
    elided_text = metrics.elidedText(
      self.full_text, Qt.ElideRight, self.width())

    # Check if the text is actually elided
    self.is_elided = (elided_text != self.full_text)

    self.setText(elided_text)
    super().resizeEvent(event)

  def enterEvent(self, event):
    # Show tooltip only if the text is elided
    if self.is_elided:
      QToolTip.showText(self.mapToGlobal(
        self.rect().bottomLeft()), self.full_text)
    super().enterEvent(event)

  def leaveEvent(self, event):
    QToolTip.hideText()
    super().leaveEvent(event)
