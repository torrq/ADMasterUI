"""Real-time log console component with ANSI color stripping and auto-scroll."""

import re
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LogConsole(QWidget):
    """Terminal-like log output viewer with search, clear, and auto-scroll."""

    ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Toolbar
        bar = QHBoxLayout()
        bar.setSpacing(8)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter logs (regex or text)...")
        self.filter_edit.textChanged.connect(self._on_filter_changed)
        bar.addWidget(self.filter_edit)

        self.autoscroll_cb = QCheckBox("Auto-scroll")
        self.autoscroll_cb.setChecked(True)
        bar.addWidget(self.autoscroll_cb)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setProperty("secondary", True)
        self.copy_btn.clicked.connect(self._on_copy_clicked)
        bar.addWidget(self.copy_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setProperty("secondary", True)
        self.clear_btn.clicked.connect(self.clear)
        bar.addWidget(self.clear_btn)

        layout.addLayout(bar)

        # Log Text Area
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumBlockCount(5000)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_edit.setFont(font)
        self.text_edit.setStyleSheet(
            "background-color: #141414; color: #d4d4d4; border: 1px solid #333333; border-radius: 4px;"
        )
        layout.addWidget(self.text_edit)

        self._all_lines = []

    def append_log(self, text: str) -> None:
        """Append raw line of text from subprocess or logger."""
        clean_line = self.ANSI_ESCAPE.sub('', text).rstrip('\r\n')
        self._all_lines.append(clean_line)

        filter_term = self.filter_edit.text().strip().lower()
        if not filter_term or filter_term in clean_line.lower():
            self.text_edit.appendPlainText(clean_line)
            if self.autoscroll_cb.isChecked():
                self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

    def _on_filter_changed(self, text: str) -> None:
        """Re-render visible lines matching filter query."""
        query = text.strip().lower()
        self.text_edit.clear()
        if not query:
            for line in self._all_lines[-1000:]:
                self.text_edit.appendPlainText(line)
        else:
            for line in self._all_lines:
                if query in line.lower():
                    self.text_edit.appendPlainText(line)

        if self.autoscroll_cb.isChecked():
            self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

    def _on_copy_clicked(self) -> None:
        self.text_edit.selectAll()
        self.text_edit.copy()
        cursor = self.text_edit.textCursor()
        cursor.clearSelection()
        self.text_edit.setTextCursor(cursor)

    def clear(self) -> None:
        self._all_lines.clear()
        self.text_edit.clear()
