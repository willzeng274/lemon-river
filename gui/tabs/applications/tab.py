"""
Tab for displaying and managing job applications
"""

import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit
from gui.widgets.inputs import SearchBar
from .table import ApplicationTable

logger = logging.getLogger(__name__)

class ApplicationsTab(QWidget):
    """Tab for displaying and managing job applications"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the applications tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        self.search_bar = SearchBar()
        self.search_bar.textChanged.connect(self.filter_applications)
        top_bar.addWidget(self.search_bar, stretch=1)

        add_button = QPushButton("+ Add Application (a)")
        add_button.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
        """)
        add_button.clicked.connect(self.add_application)
        top_bar.addWidget(add_button)

        layout.addLayout(top_bar)
        self.table = ApplicationTable()
        layout.addWidget(self.table)

    def filter_applications(self, search_text: str):
        """Filter the applications table based on search text"""
        search_text = search_text.lower()

        if not search_text:
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
            return

        for row in range(self.table.rowCount()):
            row_matches = False
            for col in range(1, self.table.columnCount()):
                widget = self.table.cellWidget(row, col)
                if widget:
                    line_edit = widget.findChild(QLineEdit)
                    if line_edit and search_text in line_edit.text().lower():
                        row_matches = True
                        break
            self.table.setRowHidden(row, not row_matches)

    def add_application(self):
        """Add a new application"""
        parent = self
        while parent and type(parent).__name__ != 'MainWindow':
            parent = parent.parent()

        if parent and hasattr(parent, 'add_application'):
            parent.add_application()
        else:
            logger.error("Could not find MainWindow parent with add_application method")

    def handle_field_update(self, app_id: int, field_name: str, new_value: object):
        """Handle field updates from other tabs"""
        row = None
        for r, aid in self.table.application_ids.items():
            if aid == app_id:
                row = r
                break

        if row is None:
            return

        field_map = {
            'company': 1,
            'url': 2,
            'check_url': 3,
            'role': 4,
            'location': 5,
            'status': 6,
            'duration': 7,
            'description': 8,
            'notes': 9,
            'created_at': 10
        }

        if field_name in field_map:
            col = field_map[field_name]
            cell_widget = self.table.cellWidget(row, col)
            if cell_widget:
                line_edit = cell_widget.findChild(QLineEdit)
                if line_edit and line_edit.text() != str(new_value):
                    line_edit.setText(str(new_value))

    def handle_application_delete(self, app_id: int):
        """Handle application deletion"""
        row = None
        for r, aid in self.table.application_ids.items():
            if aid == app_id:
                row = r
                break

        if row is not None:
            self.table.delete_row(row)

    def handle_application_add(self, application):
        """Handle new application addition"""
        self.table.add_application(application)
