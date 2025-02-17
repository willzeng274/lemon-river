"""
Export most of the widgets for easy importing
"""

from .base import DraggableWindow
from .file_explorer import CustomFileExplorer
from .inputs import SearchBar, TabNavigationLineEdit
from .labels import SectionLabel
from .lockable import LockableField
from .paste import PlainPasteLineEdit, PlainPasteTextEdit
from .pdf_viewer import PDFViewer
from .diff_viewer import DiffViewer, DiffHighlighter
from .qa_widget import QAItem, QAListWidget
from .inputs import ApplicationSelector
from .job_qa import QAItem as JobQAItem, QAListWidget as JobQAListWidget

__all__ = [
    'DraggableWindow',
    'CustomFileExplorer',
    'SearchBar',
    'TabNavigationLineEdit',
    'SectionLabel',
    'LockableField',
    'PlainPasteLineEdit',
    'PlainPasteTextEdit',
    'PDFViewer',
    'DiffViewer',
    'DiffHighlighter',
    'QAItem',
    'QAListWidget',
    'ApplicationSelector',
    'JobQAItem',
    'JobQAListWidget',
]
