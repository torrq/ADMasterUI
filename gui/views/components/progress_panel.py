"""Multi-stage pipeline progress indicator component."""

from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class ProgressPanel(QWidget):
    """Visual progress tracker with named stage steps and percentage bar."""

    DEFAULT_STAGES = ["Predecode", "Cross-Correlation", "Warping", "Encoding"]

    def __init__(self, stages: Optional[List[str]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.stage_names = stages or self.DEFAULT_STAGES
        self.current_stage_idx = -1
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Stage Breadcrumbs Row
        self.stages_layout = QHBoxLayout()
        self.stages_layout.setSpacing(6)
        self.stage_labels: List[QLabel] = []

        for idx, name in enumerate(self.stage_names):
            lbl = QLabel(f"[{idx + 1}. {name}]")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(self._get_stage_style("inactive"))
            self.stages_layout.addWidget(lbl)
            self.stage_labels.append(lbl)

        layout.addLayout(self.stages_layout)

        # Activity label + percentage bar
        self.info_label = QLabel("Idle | Ready")
        self.info_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self.info_label)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(True)
        layout.addWidget(self.bar)

    def _get_stage_style(self, status: str) -> str:
        if status == "active":
            return "background-color: #0e639c; color: #ffffff; font-weight: bold; border-radius: 3px; padding: 3px 6px;"
        elif status == "done":
            return "background-color: #1b4728; color: #4ec9b0; border-radius: 3px; padding: 3px 6px;"
        else:  # inactive
            return "background-color: #252526; color: #666666; border-radius: 3px; padding: 3px 6px;"

    def set_stage(self, stage_idx: int, message: str = "") -> None:
        """Set the active stage (0-based) and update stage label styling."""
        self.current_stage_idx = stage_idx
        for idx, lbl in enumerate(self.stage_labels):
            if idx < stage_idx:
                lbl.setStyleSheet(self._get_stage_style("done"))
            elif idx == stage_idx:
                lbl.setStyleSheet(self._get_stage_style("active"))
            else:
                lbl.setStyleSheet(self._get_stage_style("inactive"))

        if message:
            self.info_label.setText(message)

    def set_progress(self, percent: int, message: str = "") -> None:
        """Update percentage (0-100) and optional detail string."""
        self.bar.setValue(max(0, min(100, percent)))
        if message:
            self.info_label.setText(message)

    def reset(self) -> None:
        """Reset progress panel to initial idle state."""
        self.current_stage_idx = -1
        for lbl in self.stage_labels:
            lbl.setStyleSheet(self._get_stage_style("inactive"))
        self.bar.setValue(0)
        self.info_label.setText("Idle | Ready")
