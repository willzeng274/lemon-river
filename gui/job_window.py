"""
Qt window for displaying job applications
"""

import logging
import multiprocessing
from datetime import datetime
from typing import Dict

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QTextEdit,
    QListWidget,
    QLineEdit,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer

from gui.dataclasses import Application, ApplicationMetadata
from gui.widgets import PlainPasteLineEdit, PlainPasteTextEdit, JobQAListWidget, LockableField, SectionLabel, DraggableWindow

logger = logging.getLogger(__name__)


# pylint: disable=line-too-long
# pylint: disable=invalid-name
class ApplicationCard(QFrame):
    """Widget displaying a single job application"""

    def __init__(self, application):
        super().__init__()
        self.current_application = application
        self.locked_fields: Dict[str, LockableField] = {}
        self.setup_ui()

    def create_field_with_lock(self, field_name: str, widget, layout) -> None:
        """Create a field with a lock button"""
        field_layout = QHBoxLayout()
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(4)

        lockable = LockableField(widget, field_name)
        self.locked_fields[field_name] = lockable

        if field_name == "qa":
            def on_lock_toggle():
                widget.setEnabled(not self.locked_fields[field_name].is_locked)
            
            lockable.lock_button.clicked.connect(on_lock_toggle)
            widget.setEnabled(not lockable.is_locked)
        elif isinstance(widget, (QLineEdit, PlainPasteLineEdit)):
            widget.textChanged.connect(
                lambda text: self.handle_text_change(field_name, text)
            )
        elif isinstance(widget, (QTextEdit, PlainPasteTextEdit)):
            widget.textChanged.connect(
                lambda: self.handle_text_change(field_name, widget.toPlainText())
            )
        elif isinstance(widget, QListWidget):
            widget.model().rowsInserted.connect(
                lambda: self.handle_list_change(field_name, widget)
            )
            widget.model().rowsRemoved.connect(
                lambda: self.handle_list_change(field_name, widget)
            )

        field_layout.addWidget(widget)
        field_layout.addWidget(lockable.lock_button)
        layout.addLayout(field_layout)

    def handle_text_change(self, field_name: str, new_text: str) -> None:
        """Handle text changes in fields"""
        if self.locked_fields[field_name].is_locked:
            return

        if field_name == "url":
            self.current_application.metadata.url = new_text
        elif field_name == "role":
            self.current_application.metadata.role = new_text
        elif field_name == "company":
            self.current_application.metadata.company = new_text
        elif field_name == "location":
            self.current_application.metadata.location = new_text
        elif field_name == "duration":
            self.current_application.metadata.duration = new_text
        elif field_name == "description":
            self.current_application.metadata.description = new_text
        elif field_name == "notes":
            self.current_application.metadata.notes = new_text
        elif field_name == "check_url":
            self.current_application.metadata.check_url = new_text
        elif field_name == "created_at":
            self.current_application.metadata.created_at = new_text

    def handle_list_change(self, field_name: str, widget: QListWidget) -> None:
        """Handle changes to list widgets"""
        data = []
        for i in range(widget.count()):
            data.append(widget.item(i).text())

        if field_name == "qa":
            questions = []
            for item in data:
                if ":" in item:
                    q, a = item.split(":", 1)
                    questions.append((q.strip(), a.strip()))
                else:
                    questions.append((item.strip(), ""))
            self.current_application.metadata.questions = questions

    def setup_ui(self):
        """Sets up the UI for the application card"""
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet(
            """
            ApplicationCard {
                background-color: transparent;
            }
            QLabel {
                color: #24292e;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            }
            QLineEdit, QTextEdit {
                border: none;
                border-radius: 3px;
                padding: 4px;
                background-color: rgba(255, 255, 255, 0.5);
                font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
            }
            QLineEdit:focus, QTextEdit:focus {
                background-color: white;
                border: 1px solid #0366d6;
            }
            QListWidget {
                border: none;
                background-color: rgba(255, 255, 255, 0.5);
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 4px;
            }
            QScrollArea {
                border: none;
                background-color: rgba(255, 255, 255, 0.5);
                border-radius: 3px;
            }
            QPushButton {
                background-color: #fafbfc;
                border: 1px solid rgba(27, 31, 35, 0.15);
                border-radius: 3px;
                color: #24292e;
                padding: 3px 10px;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
            QPushButton:pressed {
                background-color: #e7e9eb;
            }
            QPushButton[lockButton=true] {
                background-color: transparent;
                border: none;
                padding: 2px;
                font-size: 14px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
            QPushButton[lockButton=true]:hover {
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 3px;
            }
        """
        )

        # URL Section
        layout.addWidget(SectionLabel("Posting URL"))
        url_edit = PlainPasteLineEdit(self.current_application.metadata.url or "")
        url_edit.setPlaceholderText("Enter job posting URL")
        self.create_field_with_lock("url", url_edit, layout)

        # Company Section
        layout.addWidget(SectionLabel("Company"))
        company_edit = PlainPasteLineEdit(self.current_application.metadata.company or "")
        company_edit.setPlaceholderText("Enter company name")
        self.create_field_with_lock("company", company_edit, layout)

        # Role Section
        layout.addWidget(SectionLabel("Title"))
        role_edit = PlainPasteLineEdit(self.current_application.metadata.role or "")
        role_edit.setPlaceholderText("Enter job title")
        self.create_field_with_lock("role", role_edit, layout)

        layout.addWidget(SectionLabel("Created at"))
        created_at = PlainPasteLineEdit(self.current_application.metadata.created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.create_field_with_lock("created_at", created_at, layout)

        # Job Description Section
        layout.addWidget(SectionLabel("Job Description"))
        description = PlainPasteTextEdit(self.current_application.metadata.description or "")
        description.setPlaceholderText("Enter job description")
        description.setMaximumHeight(100)
        self.create_field_with_lock("description", description, layout)

        # Duration Section
        layout.addWidget(SectionLabel("Duration"))
        duration_edit = PlainPasteLineEdit(self.current_application.metadata.duration or "")
        duration_edit.setPlaceholderText("4 months, Summer 2025")
        self.create_field_with_lock("duration", duration_edit, layout)

        # Location Section
        layout.addWidget(SectionLabel("Location"))
        location = PlainPasteLineEdit(self.current_application.metadata.location or "")
        location.setPlaceholderText("Enter location")
        self.create_field_with_lock("location", location, layout)

        # Notes Section
        layout.addWidget(SectionLabel("Notes"))
        notes = PlainPasteTextEdit(self.current_application.metadata.notes or "")
        notes.setPlaceholderText("Enter notes")
        notes.setMaximumHeight(80)
        self.create_field_with_lock("notes", notes, layout)

        # Q&A Section
        layout.addWidget(SectionLabel("Questions & Answers"))
        qa_container = QWidget()
        qa_container_layout = QVBoxLayout(qa_container)
        qa_widget = JobQAListWidget(questions=self.current_application.metadata.questions, parent=qa_container)
        qa_widget.qa_updated.connect(self.handle_qa_update)
        qa_container_layout.addWidget(qa_widget)
        
        editor_layout = QHBoxLayout()
        editor_layout.addWidget(qa_container)
        layout.addLayout(editor_layout)

        # Status Section
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addWidget(SectionLabel("Status"))
        status_label = QLabel(self.current_application.status.value)
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Check URL field
        layout.addWidget(SectionLabel("Check URL"))
        check_url = PlainPasteLineEdit(self.current_application.metadata.check_url or "")
        check_url.setPlaceholderText("Enter URL to check")
        self.create_field_with_lock("check_url", check_url, layout)

    def is_field_locked(self, field_name: str) -> bool:
        """Check if a field is locked"""
        if field_name in self.locked_fields:
            return self.locked_fields[field_name].is_locked
        return False

    def handle_qa_update(self, questions):
        """Handle updates to the QA list"""
        self.current_application.metadata.questions = questions


class JobApplicationWindow(DraggableWindow):
    """Main window for displaying all job applications"""

    def __init__(self, command_queue: multiprocessing.Queue):
        super().__init__()
        self.command_queue = command_queue
        self.current_application = Application(
            metadata=ApplicationMetadata(
                url="",
                role="",
                company="",
                location="",
                duration="",
                description="",
                questions=[],
                notes="",
                check_url="",
            )
        )

        self.focused_opacity = 0.9
        self.unfocused_opacity = 0.7

        self.setup_ui()
        self.hide()
        logger.info("Window initialized and hidden")

        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.check_queue)
        self.queue_timer.start(100)
        logger.info("Queue timer started")

    def setup_ui(self):
        """Sets up the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background-color: #a0a0a0;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #808080;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                border: none;
                background: none;
            }
        """
        )

        self.application_card = ApplicationCard(self.current_application)
        scroll.setWidget(self.application_card)
        layout.addWidget(scroll)

        central_widget.setStyleSheet(
            """
            QWidget {
                background-color: rgba(246, 248, 250, 0.95);
                border: none;
            }
        """
        )

        self.resize(300, 500)
        self.setMinimumSize(250, 400)
        self.position_window()

    def position_window(self):
        """Position window on the right side of the screen"""
        screen = self.screen().geometry()
        self.move(screen.width() - self.width() - 20, 20)

    def update_application(
        self,
        url=None,
        title=None,
        status=None,
        company=None,
        role=None,
        location=None,
        notes=None,
        description=None,
        question=None,
        answer=None,
        check_url=None,
        created_at=None,
        duration=None,
    ):
        """Update the current application"""

        if question is not None:
            question = ' '.join(question.splitlines())
        if answer is not None:
            answer = ' '.join(answer.splitlines())
        if description is not None:
            description = ' '.join(description.splitlines())
        if notes is not None:
            notes = ' '.join(notes.splitlines())

        current_card = self.findChild(ApplicationCard)
        updated_fields = set()

        if answer is not None and (
            not current_card or not current_card.is_field_locked("qa")
        ):
            logger.info("Updating answer")
            if self.current_application.metadata.questions:
                logger.info("Updating answer for existing question")
                last_q = self.current_application.metadata.questions[-1][0]
                self.current_application.metadata.questions[-1] = (last_q, answer)
                updated_fields.add("qa")

        if question is not None and (
            not current_card or not current_card.is_field_locked("qa")
        ):
            self.current_application.metadata.questions.append((question, ""))
            updated_fields.add("qa")

        if url is not None and (
            not current_card or not current_card.is_field_locked("url")
        ):
            self.current_application.metadata.url = url
            updated_fields.add("url")

        if title is not None and (
            not current_card or not current_card.is_field_locked("role")
        ):
            self.current_application.metadata.role = title
            updated_fields.add("role")

        if status is not None:  # Status can always be updated
            self.current_application.status = status
            updated_fields.add("status")

        if company is not None and (
            not current_card or not current_card.is_field_locked("company")
        ):
            self.current_application.metadata.company = company
            updated_fields.add("company")

        if role is not None and (
            not current_card or not current_card.is_field_locked("role")
        ):
            self.current_application.metadata.role = role
            updated_fields.add("role")

        if location is not None and (
            not current_card or not current_card.is_field_locked("location")
        ):
            self.current_application.metadata.location = location
            updated_fields.add("location")

        if notes is not None and (
            not current_card or not current_card.is_field_locked("notes")
        ):
            self.current_application.metadata.notes = notes
            updated_fields.add("notes")

        if description is not None and (
            not current_card or not current_card.is_field_locked("description")
        ):
            self.current_application.metadata.description = description
            updated_fields.add("description")

        if check_url is not None and (
            not current_card or not current_card.is_field_locked("check_url")
        ):
            self.current_application.metadata.check_url = check_url
            updated_fields.add("check_url")

        if created_at is not None and (
            not current_card or not current_card.is_field_locked("created_at")
        ):
            self.current_application.metadata.created_at = created_at
            updated_fields.add("created_at")

        if duration is not None and (
            not current_card or not current_card.is_field_locked("duration")
        ):
            self.current_application.metadata.duration = duration
            updated_fields.add("duration")

        old_card = self.findChild(ApplicationCard)
        if old_card:
            old_card.setParent(None)

        scroll = self.findChild(QScrollArea)
        if scroll:
            new_card = ApplicationCard(self.current_application)
            scroll.setWidget(new_card)

            if current_card:
                for field_name, lockable in current_card.locked_fields.items():
                    if lockable.is_locked and field_name in new_card.locked_fields:
                        new_card.locked_fields[field_name].toggle_lock()

            for field_name in updated_fields:
                if (
                    field_name in new_card.locked_fields
                    and not new_card.locked_fields[field_name].is_locked
                ):
                    new_card.locked_fields[field_name].toggle_lock()

        for field in updated_fields:
            if field == "status":
                self.status_combo.setCurrentText(self.current_application.status.value)
            elif field in ["url", "role", "company", "location", "notes", "check_url", "title", "duration"]:
                if hasattr(self, f"{field}_edit"):
                    getattr(self, f"{field}_edit").setText(
                        getattr(self.current_application.metadata, field) or ""
                    )
            elif field == "description":
                if hasattr(self, "description_edit"):
                    self.description_edit.setPlainText(
                        self.current_application.metadata.description or ""
                    )
            elif field == "qa":
                for child in self.findChildren(JobQAListWidget):
                    child.update_questions(self.current_application.metadata.questions)
                    break

    def check_queue(self):
        """Process commands from the queue"""
        try:
            while not self.command_queue.empty():
                command = self.command_queue.get_nowait()
                logger.info("Received window command: %s", command)

                if command["type"] == "session_start":
                    logger.info("Showing window")
                    self.show()
                elif command["type"] == "session_end":
                    logger.info("Hiding window")
                    self.hide()
                elif command["type"] == "save":
                    logger.info("Saving application")
                    self.save_application()
                    self.hide()
                elif command["type"] == "update_title":
                    logger.info("Updating application title: %s", command["title"])
                    self.update_application(title=command["title"])
                elif command["type"] == "update_status":
                    logger.info("Updating application status: %s", command["status"])
                    self.update_application(status=command["status"])
                elif command["type"] == "update_url":
                    logger.info("Updating application URL: %s", command["url"])
                    self.update_application(url=command["url"])
                elif command["type"] == "update_company":
                    logger.info("Updating application company: %s", command["company"])
                    self.update_application(company=command["company"])
                elif command["type"] == "update_role":
                    logger.info("Updating application role: %s", command["role"])
                    self.update_application(role=command["role"])
                elif command["type"] == "update_location":
                    logger.info(
                        "Updating application location: %s", command["location"]
                    )
                    self.update_application(location=command["location"])
                elif command["type"] == "update_notes":
                    logger.info("Updating application notes: %s", command["notes"])
                    self.update_application(notes=command["notes"])
                elif command["type"] == "update_description":
                    logger.info(
                        "Updating application description: %s", command["description"]
                    )
                    self.update_application(description=command["description"])
                elif command["type"] == "update_question":
                    logger.info(
                        "Updating application question: %s", command["question"]
                    )
                    self.update_application(question=command["question"])
                elif command["type"] == "update_answer":
                    logger.info("Updating application answer: %s", command["answer"])
                    self.update_application(answer=command["answer"])
                elif command["type"] == "update_note":
                    logger.info("Updating application note: %s", command["note"])
                    self.update_application(notes=command["note"])
                elif command["type"] == "update_check_url":
                    logger.info(
                        "Updating application check URL: %s", command["check_url"]
                    )
                    self.update_application(check_url=command["check_url"])
                elif command["type"] == "update_duration":
                    logger.info("Updating application duration: %s", command["duration"])
                    self.update_application(duration=command["duration"])
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Error processing window command: %s", e)

    def save_application(self):
        """Save the current application to the database"""
        from db.adapter import DatabaseAdapter

        if not self.current_application.metadata.url and not self.current_application.metadata.role:
            logger.info("Skipping save: application is empty")
            return

        if not self.current_application.metadata.created_at:
            self.current_application.metadata.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db = DatabaseAdapter("db/applications.db")

        try:
            logger.info("Adding new application")
            logger.info("Application: company=%s, role=%s", 
                       getattr(self.current_application.metadata, 'company', 'N/A'),
                       getattr(self.current_application.metadata, 'role', 'N/A'))
            app_id = db.add_application(self.current_application)
            if app_id:
                logger.info("Successfully added new application with ID: %s", app_id)
            else:
                logger.error("Failed to add new application")
        finally:
            db.close()

        self.current_application = Application(
            metadata=ApplicationMetadata(
                url="",
                role="",
                company="",
                location="",
                duration="",
                description="",
                questions=[],
                notes="",
                check_url="",
            )
        )

        old_card = self.findChild(ApplicationCard)
        if old_card:
            old_card.setParent(None)

        scroll = self.findChild(QScrollArea)
        if scroll:
            new_card = ApplicationCard(self.current_application)
            scroll.setWidget(new_card)


if __name__ == "__main__":
    app = QApplication([])
    window = JobApplicationWindow(multiprocessing.Queue(), None)
    window.show()
    app.exec()
