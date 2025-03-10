"""
Widget for displaying file differences
"""

from difflib import SequenceMatcher

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCharFormat, QSyntaxHighlighter, QColor
from diff_match_patch import diff_match_patch


# pylint: disable=invalid-name
class DiffHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for the diff viewer"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addition_format = QTextCharFormat()
        self.addition_format.setBackground(QColor("#2a4034"))
        self.deletion_format = QTextCharFormat()
        self.deletion_format.setBackground(QColor("#4b1818"))

    def highlightBlock(self, text: str):
        """Highlight diff blocks based on their prefix"""
        if text.startswith("+"):
            self.setFormat(0, len(text), self.addition_format)
        elif text.startswith("-"):
            self.setFormat(0, len(text), self.deletion_format)


class DiffViewer(QTextEdit):
    """Widget for displaying file differences"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.highlighter = DiffHighlighter(self.document())
        self.differ = diff_match_patch()

    def setup_ui(self):
        """Setup the diff viewer UI"""
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-family: 'Consolas', 'Monaco', 'Menlo', monospace;
                font-size: 13px;
                padding: 8px;
                selection-background-color: #264f78;
                selection-color: #ffffff;
                line-height: 1.2;
            }
            QScrollBar:horizontal {
                border: none;
                background: #2c2c2c;
                height: 14px;
            }
            QScrollBar::handle:horizontal {
                background: #4a4a4a;
                min-width: 20px;
                border-radius: 7px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar:vertical {
                border: none;
                background: #2c2c2c;
                width: 14px;
            }
            QScrollBar::handle:vertical {
                background: #4a4a4a;
                min-height: 20px;
                border-radius: 7px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
        )

        font = self.font()
        font.setFamily("Consolas")
        font.setStyleHint(font.StyleHint.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)

        metrics = self.fontMetrics()
        self.setTabStopDistance(4 * metrics.horizontalAdvance(" "))

    def show_diff(self, text1: str, text2: str):
        """Show the difference between two texts"""
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()

        result = []

        matcher = SequenceMatcher(None, lines1, lines2)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for line in lines1[i1:i2]:
                    result.append(f" {line}")
            elif tag == "delete":
                for line in lines1[i1:i2]:
                    result.append(f"-{line}")
            elif tag == "insert":
                for line in lines2[j1:j2]:
                    result.append(f"+{line}")
            elif tag == "replace":
                for line in lines1[i1:i2]:
                    result.append(f"-{line}")
                for line in lines2[j1:j2]:
                    result.append(f"+{line}")

        self.setPlainText("\n".join(result))
