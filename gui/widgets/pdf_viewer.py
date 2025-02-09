"""
PDF Viewer Widget
"""

import logging

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSizePolicy, QStackedWidget
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument

logger = logging.getLogger(__name__)


class PDFViewer(QScrollArea):
    """Widget for displaying PDF files"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_page = 0
        self.doc = None
        self.zoom_factor = 1.0
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def setup_ui(self):
        """Setup the PDF viewer UI"""
        self.setWidgetResizable(True)
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #262626;
            }
            QScrollBar:vertical {
                border: none;
                background: #2c2c2c;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #404040;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a4a4a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background: #2c2c2c;
                height: 10px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background: #404040;
                border-radius: 5px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #4a4a4a;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
                border: none;
                background: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        content_container = QWidget()
        content_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_container.setStyleSheet("""
            QWidget {
                background-color: #262626;
            }
        """)
        
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.content = QLabel("No PDF loaded")
        self.content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.content.setStyleSheet("""
            QLabel {
                color: #8e8e8e;
                font-size: 14px;
                background-color: #262626;
            }
        """)
        content_layout.addWidget(self.content)

        pdf_container = QWidget()
        pdf_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        pdf_layout = QVBoxLayout(pdf_container)
        pdf_layout.setContentsMargins(0, 0, 0, 0)
        pdf_layout.setSpacing(0)
        
        self.pdf_view = QPdfView(pdf_container)
        self.pdf_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pdf_view.setStyleSheet("""
            QPdfView {
                background-color: #262626;
                border: none;
            }
        """)
        self.pdf_document = QPdfDocument(self)
        self.pdf_view.setDocument(self.pdf_document)

        self.pdf_view.setPageMode(QPdfView.PageMode.SinglePage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        pdf_layout.addWidget(self.pdf_view)

        self.stack.addWidget(content_container)
        self.stack.addWidget(pdf_container)

        self.layout.addWidget(self.stack)

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(8, 8, 8, 8)
        controls_layout.setSpacing(8)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(4)

        button_style = """
            QPushButton {
                background-color: #2c2c2c;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
                border-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
            QPushButton:disabled {
                color: #666666;
                border-color: #333333;
                background-color: #2c2c2c;
            }
        """

        self.prev_btn = QPushButton("←")
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self.previous_page)
        self.prev_btn.setStyleSheet(button_style)
        self.prev_btn.setFixedWidth(40)

        self.page_label = QLabel("Page 0 of 0")
        self.page_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                padding: 0 12px;
                min-width: 80px;
            }
        """)
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_btn = QPushButton("→")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setStyleSheet(button_style)
        self.next_btn.setFixedWidth(40)

        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_btn)

        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(4)

        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_out_btn.setStyleSheet(button_style)
        self.zoom_out_btn.setFixedWidth(40)

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_in_btn.setStyleSheet(button_style)
        self.zoom_in_btn.setFixedWidth(40)

        self.fit_btn = QPushButton("Fit")
        self.fit_btn.clicked.connect(self.fit_to_height)
        self.fit_btn.setStyleSheet(button_style)
        self.fit_btn.setFixedWidth(60)

        zoom_layout.addWidget(self.zoom_out_btn)
        zoom_layout.addWidget(self.zoom_in_btn)
        zoom_layout.addWidget(self.fit_btn)

        controls_layout.addLayout(nav_layout)
        controls_layout.addStretch()
        controls_layout.addLayout(zoom_layout)

        controls_container = QWidget()
        controls_container.setStyleSheet("""
            QWidget {
                background-color: #262626;
                border-top: 1px solid #333333;
            }
        """)
        controls_container.setLayout(controls_layout)

        self.layout.addWidget(controls_container)
        self.setWidget(container)

    def load_pdf(self, path: str):
        """Load and display a PDF file"""
        try:
            if not path:
                self.show_message("No PDF loaded")
                return

            self.pdf_document.load(path)
            self.current_page = 0
            self.update_navigation()
            
            if self.pdf_document.pageCount() > 0:
                self.show_pdf()
                logger.info("Automatically fitting to height")
                self.fit_to_height()
            else:
                self.show_message("Empty PDF document")
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Error loading PDF: %s", str(e))
            self.show_message(f"Error loading PDF: {str(e)}")
            self.pdf_document.close()

    def show_message(self, message: str):
        """Show a message instead of PDF"""
        self.content.setText(message)
        self.stack.setCurrentIndex(0)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.zoom_in_btn.setEnabled(False)
        self.zoom_out_btn.setEnabled(False)
        self.fit_btn.setEnabled(False)
        self.page_label.setText("No PDF loaded")

    def show_pdf(self):
        """Show the PDF viewer"""
        self.stack.setCurrentIndex(1)
        self.zoom_in_btn.setEnabled(True)
        self.zoom_out_btn.setEnabled(True)
        self.fit_btn.setEnabled(True)
        self.update_navigation()

    def update_navigation(self):
        """Update navigation buttons and page label"""
        page_count = self.pdf_document.pageCount()
        current_page = self.pdf_view.pageNavigator().currentPage()
        
        self.prev_btn.setEnabled(current_page > 0)
        self.next_btn.setEnabled(current_page < page_count - 1)
        
        if page_count > 0:
            self.page_label.setText(f"Page {current_page + 1} of {page_count}")
        else:
            self.page_label.setText("No PDF loaded")

    def next_page(self):
        """Go to next page"""
        nav = self.pdf_view.pageNavigator()
        if nav.currentPage() < self.pdf_document.pageCount() - 1:
            nav.jump(nav.currentPage() + 1, QPointF())
            self.update_navigation()

    def previous_page(self):
        """Go to previous page"""
        nav = self.pdf_view.pageNavigator()
        if nav.currentPage() > 0:
            nav.jump(nav.currentPage() - 1, QPointF())
            self.update_navigation()

    def zoom_in(self):
        """Zoom in the PDF view"""
        current_zoom = self.pdf_view.zoomFactor()
        self.pdf_view.setZoomFactor(current_zoom * 1.2)

    def zoom_out(self):
        """Zoom out the PDF view"""
        current_zoom = self.pdf_view.zoomFactor()
        self.pdf_view.setZoomFactor(current_zoom / 1.2)

    def fit_to_height(self):
        """Fit the PDF page to the view height"""
        if not self.pdf_document.pageCount():
            return

        page_size = self.pdf_document.pagePointSize(self.pdf_view.pageNavigator().currentPage())
        if not page_size.isValid():
            return

        view_height = self.pdf_view.height() - 20
        zoom_factor = view_height / page_size.height()

        self.pdf_view.setZoomFactor(zoom_factor)
