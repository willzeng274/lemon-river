"""
Widgets that can be locked/unlocked
"""

import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QPushButton, QLineEdit, QTextEdit, QListWidget
from PyQt6.QtCore import QSize
from .paste import PlainPasteLineEdit, PlainPasteTextEdit

logger = logging.getLogger(__name__)


class LockableField:
    """A field that can be locked"""

    def __init__(self, field_widget, field_name: str):
        self.widget = field_widget
        self.field_name = field_name
        self.is_locked = False

        self.lock_button = QPushButton("⚡")
        self.lock_button.setProperty("lockButton", True)
        self.lock_button.setFixedSize(QSize(24, 24))
        self.lock_button.clicked.connect(self.toggle_lock)

    def toggle_lock(self):
        """Toggle the lock state"""
        self.is_locked = not self.is_locked
        self.lock_button.setText("🔒" if self.is_locked else "⚡")

        if isinstance(
            self.widget, (QLineEdit, PlainPasteLineEdit, QTextEdit, PlainPasteTextEdit)
        ):
            self.widget.setReadOnly(self.is_locked)
            if isinstance(self.widget, (QTextEdit, PlainPasteTextEdit)):
                self.widget.setStyleSheet(
                    "background-color: rgba(0, 0, 0, 0.05);" if self.is_locked else ""
                )
        elif isinstance(self.widget, QListWidget):
            self.widget.setEnabled(not self.is_locked)
            self.widget.setStyleSheet(
                "background-color: rgba(0, 0, 0, 0.05);" if self.is_locked else ""
            )
