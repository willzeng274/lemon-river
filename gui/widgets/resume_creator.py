"""
Resume creation dialog for selecting templates and generating LaTeX resumes
"""

import os
import re
import logging
import datetime
import shutil
import subprocess
from typing import List, Tuple

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QWidget,
    QLabel,
    QMessageBox,
    QGroupBox,
    QFrame,
    QApplication,
    QTextEdit,
    QScrollArea,
    QSplitter,
    QGridLayout,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QObject, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QMouseEvent, QTextCursor, QTextCharFormat

logger = logging.getLogger(__name__)


class GroupSelector(QFrame):
    """Custom group selector widget similar to ApplicationSelector"""
    
    selectionChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("groupSelector")
        self.current_text = "General"
        self.is_open = False
        self.groups = []
        # Will be populated in setup_ui
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the selector UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = QWidget(self)
        self.header.setObjectName("selectorHeader")
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.mousePressEvent = self.toggle_dropdown
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)
        
        self.selected_label = QLabel("Select group")
        self.selected_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
        """)
        header_layout.addWidget(self.selected_label)
        header_layout.addStretch()
        
        layout.addWidget(self.header)

        self.dropdown = QFrame()
        self.dropdown.setObjectName("dropdown")
        self.dropdown.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.dropdown.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.dropdown.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.dropdown.setVisible(False)

        QApplication.instance().installEventFilter(self)
        
        dropdown_layout = QVBoxLayout(self.dropdown)
        dropdown_layout.setContentsMargins(0, 0, 0, 0)
        dropdown_layout.setSpacing(0)
        
        self.options_container = QWidget(self.dropdown)
        self.options_container.setObjectName("optionsContainer")
        self.options_layout = QVBoxLayout(self.options_container)
        self.options_layout.setContentsMargins(0, 4, 0, 4)
        self.options_layout.setSpacing(0)
        
        dropdown_layout.addWidget(self.options_container)

        self.setStyleSheet("""
            #groupSelector {
                background-color: #2c2c2c;
                border: none;
                border-radius: 6px;
                min-width: 200px;
                max-width: 200px;
            }
            #selectorHeader {
                background-color: transparent;
                border-radius: 6px;
                padding: 0px;
            }
            #selectorHeader:hover {
                background-color: #3c3c3c;
            }
        """)
        
        self.dropdown.setStyleSheet("""
            #dropdown {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
            }
            #optionsContainer {
                background-color: transparent;
            }
            .OptionWidget {
                background-color: transparent;
                border-radius: 4px;
                margin: 0px 4px;
                min-height: 32px;
                max-height: 32px;
            }
            .OptionWidget:hover {
                background-color: #3c3c3c;
            }
            .OptionWidget[selected="true"] {
                background-color: #094771;
            }
            .OptionLabel {
                color: #ffffff;
                font-size: 13px;
                padding: 0px 8px;
            }
        """)
        
    def load_groups(self, output_path):
        """Load groups from output path"""
        self.groups = []
        try:
            self.groups.append("General")
            
            if os.path.exists(output_path):
                for item in os.listdir(output_path):
                    item_path = os.path.join(output_path, item)
                    if os.path.isdir(item_path) and item.lower() != "templates":
                        self.groups.append(item)
            
            while self.options_layout.count():
                widget = self.options_layout.takeAt(0).widget()
                if widget:
                    widget.deleteLater()
                    
            for group in self.groups:
                self.add_option(group)
                
            if self.groups:
                self.select_option(self.groups[0])
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Error loading groups: %s", str(e))
            self.groups = ["General"]
            self.add_option("General")
            self.select_option("General")
        
    def add_option(self, text: str):
        """Add an option to the dropdown"""
        option = QWidget()
        option.setObjectName(f"option_{text}")
        option.setProperty("class", "OptionWidget")
        option.setProperty("selected", "true" if text == self.current_text else "false")
        option.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(option)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(0)
        
        label = QLabel(text)
        label.setObjectName(f"label_{text}")
        label.setProperty("class", "OptionLabel")
        layout.addWidget(label)
        
        self.options_layout.addWidget(option)
        
        def handle_option_click(e):
            if e.button() == Qt.MouseButton.LeftButton:
                self.select_option(text)
                self.hide_dropdown()
        
        option.mousePressEvent = handle_option_click
        
    def select_option(self, text: str):
        """Select an option by text"""
        if text == self.current_text:
            return
            
        self.current_text = text
        self.selected_label.setText(text)
        
        for i in range(self.options_layout.count()):
            widget = self.options_layout.itemAt(i).widget()
            if widget:
                widget_text = widget.objectName().replace("option_", "")
                widget.setProperty("selected", "true" if widget_text == text else "false")
                widget.style().unpolish(widget)
                widget.style().polish(widget)
            
        self.selectionChanged.emit(text)
        
    def toggle_dropdown(self, _event=None):
        """Toggle the dropdown visibility"""
        if self.is_open:
            self.hide_dropdown()
        else:
            self.show_dropdown()
    
    def show_dropdown(self):
        """Show the dropdown"""
        if not self.is_open:
            pos = self.mapToGlobal(self.rect().bottomLeft())
            content_height = min(300, max(32, self.options_layout.sizeHint().height()))
            
            self.dropdown.setGeometry(
                pos.x(),
                pos.y() + 4,
                self.width(),
                content_height
            )
            
            self.dropdown.show()
            self.dropdown.raise_()
            self.is_open = True
            self.update()
            
    def hide_dropdown(self):
        """Hide the dropdown"""
        if self.is_open:
            self.dropdown.hide()
            self.is_open = False
            self.update()
            
    def paintEvent(self, event):
        """Paint the selector with arrow indicator"""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        arrow_color = QColor("#ffffff")
        painter.setPen(QPen(arrow_color, 1.5))
        
        arrow_size = 8
        arrow_x = self.width() - 16
        arrow_y = self.height() // 2
        
        if self.is_open:
            painter.drawLine(arrow_x - arrow_size//2, arrow_y + arrow_size//4, arrow_x, arrow_y - arrow_size//4)
            painter.drawLine(arrow_x + arrow_size//2, arrow_y + arrow_size//4, arrow_x, arrow_y - arrow_size//4)
        else:
            painter.drawLine(arrow_x - arrow_size//2, arrow_y - arrow_size//4, arrow_x, arrow_y + arrow_size//4)
            painter.drawLine(arrow_x + arrow_size//2, arrow_y - arrow_size//4, arrow_x, arrow_y + arrow_size//4)
        
    def eventFilter(self, obj, event):
        """Filter global events to close dropdown when clicking outside"""
        if event.type() == event.Type.MouseButtonPress and self.is_open:
            dropdown_rect = self.dropdown.geometry()
            
            header_rect_global = QRect(
                self.mapToGlobal(self.header.geometry().topLeft()),
                self.mapToGlobal(self.header.geometry().bottomRight())
            )
            
            global_pos = event.globalPosition().toPoint()
            if not dropdown_rect.contains(global_pos) and not header_rect_global.contains(global_pos):
                self.hide_dropdown()
                
        return super().eventFilter(obj, event)
    
    def hideEvent(self, event):
        """Handle widget being hidden"""
        self.hide_dropdown()
        super().hideEvent(event)
            
    def __del__(self):
        """Clean up event filter"""
        try:
            QApplication.instance().removeEventFilter(self)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.debug("Failed to remove event filter: %s", str(e))


class DraggableDialog(QDialog):
    """Base class for frameless, draggable dialogs"""
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.dragging = False
        self.drag_position = None
        
    def mousePressEvent(self, event: QMouseEvent):
        """Start dragging on left button press in title bar area"""
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 40:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle dragging the window"""
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Stop dragging on button release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()


class TemplateItemWidget(QWidget):
    """Widget for displaying a template in a list"""
    
    clicked = pyqtSignal(str)
    focused = pyqtSignal(str)
    
    def __init__(self, template_path: str, match_lines: List[Tuple[int, str]] = None, parent=None):
        super().__init__(parent)
        self.template_path = template_path
        self.match_lines = match_lines or []
        self.is_selected = False
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the template item UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(0)
        
        filename = os.path.basename(self.template_path)
        self.name_label = QLabel(filename)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.name_label)
        
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-radius: 0px;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(24)
        
    def set_selected(self, selected: bool):
        """Set the selected state of this item"""
        self.is_selected = selected
        if selected:
            self.setStyleSheet("""
                QWidget {
                    background-color: #094771;
                    border-radius: 0px;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border-radius: 0px;
                }
            """)
    
    def enterEvent(self, event):
        """Handle mouse enter to emit focused signal"""
        if not self.is_selected:
            self.setStyleSheet("""
                QWidget {
                    background-color: #3c3c3c;
                    border-radius: 0px;
                }
            """)
        self.focused.emit(self.template_path)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave to reset styling"""
        if not self.is_selected:
            self.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border-radius: 0px;
                }
            """)
        super().leaveEvent(event)
            
    def mousePressEvent(self, event):
        """Handle mouse press to select this template"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.template_path)
            self.set_selected(True)
            super().mousePressEvent(event)


class FilePreviewWidget(QWidget):
    """Widget for displaying a preview of a file with context around matched lines"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.match_lines = []
        self.context_lines = 5
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the preview UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.header_label = QLabel("File Preview")
        self.header_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 13px;
                font-weight: bold;
                padding: 4px 0px;
                margin: 0px;
                border-bottom: 1px solid #3c3c3c;
            }
        """)
        layout.addWidget(self.header_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #1c1c1c;
                color: #cccccc;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
                font-size: 12px;
                selection-background-color: #094771;
            }
            QScrollBar:vertical {
                border: none;
                background: #2c2c2c;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a4a4a;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background: #2c2c2c;
                height: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #4a4a4a;
                min-width: 20px;
                border-radius: 3px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        
        self.preview_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.preview_text)
        
        self.preview_text.setText("Select a template file to see a preview")

    def load_file_preview(self, file_path: str, match_lines: List[Tuple[int, str]] = None):
        """Load a file preview with context around matched lines"""
        self.current_file = file_path
        self.match_lines = match_lines or []
        
        if not file_path or not os.path.exists(file_path):
            self.preview_text.setText("File not found")
            return
            
        try:
            filename = os.path.basename(file_path)
            self.header_label.setText(f"Preview: {filename}")
            
            if not self.match_lines:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    preview_text = ''.join(lines[:20])
                    self.preview_text.setText(preview_text)
                return
                
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            preview_text = ""
            processed_line_nums = set()
            
            for line_num, _ in sorted(self.match_lines):
                if line_num in processed_line_nums:
                    continue
                    
                start_line = max(0, line_num - self.context_lines - 1)
                end_line = min(len(lines), line_num + self.context_lines)
                
                if preview_text:
                    preview_text += "\n\n...\n\n"
                
                preview_text += f"--- Lines {start_line+1}-{end_line} ---\n"
                
                for i in range(start_line, end_line):
                    is_match = any(m[0] == i+1 for m in self.match_lines)
                    line_prefix = f"{i+1:4d}: "
                    
                    if is_match:
                        preview_text += f"→ {line_prefix}{lines[i]}"
                    else:
                        preview_text += f"  {line_prefix}{lines[i]}"
                        
                    processed_line_nums.add(i+1)
            
            self.preview_text.setText(preview_text)
            
            doc = self.preview_text.document()
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            
            text_format = QTextCharFormat()
            text_format.setBackground(QColor("#2f4f6f"))
            text_format.setForeground(QColor("#ffffff"))
            
            while not cursor.atEnd():
                cursor.select(QTextCursor.SelectionType.LineUnderCursor)
                line_text = cursor.selectedText()
                
                if line_text.startswith("→"):
                    cursor.setCharFormat(text_format)
                
                cursor.movePosition(QTextCursor.MoveOperation.Down)
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            
            cursor = self.preview_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.preview_text.setTextCursor(cursor)
        
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Error loading file preview: %s", str(e))
            self.preview_text.setText(f"Error loading preview: {str(e)}")


class DebounceTimer(QObject):
    """Timer for debouncing function calls"""
    
    timeout = pyqtSignal()
    
    def __init__(self, interval=300, parent=None):
        super().__init__(parent)
        self.interval = interval
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.timeout.emit)
        
    def start(self):
        """Start or restart the timer"""
        self.timer.stop()
        self.timer.start(self.interval)


class ResumeCreationDialog(DraggableDialog):
    """Dialog for creating resumes from templates"""
    
    resume_created = pyqtSignal(str)
    
    def __init__(self, company: str = "", role: str = "", parent=None):
        super().__init__(parent)
        self.templates_path = os.path.expanduser("~/Desktop/resumes")
        self.output_path = os.path.expanduser("~/Desktop/resumes")
        self.selected_template = None
        self.company = company
        self.role = role
        self.date = datetime.datetime.now().strftime("%Y%m%d")
        self.template_items = []
        self.debounce_timer = DebounceTimer(300, self)
        self.debounce_timer.timeout.connect(self._perform_search)
        self.current_search = ""
        self.setup_ui()
        self.load_templates()

    def setup_ui(self):
        """Setup the resume creation UI"""
        self.setMinimumSize(1000, 800)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        container = QWidget()
        container.setObjectName("mainContainer")
        container.setStyleSheet("""
            #mainContainer {
                background-color: #1e1e1e;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        
        template_group = QGroupBox("1. Select Template")
        template_group.setStyleSheet("""
            QGroupBox {
                background-color: #252525;
                border-radius: 8px;
                border: none;
                margin-top: 24px;
                padding: 12px;
                color: #ffffff;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 12px;

            }
        """)
        
        template_layout = QVBoxLayout(template_group)
        template_layout.setContentsMargins(12, 20, 12, 12)
        template_layout.setSpacing(12)
        
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)
        
        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: #cccccc; font-size: 13px;")
        search_layout.addWidget(search_label)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search templates...")
        self.search_bar.textChanged.connect(self.debounce_search)
        self.search_bar.setStyleSheet("""
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
                outline: none;
            }
        """)
        search_layout.addWidget(self.search_bar)
        template_layout.addLayout(search_layout)
        
        template_split = QSplitter(Qt.Orientation.Horizontal)
        template_split.setChildrenCollapsible(False)
        template_split.setHandleWidth(1)
        template_split.setStyleSheet("""
            QSplitter::handle {
                background-color: #3c3c3c;
            }
        """)
        
        template_list_container = QWidget()
        template_list_layout = QVBoxLayout(template_list_container)
        template_list_layout.setContentsMargins(0, 0, 0, 0)
        template_list_layout.setSpacing(0)
        
        list_label = QLabel("Template Files")
        list_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 13px;
                padding-bottom: 4px;
            }
        """)
        template_list_layout.addWidget(list_label)
        
        self.template_scroll = QScrollArea()
        self.template_scroll.setWidgetResizable(True)
        self.template_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.template_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1c1c1c;
                border: none;
                border-radius: 6px;
            }
            QScrollBar:vertical {
                border: none;
                background: #2c2c2c;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a4a4a;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        self.template_container = QWidget()
        self.template_container.setObjectName("templateContainer")
        self.template_container.setStyleSheet("""
            #templateContainer {
                background-color: transparent;
            }
        """)
        
        self.template_layout = QVBoxLayout(self.template_container)
        self.template_layout.setContentsMargins(4, 4, 4, 4)
        self.template_layout.setSpacing(0)  # No spacing between items
        self.template_layout.addStretch()
        
        self.template_scroll.setWidget(self.template_container)
        template_list_layout.addWidget(self.template_scroll)
        
        self.preview_panel = FilePreviewWidget()
        
        template_split.addWidget(template_list_container)
        template_split.addWidget(self.preview_panel)
        template_split.setSizes([250, 750])
        
        template_layout.addWidget(template_split)
        
        self.selection_label = QLabel("Selected: None")
        self.selection_label.setStyleSheet("color: #cccccc; font-size: 13px;")
        template_layout.addWidget(self.selection_label)
        
        content_layout.addWidget(template_group)
        
        details_group = QGroupBox("2. Resume Details")
        details_group.setStyleSheet(template_group.styleSheet())
        
        details_layout = QGridLayout(details_group)
        details_layout.setContentsMargins(12, 20, 12, 12)
        details_layout.setHorizontalSpacing(12)
        details_layout.setVerticalSpacing(16)
        
        form_label_style = """
            QLabel {
                color: #cccccc;
                font-size: 13px;
            }
        """
        
        group_label = QLabel("Group:")
        group_label.setStyleSheet(form_label_style)
        group_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.group_selector = GroupSelector()
        self.group_selector.load_groups(self.output_path)
        self.group_selector.selectionChanged.connect(self.update_preview)
        self.group_selector.setFixedWidth(200)
        
        details_layout.addWidget(group_label, 0, 0)
        details_layout.addWidget(self.group_selector, 0, 1)
        
        details_layout.setColumnStretch(2, 1)
        
        company_label = QLabel("Company:")
        company_label.setStyleSheet(form_label_style)
        company_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.company_edit = QLineEdit()
        self.company_edit.setText(self.company)
        self.company_edit.setPlaceholderText("Company name...")
        self.company_edit.setStyleSheet(self.search_bar.styleSheet())
        self.company_edit.textChanged.connect(self.update_preview)
        self.company_edit.setMinimumWidth(300)
        
        details_layout.addWidget(company_label, 1, 0)
        details_layout.addWidget(self.company_edit, 1, 1, 1, 2)
        
        role_label = QLabel("Role:")
        role_label.setStyleSheet(form_label_style)
        role_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.role_edit = QLineEdit()
        self.role_edit.setText(self.role)
        self.role_edit.setPlaceholderText("Job role...")
        self.role_edit.setStyleSheet(self.search_bar.styleSheet())
        self.role_edit.textChanged.connect(self.update_preview)
        self.role_edit.setMinimumWidth(300)
        
        details_layout.addWidget(role_label, 2, 0)
        details_layout.addWidget(self.role_edit, 2, 1, 1, 2)
        
        date_label = QLabel("Date:")
        date_label.setStyleSheet(form_label_style)
        date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.date_edit = QLineEdit()
        self.date_edit.setText(self.date)
        self.date_edit.setPlaceholderText("YYYYMMDD")
        self.date_edit.setStyleSheet(self.search_bar.styleSheet())
        self.date_edit.textChanged.connect(self.update_preview)
        self.date_edit.setMinimumWidth(300)
        
        details_layout.addWidget(date_label, 3, 0)
        details_layout.addWidget(self.date_edit, 3, 1, 1, 2)
        
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet(form_label_style)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        preview_label.setContentsMargins(0, 6, 0, 0)
        
        preview_container = QWidget()
        preview_container_layout = QVBoxLayout(preview_container)
        preview_container_layout.setContentsMargins(0, 0, 0, 0)
        preview_container_layout.setSpacing(4)
        
        self.output_path_label = QLabel()
        self.output_path_label.setWordWrap(True)
        self.output_path_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 13px;
                background-color: #2c2c2c;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        preview_container_layout.addWidget(self.output_path_label)
        
        self.pdf_path_label = QLabel()
        self.pdf_path_label.setWordWrap(True)
        self.pdf_path_label.setStyleSheet(self.output_path_label.styleSheet())
        preview_container_layout.addWidget(self.pdf_path_label)
        
        details_layout.addWidget(preview_label, 4, 0, Qt.AlignmentFlag.AlignTop)
        details_layout.addWidget(preview_container, 4, 1, 1, 2)
        
        content_layout.addWidget(details_group)
        
        button_bar = QWidget()
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(0, 16, 0, 0)
        button_layout.setSpacing(8)
        
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2c;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
        """)
        button_layout.addWidget(cancel_button)
        
        self.create_button = QPushButton("Create Resume")
        self.create_button.clicked.connect(self.create_resume)
        self.create_button.setEnabled(False)
        self.create_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #0098ff;
            }
            QPushButton:disabled {
                background-color: #2c2c2c;
                color: #808080;
            }
        """)
        button_layout.addWidget(self.create_button)
        
        content_layout.addWidget(button_bar)
        
        layout.addWidget(content)
        
        main_layout.addWidget(container)
        
        self.update_preview()
        
        self.search_bar.setFocus()

    def load_templates(self):
        """Load resume templates"""
        self.clear_templates()
        
        if not os.path.exists(self.templates_path):
            os.makedirs(self.templates_path, exist_ok=True)
            self.add_message_item("No templates found. Please add .tex files to templates directory.")
            return
            
        tex_files = []
        for root, _, files in os.walk(self.templates_path):
            for file in files:
                if file.endswith('.tex'):
                    tex_files.append(os.path.join(root, file))
        
        if not tex_files:
            self.add_message_item("No templates found. Please add .tex files to templates directory.")
            return
            
        for tex_file in tex_files:
            self.add_template_item(tex_file)

    def add_template_item(self, template_path: str, match_lines: List[Tuple[int, str]] = None):
        """Add a template item to the container"""
        item = TemplateItemWidget(template_path, match_lines)
        item.clicked.connect(self.handle_template_selected)
        item.focused.connect(self.handle_template_focused)
        
        self.template_layout.insertWidget(self.template_layout.count() - 1, item)
        self.template_items.append(item)
        
    def add_message_item(self, message: str):
        """Add a message item to the container"""
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 13px;
                padding: 20px;
            }
        """)
        
        self.template_layout.insertWidget(self.template_layout.count() - 1, message_label)
        
    def clear_templates(self):
        """Clear all template items"""
        self.template_items = []
        
        while self.template_layout.count() > 1:
            item = self.template_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
    def debounce_search(self, search_text: str):
        """Debounce search to prevent too many searches while typing"""
        self.current_search = search_text
        self.debounce_timer.start()
        
    def _perform_search(self):
        """Actual search function that gets called after debounce"""
        search_text = self.current_search
        self.filter_templates(search_text)

    def filter_templates(self, search_text: str):
        """Filter templates using ripgrep-like search"""
        if not search_text:
            self.load_templates()
            return
            
        self.clear_templates()
        
        try:
            loading_label = QLabel("Searching...")
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_label.setStyleSheet("""
                QLabel {
                    color: #cccccc;
                    font-size: 13px;
                    padding: 20px;
                }
            """)
            self.template_layout.insertWidget(self.template_layout.count() - 1, loading_label)
            
            QApplication.processEvents()
            
            matching_files = {}
            
            try:
                process = subprocess.run(
                    ["rg", "--follow", "--hidden", "--no-heading", "--with-filename", "--line-number", "--column", "--smart-case", "--no-ignore-vcs", "--no-ignore-global", "-t", "tex", search_text, self.templates_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if process.returncode == 0 and process.stdout:
                    for line in process.stdout.splitlines():
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            file_path = parts[0]
                            line_num = int(parts[1])
                            line_text = parts[2]
                            
                            if file_path not in matching_files:
                                matching_files[file_path] = []
                                
                            matching_files[file_path].append((line_num, line_text))
                
            except FileNotFoundError:
                logger.warning("Ripgrep not found, using fallback search method")
                
                for root, _, files in os.walk(self.templates_path):
                    for file in files:
                        if file.endswith('.tex'):
                            full_path = os.path.join(root, file)
                            
                            if search_text.lower() in file.lower():
                                matching_files[full_path] = []
                                continue
                                
                            try:
                                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read().lower()
                                    if search_text.lower() in content:
                                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f2:
                                            lines = f2.readlines()
                                            matches = []
                                            for i, line in enumerate(lines):
                                                if search_text.lower() in line.lower():
                                                    matches.append((i + 1, line))
                                                    if len(matches) >= 3:
                                                        break
                                        
                                        matching_files[full_path] = matches
                            # pylint: disable=broad-exception-caught
                            except Exception as e:
                                logger.error("Error reading file %s: %s", full_path, str(e))
            
            if self.template_layout.count() > 1:
                item = self.template_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            for file_path, matches in matching_files.items():
                self.add_template_item(file_path, matches)
                
            if not matching_files:
                self.add_message_item(f"No matches found for '{search_text}'")
                
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Error filtering templates: %s", str(e))
            self.add_message_item(f"Error searching templates: {str(e)}")

    def handle_template_focused(self, template_path: str):
        """Handle when a template is focused/hovered"""
        match_lines = []
        for item in self.template_items:
            if item.template_path == template_path:
                match_lines = item.match_lines
                break
                
        self.preview_panel.load_file_preview(template_path, match_lines)

    def handle_template_selected(self, template_path: str):
        """Handle template selection"""
        self.selected_template = template_path
        self.selection_label.setText(f"Selected: {os.path.basename(template_path)}")
        
        self.create_button.setEnabled(self.is_form_valid())
        
        for item in self.template_items:
            item.set_selected(item.template_path == template_path)
            
        self.handle_template_focused(template_path)

    def update_preview(self):
        """Update the preview label based on current input"""
        self.company = self.company_edit.text()
        self.role = self.role_edit.text()
        self.date = self.date_edit.text()
        
        if not self.company and not self.role:
            self.output_path_label.setText("Please enter company and role")
            self.pdf_path_label.setText("")
            self.create_button.setEnabled(False)
            self.create_button.setText("Create Resume")
            return
            
        company = re.sub(r'[^a-zA-Z0-9]', '-', self.company.lower().strip())
        role = re.sub(r'[^a-zA-Z0-9]', '-', self.role.lower().strip())
        
        date_valid = re.match(r'^\d{8}$', self.date) is not None
        if not date_valid:
            self.date = datetime.datetime.now().strftime("%Y%m%d")
            self.date_edit.setText(self.date)
        
        group = self.group_selector.current_text.lower().replace(' ', '_')
        dir_name = f"{company}_{role}_{self.date}"
        file_name = f"resume_{company}_{role}_{self.date}"
        
        output_dir = os.path.join(self.output_path, group, dir_name)
        tex_path = os.path.join(output_dir, f"{file_name}.tex")
        pdf_path = os.path.join(output_dir, f"{file_name}.pdf")
        
        self.output_path_label.setText(f"Resume will be saved as:\n{tex_path}")
        self.pdf_path_label.setText(f"PDF will be generated as:\n{pdf_path}")
        
        form_valid = self.is_form_valid()
        pdf_exists = os.path.exists(pdf_path)
        
        if pdf_exists:
            self.create_button.setEnabled(False)
            self.create_button.setText("PDF Already Exists")
            logger.info("[Signal] Emitting resume_created signal for existing PDF: %s", pdf_path)
            self.resume_created.emit(pdf_path)
        else:
            self.create_button.setEnabled(form_valid)
            self.create_button.setText("Create Resume")

    def is_form_valid(self) -> bool:
        """Check if the form is valid for resume creation"""
        return (
            self.selected_template is not None and 
            self.company.strip() != "" and 
            self.role.strip() != "" and 
            re.match(r'^\d{8}$', self.date) is not None
        )

    def create_resume(self):
        """Create resume from selected template"""
        if not self.is_form_valid():
            return
            
        try:
            company = re.sub(r'[^a-zA-Z0-9]', '-', self.company.lower().strip())
            role = re.sub(r'[^a-zA-Z0-9]', '-', self.role.lower().strip())
            group = self.group_selector.current_text.lower().replace(' ', '_')
            
            dir_name = f"{company}_{role}_{self.date}"
            file_name = f"resume_{company}_{role}_{self.date}"
            
            output_dir = os.path.join(self.output_path, group, dir_name)
            os.makedirs(output_dir, exist_ok=True)
            
            tex_path = os.path.join(output_dir, f"{file_name}.tex")
            pdf_path = os.path.join(output_dir, f"{file_name}.pdf")
            
            if os.path.exists(pdf_path):
                QMessageBox.warning(
                    self,
                    "PDF Already Exists",
                    f"A PDF already exists at:\n{pdf_path}\nPlease use a different name or date."
                )
                self.create_button.setEnabled(False)
                self.create_button.setText("PDF Already Exists")
                logger.info("[Signal] Emitting resume_created signal for existing PDF: %s", pdf_path)
                self.resume_created.emit(pdf_path)
                return
            
            shutil.copy2(self.selected_template, tex_path)
            logger.info("Copied template from %s to %s", self.selected_template, tex_path)
            
            logger.info("Running pdflatex on %s", tex_path)
            
            original_dir = os.getcwd()
            os.chdir(output_dir)
            
            try:
                for _ in range(2):
                    process = subprocess.run(
                        ["pdflatex", "-interaction=nonstopmode", f"{file_name}.tex"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    if process.returncode != 0:
                        logger.error("pdflatex error: %s", process.stderr)
                        # pylint: disable=broad-exception-raised
                        raise Exception(f"PDF generation failed. Error: {process.stderr}")
                
                if not os.path.exists(pdf_path):
                    # pylint: disable=broad-exception-raised
                    raise Exception("PDF file was not created")
                    
                logger.info("Successfully created PDF: %s", pdf_path)
                
                os.chdir(original_dir)
                
                logger.info("[Signal] Emitting resume_created signal for newly created PDF: %s", pdf_path)
                self.resume_created.emit(pdf_path)
                
                self.create_button.setEnabled(False)
                self.create_button.setText("PDF Already Exists")
                
                QMessageBox.information(
                    self,
                    "Resume Created",
                    f"Resume PDF successfully generated at:\n{pdf_path}"
                )
                
                self.accept()
                
            finally:
                os.chdir(original_dir)
                
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Error creating resume: %s", str(e))
            QMessageBox.critical(
                self,
                "Error Creating Resume",
                f"Failed to create resume: {str(e)}"
            )
