"""
Custom label widgets
"""

import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class SectionLabel(QLabel):
    """Section header label with consistent styling"""

    def __init__(self, text: str):
        super().__init__(text)
        self.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.setStyleSheet("color: #333; margin-top: 10px;")
