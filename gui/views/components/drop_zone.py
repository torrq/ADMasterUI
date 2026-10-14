"""Drag-and-drop file and directory picker component."""

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DropZone(QFrame):
    """Interactive drag-and-drop target and file path selector."""

    path_changed = pyqtSignal(str)

    def __init__(
        self,
        label_text: str = "Drop file here or click Browse",
        is_directory: bool = False,
        allowed_extensions: Optional[List[str]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.label_text = label_text
        self.is_directory = is_directory
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions] if allowed_extensions else []

        self.setAcceptDrops(True)
        self._init_ui()
        self._apply_style(drag_over=False)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        self.prompt_label = QLabel(self.label_text)
        self.prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prompt_label.setStyleSheet("color: #888888; font-size: 12px; font-weight: 500;")
        layout.addWidget(self.prompt_label)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("No file or directory selected...")
        self.path_edit.textChanged.connect(self._on_text_changed)
        input_row.addWidget(self.path_edit)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setProperty("secondary", True)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        input_row.addWidget(self.browse_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setProperty("secondary", True)
        self.clear_btn.clicked.connect(self.clear)
        input_row.addWidget(self.clear_btn)

        layout.addLayout(input_row)

    def _apply_style(self, drag_over: bool = False) -> None:
        if drag_over:
            self.setStyleSheet(
                "DropZone { border: 2px dashed #007acc; border-radius: 6px; background-color: #1e2633; }"
            )
        else:
            self.setStyleSheet(
                "DropZone { border: 1px dashed #444444; border-radius: 6px; background-color: #222222; }"
            )

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = Path(urls[0].toLocalFile())
                if self.is_directory and path.is_dir():
                    event.acceptProposedAction()
                    self._apply_style(drag_over=True)
                    return
                elif not self.is_directory and path.is_file():
                    if not self.allowed_extensions or path.suffix.lower() in self.allowed_extensions:
                        event.acceptProposedAction()
                        self._apply_style(drag_over=True)
                        return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._apply_style(drag_over=False)
        event.accept()

    def dropEvent(self, event) -> None:
        self._apply_style(drag_over=False)
        urls = event.mimeData().urls()
        if urls:
            local_path = urls[0].toLocalFile()
            self.set_path(local_path)
            event.acceptProposedAction()

    def _on_browse_clicked(self) -> None:
        if self.is_directory:
            folder = QFileDialog.getExistingDirectory(self, "Select Directory")
            if folder:
                self.set_path(folder)
        else:
            filter_str = "All Files (*.*)"
            if self.allowed_extensions:
                patterns = " ".join(f"*{ext}" for ext in self.allowed_extensions)
                filter_str = f"Media Files ({patterns});;All Files (*.*)"
            filepath, _ = QFileDialog.getOpenFileName(self, "Select File", "", filter_str)
            if filepath:
                self.set_path(filepath)

    def _on_text_changed(self, text: str) -> None:
        self.path_changed.emit(text.strip())

    def get_path(self) -> str:
        return self.path_edit.text().strip()

    def set_path(self, path: str) -> None:
        self.path_edit.setText(path)

    def clear(self) -> None:
        self.path_edit.clear()
