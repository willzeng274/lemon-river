"""
Tab for editing application details and documents
"""

import os
import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QScrollArea,
)
from PyQt6.QtCore import Qt
from gui.widgets import PDFViewer, QAListWidget, ApplicationSelector
from gui.widgets.resume_creator import ResumeCreationDialog
from gui.widgets.qa_widget import QAItem
from gui.widgets.inputs import StatusDropdown
from gui.dataclasses import ApplicationStatus

logger = logging.getLogger(__name__)


# pylint: disable=invalid-name
class WorkspaceTab(QWidget):
    """Tab for editing application details and documents"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating_application_selector = False
        self.setup_ui()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def setup_ui(self):
        """Setup the workspace tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        selector_layout = QHBoxLayout()
        selector_layout.setContentsMargins(0, 0, 0, 16)
        selector_layout.setSpacing(12)

        self.application_selector = ApplicationSelector()
        self.application_selector.currentApplicationChanged.connect(
            self.load_selected_application
        )
        selector_layout.addWidget(self.application_selector)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        self.setStyleSheet(
            """
            QWidget {
                background: transparent;
            }
        """
        )

        split_widget = QWidget()
        split_layout = QHBoxLayout(split_widget)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(12)

        pdf_widget = QWidget()
        pdf_layout = QVBoxLayout(pdf_widget)
        pdf_layout.setContentsMargins(0, 0, 0, 0)
        pdf_layout.setSpacing(8)

        self.pdf_viewer = PDFViewer()
        pdf_layout.addWidget(self.pdf_viewer)

        editor_scroll = QScrollArea()
        editor_scroll.setWidgetResizable(True)
        editor_scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: transparent;
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
        """
        )

        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 16, 0)
        editor_layout.setSpacing(16)

        button_layout = QHBoxLayout()
        self.create_resume_btn = QPushButton("Create Resume (c)")
        self.create_resume_btn.clicked.connect(self.create_resume)
        self.create_resume_btn.setStyleSheet(
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
        # create_cover_btn = QPushButton("Create Cover Letter")
        # create_cover_btn.setStyleSheet(create_resume_btn.styleSheet())

        button_layout.addWidget(self.create_resume_btn)
        # button_layout.addWidget(create_cover_btn)
        button_layout.addStretch()

        editor_layout.addLayout(button_layout)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(16)

        fields = [
            ("Company", "company_edit", QLineEdit),
            ("Role", "role_edit", QLineEdit),
            ("Location", "location_edit", QLineEdit),
            ("URL", "url_edit", QLineEdit),
            ("Check URL", "check_url_edit", QLineEdit),
            ("Duration", "duration_edit", QLineEdit),
            ("Status", "status_edit", StatusDropdown),
            ("Description", "description_edit", QTextEdit),
            ("Notes", "notes_edit", QTextEdit),
        ]

        for label_text, obj_name, widget_class in fields:
            field_layout = QVBoxLayout()
            label = QLabel(label_text)
            label.setStyleSheet("color: #8e8e8e; font-size: 13px;")
            field_layout.addWidget(label)

            widget = widget_class()
            widget.setObjectName(obj_name)
            if isinstance(widget, QLineEdit):
                widget.setStyleSheet(
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
                widget.textChanged.connect(self.handle_field_change)
            elif isinstance(widget, StatusDropdown):
                widget.currentTextChanged.connect(self.handle_field_change)
            elif isinstance(widget, QTextEdit):
                widget.setStyleSheet(
                    """
                    QTextEdit {
                        background-color: #2c2c2c;
                        color: #ffffff;
                        border: none;
                        border-radius: 6px;
                        padding: 8px;
                        font-size: 13px;
                    }
                    QTextEdit:focus {
                        background-color: #3c3c3c;
                    }
                """
                )
                widget.textChanged.connect(self.handle_field_change)
                widget.setMinimumHeight(100)

            field_layout.addWidget(widget)
            form_layout.addLayout(field_layout)
            setattr(self, obj_name, widget)

        editor_layout.addLayout(form_layout)

        qa_label = QLabel("Questions & Answers")
        qa_label.setStyleSheet("color: #8e8e8e; font-size: 13px; margin-top: 16px;")
        editor_layout.addWidget(qa_label)

        add_qa_btn = QPushButton("+ Add Question")
        add_qa_btn.setObjectName("addQuestionButton")
        add_qa_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2c2c2c;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                min-width: 120px;
                margin-bottom: 8px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
        """
        )
        editor_layout.addWidget(add_qa_btn)

        qa_container = QWidget()
        qa_container.setObjectName("qaContainer")
        qa_container_layout = QVBoxLayout(qa_container)
        qa_container_layout.setContentsMargins(0, 0, 0, 0)
        qa_container_layout.setSpacing(8)

        self.qa_list = QAListWidget(parent=qa_container)
        self.qa_list.qa_updated.connect(self.handle_qa_update)
        qa_container_layout.addWidget(self.qa_list)

        editor_layout.addWidget(qa_container)

        add_qa_btn.clicked.connect(self.add_qa)

        editor_layout.addStretch()
        editor_scroll.setWidget(editor_widget)

        split_layout.addWidget(pdf_widget, 1)
        split_layout.addWidget(editor_scroll, 1)

        layout.addWidget(split_widget)

    def handle_field_change(self):
        """Handle changes in input fields"""
        sender = self.sender()
        if not sender:
            return

        parent = self
        while parent:
            if type(parent).__name__ == "MainWindow":
                break
            parent = parent.parent()

        if not parent or not hasattr(parent, "db"):
            logger.error("Could not find MainWindow parent with database connection")
            return

        application = parent.db.get_application(self.current_application_id)
        if not application:
            logger.error("Could not find application %d", self.current_application_id)
            return

        # old_company = application.metadata.company
        # old_role = application.metadata.role

        application.metadata.company = self.company_edit.text()
        application.metadata.role = self.role_edit.text()
        application.metadata.location = self.location_edit.text()
        application.metadata.url = self.url_edit.text()
        application.metadata.check_url = self.check_url_edit.text()
        application.metadata.duration = self.duration_edit.text()
        application.metadata.resume_path = getattr(
            application.metadata, "resume_path", None
        )

        status_text = self.status_edit.currentText()
        try:
            application.status = ApplicationStatus(status_text)
        except ValueError:
            logger.warning("Invalid status value: %s. Setting to APPLYING", status_text)
            application.status = ApplicationStatus.APPLYING
            self.status_edit.setCurrentText(ApplicationStatus.APPLYING.value)

        application.metadata.description = self.description_edit.toPlainText()
        application.metadata.notes = self.notes_edit.toPlainText()

        if parent.db.update_application(self.current_application_id, application):
            if sender in [self.company_edit, self.role_edit]:
                new_text = (
                    f"{application.metadata.company} - {application.metadata.role}"
                )
                self.application_selector.update_option(
                    self.current_application_id, new_text
                )

            parent.emit_field_update(
                self.current_application_id, "company", application.metadata.company
            )
            parent.emit_field_update(
                self.current_application_id, "role", application.metadata.role
            )
            parent.emit_field_update(
                self.current_application_id, "location", application.metadata.location
            )
            parent.emit_field_update(
                self.current_application_id, "url", application.metadata.url
            )
            parent.emit_field_update(
                self.current_application_id, "check_url", application.metadata.check_url
            )
            parent.emit_field_update(
                self.current_application_id, "duration", application.metadata.duration
            )
            parent.emit_field_update(
                self.current_application_id, "status", application.status.value
            )
            parent.emit_field_update(
                self.current_application_id,
                "description",
                application.metadata.description,
            )
            parent.emit_field_update(
                self.current_application_id, "notes", application.metadata.notes
            )

    def refresh_selector(self):
        """Refresh the application selector while maintaining current selection"""
        parent = self
        while parent:
            if type(parent).__name__ == "MainWindow":
                break
            parent = parent.parent()

        if not parent or not hasattr(parent, "db"):
            logger.error("Could not find MainWindow parent with database connection")
            return

        current_id = getattr(self, "current_application_id", None)

        self.application_selector.blockSignals(True)
        try:
            self.application_selector.clear()

            applications = sorted(
                parent.applications, key=lambda x: x.metadata.created_at, reverse=True
            )

            for app in applications:
                app_id = getattr(app, "id", None)
                if app_id is not None:
                    self.application_selector.add_option(
                        f"{app.metadata.company} - {app.metadata.role}", app_id
                    )

            if current_id is not None:
                app = parent.db.get_application(current_id)
                if app:
                    self.application_selector.select_option_no_signal(current_id)
        finally:
            self.application_selector.blockSignals(False)

    def handle_qa_update(self, questions_list):
        """Handle updates to the Q&A list from the QA widget"""
        logger.info(
            "Handling QA update from widget with %d questions", len(questions_list)
        )

        if (
            not hasattr(self, "current_application_id")
            or self.current_application_id < 0
        ):
            logger.warning("Cannot handle QA update: No application selected")
            return

        parent = self
        while parent:
            if type(parent).__name__ == "MainWindow":
                break
            parent = parent.parent()

        if not parent or not hasattr(parent, "db"):
            logger.error("Could not find MainWindow parent with database connection")
            return

        application = parent.db.get_application(self.current_application_id)
        if not application:
            logger.error("Application not found for ID %d", self.current_application_id)
            return

        for question_id, question, answer in questions_list:
            if not question.strip() and not answer.strip():
                logger.debug("Skipping empty question")
                continue

            if question_id < 0:
                logger.info("Adding new question: %s", question[:50])
                new_question_id = parent.db.add_question(
                    self.current_application_id, question, answer
                )
                if new_question_id > 0:
                    self._update_qa_item_id(question, answer, new_question_id)
                    parent.emit_qa_add(self.current_application_id, new_question_id)
            else:
                logger.info(
                    "Updating existing question ID %d: %s", question_id, question[:50]
                )
                if parent.db.update_question(question_id, question, answer):
                    parent.emit_qa_update(
                        self.current_application_id, question_id, question, answer
                    )

        all_questions = parent.db.get_questions_for_application(
            self.current_application_id
        )
        current_question_ids = {q[0] for q in questions_list}
        for q_id, _, _ in all_questions:
            if q_id not in current_question_ids:
                logger.info("Deleting question ID %d", q_id)
                if parent.db.delete_question(q_id):
                    parent.emit_qa_delete(self.current_application_id, q_id)

    def _update_qa_item_id(self, question, answer, new_id):
        """Update the question ID for a QA item after adding to database"""
        for i in range(self.qa_list.layout.count()):
            item = self.qa_list.layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QAItem):
                widget = item.widget()
                q, a = widget.question, widget.answer
                if q == question and a == answer and widget.question_id < 0:
                    widget.question_id = new_id
                    logger.debug(
                        "Updated question ID for '%s' to %d", question[:50], new_id
                    )
                    break

    def handle_qa_table_update(self, app_id, question_id):
        """Handle updates from the QA table"""
        logger.info(
            "Handling QA update from table for app %d, question ID %d",
            app_id,
            question_id,
        )

        if (
            not hasattr(self, "current_application_id")
            or self.current_application_id != app_id
        ):
            return

        parent = self
        while parent:
            if type(parent).__name__ == "MainWindow":
                break
            parent = parent.parent()

        if not parent or not hasattr(parent, "db"):
            logger.error("Could not find MainWindow parent with database connection")
            return

        questions = parent.db.get_questions_for_application(app_id)

        self.qa_list.blockSignals(True)
        try:
            self.qa_list.update_questions(questions)
        finally:
            self.qa_list.blockSignals(False)

    def handle_qa_table_delete(self, app_id, question_id):
        """Handle deletion from the QA table"""
        logger.info(
            "Handling QA deletion from table for app %d, question ID %d",
            app_id,
            question_id,
        )

        if (
            not hasattr(self, "current_application_id")
            or self.current_application_id != app_id
        ):
            return

        parent = self
        while parent:
            if type(parent).__name__ == "MainWindow":
                break
            parent = parent.parent()

        if not parent or not hasattr(parent, "db"):
            logger.error("Could not find MainWindow parent with database connection")
            return

        questions = parent.db.get_questions_for_application(app_id)

        self.qa_list.blockSignals(True)
        try:
            self.qa_list.update_questions(questions)
        finally:
            self.qa_list.blockSignals(False)

    def load_selected_application(self, app_id: int):
        """Load the selected application into the workspace"""
        if app_id < 0:
            self.pdf_viewer.show_message("No application selected")
            return

        parent = self
        while parent:
            if type(parent).__name__ == "MainWindow":
                break
            parent = parent.parent()

        if not parent or not hasattr(parent, "db"):
            logger.error("Could not find MainWindow parent with database connection")
            return

        application = parent.db.get_application(app_id)
        if not application:
            logger.error("Failed to load application with ID %d", app_id)
            return

        # since we are using getattr, we don't need to set this in the constructor
        # pylint: disable=attribute-defined-outside-init
        self.current_application_id = app_id

        self.application_selector.select_option_no_signal(app_id)

        questions = parent.db.get_questions_for_application(app_id)

        self.company_edit.setText(application.metadata.company or "")
        self.role_edit.setText(application.metadata.role or "")
        self.location_edit.setText(application.metadata.location or "")
        self.url_edit.setText(application.metadata.url or "")
        self.check_url_edit.setText(application.metadata.check_url or "")
        self.duration_edit.setText(application.metadata.duration or "")
        self.status_edit.setCurrentText(application.status.value)
        self.description_edit.setText(application.metadata.description or "")
        self.notes_edit.setText(application.metadata.notes or "")

        if application.metadata.resume_path and os.path.exists(
            application.metadata.resume_path
        ):
            self.pdf_viewer.load_pdf(application.metadata.resume_path)
            self.create_resume_btn.hide()
        else:
            self.pdf_viewer.show_message("No resume available")
            self.create_resume_btn.show()

        self.qa_list.blockSignals(True)
        try:
            self.qa_list.update_questions(questions)
        finally:
            self.qa_list.blockSignals(False)

        logger.info(
            "Application %d loaded successfully with %d questions",
            app_id,
            len(questions),
        )

    def add_qa(self):
        """Add a new Q&A item"""
        logger.info("Adding new Q&A item")

        if not hasattr(self, "current_application_id"):
            logger.warning("Cannot add Q&A: No application selected")
            return

        parent = self
        while parent:
            if type(parent).__name__ == "MainWindow":
                break
            parent = parent.parent()

        if not parent or not hasattr(parent, "db"):
            logger.error("Could not find MainWindow parent with database connection")
            return

        new_question_id = parent.db.add_question(self.current_application_id, "", "")
        if new_question_id > 0:
            logger.info("Created new question with ID %d", new_question_id)
            self.qa_list.add_qa_item(new_question_id, "", "")
            parent.emit_qa_add(self.current_application_id, new_question_id)
        else:
            logger.error("Failed to create new question in database")
            self.qa_list.add_qa_item(-1, "", "")

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_C:
            if self.create_resume_btn.isVisible():
                self.create_resume()
            return
        super().keyPressEvent(event)

    def create_resume(self):
        """Open resume creation dialog"""
        logger.info("Opening resume creation dialog")

        if not hasattr(self, "current_application_id"):
            logger.warning("Cannot create resume: No application selected")
            return

        company = self.company_edit.text()
        role = self.role_edit.text()

        dialog = ResumeCreationDialog(company=company, role=role, parent=self)
        logger.info("[Signal] Connecting resume_created signal to handler")
        dialog.resume_created.connect(self.handle_resume_created)
        dialog.exec()

    def handle_resume_created(self, pdf_path):
        """Handle when a resume is created"""
        logger.info("[Signal] Resume created signal received with path: %s", pdf_path)

        if (
            not hasattr(self, "current_application_id")
            or not pdf_path
            or not os.path.exists(pdf_path)
        ):
            logger.warning(
                "[Signal] Cannot handle resume_created: current_application_id=%s, pdf_path=%s, exists=%s",
                getattr(self, "current_application_id", None),
                pdf_path,
                os.path.exists(pdf_path) if pdf_path else False,
            )
            return

        parent = self
        while parent:
            if type(parent).__name__ == "MainWindow":
                break
            parent = parent.parent()

        if not parent or not hasattr(parent, "db"):
            logger.error(
                "[Signal] Could not find MainWindow parent with database connection"
            )
            return

        application = parent.db.get_application(self.current_application_id)
        if not application:
            logger.error(
                "[Signal] Application not found for ID %s", self.current_application_id
            )
            return

        application.metadata.resume_path = pdf_path
        if parent.db.update_application(self.current_application_id, application):
            logger.info(
                "[Signal] Successfully updated application %d with resume path: %s",
                self.current_application_id,
                pdf_path,
            )
            self.create_resume_btn.hide()
        else:
            logger.error(
                "[Signal] Failed to update application %d with resume path",
                self.current_application_id,
            )

        self.pdf_viewer.load_pdf(pdf_path)

    def handle_field_update(self, app_id: int, field_name: str, new_value: object):
        """Handle field updates from other tabs"""
        if (
            not hasattr(self, "current_application_id")
            or app_id != self.current_application_id
        ):
            return

        if field_name in ["company", "role"]:
            parent = self
            while parent:
                if type(parent).__name__ == "MainWindow":
                    break
                parent = parent.parent()

            if parent and hasattr(parent, "db"):
                application = parent.db.get_application(app_id)
                if application:
                    new_text = (
                        f"{application.metadata.company} - {application.metadata.role}"
                    )
                    self.application_selector.update_option(app_id, new_text)

        field_map = {
            "company": self.company_edit,
            "role": self.role_edit,
            "location": self.location_edit,
            "url": self.url_edit,
            "check_url": self.check_url_edit,
            "duration": self.duration_edit,
            "status": self.status_edit,
            "description": self.description_edit,
            "notes": self.notes_edit,
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

    def handle_qa_add(self, app_id: int, question_id: int):
        """Handle Q&A additions from other tabs"""
        logger.info("Handling QA add for app %d, question ID %d", app_id, question_id)

        if (
            not hasattr(self, "current_application_id")
            or self.current_application_id != app_id
        ):
            return

        self.qa_list.blockSignals(True)
        try:
            parent = self
            while parent:
                if type(parent).__name__ == "MainWindow":
                    break
                parent = parent.parent()

            if not parent or not hasattr(parent, "db"):
                logger.error(
                    "Could not find MainWindow parent with database connection"
                )
                return

            questions = parent.db.get_questions_for_application(app_id)
            self.qa_list.update_questions(questions)
        finally:
            self.qa_list.blockSignals(False)

    def handle_qa_delete(self, app_id: int, question_id: int):
        """Handle Q&A deletions from other tabs"""
        logger.info(
            "Handling QA delete for app %d, question ID %d", app_id, question_id
        )

        if (
            not hasattr(self, "current_application_id")
            or self.current_application_id != app_id
        ):
            return

        self.qa_list.blockSignals(True)
        try:
            parent = self
            while parent:
                if type(parent).__name__ == "MainWindow":
                    break
                parent = parent.parent()

            if not parent or not hasattr(parent, "db"):
                logger.error(
                    "Could not find MainWindow parent with database connection"
                )
                return

            questions = parent.db.get_questions_for_application(app_id)
            self.qa_list.update_questions(questions)
        finally:
            self.qa_list.blockSignals(False)

    def handle_application_delete(self, app_id: int):
        """Handle application deletion from other tabs"""
        if not hasattr(self, "current_application_id"):
            return

        if self.current_application_id == app_id:
            self.pdf_viewer.show_message("Application deleted")
            self.company_edit.clear()
            self.role_edit.clear()
            self.location_edit.clear()
            self.url_edit.clear()
            self.check_url_edit.clear()
            self.duration_edit.clear()
            self.status_edit.clear()
            self.description_edit.clear()
            self.notes_edit.clear()
            self.qa_list.update_questions([])
            self.create_resume_btn.show()

    def handle_application_add(self, application):
        """Handle new application addition"""
        app_id = getattr(application, "id", None)
        if app_id is None:
            return

        self.refresh_selector()

    def handle_resume_update(self, app_id: int, resume_path: str):
        """Handle resume updates"""
        if (
            not hasattr(self, "current_application_id")
            or self.current_application_id != app_id
        ):
            return

        if resume_path and os.path.exists(resume_path):
            self.pdf_viewer.load_pdf(resume_path)
            self.create_resume_btn.hide()
        else:
            self.pdf_viewer.show_message("No resume yet")
            self.create_resume_btn.show()

    def showEvent(self, event):
        """Handle when the tab becomes visible"""
        super().showEvent(event)

        if (
            hasattr(self, "_updating_application_selector")
            and self._updating_application_selector
        ):
            return

        # update the dropdown

        self._updating_application_selector = True
        try:
            parent = self
            while parent:
                if type(parent).__name__ == "MainWindow":
                    break
                parent = parent.parent()

            if parent:
                parent.update_application_selector()

            if (
                hasattr(self, "pdf_viewer")
                and self.pdf_viewer.pdf_document.pageCount() > 0
            ):
                logger.info("Tab shown, fitting PDF to height")
                self.pdf_viewer.fit_to_height()
        finally:
            self._updating_application_selector = False
