"""
Widget for displaying a list of question-answer pairs
"""

# pylint: disable=no-name-in-module
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget, QDialog, QDialogButtonBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal

from .paste import PlainPasteTextEdit


class QAItem(QFrame):
    """Widget representing a question and answer pair"""
    
    deleted = pyqtSignal(QWidget) # sends itself to be deleted
    edited = pyqtSignal(str, str, QWidget) # sends new question, answer, and itself
    
    def __init__(self, question: str, answer: str, parent=None):
        super().__init__(parent)
        self.question = question
        self.answer = answer
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI for the question-answer item"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        question_layout = QHBoxLayout()
        question_label = QLabel("<b>Q:</b>")
        question_label.setFont(QFont("Arial", 10))
        question_label.setStyleSheet("color: #0366d6;")
        question_text = QLabel(self.question)
        question_text.setWordWrap(True)
        question_text.setStyleSheet("""
            font-size: 10pt;
            color: #24292e;
            padding: 4px;
        """)
        
        question_layout.addWidget(question_label)
        question_layout.addWidget(question_text, 1)
        layout.addLayout(question_layout)
        
        if self.answer:
            answer_layout = QHBoxLayout()
            answer_label = QLabel("<b>A:</b>")
            answer_label.setFont(QFont("Arial", 10))
            answer_label.setStyleSheet("color: #28a745;")
            answer_text = QLabel(self.answer)
            answer_text.setWordWrap(True)
            answer_text.setStyleSheet("""
                font-size: 10pt;
                color: #586069;
                padding: 4px;
            """)
            
            answer_layout.addWidget(answer_label)
            answer_layout.addWidget(answer_text, 1)
            layout.addLayout(answer_layout)
        
        # Buttons with improved styling
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        edit_button = QPushButton("Edit")
        edit_button.setMaximumWidth(60)
        edit_button.setMinimumHeight(24)
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #fafbfc;
                border: 1px solid rgba(27, 31, 35, 0.15);
                border-radius: 3px;
                color: #24292e;
                font-size: 8pt;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
        """)
        edit_button.clicked.connect(self.edit_qa)
        
        delete_button = QPushButton("Delete")
        delete_button.setMaximumWidth(60)
        delete_button.setMinimumHeight(24)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #fafbfc;
                border: 1px solid rgba(27, 31, 35, 0.15);
                border-radius: 3px;
                color: #d73a49;
                font-size: 8pt;
            }
            QPushButton:hover {
                color: white;
                background-color: #d73a49;
            }
        """)
        delete_button.clicked.connect(self.delete_qa)
        
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)
        
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QAItem {
                background-color: #ffffff;
                border: 1px solid #e1e4e8;
                border-radius: 6px;
            }
            QAItem:hover {
                border-color: #0366d6;
            }
        """)
        
    def edit_qa(self):
        """Edit this QA item"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Question & Answer")
        dialog_layout = QVBoxLayout(dialog)
        
        question_label = QLabel("Question:")
        question_edit = PlainPasteTextEdit(self.question)
        question_edit.setMaximumHeight(80)
        
        answer_label = QLabel("Answer:")
        answer_edit = PlainPasteTextEdit(self.answer)
        answer_edit.setMaximumHeight(80)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        dialog_layout.addWidget(question_label)
        dialog_layout.addWidget(question_edit)
        dialog_layout.addWidget(answer_label)
        dialog_layout.addWidget(answer_edit)
        dialog_layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_question = question_edit.toPlainText().strip()
            new_answer = answer_edit.toPlainText().strip()
            if new_question:
                self.edited.emit(new_question, new_answer, self)
                
    def delete_qa(self):
        """Delete this QA item"""
        self.deleted.emit(self)


class QAListWidget(QScrollArea):
    """Widget for displaying a list of question-answer pairs"""
    
    qa_updated = pyqtSignal(list)
    
    def __init__(self, questions=None, parent=None):
        super().__init__(parent)
        self.questions = questions or []
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 5)
        
        add_button = QPushButton("+")
        add_button.setObjectName("addButton")
        add_button.setFixedSize(24, 24)
        add_button.setToolTip("Add New Question & Answer")
        add_button.clicked.connect(self.add_qa)
        
        header_layout.addStretch()
        header_layout.addWidget(add_button)
        self.layout.addLayout(header_layout)

        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.setMinimumHeight(200)
        self.setMaximumHeight(400)
        
        self.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 5px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QPushButton#addButton {
                background-color: #2ea44f;
                color: white;
                border: 1px solid rgba(27, 31, 35, 0.15);
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                padding: 0;
                margin: 0;
            }
            QPushButton#addButton:hover {
                background-color: #2c974b;
            }
            QPushButton#addButton:pressed {
                background-color: #298e46;
            }
        """)

        self.update_questions(self.questions)
        
    def update_questions(self, questions):
        """Update the list of questions"""
        self.questions = questions
        
        for i in reversed(range(1, self.layout.count())):
            item = self.layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
        
        for question, answer in self.questions:
            self.add_qa_item(question, answer)
    
    def add_qa_item(self, question, answer):
        """Add a QA item to the list"""
        qa_item = QAItem(question, answer, self)
        qa_item.deleted.connect(self.remove_qa_item)
        qa_item.edited.connect(self.edit_qa_item)
        self.layout.addWidget(qa_item)
        
    def add_qa(self):
        """Add a new Q&A pair"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Question & Answer")
        dialog_layout = QVBoxLayout(dialog)
        
        question_label = QLabel("Question:")
        question_edit = PlainPasteTextEdit()
        question_edit.setMaximumHeight(80)
        
        answer_label = QLabel("Answer:")
        answer_edit = PlainPasteTextEdit()
        answer_edit.setMaximumHeight(80)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        dialog_layout.addWidget(question_label)
        dialog_layout.addWidget(question_edit)
        dialog_layout.addWidget(answer_label)
        dialog_layout.addWidget(answer_edit)
        dialog_layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            question = question_edit.toPlainText().strip()
            answer = answer_edit.toPlainText().strip()
            if question:
                self.questions.append((question, answer))
                self.add_qa_item(question, answer)
                self.qa_updated.emit(self.questions)
    
    def remove_qa_item(self, item):
        """Remove a QA item from the list"""
        for i, (q, a) in enumerate(self.questions):
            if q == item.question and a == item.answer:
                del self.questions[i]
                break
        
        item.setParent(None)
        self.qa_updated.emit(self.questions)
    
    def edit_qa_item(self, new_question, new_answer, item):
        """Edit a QA item in the list"""
        for i, (q, a) in enumerate(self.questions):
            if q == item.question and a == item.answer:
                self.questions[i] = (new_question, new_answer)
                break
        
        index = self.layout.indexOf(item)
        if index != -1:
            item.setParent(None)
            new_item = QAItem(new_question, new_answer, self)
            new_item.deleted.connect(self.remove_qa_item)
            new_item.edited.connect(self.edit_qa_item)
            self.layout.insertWidget(index, new_item)
        
        self.qa_updated.emit(self.questions)
