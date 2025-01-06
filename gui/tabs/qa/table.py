"""
Table widget for displaying Q&A entries
"""

import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (
    QTableWidget,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QHeaderView,
)
from PyQt6.QtCore import Qt
from gui.widgets import TabNavigationLineEdit

logger = logging.getLogger(__name__)


class QATable(QTableWidget):
    """Table widget for displaying questions and answers"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.qa_ids = {}  # Map of row -> application ID
        self.question_id_map = {}  # Map of row -> question ID

    def setup_ui(self):
        """Setup the table UI"""
        headers = ["", "Company", "Role", "Question", "Answer"]
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
            1: 120,  # Company
            2: 120,  # Role
            3: 400,  # Question
            4: 400,  # Answer
        }

        for col, width in column_widths.items():
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.setColumnWidth(col, width)

        self.verticalHeader().setDefaultSectionSize(40)

        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)

    def cell_edited(self, row: int, col: int, text: str):
        """Handle cell edits"""
        logger.info("Cell edited at row %d, col %d: %s", row, col, text)
        self.save_cell_edit(row, col, text)

    def save_cell_edit(self, row: int, col: int, text: str):
        """Save cell edits to the database"""
        if row not in self.qa_ids or row not in self.question_id_map:
            logger.error("No application ID or question ID found for row %d", row)
            return

        # app_id = self.qa_ids[row]
        # question_id = self.question_id_map[row]

        parent = self
        while parent:
            if type(parent).__name__ == 'QATab':
                break
            parent = parent.parent()

        if not parent:
            logger.error("Could not find QATab parent")
            return

        parent.save_cell_edit(row, col, text)

    def add_qa_row(self, app_id: int, company: str, role: str, question: str, answer: str, question_id: int = -1):
        """Add a new Q&A row to the table"""
        logger.info("Adding QA row for app %d, question ID %d: %s", app_id, question_id, question[:50])

        row = self.rowCount()
        self.insertRow(row)

        self.qa_ids[row] = app_id
        self.question_id_map[row] = question_id

        delete_btn = QPushButton("×")
        delete_btn.setObjectName("deleteButton")
        delete_btn.setFixedWidth(24)
        delete_btn.clicked.connect(lambda: self.delete_row(row))

        delete_widget = QWidget()
        delete_layout = QHBoxLayout(delete_widget)
        delete_layout.addWidget(delete_btn)
        delete_layout.setContentsMargins(0, 0, 0, 0)
        delete_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setCellWidget(row, 0, delete_widget)

        company_widget = QWidget()
        company_layout = QHBoxLayout(company_widget)
        company_layout.setContentsMargins(0, 0, 0, 0)
        company_layout.setSpacing(0)
        company_edit = TabNavigationLineEdit(row, 1, self, company)
        company_edit.setReadOnly(True)
        company_edit.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                color: #8e8e8e;
                border: none;
                padding: 8px;
                margin: 0;
                font-size: 13px;
            }
        """)
        company_layout.addWidget(company_edit)
        self.setCellWidget(row, 1, company_widget)

        role_widget = QWidget()
        role_layout = QHBoxLayout(role_widget)
        role_layout.setContentsMargins(0, 0, 0, 0)
        role_layout.setSpacing(0)
        role_edit = TabNavigationLineEdit(row, 2, self, role)
        role_edit.setReadOnly(True)
        role_edit.setStyleSheet(company_edit.styleSheet())
        role_layout.addWidget(role_edit)
        self.setCellWidget(row, 2, role_widget)

        question_widget = QWidget()
        question_layout = QHBoxLayout(question_widget)
        question_layout.setContentsMargins(0, 0, 0, 0)
        question_layout.setSpacing(0)
        question_edit = TabNavigationLineEdit(row, 3, self, question)
        question_edit.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                color: #ffffff;
                border: none;
                padding: 8px;
                margin: 0;
                font-size: 13px;
            }
        """)
        question_edit.textChanged.connect(lambda text: self.cell_edited(row, 3, text))
        question_layout.addWidget(question_edit)
        self.setCellWidget(row, 3, question_widget)

        answer_widget = QWidget()
        answer_layout = QHBoxLayout(answer_widget)
        answer_layout.setContentsMargins(0, 0, 0, 0)
        answer_layout.setSpacing(0)
        answer_edit = TabNavigationLineEdit(row, 4, self, answer)
        answer_edit.setStyleSheet(question_edit.styleSheet())
        answer_edit.textChanged.connect(lambda text: self.cell_edited(row, 4, text))
        answer_layout.addWidget(answer_edit)
        self.setCellWidget(row, 4, answer_widget)

        return row

    def update_qa_data(self, applications):
        """Update the table with Q&A data from applications"""
        logger.info("Updating QA table with %d applications", len(applications))

        self.setRowCount(0)
        self.qa_ids.clear()
        self.question_id_map.clear()

        all_questions = []
        for app in applications:
            if not hasattr(app.metadata, 'questions') or not app.metadata.questions:
                continue

            question_ids = getattr(app.metadata, 'question_ids', {})

            for i, (question, answer) in enumerate(app.metadata.questions):
                question_id = question_ids.get(i, -1)
                all_questions.append((
                    question_id,
                    app.id,
                    app.metadata.company,
                    app.metadata.role,
                    question,
                    answer
                ))

        all_questions.sort(key=lambda x: x[0], reverse=True)

        for question_id, app_id, company, role, question, answer in all_questions:
            self.add_qa_row(
                app_id,
                company,
                role,
                question,
                answer,
                question_id
            )

        logger.info("QA table updated with %d rows", self.rowCount())

    def delete_row(self, row):
        """Delete a row from the table and the database"""
        if row < 0 or row >= self.rowCount():
            logger.error("Invalid row index: %d", row)
            return

        if row not in self.qa_ids or row not in self.question_id_map:
            logger.error("No application ID or question ID found for row %d", row)
            return

        app_id = self.qa_ids[row]
        question_id = self.question_id_map[row]

        parent = self
        while parent:
            if type(parent).__name__ == 'MainWindow':
                break
            parent = parent.parent()

        if parent and hasattr(parent, 'db'):
            if parent.db.delete_question(question_id):
                logger.info("Deleted question ID %d for application %d", question_id, app_id)
                parent.emit_qa_table_delete(app_id, question_id)
            else:
                logger.error("Failed to delete question ID %d for application %d", question_id, app_id)

        self.removeRow(row)

        new_qa_ids = {}
        new_question_id_map = {}

        for old_row, app_id in self.qa_ids.items():
            if old_row < row:
                new_qa_ids[old_row] = app_id
            elif old_row > row:
                new_qa_ids[old_row - 1] = app_id

        for old_row, q_id in self.question_id_map.items():
            if old_row < row:
                new_question_id_map[old_row] = q_id
            elif old_row > row:
                new_question_id_map[old_row - 1] = q_id

        self.qa_ids = new_qa_ids
        self.question_id_map = new_question_id_map
