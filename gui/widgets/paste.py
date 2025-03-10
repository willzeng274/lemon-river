"""
Widgets that paste plain text without formatting
"""

import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QLineEdit, QTextEdit, QApplication
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


# pylint: disable=invalid-name
class PlainPasteLineEdit(QLineEdit):
    """QLineEdit with plain text paste behavior"""

    def keyPressEvent(self, event):
        """Override keyPressEvent to handle Ctrl+V (Command+V on Mac)"""
        modifiers = QApplication.keyboardModifiers()
        if event.key() == Qt.Key.Key_V and (
            modifiers & Qt.KeyboardModifier.ControlModifier
        ):
            clipboard = QApplication.clipboard()
            self.insert(clipboard.text())
            return
        super().keyPressEvent(event)


class PlainPasteTextEdit(QTextEdit):
    """TextEdit that pastes plain text"""

    def keyPressEvent(self, event):
        """Handle key press events"""
        if (
            event.key() == Qt.Key.Key_V
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.insertPlainText(QApplication.clipboard().text())
        else:
            super().keyPressEvent(event)
