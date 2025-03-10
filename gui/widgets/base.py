"""Base widget"""

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt


# pylint: disable=invalid-name
class DraggableWindow(QMainWindow):
    """Base window class that can be dragged by clicking and holding anywhere"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, False)
        self._drag_pos = None
        self.focused_opacity = 1.0
        self.unfocused_opacity = 0.8

    def mousePressEvent(self, event):
        """Handle mouse press events for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging"""
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos:
            diff = event.globalPosition().toPoint() - self._drag_pos
            new_pos = self.pos() + diff
            self.move(new_pos)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None

    def changeEvent(self, event):
        """Handle window activation changes"""
        if event.type() == event.Type.ActivationChange:
            if self.isActiveWindow():
                self.setWindowOpacity(self.focused_opacity)
            else:
                self.setWindowOpacity(self.unfocused_opacity)
        super().changeEvent(event)
