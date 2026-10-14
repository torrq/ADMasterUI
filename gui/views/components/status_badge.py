"""Visual status badge component for tool and task status display."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel


class StatusBadge(QLabel):
    """Custom QLabel styled as a colored status badge."""

    STYLES = {
        "ok": (
            "background-color: #1b4728; color: #4ec9b0; border: 1px solid #2e7d32; "
            "border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;"
        ),
        "missing": (
            "background-color: #4a151b; color: #f48771; border: 1px solid #d32f2f; "
            "border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;"
        ),
        "warning": (
            "background-color: #4d3800; color: #dcdcaa; border: 1px solid #fbc02d; "
            "border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;"
        ),
        "running": (
            "background-color: #0e3a5a; color: #569cd6; border: 1px solid #1976d2; "
            "border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;"
        ),
        "neutral": (
            "background-color: #2d2d30; color: #cccccc; border: 1px solid #3e3e42; "
            "border-radius: 4px; padding: 2px 8px; font-weight: normal; font-size: 11px;"
        ),
    }

    def __init__(self, text: str = "[OK]", status_type: str = "ok", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status(text, status_type)

    def set_status(self, text: str, status_type: str = "neutral") -> None:
        """Update badge text and visual color scheme."""
        self.setText(text)
        style = self.STYLES.get(status_type.lower(), self.STYLES["neutral"])
        self.setStyleSheet(style)
