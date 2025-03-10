"""
Tab for displaying and managing Q&A entries
"""

import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
)
from gui.widgets import SearchBar
from .table import QATable

logger = logging.getLogger(__name__)


class QATab(QWidget):
    """Tab for displaying and managing Q&A entries"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the Q&A tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        qa_top_bar = QHBoxLayout()
        qa_top_bar.setSpacing(8)

        self.search_bar = SearchBar(placeholder="Search questions and answers... (f)")
        self.search_bar.textChanged.connect(self.filter_qa)
        qa_top_bar.addWidget(self.search_bar, stretch=1)

        layout.addLayout(qa_top_bar)
        self.qa_table = QATable()
        layout.addWidget(self.qa_table)

    def filter_qa(self, search_text: str):
        """Filter the Q&A table based on search text"""
        search_text = search_text.lower()

        if not search_text:
            for row in range(self.qa_table.rowCount()):
                self.qa_table.setRowHidden(row, False)
            return

        for row in range(self.qa_table.rowCount()):
            row_matches = False
            for col in range(1, self.qa_table.columnCount()):
                widget = self.qa_table.cellWidget(row, col)
                if widget:
                    line_edit = widget.findChild(QLineEdit)
                    if line_edit and search_text in line_edit.text().lower():
                        row_matches = True
                        break
            self.qa_table.setRowHidden(row, not row_matches)

    def delete_qa(self, row: int):
        """Delete a Q&A entry"""
        parent = self
        while parent and not hasattr(parent, "delete_qa"):
            parent = parent.parent()

        if parent:
            parent.delete_qa(row)
        else:
            logger.error("Could not find parent with delete_qa method")

    def handle_field_update(self, app_id: int, field_name: str, new_value: object):
        """Handle field updates from other tabs"""
        if field_name not in ["company", "role"]:
            return

        for row in range(self.qa_table.rowCount()):
            if self.qa_table.qa_ids.get(row) == app_id:
                col = 1 if field_name == "company" else 2
                cell_widget = self.qa_table.cellWidget(row, col)
                if cell_widget:
                    line_edit = cell_widget.findChild(QLineEdit)
                    if line_edit and line_edit.text() != str(new_value):
                        line_edit.setText(str(new_value))

    def handle_qa_update(
        self, app_id: int, question_id: int, question: str, answer: str
    ):
        """Handle question update from workspace"""
        logger.info(
            "Handling QA update for app %d, question ID %d", app_id, question_id
        )

        row = -1
        for r, q_id in self.qa_table.question_id_map.items():
            if q_id == question_id:
                row = r
                break

        if row < 0:
            logger.warning(
                "Question ID %d not found in QA table, may need to add it", question_id
            )
            application = self.get_application(app_id)
            if application:
                company = application.metadata.company
                role = application.metadata.role
                self.qa_table.add_qa_row(
                    app_id, company, role, question, answer, question_id
                )
            return

        logger.debug("Updating row %d with question ID %d", row, question_id)

        self.qa_table.blockSignals(True)
        try:
            q_widget = self.qa_table.cellWidget(row, 3)
            if q_widget:
                q_edit = q_widget.findChild(QLineEdit)
                if q_edit and q_edit.text() != question:
                    q_edit.setText(question)

            a_widget = self.qa_table.cellWidget(row, 4)
            if a_widget:
                a_edit = a_widget.findChild(QLineEdit)
                if a_edit and a_edit.text() != answer:
                    a_edit.setText(answer)
        finally:
            self.qa_table.blockSignals(False)

    def handle_qa_add(self, app_id: int, question_id: int, question: str, answer: str):
        """Handle question addition from workspace"""
        logger.info("Handling QA add for app %d, question ID %d", app_id, question_id)

        for q_id in self.qa_table.question_id_map.values():
            if q_id == question_id:
                logger.warning(
                    "Question ID %d already exists, updating instead", question_id
                )
                self.handle_qa_update(app_id, question_id, question, answer)
                return

        application = self.get_application(app_id)
        if application:
            company = application.metadata.company
            role = application.metadata.role
            self.qa_table.add_qa_row(
                app_id, company, role, question, answer, question_id
            )
        else:
            logger.error("Could not find application %d to add question", app_id)

    def handle_qa_delete(self, app_id: int, question_id: int):
        """Handle question deletion from workspace"""
        logger.info(
            "Handling QA delete for app %d, question ID %d", app_id, question_id
        )

        row = -1
        for r, q_id in self.qa_table.question_id_map.items():
            if q_id == question_id:
                row = r
                break

        if row >= 0:
            logger.debug("Deleting row %d with question ID %d", row, question_id)
            self.qa_table.delete_row(row)
        else:
            logger.warning(
                "Question ID %d not found in QA table, nothing to delete", question_id
            )

    def handle_application_delete(self, app_id: int):
        """Handle application deletion"""
        rows_to_delete = []
        for row, aid in self.qa_table.qa_ids.items():
            if aid == app_id:
                rows_to_delete.append(row)

        for row in sorted(rows_to_delete, reverse=True):
            self.qa_table.delete_row(row)

    def get_application(self, app_id: int):
        """Get application from parent's database"""
        parent = self
        while parent:
            if type(parent).__name__ == "MainWindow":
                break
            parent = parent.parent()

        if parent and hasattr(parent, "db"):
            return parent.db.get_application(app_id)
        return None

    def save_cell_edit(self, row: int, col: int, text: str):
        """Save cell edits to the database"""
        if row not in self.qa_table.qa_ids:
            logger.error("No application ID found for row %d", row)
            return

        app_id = self.qa_table.qa_ids[row]
        question_id = self.qa_table.question_id_map.get(row, -1)

        if question_id < 0:
            logger.error("No question ID found for row %d", row)
            return

        q_widget = self.qa_table.cellWidget(row, 3)
        a_widget = self.qa_table.cellWidget(row, 4)
        if not q_widget or not a_widget:
            logger.error("Could not find Q&A widgets for row %d", row)
            return

        q_edit = q_widget.findChild(QLineEdit)
        a_edit = a_widget.findChild(QLineEdit)
        if not q_edit or not a_edit:
            logger.error("Could not find Q&A edit widgets for row %d", row)
            return

        current_q = q_edit.text()
        current_a = a_edit.text()

        if col == 3:  # the question column
            current_q = text
        elif col == 4:  # the answer column
            current_a = text
        else:
            return  # not a question or answer column

        parent = self
        while parent:
            if type(parent).__name__ == "MainWindow":
                break
            parent = parent.parent()

        if parent and hasattr(parent, "db"):
            if parent.db.update_question(question_id, current_q, current_a):
                logger.info(
                    "Updated question ID %d for application %d", question_id, app_id
                )
                parent.emit_qa_table_update(app_id, question_id, current_q, current_a)
            else:
                logger.error(
                    "Failed to update question ID %d for application %d",
                    question_id,
                    app_id,
                )
        else:
            logger.error("Could not find MainWindow parent with database connection")
