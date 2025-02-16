"""
Widgets for managing question-answer pairs
"""

from typing import List, Tuple
import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
)
from PyQt6.QtCore import pyqtSignal

logger = logging.getLogger(__name__)


class QAItem(QWidget):
    """Widget representing a question and answer pair"""
    
    deleted = pyqtSignal(QWidget)
    qa_changed = pyqtSignal(int, str, str)
    
    def __init__(self, question_id: int, question: str, answer: str, parent=None):
        super().__init__(parent)
        self.question_id = question_id
        self.question = question
        self.answer = answer
        logger.info("Creating new QA item - Question ID: %d, Question: %s, Answer: %s", 
                   question_id, 
                   question[:30] if question else "", 
                   answer[:30] if answer else "")
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI for the question-answer item"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        question_layout = QHBoxLayout()
        question_layout.setSpacing(8)
        
        question_label = QLabel("Q:")
        question_label.setStyleSheet("color: #0366d6; font-weight: bold; font-size: 13px;")
        question_layout.addWidget(question_label)
        
        self.question_edit = QTextEdit()
        self.question_edit.setPlaceholderText("Enter question...")
        self.question_edit.setMaximumHeight(60)
        self.question_edit.setStyleSheet("""
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
        """)
        self.question_edit.setPlainText(self.question)
        self.question_edit.textChanged.connect(self._handle_text_change)
        question_layout.addWidget(self.question_edit)
        
        delete_button = QPushButton("×")
        delete_button.setFixedSize(24, 24)
        delete_button.clicked.connect(self.delete_qa)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8e8e8e;
                border: none;
                font-size: 18px;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                color: #ff4444;
            }
        """)
        question_layout.addWidget(delete_button)
        
        layout.addLayout(question_layout)
        
        answer_layout = QHBoxLayout()
        answer_layout.setSpacing(8)
        
        answer_label = QLabel("A:")
        answer_label.setStyleSheet("color: #28a745; font-weight: bold; font-size: 13px;")
        answer_layout.addWidget(answer_label)
        
        self.answer_edit = QTextEdit()
        self.answer_edit.setPlaceholderText("Enter answer...")
        self.answer_edit.setMinimumHeight(80)
        self.answer_edit.setStyleSheet(self.question_edit.styleSheet())
        self.answer_edit.setPlainText(self.answer)
        self.answer_edit.textChanged.connect(self._handle_text_change)
        answer_layout.addWidget(self.answer_edit)
        
        spacer = QWidget()
        spacer.setFixedSize(24, 24)
        answer_layout.addWidget(spacer)
        
        layout.addLayout(answer_layout)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border-radius: 8px;
            }
        """)
        logger.debug("QA item UI setup complete")

    def _handle_text_change(self):
        """Handle text changes in either question or answer"""
        logger.debug("Text changed in QA item")
        question = self.question_edit.toPlainText()
        answer = self.answer_edit.toPlainText()
        self.question = question
        self.answer = answer
        self.qa_changed.emit(self.question_id, question, answer)

    def get_qa(self):
        """Get the question and answer"""
        try:
            q = self.question_edit.toPlainText().strip()
            a = self.answer_edit.toPlainText().strip()
            logger.debug("Getting Q&A - ID: %d, Q: %s, A: %s", 
                        self.question_id,
                        q[:50] if q else "", 
                        a[:50] if a else "")
            return (self.question_id, str(q), str(a))
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Error getting Q&A: %s", str(e), exc_info=True)
            return (-1, "", "")
        
    def delete_qa(self):
        """Delete this QA item"""
        logger.info("Deleting QA item - Q: %s", self.question_edit.toPlainText()[:50])
        self.deleted.emit(self)


class QAListWidget(QWidget):
    """Widget for managing a list of Q&A items"""
    qa_updated = pyqtSignal(list)

    def __init__(self, questions=None, parent=None):
        super().__init__(parent)
        self.questions = questions or []
        self.setup_ui()
        self.update_questions(self.questions)

    def setup_ui(self):
        """Setup the Q&A list UI"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(16)
        logger.debug("QAListWidget UI setup complete")

    def add_qa_item(self, question_id: int = -1, question: str = "", answer: str = ""):
        """Add a new Q&A item"""
        logger.info("Adding new QA item - ID: %d, Q: %s, A: %s", 
                   question_id, 
                   question[:50] if question else "empty", 
                   answer[:50] if answer else "empty")
        item = QAItem(question_id, str(question) if question else "", str(answer) if answer else "")
        item.qa_changed.connect(self.handle_qa_change)
        item.deleted.connect(self.handle_item_deleted)
        self.layout.addWidget(item)
        logger.debug("QA item added at position %d", self.layout.count() - 1)
        return item

    def handle_item_deleted(self, item):
        """Handle item deletion and adjust size"""
        logger.info("Handling item deletion")
        item.deleteLater()
        self.handle_qa_change()

    def get_all_questions(self) -> List[Tuple[int, str, str]]:
        """Get all questions and answers from the list"""
        try:
            questions = []
            count = self.layout.count()
            logger.debug("Getting questions from %d layout items", count)
            
            for i in range(count):
                item = self.layout.itemAt(i)
                if not item:
                    continue
                    
                widget = item.widget()
                logger.debug("Checking widget at index %d: %s", i, type(widget).__name__ if widget else None)
                
                if widget and isinstance(widget, QAItem):
                    qa_tuple = widget.get_qa()
                    if qa_tuple[1].strip() or qa_tuple[2].strip():
                        questions.append(qa_tuple)
            
            logger.info("Got %d questions from QA list", len(questions))
            return questions
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Error getting questions: %s", str(e))
            return []

    def handle_qa_change(self):
        """Handle any change in the Q&A list"""
        try:
            logger.debug("Handling QA change")
            questions = self.get_all_questions()
            logger.info("Emitting update with %d questions", len(questions))
            self.qa_updated.emit(questions)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Error handling QA change: %s", str(e))

    def update_questions(self, questions: List[Tuple[int, str, str]]):
        """Update the list of questions"""
        logger.debug("Updating QA list with %d questions", len(questions))
        
        focused_widget = None
        focused_text = None
        focused_row = -1
        focused_is_question = False
        
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item and item.widget():
                qa_item = item.widget()
                if qa_item.question_edit.hasFocus():
                    focused_widget = qa_item.question_edit
                    focused_text = focused_widget.toPlainText()
                    focused_row = i
                    focused_is_question = True
                    break
                elif qa_item.answer_edit.hasFocus():
                    focused_widget = qa_item.answer_edit
                    focused_text = focused_widget.toPlainText()
                    focused_row = i
                    focused_is_question = False
                    break
                
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        for question_id, question, answer in questions:
            self.add_qa_item(question_id, question, answer)
            
        if focused_widget and focused_row >= 0 and focused_row < self.layout.count():
            qa_item = self.layout.itemAt(focused_row).widget()
            if qa_item:
                if focused_is_question:
                    qa_item.question_edit.setFocus()
                    qa_item.question_edit.setPlainText(focused_text)
                    cursor = qa_item.question_edit.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    qa_item.question_edit.setTextCursor(cursor)
                else:
                    qa_item.answer_edit.setFocus()
                    qa_item.answer_edit.setPlainText(focused_text)
                    cursor = qa_item.answer_edit.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    qa_item.answer_edit.setTextCursor(cursor)
            
        logger.debug("QA list updated with %d questions", len(questions)) 