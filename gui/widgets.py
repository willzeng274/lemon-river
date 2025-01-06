"""
Widgets for the GUI
"""

import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (
    QMainWindow, QLineEdit, QTextEdit, QApplication, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget, QDialog, QDialogButtonBox, QListWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QEvent, QSize
from PyQt6.QtGui import QFont

from gui.dataclasses import ApplicationStatus

logger = logging.getLogger(__name__)

# pylint: disable=invalid-name
class DraggableWindow(QMainWindow):
    """Base window class that can be dragged by clicking and holding anywhere"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, False)
        self._drag_pos = None
        self.focused_opacity = 1.0
        self.unfocused_opacity = 0.8

    def mousePressEvent(self, event):
        """Handle mouse press events for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging"""
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos:
            diff = event.globalPosition().toPoint() - self._drag_pos
            new_pos = self.pos() + diff
            self.move(new_pos)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None

    def changeEvent(self, event):
        """Handle window activation changes"""
        if event.type() == event.Type.ActivationChange:
            if self.isActiveWindow():
                self.setWindowOpacity(self.focused_opacity)
            else:
                self.setWindowOpacity(self.unfocused_opacity)
        super().changeEvent(event)


class PlainPasteLineEdit(QLineEdit):
    """QLineEdit with plain text paste behavior"""

    def keyPressEvent(self, event):
        """Override keyPressEvent to handle Ctrl+V (Command+V on Mac)"""
        modifiers = QApplication.keyboardModifiers()
        if event.key() == Qt.Key.Key_V and (
            modifiers & Qt.KeyboardModifier.ControlModifier
        ):
            clipboard = QApplication.clipboard()
            self.insert(clipboard.text())
            return
        super().keyPressEvent(event)


class PlainPasteTextEdit(QTextEdit):
    """TextEdit that pastes plain text"""

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.insertPlainText(QApplication.clipboard().text())
        else:
            super().keyPressEvent(event)

class JobQAItem(QFrame):
    """Widget representing a question and answer pair"""
    
    deleted = pyqtSignal(QWidget)
    edited = pyqtSignal(str, str, QWidget)
    
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


class JobQAListWidget(QScrollArea):
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
        qa_item = JobQAItem(question, answer, self)
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
            new_item = JobQAItem(new_question, new_answer, self)
            new_item.deleted.connect(self.remove_qa_item)
            new_item.edited.connect(self.edit_qa_item)
            self.layout.insertWidget(index, new_item)
        
        self.qa_updated.emit(self.questions)


class SearchBar(QLineEdit):
    """Search bar with consistent styling"""
    def __init__(self, placeholder="Search for applications... (f)"):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #3c3c3c;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus {
                background-color: #4a4a4a;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #8e8e8e;
            }
        """)


class TabNavigationLineEdit(QLineEdit):
    """LineEdit that supports tab navigation between cells"""
    def __init__(self, row: int, col: int, table, text: str = ""):
        super().__init__()  # Initialize without text
        self.row = row
        self.col = col
        self.table = table
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # self.textChanged.connect(self._handle_text_changed)
        self.editingFinished.connect(self._handle_editing_finished)
        self._original_text = text
        self.setText(text)  # Set text after initialization
        self.setCursorPosition(0)  # Now set cursor position after text is set
        self.is_editing = False

    def setText(self, text: str):
        """Override setText to ensure cursor position is reset"""
        super().setText(text)
        if not self.hasFocus():
            self.setCursorPosition(0)
            self.deselect()

    def event(self, event):
        """Handle all events to capture tab before it's handled by Qt"""
        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Tab:
                self.focusNextCell()
                return True
            elif event.key() == Qt.Key.Key_Backtab:
                self.focusPreviousCell()
                return True
        return super().event(event)

    def focusOutEvent(self, event):
        """Reset cursor position to start when losing focus"""
        super().focusOutEvent(event)
        self.setCursorPosition(0)
        self.deselect()

    # def _handle_text_changed(self, text: str):
    #     """Handle text changes in the cell"""
    #     if text != self._original_text:
    #         self.table.cell_edited(self.row, self.col, text)

    def _handle_editing_finished(self):
        """Handle when editing is finished (Enter pressed or focus lost)"""
        if self.text() != self._original_text:
            self.table.save_cell_edit(self.row, self.col, self.text())
            self._original_text = self.text()
        self.setCursorPosition(0)
        self.deselect()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to track editing state"""
        super().mouseReleaseEvent(event)
        if self.hasSelectedText() or self.cursorPosition() != 0:
            self.is_editing = True

    def mousePressEvent(self, event):
        """Handle mouse press to track editing state"""
        super().mousePressEvent(event)
        self.is_editing = True

    def focusNextCell(self):
        """Focus the next editable cell"""
        next_col = self.col + 1
        next_row = self.row

        if next_col == 0:
            next_col = 1

        if next_col >= self.table.columnCount():
            next_col = 1
            next_row += 1

        if next_row >= self.table.rowCount():
            next_row = 0

        logger.info("Moving to next cell - row: %d, col: %d", next_row, next_col)
        self.focusCell(next_row, next_col)

    def focusPreviousCell(self):
        """Focus the previous editable cell"""
        prev_col = self.col - 1
        prev_row = self.row

        if prev_col == 0:
            prev_col = self.table.columnCount() - 1
            prev_row -= 1

        if prev_row < 0:
            prev_row = self.table.rowCount() - 1

        logger.info("Moving to previous cell - row: %d, col: %d", prev_row, prev_col)
        self.focusCell(prev_row, prev_col)

    def focusCell(self, row: int, col: int):
        """Focus a specific cell"""
        cell_widget = self.table.cellWidget(row, col)
        if cell_widget:
            line_edit = cell_widget.findChild(QLineEdit)
            if line_edit:
                logger.info("Focusing cell at row: %d, col: %d", row, col)
                line_edit.setFocus()
                line_edit.selectAll()
            else:
                logger.info("No QLineEdit found in cell at row: %d, col: %d", row, col)
        else:
            logger.info("No widget found at row: %d, col: %d", row, col)


class DropdownContainer(QWidget):
    """Container widget for dropdown options that forwards events to parent"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selector = None
        self.setObjectName("optionsContainer")

    def keyPressEvent(self, event):
        """Forward key events to selector"""
        if self.selector:
            self.selector.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

class DropdownScrollArea(QScrollArea):
    """Custom scroll area that forwards events to parent"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selector = None
        self.setObjectName("dropdown")

    def keyPressEvent(self, event):
        """Forward key events to selector"""
        if self.selector:
            self.selector.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def event(self, event):
        """Handle press events"""
        if event.type() == QEvent.Type.MouseButtonPress:
            self.selector.toggle_dropdown()
            return True
        return super().event(event)

class ApplicationSelector(QFrame):
    """Custom application selector widget with modern styling"""

    currentApplicationChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        """Initialize the application selector"""
        super().__init__(parent)

        self.current_id = None
        self.current_text = "Select Application"
        self.options = {}  # {app_id: {'text': display_text, 'widget': option_widget}}
        self.focused_id = None
        self.is_open = False

        self.setup_ui()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        """Handle keyboard events"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide_dropdown()
            event.accept()
        elif event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space]:
            if self.is_open and self.focused_id is not None:
                self.select_option(self.focused_id)
            else:
                self.toggle_dropdown()
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            if not self.is_open:
                self.show_dropdown()
            self.focus_previous_option()
            event.accept()
        elif event.key() == Qt.Key.Key_Up:
            if not self.is_open:
                self.show_dropdown()
            self.focus_next_option()
            event.accept()
        else:
            super().keyPressEvent(event)

    def focus_next_option(self):
        """Focus the next option in the list without selecting it"""
        if not self.options:
            return

        app_ids = sorted(self.options.keys())
        if not app_ids:
            return

        try:
            current_idx = app_ids.index(self.focused_id if self.focused_id is not None else self.current_id)
            next_idx = current_idx + 1
            if next_idx >= len(app_ids):
                return
        except ValueError:
            next_idx = 0

        self.focus_option(app_ids[next_idx])

    def focus_previous_option(self):
        """Focus the previous option in the list without selecting it"""
        if not self.options:
            return

        app_ids = sorted(self.options.keys())
        if not app_ids:
            return

        try:
            current_idx = app_ids.index(self.focused_id if self.focused_id is not None else self.current_id)
            prev_idx = current_idx - 1
            if prev_idx < 0:
                return
        except ValueError:
            prev_idx = len(app_ids) - 1

        self.focus_option(app_ids[prev_idx])

    def focus_option(self, app_id):
        """Focus an option without selecting it"""
        if app_id not in self.options:
            return False

        if self.focused_id is not None and self.focused_id in self.options:
            prev_option = self.options[self.focused_id]['widget']
            prev_option.setProperty("focused", "false")
            prev_option.style().unpolish(prev_option)
            prev_option.style().polish(prev_option)

        option = self.options[app_id]['widget']
        option.setProperty("focused", "true")
        option.style().unpolish(option)
        option.style().polish(option)

        self.focused_id = app_id
        return True

    def show_dropdown(self):
        """Show the dropdown with options"""
        if self.is_open:
            return

        pos = self.mapToGlobal(QPoint(0, self.height()))

        self.dropdown.setFixedWidth(self.width())

        content_height = min(300, self.options_layout.sizeHint().height() + 10)

        self.dropdown.setGeometry(
            pos.x(),
            pos.y() + 4,
            self.width(),
            content_height
        )

        self.arrow_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 10px;
            }
        """)
        self.arrow_label.setText("▲")

        if self.current_id is not None:
            self.focus_option(self.current_id)

        self.dropdown.show()
        self.dropdown.raise_()
        self.is_open = True
        self.update()

    def hide_dropdown(self):
        """Hide the dropdown"""
        if self.is_open:
            self.dropdown.hide()
            self.is_open = False
            self.focused_id = None

            self.arrow_label.setStyleSheet("""
                QLabel {
                    color: #aaaaaa;
                    font-size: 10px;
                }
            """)
            self.arrow_label.setText("▼")

            for option_data in self.options.values():
                option = option_data['widget']
                option.setProperty("focused", "false")
                option.style().unpolish(option)

            self.update()

    def add_option(self, text, app_id):
        """Add an option to the dropdown"""
        if app_id in self.options:
            return self.update_option(app_id, text)

        option = QWidget()
        option.setObjectName(f"option_{app_id}")
        option.setProperty("class", "OptionWidget")
        option.setProperty("selected", "false")
        option.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(option)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(6)

        label = QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)

        self.options[app_id] = {
            'text': text,
            'widget': option,
            'label': label
        }

        def handle_option_click(e):
            if e.button() == Qt.MouseButton.LeftButton:
                self.select_option(app_id)
                e.accept()

        option.mousePressEvent = handle_option_click

        self.options_layout.addWidget(option)

        if len(self.options) == 1 and self.current_id is None:
            self.select_option(app_id)

    def update_option(self, app_id, new_text):
        """Update an existing option's text"""
        if app_id not in self.options:
            return False

        self.options[app_id]['text'] = new_text

        self.options[app_id]['label'].setText(new_text)

        if self.current_id == app_id:
            self.current_text = new_text
            self.selected_label.setText(new_text)

        return True

    def select_option(self, app_id):
        """Select an option by ID"""
        if app_id not in self.options:
            return False

        if self.current_id is not None and self.current_id in self.options:
            prev_option = self.options[self.current_id]['widget']
            prev_option.setProperty("selected", "false")
            prev_option.style().unpolish(prev_option)
            prev_option.style().polish(prev_option)

        option = self.options[app_id]['widget']
        option.setProperty("selected", "true")
        option.style().unpolish(option)
        option.style().polish(option)

        self.current_id = app_id
        self.current_text = self.options[app_id]['text']
        self.selected_label.setText(self.current_text)

        self.hide_dropdown()
        self.currentApplicationChanged.emit(app_id)
        return True

    def select_option_no_signal(self, app_id):
        """Select an option without emitting the signal"""
        if app_id not in self.options:
            return False

        if self.current_id is not None and self.current_id in self.options:
            prev_option = self.options[self.current_id]['widget']
            prev_option.setProperty("selected", "false")
            prev_option.style().unpolish(prev_option)
            prev_option.style().polish(prev_option)

        option = self.options[app_id]['widget']
        option.setProperty("selected", "true")
        option.style().unpolish(option)
        option.style().polish(option)

        self.current_id = app_id
        self.current_text = self.options[app_id]['text']
        self.selected_label.setText(self.current_text)

        self.hide_dropdown()
        return True

    def remove_option(self, app_id):
        """Remove an option from the dropdown"""
        if app_id not in self.options:
            return False

        option = self.options[app_id]['widget']
        self.options_layout.removeWidget(option)
        option.setParent(None)
        option.deleteLater()

        del self.options[app_id]

        if self.current_id == app_id:
            self.current_id = None
            self.current_text = "Select Application"
            self.selected_label.setText(self.current_text)

        return True

    def clear(self):
        """Clear all options"""
        self.blockSignals(True)

        try:
            if self.is_open:
                self.hide_dropdown()

            app_ids = list(self.options.keys())
            for app_id in app_ids:
                self.remove_option(app_id)

            self.current_id = None
            self.current_text = "Select Application"
            self.selected_label.setText(self.current_text)
        finally:
            self.blockSignals(False)

    def eventFilter(self, obj, event):
        """Filter events to handle clicking outside the dropdown"""
        if self.is_open and event.type() == QEvent.Type.MouseButtonPress:
            pos = event.globalPosition().toPoint()

            in_header = self.header.rect().contains(self.header.mapFromGlobal(pos))
            in_dropdown = self.dropdown.rect().contains(self.dropdown.mapFromGlobal(pos))

            if not in_header and not in_dropdown:
                self.hide_dropdown()

        return super().eventFilter(obj, event)

    def hideEvent(self, event):
        """Handle when the selector is hidden"""
        self.hide_dropdown()
        super().hideEvent(event)

    def __del__(self):
        """Clean up resources"""
        app = QApplication.instance()
        if app:
            app.removeEventFilter(self)

    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = QWidget(self)
        self.header.setObjectName("selectorHeader")
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)

        self.selected_label = QLabel(self.current_text)
        self.selected_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
        """)
        header_layout.addWidget(self.selected_label)
        header_layout.addStretch()

        self.arrow_label = QLabel("▼")
        self.arrow_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 10px;
            }
        """)
        header_layout.addWidget(self.arrow_label)

        layout.addWidget(self.header)

        self.header.mousePressEvent = lambda event: self.toggle_dropdown()

        self.dropdown = DropdownScrollArea()
        self.dropdown.selector = self
        self.dropdown.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.dropdown.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.dropdown.setAttribute(Qt.WidgetAttribute.WA_X11NetWmWindowTypeDropDownMenu)
        self.dropdown.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dropdown.setWidgetResizable(True)
        self.dropdown.setVisible(False)

        self.dropdown.setStyleSheet("""
            QScrollArea#dropdown {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
            }
            
            QWidget#optionsContainer {
                background-color: transparent;
            }
            
            .OptionWidget {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                min-height: 20px;
            }
            
            .OptionWidget:hover {
                background-color: #3a3a3a;
            }
            
            .OptionWidget[focused="true"] {
                background-color: #3a3a3a;
            }
            
            .OptionWidget[selected="true"] {
                background-color: #404040;
            }
            
            .OptionWidget QLabel {
                color: #ffffff;
                font-size: 13px;
                padding: 2px 0px;
            }
            
            QScrollBar:vertical {
                border: none;
                background: #2a2a2a;
                width: 6px;
                margin: 4px 0;
            }
            
            QScrollBar::handle:vertical {
                background: #4a4a4a;
                border-radius: 3px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #5a5a5a;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
                border: none;
                background: none;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        self.options_container = DropdownContainer()
        self.options_container.selector = self
        self.dropdown.setWidget(self.options_container)

        self.options_layout = QVBoxLayout(self.options_container)
        self.options_layout.setContentsMargins(4, 4, 4, 4)
        self.options_layout.setSpacing(4)

        self.is_open = False

        QApplication.instance().installEventFilter(self)

        self.setStyleSheet("""
            ApplicationSelector {
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                background-color: #2a2a2a;
            }
            
            ApplicationSelector:hover {
                border-color: #4a4a4a;
            }
            
            #selectorHeader {
                background-color: transparent;
                border-radius: 6px;
            }
            
            #selectorHeader:hover {
                background-color: #333333;
            }
        """)

    def toggle_dropdown(self):
        """Toggle dropdown visibility"""
        if self.is_open:
            self.hide_dropdown()
        else:
            self.show_dropdown()

class StatusDropdown(QWidget):
    """Custom dropdown for selecting application status with consistent styling"""

    statusChanged = pyqtSignal(str)
    currentTextChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.current_status = ApplicationStatus.APPLYING.value
        self.is_popup_visible = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.button = QFrame(self)
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button.mousePressEvent = self.toggle_popup

        button_layout = QHBoxLayout(self.button)
        button_layout.setContentsMargins(12, 8, 12, 8)

        self.label = QLabel(self.current_status)
        self.arrow = QLabel("▼")
        self.arrow.setFixedWidth(16)
        self.arrow.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        button_layout.addWidget(self.label)
        button_layout.addWidget(self.arrow)

        layout.addWidget(self.button)

        self.popup = QFrame(self)
        self.popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.popup.setVisible(False)

        popup_layout = QVBoxLayout(self.popup)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        popup_layout.setSpacing(0)

        self.option_items = []
        for status in ApplicationStatus:
            option = QFrame()
            option.setCursor(Qt.CursorShape.PointingHandCursor)
            option.status_value = status.value

            option.mousePressEvent = lambda e, s=status.value: self.select_option(s)
            
            # Option layout
            option_layout = QHBoxLayout(option)
            option_layout.setContentsMargins(12, 8, 12, 8)
            
            # Check mark (visible when selected)
            check = QLabel("✓")
            check.setFixedWidth(16)
            check.setVisible(status.value == self.current_status)
            
            # Option text
            text = QLabel(status.value)
            
            option_layout.addWidget(check)
            option_layout.addWidget(text)
            
            # Store references
            option.check = check
            option.text = text
            
            popup_layout.addWidget(option)
            self.option_items.append(option)
        
        # Apply styles
        self.apply_styles()
        
        # Install event filter for detecting clicks outside
        QApplication.instance().installEventFilter(self)
        
        # Connect signals
        self.statusChanged.connect(self.currentTextChanged)
    
    def apply_styles(self):
        """Apply consistent styling"""
        # Button styling
        self.button.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
            }
            QFrame:hover {
                background-color: #333333;
            }
            QLabel {
                color: white;
                font-size: 13px;
                background: transparent;
                border: none;
            }
        """)

        self.popup.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
            }
            QLabel {
                color: white;
                font-size: 13px;
                background: transparent;
                border: none;
            }
        """)

        for option in self.option_items:
            option.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                }
                QFrame:hover {
                    background-color: #333333;
                }
                QLabel {
                    color: white;
                    font-size: 13px;
                    background: transparent;
                    border: none;
                }
            """)

            option.check.setStyleSheet("""
                QLabel {
                    color: #64b5f6;
                    font-weight: bold;
                    font-size: 13px;
                    background: transparent;
                    border: none;
                }
            """)

    def toggle_popup(self, event=None):
        """Toggle the popup visibility"""
        if event:
            event.accept()

        if not self.is_popup_visible:
            self.show_popup()
        else:
            self.hide_popup()

    def show_popup(self):
        """Show the popup menu"""
        if self.is_popup_visible:
            return

        pos = self.mapToGlobal(QPoint(0, self.height()))
        self.popup.move(pos)
        self.popup.setFixedWidth(self.width())

        self.popup.show()
        self.is_popup_visible = True

        self.arrow.setText("▲")

    def hide_popup(self):
        """Hide the popup menu"""
        if not self.is_popup_visible:
            return

        self.popup.hide()
        self.is_popup_visible = False

        self.arrow.setText("▼")

    def select_option(self, status):
        """Select an option from the popup"""
        if self.current_status != status:
            for option in self.option_items:
                option.check.setVisible(option.status_value == status)

            self.current_status = status
            self.label.setText(status)

            self.statusChanged.emit(status)

        self.hide_popup()

    def eventFilter(self, obj, event):
        """Filter events to detect clicks outside the popup"""
        if event.type() == QEvent.Type.MouseButtonPress and self.is_popup_visible:
            if obj is self.popup or obj is self:
                return super().eventFilter(obj, event)

            if isinstance(obj, QWidget):
                if not self.isAncestorOf(obj):
                    self.hide_popup()
            else:
                self.hide_popup()

        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """Handle keyboard navigation"""
        if event.key() == Qt.Key.Key_Escape and self.is_popup_visible:
            self.hide_popup()
            event.accept()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.toggle_popup()
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            if not self.is_popup_visible:
                self.show_popup()
                event.accept()
            else:
                self.navigate_options(1)
                event.accept()
        elif event.key() == Qt.Key.Key_Up and self.is_popup_visible:
            self.navigate_options(-1)
            event.accept()
        else:
            super().keyPressEvent(event)

    def navigate_options(self, direction):
        """Navigate through options using keyboard"""
        current_index = -1
        for i, option in enumerate(self.option_items):
            if option.status_value == self.current_status:
                current_index = i
                break

        if direction > 0:
            new_index = min(len(self.option_items) - 1, current_index + 1)
        else:
            new_index = max(0, current_index - 1)

        if new_index != current_index:
            self.select_option(self.option_items[new_index].status_value)
            self.show_popup()

    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        self.hide_popup()

    def hideEvent(self, event):
        """Handle hide event"""
        super().hideEvent(event)
        self.hide_popup()

    def currentText(self):
        """Get the current text (for compatibility with QComboBox)"""
        return self.current_status

    def setCurrentText(self, text):
        """Set the current text (for compatibility with QComboBox)"""
        valid_statuses = [status.value for status in ApplicationStatus]
        if text in valid_statuses:
            for option in self.option_items:
                option.check.setVisible(option.status_value == text)

            self.current_status = text
            self.label.setText(text)

    def sizeHint(self):
        """Suggest a size for the widget"""
        return QSize(180, 36)

class SectionLabel(QLabel):
    """Section header label with consistent styling"""

    def __init__(self, text: str):
        super().__init__(text)
        self.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.setStyleSheet("color: #333; margin-top: 10px;")

class LockableField:
    """A field that can be locked"""

    def __init__(self, field_widget, field_name: str):
        self.widget = field_widget
        self.field_name = field_name
        self.is_locked = False

        self.lock_button = QPushButton("⚡")
        self.lock_button.setProperty("lockButton", True)
        self.lock_button.setFixedSize(QSize(24, 24))
        self.lock_button.clicked.connect(self.toggle_lock)

    def toggle_lock(self):
        """Toggle the lock state"""
        self.is_locked = not self.is_locked
        self.lock_button.setText("🔒" if self.is_locked else "⚡")

        if isinstance(
            self.widget, (QLineEdit, PlainPasteLineEdit, QTextEdit, PlainPasteTextEdit)
        ):
            self.widget.setReadOnly(self.is_locked)
            if isinstance(self.widget, (QTextEdit, PlainPasteTextEdit)):
                self.widget.setStyleSheet(
                    "background-color: rgba(0, 0, 0, 0.05);" if self.is_locked else ""
                )
        elif isinstance(self.widget, QListWidget):
            self.widget.setEnabled(not self.is_locked)
            self.widget.setStyleSheet(
                "background-color: rgba(0, 0, 0, 0.05);" if self.is_locked else ""
            )
