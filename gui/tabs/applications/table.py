"""
Table widget for displaying job applications
"""

import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (
    QTableWidget,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QHeaderView,
    QTextEdit,
)
from PyQt6.QtCore import Qt
from gui.widgets import TabNavigationLineEdit, StatusDropdown
from gui.dataclasses import ApplicationStatus

logger = logging.getLogger(__name__)


# pylint: disable=invalid-name
class ApplicationTable(QTableWidget):
    """Table widget for displaying job applications"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.application_ids = {}

    def setup_ui(self):
        """Setup the table UI"""
        headers = ["", "Company", "URL", "Check URL", "Role", "Location", "Status", "Duration", "Description", "Notes", "Created at", "Edit"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        self.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: #2c2c2c;
                gridline-color: #3c3c3c;
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 0;
                border-bottom: 1px solid #3c3c3c;
            }
            QTableWidget::item:selected {
                background-color: #4a4a4a;
            }
            QTableWidget QLineEdit {
                background-color: transparent;
                color: #ffffff;
                border: none;
                padding: 8px;
                margin: 0;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #2c2c2c;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #3c3c3c;
                color: #8e8e8e;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton#deleteButton {
                background-color: transparent;
                color: #8e8e8e;
                border: none;
                padding: 0;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton#deleteButton:hover {
                color: #ff4444;
            }
            QScrollBar:horizontal {
                border: none;
                background: #2c2c2c;
                height: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #4a4a4a;
                min-width: 20px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar:vertical {
                border: none;
                background: #2c2c2c;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #4a4a4a;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        header = self.horizontalHeader()
        column_widths = {
            0: 25,   # Delete button
            1: 100,  # Company
            2: 100,  # URLs
            3: 100,  # Check URL
            4: 200,  # Role
            5: 80,   # Location
            6: 80,   # Status
            7: 80,   # Duration
            8: 200,  # Description
            9: 200,  # Notes
            10: 160, # Created at
            11: 40,  # Edit button
        }

        for col, width in column_widths.items():
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.setColumnWidth(col, width)

        self.verticalHeader().setDefaultSectionSize(40)

        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)

    # don't change on cell_edited because it's too expensive

    # def cell_edited(self, row: int, col: int, text: str):
    #     """Handle cell edits before they are committed"""
    #     pass

    def save_cell_edit(self, row: int, col: int, text: str):
        """Save cell edits to the database"""
        if row not in self.application_ids:
            logger.error("No application ID found for row %d", row)
            return

        parent = self
        while parent and not hasattr(parent, 'db'):
            parent = parent.parent()

        if not parent:
            logger.error("Could not find parent with database connection")
            return

        app_id = self.application_ids[row]
        application = parent.db.get_application(app_id)
        if not application:
            logger.error("Application not found for ID %d", app_id)
            return

        field_map = {
            1: ("company", lambda x: setattr(application.metadata, "company", x)),
            2: ("url", lambda x: setattr(application.metadata, "url", x)),
            3: ("check_url", lambda x: setattr(application.metadata, "check_url", x)),
            4: ("role", lambda x: setattr(application.metadata, "role", x)),
            5: ("location", lambda x: setattr(application.metadata, "location", x)),
            6: ("status", lambda x: setattr(application, "status", ApplicationStatus(x.strip() or ApplicationStatus.APPLYING.value))),
            7: ("duration", lambda x: setattr(application.metadata, "duration", x)),
            8: ("description", lambda x: setattr(application.metadata, "description", x)),
            9: ("notes", lambda x: setattr(application.metadata, "notes", x)),
            10: ("created_at", lambda x: setattr(application.metadata, "created_at", x)),
        }

        if col in field_map:
            field_name, setter = field_map[col]
            try:
                setter(text)
                if parent.db.update_application(app_id, application):
                    logger.info("Updated %s for application %d", field_name, app_id)
                    main_window = parent
                    while main_window and type(main_window).__name__ != 'MainWindow':
                        main_window = main_window.parent()

                    if main_window:
                        if field_name == 'status':
                            main_window.emit_field_update(app_id, field_name, application.status.value)
                        else:
                            main_window.emit_field_update(app_id, field_name, text)
                    else:
                        logger.error("Could not find MainWindow to emit signals")
                else:
                    logger.error("Failed to update %s for application %d", field_name, app_id)
            except ValueError as e:
                logger.error("Invalid value for %s: %s", field_name, e)
                cell_widget = self.cellWidget(row, col)
                if cell_widget:
                    line_edit = cell_widget.findChild(QLineEdit)
                    if line_edit:
                        current_value = getattr(application.metadata, field_name) if hasattr(application.metadata, field_name) else getattr(application, field_name)
                        if field_name == 'status':
                            current_value = current_value.value
                        line_edit.setText(str(current_value))

    def add_application(self, application):
        """Add a new application to the table"""
        # insert a new row at the top of the table
        row = 0
        self.insertRow(row)

        app_id = getattr(application, 'id', None)
        if app_id is None:
            logger.error("Application has no ID when adding to table")
            return

        logger.info("Adding application %d to row %d", app_id, row)
        self.application_ids[row] = app_id

        delete_container = QWidget()
        delete_layout = QHBoxLayout(delete_container)
        delete_layout.setContentsMargins(0, 0, 0, 0)
        delete_layout.setSpacing(0)
        delete_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        delete_button = QPushButton("×")
        delete_button.setObjectName("deleteButton")
        delete_button.setFixedSize(24, 24)
        delete_button.clicked.connect(lambda checked, r=row: self.delete_application_row(r))
        delete_layout.addWidget(delete_button)
        self.setCellWidget(row, 0, delete_container)

        edit_container = QWidget()
        edit_layout = QHBoxLayout(edit_container)
        edit_layout.setContentsMargins(0, 0, 0, 0)
        edit_layout.setSpacing(0)
        edit_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        edit_button = QPushButton("✎")
        edit_button.setObjectName("editButton")
        edit_button.setFixedSize(24, 24)

        main_window = None
        parent = self
        while parent:
            if type(parent).__name__ == 'MainWindow':
                main_window = parent
                break
            parent = parent.parent()

        if main_window:
            edit_button.clicked.connect(lambda checked, r=row: main_window.open_workspace_tab(r))
        else:
            logger.error("Could not find MainWindow parent")

        edit_button.setStyleSheet("""
            QPushButton#editButton {
                background-color: transparent;
                color: #8e8e8e;
                border: none;
                padding: 0;
                font-size: 16px;
            }
            QPushButton#editButton:hover {
                color: #007acc;
            }
        """)

        edit_layout.addWidget(edit_button)
        self.setCellWidget(row, 11, edit_container)

        items = [
            (1, application.metadata.company),
            (2, application.metadata.url),
            (3, application.metadata.check_url),
            (4, application.metadata.role),
            (5, application.metadata.location),
            (6, application.status.value),
            (7, application.metadata.duration),
            (8, application.metadata.description[:100] + "..." if len(application.metadata.description) > 100 else application.metadata.description),
            (9, application.metadata.notes[:100] + "..." if len(application.metadata.notes) > 100 else application.metadata.notes),
            (10, application.metadata.created_at),
        ]

        for col, text in items:
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            text_edit = TabNavigationLineEdit(row, col, self, text or "")
            text_edit.setStyleSheet("""
                QLineEdit {
                    background-color: transparent;
                    color: #ffffff;
                    border: none;
                    padding: 8px;
                    margin: 0;
                    font-size: 13px;
                }
            """)
            layout.addWidget(text_edit)
            self.setCellWidget(row, col, container)

    def delete_application_row(self, row: int):
        """Handle deletion of an application row"""
        main_window = None
        parent = self
        while parent:
            if type(parent).__name__ == 'MainWindow':
                main_window = parent
                break
            parent = parent.parent()

        if main_window:
            main_window.delete_application(row)
        else:
            logger.error("Could not find MainWindow parent to delete application")

    def delete_row(self, row):
        """Delete a row from the table"""
        if row in self.application_ids:
            logger.info("Deleting row %d with application ID %d", row, self.application_ids[row])
            del self.application_ids[row]

        self.removeRow(row)

        new_ids = {}
        for old_row, app_id in self.application_ids.items():
            if old_row > row:
                new_ids[old_row - 1] = app_id
                logger.info("Moving application %d from row %d to %d", app_id, old_row, old_row - 1)
            else:
                new_ids[old_row] = app_id
        self.application_ids = new_ids 

    def handle_field_update(self, app_id: int, field_name: str, new_value: object):
        """Handle field updates from other tabs"""
        if not hasattr(self, 'current_application_id') or app_id != self.current_application_id:
            return

        field_map = {
            'company': self.company_edit,
            'role': self.role_edit,
            'location': self.location_edit,
            'url': self.url_edit,
            'check_url': self.check_url_edit,
            'duration': self.duration_edit,
            'status': self.status_edit,
            'description': self.description_edit,
            'notes': self.notes_edit,
        }

        if field_name in field_map:
            widget = field_map[field_name]
            if isinstance(widget, QTextEdit):
                if widget.toPlainText() != new_value:
                    widget.setText(str(new_value))
            elif isinstance(widget, StatusDropdown):
                if widget.currentText() != new_value:
                    widget.setCurrentText(str(new_value))
            else:
                if widget.text() != new_value:
                    widget.setText(str(new_value))
                    widget.setCursorPosition(0)

    def focusOutEvent(self, event):
        """Reset cursor position to start when losing focus for all line edits"""
        super().focusOutEvent(event)
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                cell_widget = self.cellWidget(row, col)
                if cell_widget:
                    line_edit = cell_widget.findChild(QLineEdit)
                    if line_edit:
                        line_edit.setCursorPosition(0)
                        line_edit.deselect()
