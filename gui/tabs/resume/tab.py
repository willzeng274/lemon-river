"""
Tab for viewing and comparing resumes
"""

import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
)
from gui.widgets import PDFViewer, DiffViewer

logger = logging.getLogger(__name__)


class ResumeTab(QWidget):
    """Tab for viewing and comparing resumes"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the resume tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        split_widget = QWidget()
        split_layout = QHBoxLayout(split_widget)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(12)

        pdf_widget = QWidget()
        pdf_layout = QVBoxLayout(pdf_widget)
        pdf_layout.setContentsMargins(0, 0, 0, 0)
        pdf_layout.setSpacing(8)

        pdf_header = QHBoxLayout()
        pdf_header.setSpacing(8)

        self.pdf_input = QLineEdit()
        self.pdf_input.setPlaceholderText("Enter PDF path... (P)")
        self.pdf_input.setStyleSheet(
            """
            QLineEdit {
                background-color: #2c2c2c;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                background-color: #3c3c3c;
            }
        """
        )
        pdf_header.addWidget(self.pdf_input)

        self.browse_pdf_btn = QPushButton("Browse (B)")
        self.browse_pdf_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2c2c2c;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
        """
        )
        pdf_header.addWidget(self.browse_pdf_btn)

        pdf_layout.addLayout(pdf_header)

        self.pdf_viewer = PDFViewer()
        pdf_layout.addWidget(self.pdf_viewer)

        diff_widget = QWidget()
        diff_layout = QVBoxLayout(diff_widget)
        diff_layout.setContentsMargins(0, 0, 0, 0)
        diff_layout.setSpacing(8)

        diff_header = QHBoxLayout()
        diff_header.setSpacing(8)

        self.file1_input = QLineEdit()
        self.file1_input.setPlaceholderText("First file path... (I)")
        self.file1_input.setStyleSheet(self.pdf_input.styleSheet())
        diff_header.addWidget(self.file1_input)

        self.browse1_btn = QPushButton("Browse (F)")
        self.browse1_btn.setStyleSheet(self.browse_pdf_btn.styleSheet())
        diff_header.addWidget(self.browse1_btn)

        self.file2_input = QLineEdit()
        self.file2_input.setPlaceholderText("Second file path... (O)")
        self.file2_input.setStyleSheet(self.pdf_input.styleSheet())
        diff_header.addWidget(self.file2_input)

        self.browse2_btn = QPushButton("Browse (G)")
        self.browse2_btn.setStyleSheet(self.browse_pdf_btn.styleSheet())
        diff_header.addWidget(self.browse2_btn)

        self.compare_btn = QPushButton("Compare (C)")
        self.compare_btn.setStyleSheet(self.browse_pdf_btn.styleSheet())
        diff_header.addWidget(self.compare_btn)

        diff_layout.addLayout(diff_header)

        self.diff_viewer = DiffViewer()
        diff_layout.addWidget(self.diff_viewer)

        split_layout.addWidget(pdf_widget)
        split_layout.addWidget(diff_widget)
        layout.addWidget(split_widget)

        self.browse_pdf_btn.clicked.connect(lambda: self.browse_file(self.pdf_input))
        self.browse1_btn.clicked.connect(lambda: self.browse_file(self.file1_input))
        self.browse2_btn.clicked.connect(lambda: self.browse_file(self.file2_input))
        self.compare_btn.clicked.connect(self.compare_files)
        self.pdf_input.textChanged.connect(self.on_pdf_path_changed)

    def browse_file(self, line_edit: QLineEdit):
        """Open file browser dialog and set the selected path"""
        parent = self
        while parent:
            if type(parent).__name__ == "MainWindow":
                break
            parent = parent.parent()

        if parent:
            parent.browse_file(line_edit)
        else:
            logger.error("Could not find MainWindow parent")

    def on_pdf_path_changed(self, path: str):
        """Handle PDF path changes and load the PDF"""
        if path and path.lower().endswith(".pdf"):
            self.pdf_viewer.load_pdf(path)

    def compare_files(self):
        """Compare two text files"""
        try:
            with open(self.file1_input.text(), "r", encoding="utf-8") as f1, open(
                self.file2_input.text(), "r", encoding="utf-8"
            ) as f2:
                content1 = f1.read()
                content2 = f2.read()
                self.diff_viewer.show_diff(content1, content2)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            self.diff_viewer.setPlainText(f"Error loading files: {str(e)}")
