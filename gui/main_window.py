"""
Main window for the application
"""

import os
import logging
import threading
from pynput import keyboard

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication, QDialog, QLineEdit, QTabWidget
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QObject

from gui.widgets import DraggableWindow, CustomFileExplorer
from gui.tabs.applications.tab import ApplicationsTab
from gui.tabs.qa.tab import QATab
from gui.dataclasses import Application, ApplicationMetadata, ApplicationStatus
from db.adapter import DatabaseAdapter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GlobalHotkeyListener(QObject):
    """Global hotkey listener using pynput"""
    toggle_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_keys = set()
        self.listener = None
        self.running = True

        self.thread = threading.Thread(target=self._start_listener, daemon=True)
        self.thread.start()
        logger.info("[Hotkey] Started listener in thread %s", self.thread.name)

    def _start_listener(self):
        """Start the keyboard listener"""
        try:
            logger.info("[Hotkey] Starting keyboard listener...")
            with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
                self.listener = listener
                logger.info("[Hotkey] Keyboard listener started successfully")
                listener.join()
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("[Hotkey] Error in keyboard listener: %s", str(e))
            import traceback
            logger.error(traceback.format_exc())

    def _on_press(self, key):
        """Handle key press"""
        try:
            if hasattr(key, 'char'):
                key_val = key.char.lower() if key.char else None
                if key_val:
                    self.current_keys.add(key_val)
            else:
                self.current_keys.add(key)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("[Hotkey] Error handling key press: %s", str(e))
            import traceback
            logger.error(traceback.format_exc())
        return self.running

    def _on_release(self, key):
        """Handle key release"""
        try:
            if hasattr(key, 'char') and key.char == '¬':
                self.toggle_signal.emit()
            elif hasattr(key, 'vk') and key.vk == keyboard.Key.alt_l:
                self.toggle_signal.emit()

            if hasattr(key, 'char'):
                key_val = key.char.lower() if key.char else None
                if key_val:
                    self.current_keys.discard(key_val)
            else:
                self.current_keys.discard(key)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("[Hotkey] Error handling key release: %s", str(e))
            import traceback
            logger.error(traceback.format_exc())
        return self.running

    def stop(self):
        """Stop the listener"""
        logger.info("[Hotkey] Stopping listener...")
        self.running = False
        if self.listener:
            self.listener.stop()
        self.thread.join(timeout=1.0)
        logger.info("[Hotkey] Listener stopped")


class ApplicationUpdateSignals(QObject):
    """Centralized signals for application updates"""
    field_updated = pyqtSignal(int, str, object)
    
    qa_updated = pyqtSignal(int, int, str, str)  # app_id, question_id, question, answer
    qa_added = pyqtSignal(int, int, str, str)  # app_id, question_id, question, answer
    qa_deleted = pyqtSignal(int, int)  # app_id, question_id
    
    qa_table_update = pyqtSignal(int, int, str, str)  # app_id, question_id, question, answer
    qa_table_delete = pyqtSignal(int, int)  # app_id, question_id
    
    application_deleted = pyqtSignal(int)
    application_added = pyqtSignal(object)  # Application object
    
    resume_updated = pyqtSignal(int, str) # app_id, resume_path
    
    def emit_field_update(self, app_id: int, field_name: str, new_value: object):
        """Emit signal for field update"""
        logger.debug("Emitting field_updated for app %d, field %s", app_id, field_name)
        self.field_updated.emit(app_id, field_name, new_value)
        
    def emit_qa_update(self, app_id: int, question_id: int, question: str, answer: str):
        """Emit signal for question update"""
        logger.debug("Emitting qa_updated for app %d, question ID %d", app_id, question_id)
        self.qa_updated.emit(app_id, question_id, question, answer)
        
    def emit_qa_add(self, app_id: int, question_id: int, question: str, answer: str):
        """Emit signal for question addition"""
        logger.debug("Emitting qa_added for app %d, question ID %d", app_id, question_id)
        self.qa_added.emit(app_id, question_id, question, answer)
        
    def emit_qa_delete(self, app_id: int, question_id: int):
        """Emit signal for question deletion"""
        logger.debug("Emitting qa_deleted for app %d, question ID %d", app_id, question_id)
        self.qa_deleted.emit(app_id, question_id)
        
    def emit_qa_table_update(self, app_id: int, question_id: int):
        """Emit signal for question update from QA table"""
        logger.debug("Emitting qa_table_update for app %d, question ID %d", app_id, question_id)
        self.qa_table_update.emit(app_id, question_id)
        
    def emit_qa_table_delete(self, app_id: int, question_id: int):
        """Emit signal for question deletion from QA table"""
        logger.debug("Emitting qa_table_delete for app %d, question ID %d", app_id, question_id)
        self.qa_table_delete.emit(app_id, question_id)
        
    def emit_application_delete(self, app_id: int):
        """Emit signal for application deletion"""
        logger.debug("Emitting application_deleted for app %d", app_id)
        self.application_deleted.emit(app_id)
        
    def emit_application_add(self, application: object):
        """Emit signal for application addition"""
        logger.debug("Emitting application_added")
        self.application_added.emit(application)
        
    def emit_resume_update(self, app_id: int, resume_path: str):
        """Emit signal for resume update"""
        logger.debug("Emitting resume_updated for app %d", app_id)
        self.resume_updated.emit(app_id, resume_path)


class MainWindow(DraggableWindow):
    """
    Main window for the application
    """

    def __init__(self):
        super().__init__()
        self.applications = []
        self.db = DatabaseAdapter("db/applications.db")

        self.update_signals = ApplicationUpdateSignals()
        
        self.focused_opacity = 1.0
        self.unfocused_opacity = 0.8
        
        self.setup_ui()
        self.setup_global_hotkey()
        self.center_window()
        self.setup_update_handlers()
        self.load_applications()

    def setup_global_hotkey(self):
        """Setup global hotkey listener"""
        self.hotkey_listener = GlobalHotkeyListener()
        self.hotkey_listener.toggle_signal.connect(self.toggle_visibility)
        logger.info("[Hotkey] Global hotkey handler initialized")

    def setup_ui(self):
        """Setup the UI for the main window"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #1c1c1c;
                margin-top: -1px;
            }
            QTabBar {
                background: transparent;
            }
            QTabWidget::tab-bar {
                alignment: center;
                background: transparent;
                margin-bottom: 16px;
            }
            QTabBar {
                background: #2c2c2c;
                border-radius: 8px;
            }
            QTabBar::tab {
                padding: 6px 20px;
                min-width: 100px;
                font-size: 13px;
                margin-top: 4px;
                margin-bottom: 4px;
                border-radius: 6px;
                color: #8e8e8e;
                background: transparent;
                font-weight: 500;
                border: none;
            }
            QTabBar::tab:!first {
                margin-left: 1px;
            }
            QTabBar::tab:first {
                margin-left: 4px;
            }
            QTabBar::tab:last {
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                color: #ffffff;
                background: #3c3c3c;
            }
            QTabBar::tab:!selected {
                background: transparent;
            }
            QTabWidget::pane {
                border: none;
                padding-top: 16px;
            }
        """)

        self.applications_tab = ApplicationsTab()
        self.qa_tab = QATab()

        self.tab_widget.addTab(self.applications_tab, "Applications (1)")
        self.tab_widget.addTab(self.qa_tab, "Questions (2)")

        layout.addWidget(self.tab_widget)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #1c1c1c;
            }
            QWidget {
                background-color: #1c1c1c;
            }
        """)

        self.setMinimumSize(1400, 900)

        self.applications_tab.installEventFilter(self)
        self.qa_tab.installEventFilter(self)

    def center_window(self):
        """Center the window on the screen"""
        screen = self.screen().geometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)

    def load_applications(self):
        """Load all applications from the database"""
        self.applications = self.db.get_all_applications()
        self.applications.sort(key=lambda x: x.metadata.created_at, reverse=True)

        for application in self.applications:
            app_id = getattr(application, 'id', None)
            if app_id is None:
                logger.error("Application from database has no ID")
                continue
            logger.info("Loading application %d", app_id)
            self.applications_tab.table.add_application(application)
        
        self.qa_tab.qa_table.update_qa_data(self.applications)
        self.update_application_selector()

    def add_application(self):
        """Add a new application to the table and database"""
        application = Application(
            metadata=ApplicationMetadata(
                url="",
                role="New Role",
                company="New Company",
                location="",
                duration="",
                description="",
                questions=[],
                notes="",
                check_url="",
            ),
            status=ApplicationStatus.APPLYING
        )

        app_id = self.db.add_application(application)
        if app_id:
            logger.info("Created new application with ID %d", app_id)
            setattr(application, 'id', app_id)
            self.applications.append(application)
            self.applications_tab.table.add_application(application)
            self.update_application_selector()

    def delete_application(self, row: int):
        """Delete an application from the database and table"""
        app_id = self.applications_tab.table.application_ids.get(row)
        if app_id is None:
            logger.error("No application ID found for row %d", row)
            return

        logger.info("Deleting application %d from row %d", app_id, row)
        if self.db.delete_application(app_id):
            for i, app in enumerate(self.applications):
                if getattr(app, 'id', None) == app_id:
                    self.applications.pop(i)
                    break
            self.applications_tab.table.delete_row(row)
            self.update_application_selector()
            logger.info("Successfully deleted application %d", app_id)
        else:
            logger.error("Failed to delete application %d", app_id)

    def toggle_visibility(self):
        """Toggle the window visibility"""
        try:
            if self.isVisible():
                self.hide()
            else:
                last_pos = self.pos()
                self.show()
                self.raise_()
                self.activateWindow()
                if last_pos != QPoint(0, 0):
                    self.move(last_pos)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("[Hotkey] Error toggling visibility: %s", str(e))

    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'hotkey_listener'):
            self.hotkey_listener.stop()
        if hasattr(self, 'db'):
            self.db.close()
        super().closeEvent(event)

    def refresh_applications(self):
        """Refresh the applications list from the database"""
        logger.info("Refreshing applications list")
        
        self.applications_tab.table.setRowCount(0)
        self.load_applications()

    def browse_file(self, line_edit):
        """Open file browser dialog and set the selected path"""
        dialog = CustomFileExplorer(self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_file:
            line_edit.setText(dialog.selected_file)

    def delete_qa(self, row: int):
        """Delete a Q&A entry from the application"""
        app_id = self.qa_tab.qa_table.qa_ids.get(row)
        if app_id is None:
            logger.error("No application ID found for row %d", row)
            return

        application = self.db.get_application(app_id)
        if not application:
            logger.error("Application not found for ID %d", app_id)
            return

        question_widget = self.qa_tab.qa_table.cellWidget(row, 3)
        if not question_widget:
            logger.error("No question widget found for row %d", row)
            return

        question_text = question_widget.findChild(QLineEdit).text()
        
        if application.metadata.questions:
            for i, (q, _) in enumerate(application.metadata.questions):
                if q == question_text:
                    application.metadata.questions.pop(i)
                    break

        if self.db.update_application(app_id, application):
            logger.info("Deleted Q&A from application %d", app_id)
            self.qa_tab.qa_table.delete_row(row)
        else:
            logger.error("Failed to delete Q&A from application %d", app_id)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        key = event.key()
        focused_widget = QApplication.focusWidget()

        if key == Qt.Key.Key_Escape and focused_widget:
            focused_widget.clearFocus()
            return

        if key == Qt.Key.Key_Tab and focused_widget:
            current_tab = self.tab_widget.currentIndex()
            if current_tab == 0:
                if isinstance(focused_widget, QLineEdit):
                    return super().keyPressEvent(event)
            return

        if key == Qt.Key.Key_1:
            self.tab_widget.setCurrentIndex(0)
            return
        elif key == Qt.Key.Key_2:
            self.tab_widget.setCurrentIndex(1)
            return
        elif key == Qt.Key.Key_3:
            self.tab_widget.setCurrentIndex(2)
            return
        elif key == Qt.Key.Key_4:
            self.tab_widget.setCurrentIndex(3)
            return

        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:
            if key == Qt.Key.Key_A:
                self.add_application()
                return
            elif key == Qt.Key.Key_F:
                self.applications_tab.search_bar.setFocus()
                return

        elif current_tab == 1:
            if key == Qt.Key.Key_F:
                self.qa_tab.search_bar.setFocus()
                return

        super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        """Global event filter to handle key events from child widgets"""
        if event.type() == event.Type.KeyPress:
            if obj.event(event):
                return True
            self.keyPressEvent(event)
            return True
        return super().eventFilter(obj, event)

    def setup_update_handlers(self):
        """Setup handlers for update signals"""
        signals = self.update_signals
        
        signals.field_updated.connect(self.applications_tab.handle_field_update)
        signals.field_updated.connect(self.qa_tab.handle_field_update)
        
        signals.qa_updated.connect(self.qa_tab.handle_qa_update)
        signals.qa_added.connect(self.qa_tab.handle_qa_add)
        signals.qa_deleted.connect(self.qa_tab.handle_qa_delete)
        
        signals.application_deleted.connect(self.applications_tab.handle_application_delete)
        signals.application_deleted.connect(self.qa_tab.handle_application_delete)
        
        signals.application_added.connect(self.applications_tab.handle_application_add)

    def emit_field_update(self, app_id: int, field_name: str, new_value: object):
        """Emit a field update signal"""
        self.update_signals.field_updated.emit(app_id, field_name, new_value)

    def emit_qa_update(self, app_id: int, question_id: int, question: str, answer: str):
        """Emit a Q&A update signal from workspace to QA table"""
        self.update_signals.qa_updated.emit(app_id, question_id, question, answer)

    def emit_qa_delete(self, app_id: int, question_id: int):
        """Emit a Q&A deletion signal from workspace to QA table"""
        self.update_signals.qa_deleted.emit(app_id, question_id)

    def emit_application_delete(self, app_id: int):
        """Emit an application deletion signal"""
        self.update_signals.application_deleted.emit(app_id)

    def emit_application_add(self, application: object):
        """Emit an application addition signal"""
        self.update_signals.application_added.emit(application)

    def emit_resume_update(self, app_id: int, resume_path: str):
        """Emit a resume update signal"""
        self.update_signals.resume_updated.emit(app_id, resume_path)

    def emit_qa_table_update(self, app_id: int, question_id: int, question: str, answer: str):
        """Emit a Q&A update signal from QA table to workspace"""
        self.update_signals.qa_table_update.emit(app_id, question_id, question, answer)

    def emit_qa_add(self, app_id: int, question_id: int, question: str, answer: str):
        """Emit a Q&A add signal from workspace to QA table"""
        self.update_signals.qa_added.emit(app_id, question_id, question, answer)
        
    def emit_qa_table_delete(self, app_id: int, question_id: int):
        """Emit a Q&A delete signal from QA table to workspace"""
        self.update_signals.qa_table_delete.emit(app_id, question_id)


if __name__ == "__main__":
    app_ = QApplication([])
    window = MainWindow()
    window.show()
    app_.exec()
