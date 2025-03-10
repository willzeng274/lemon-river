"""
Custom file explorer dialog with VSCode-like tree view
"""

import os
import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QLineEdit,
    QWidget,
)
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


# pylint: disable=invalid-name
class CustomFileExplorer(QDialog):
    """Custom file explorer dialog with VSCode-like tree view"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_path = os.path.expanduser("~/Desktop/resumes")
        self.selected_file = None
        self.all_items = []
        self.setup_ui()
        self.load_directory()

    def setup_ui(self):
        """Setup the file explorer UI"""
        self.setWindowTitle("Browse Files")
        self.setMinimumSize(400, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search files...")
        self.search_bar.textChanged.connect(self.filter_items)
        self.search_bar.setStyleSheet(
            """
            QLineEdit {
                background-color: #2c2c2c;
                color: #ffffff;
                border: none;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                background-color: #3c3c3c;
                outline: none;
            }
        """
        )
        layout.addWidget(self.search_bar)

        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setIndentation(12)
        self.file_tree.setAnimated(True)
        self.file_tree.itemExpanded.connect(self.handle_item_expanded)
        self.file_tree.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.file_tree.itemClicked.connect(self.handle_item_clicked)
        self.file_tree.setStyleSheet(
            """
            QTreeWidget {
                background-color: #1c1c1c;
                border: none;
            }
            QTreeWidget:focus {
                border: 1px solid #007acc;
            }
            QTreeWidget::item {
                color: #ffffff;
                padding: 4px;
                padding-left: 0px;
                border-radius: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #2c2c2c;
            }
            QTreeWidget::item:selected {
                background-color: #37373d;
            }
            QTreeWidget::item:selected:!active {
                background-color: #37373d;
            }
            QTreeWidget::item:selected:active {
                background-color: #094771;
            }
            QTreeWidget::branch {
                background: transparent;
            }
        """
        )
        layout.addWidget(self.file_tree)

        button_bar = QWidget()
        button_bar.setStyleSheet(
            """
            QWidget {
                background-color: #2c2c2c;
                border-top: 1px solid #3c3c3c;
            }
        """
        )
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(8, 8, 8, 8)
        button_layout.setSpacing(8)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cancel_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2c2c2c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
        """
        )

        select_button = QPushButton("Select")
        select_button.clicked.connect(self.handle_select)
        select_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        select_button.setStyleSheet(cancel_button.styleSheet())

        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(select_button)
        layout.addWidget(button_bar)

        self.setTabOrder(self.search_bar, self.file_tree)
        self.setTabOrder(self.file_tree, self.search_bar)

        self.installEventFilter(self)
        self.search_bar.installEventFilter(self)
        self.file_tree.installEventFilter(self)

        self.file_tree.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def load_directory(self):
        """Load the root directory"""
        self.file_tree.clear()
        root_item = self.create_tree_item(self.root_path, is_root=True)
        self.file_tree.addTopLevelItem(root_item)
        root_item.setExpanded(True)
        self.search_bar.setFocus()

    def create_tree_item(self, path: str, is_root: bool = False) -> QTreeWidgetItem:
        """Create a tree item for a file or directory"""
        name = os.path.basename(path) or path
        item = QTreeWidgetItem()
        item.setData(0, Qt.ItemDataRole.UserRole, path)

        if os.path.isdir(path):
            if is_root:
                item.setText(0, "  📂 resumes")
            else:
                item.setText(0, f"  📁 {name}")
            if self.has_valid_children(path):
                self.load_children(item)
        else:
            ext = os.path.splitext(name)[1].lower()
            if ext == ".pdf":
                item.setText(0, f"  📕 {name}")
            elif ext == ".tex":
                item.setText(0, f"  📝 {name}")
            elif ext == ".txt":
                item.setText(0, f"  📄 {name}")

        return item

    def has_valid_children(self, path: str) -> bool:
        """Check if directory has any valid children"""
        try:
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    return True
                ext = os.path.splitext(item)[1].lower()
                if ext in [".pdf", ".tex", ".txt"]:
                    return True
        # pylint: disable=broad-exception-caught
        except Exception:
            pass
        return False

    def load_children(self, item: QTreeWidgetItem):
        """Load children for a directory item"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not os.path.isdir(path):
            return

        item.takeChildren()

        try:
            dirs = []
            files = []

            for name in os.listdir(path):
                full_path = os.path.join(path, name)
                mod_time = os.path.getmtime(full_path)

                if os.path.isdir(full_path):
                    dirs.append((mod_time, full_path))
                else:
                    ext = os.path.splitext(name)[1].lower()
                    if ext in [".pdf", ".tex", ".txt"]:
                        files.append((mod_time, full_path))

            dirs.sort(key=lambda x: x[0], reverse=True)
            files.sort(key=lambda x: x[0], reverse=True)

            for _, dir_path in dirs:
                child = self.create_tree_item(dir_path)
                item.addChild(child)

            for _, file_path in files:
                child = self.create_tree_item(file_path)
                item.addChild(child)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            error_item = QTreeWidgetItem(["Error: " + str(e)])
            item.addChild(error_item)

    def handle_item_expanded(self, item: QTreeWidgetItem):
        """Handle item expansion"""
        self.load_children(item)

    def handle_item_clicked(self, item):
        """Handle item click to ensure proper selection"""
        self.file_tree.setFocus()
        self.file_tree.setCurrentItem(item)

    def handle_select(self):
        """Handle select button click"""
        current_item = self.file_tree.currentItem()
        if current_item:
            path = current_item.data(0, Qt.ItemDataRole.UserRole)
            if os.path.isfile(path):
                self.selected_file = path
                self.accept()

    def filter_items(self, search_text: str):
        """Filter items based on fuzzy search"""
        search_text = search_text.lower()

        def process_item(item):
            """Process an item and its children recursively"""
            try:
                if not item:
                    return

                item_text = item.text(0).lower()
                # item_path = item.data(0, Qt.ItemDataRole.UserRole)

                should_show = bool(
                    search_text == "" or self.fuzzy_match(search_text, item_text)
                )

                child_visible = False
                for child_idx in range(item.childCount()):
                    child = item.child(child_idx)
                    if process_item(child):
                        child_visible = True

                is_visible = should_show or child_visible
                item.setHidden(not is_visible)

                if is_visible and item.childCount() > 0 and search_text:
                    item.setExpanded(True)

                return is_visible

            except RuntimeError:
                return False

        root = self.file_tree.topLevelItem(0)
        if root:
            process_item(root)

    def fuzzy_match(self, pattern: str, text: str) -> bool:
        """Implement fuzzy matching similar to fzf"""
        pattern_idx = 0
        for char in text:
            if pattern_idx < len(pattern) and pattern[pattern_idx] == char:
                pattern_idx += 1
        return pattern_idx == len(pattern)

    def eventFilter(self, obj, event):
        """Handle events for all widgets"""
        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.setFocus()
                return True
            elif event.key() == Qt.Key.Key_Tab:
                if obj == self.search_bar:
                    self.file_tree.setFocus()
                    if self.file_tree.topLevelItemCount() > 0:
                        first_visible_item = self.find_first_visible_item(
                            self.file_tree.topLevelItem(0)
                        )
                        if first_visible_item:
                            self.file_tree.setCurrentItem(first_visible_item)
                    return True
                elif (
                    obj == self.file_tree
                    and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
                ):
                    self.search_bar.setFocus()
                    return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if obj == self.file_tree:
                    current_item = self.file_tree.currentItem()
                    if current_item:
                        path = current_item.data(0, Qt.ItemDataRole.UserRole)
                        if os.path.isfile(path):
                            self.selected_file = path
                            self.accept()
                        elif os.path.isdir(path):
                            current_item.setExpanded(not current_item.isExpanded())
                        return True
            elif obj == self.file_tree:
                if event.key() == Qt.Key.Key_J:
                    current_item = self.file_tree.currentItem()
                    if current_item:
                        next_item = self.get_next_visible_item(current_item)
                        if next_item:
                            self.file_tree.setCurrentItem(next_item)
                    return True
                elif event.key() == Qt.Key.Key_K:
                    current_item = self.file_tree.currentItem()
                    if current_item:
                        prev_item = self.get_previous_visible_item(current_item)
                        if prev_item:
                            self.file_tree.setCurrentItem(prev_item)
                    return True
        return super().eventFilter(obj, event)

    def get_next_visible_item(self, current_item):
        """Get the next visible item in the tree"""
        if current_item.isExpanded() and current_item.childCount() > 0:
            for i in range(current_item.childCount()):
                child = current_item.child(i)
                if not child.isHidden():
                    return child

        while current_item:
            parent = current_item.parent() or self.file_tree.invisibleRootItem()
            current_index = parent.indexOfChild(current_item)

            for i in range(current_index + 1, parent.childCount()):
                sibling = parent.child(i)
                if not sibling.isHidden():
                    return sibling

            current_item = (
                parent if parent != self.file_tree.invisibleRootItem() else None
            )

        return None

    def get_previous_visible_item(self, current_item):
        """Get the previous visible item in the tree"""
        parent = current_item.parent() or self.file_tree.invisibleRootItem()
        current_index = parent.indexOfChild(current_item)

        if current_index > 0:
            sibling = parent.child(current_index - 1)
            while sibling and sibling.isHidden():
                current_index -= 1
                if current_index <= 0:
                    break
                sibling = parent.child(current_index - 1)

            if sibling and not sibling.isHidden():
                while sibling.isExpanded() and sibling.childCount() > 0:
                    last_visible_child = None
                    for i in range(sibling.childCount() - 1, -1, -1):
                        child = sibling.child(i)
                        if not child.isHidden():
                            last_visible_child = child
                            break
                    if last_visible_child:
                        sibling = last_visible_child
                    else:
                        break
                return sibling

        if parent != self.file_tree.invisibleRootItem():
            return (
                parent
                if not parent.isHidden()
                else self.get_previous_visible_item(parent)
            )

        return None

    def find_first_visible_item(self, item):
        """Find the first visible item in the tree"""
        if not item.isHidden():
            return item

        for i in range(item.childCount()):
            child = item.child(i)
            result = self.find_first_visible_item(child)
            if result:
                return result
        return None

    def focusInEvent(self, event):
        """Handle focus in event"""
        super().focusInEvent(event)
        if not self.search_bar.hasFocus() and not self.file_tree.hasFocus():
            self.search_bar.setFocus()

    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        self.search_bar.setFocus()
