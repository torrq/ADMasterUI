"""TV Season Orchestrator tab view for ADMasterUI."""

import os
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.models.config_manager import ConfigManager
from gui.views.components.drop_zone import DropZone
from gui.views.components.log_console import LogConsole
from gui.views.components.progress_panel import ProgressPanel
from gui.views.components.status_badge import StatusBadge
from gui.workers.base_worker import BaseSubprocessWorker


class SeasonTab(QWidget):
    """View for analyzing TV seasons and executing automated strategy routing."""

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.worker: Optional[BaseSubprocessWorker] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Season Folder Drop Zone
        self.drop_zone = DropZone(
            label_text="Select or drop TV Season Directory containing source/ and tosync/",
            is_directory=True
        )
        layout.addWidget(self.drop_zone)

        # Actions & Strategy Header
        header_row = QHBoxLayout()
        self.analyze_btn = QPushButton("Analyze Season Strategy (Dry Run)")
        self.analyze_btn.clicked.connect(self._on_analyze_clicked)
        header_row.addWidget(self.analyze_btn)

        self.execute_btn = QPushButton("Execute Full Season Sync")
        self.execute_btn.setStyleSheet("background-color: #1b4728; border-color: #2e7d32; font-weight: bold;")
        self.execute_btn.clicked.connect(self._on_execute_clicked)
        header_row.addWidget(self.execute_btn)

        self.cancel_btn = QPushButton("Cancel Execution")
        self.cancel_btn.setProperty("secondary", True)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        header_row.addWidget(self.cancel_btn)

        header_row.addStretch()
        self.strategy_summary = QLabel("No season analyzed yet.")
        self.strategy_summary.setStyleSheet("color: #888888; font-size: 12px;")
        header_row.addWidget(self.strategy_summary)
        layout.addLayout(header_row)

        # Episode Strategy Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Strategy Decision", "Episode Code", "Source MKV", "AD Audio Track"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

        # Progress Panel & Log Console
        self.progress_panel = ProgressPanel(["Scan & Black Detect", "Acoustic Correlation", "Routing", "Execution"])
        layout.addWidget(self.progress_panel)

        self.console = LogConsole()
        layout.addWidget(self.console, 1)

    def _start_orchestrator(self, dry_run: bool) -> None:
        season_dir = self.drop_zone.get_path()
        if not season_dir or not os.path.isdir(season_dir):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid TV Season directory.")
            return

        orchestrator_script = self.config_manager.core_dir / "batch_orchestrator.py"
        if not orchestrator_script.is_file():
            QMessageBox.critical(self, "Script Missing", "Cannot locate core/batch_orchestrator.py.")
            return

        cmd = [sys.executable, str(orchestrator_script), "--season-dir", season_dir]
        if dry_run:
            cmd.append("--dry-run")

        self.analyze_btn.setEnabled(False)
        self.execute_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.console.clear()
        self.table.setRowCount(0)
        self.progress_panel.reset()
        self.progress_panel.set_stage(0, "Analyzing season with TV Orchestrator...")

        self.worker = BaseSubprocessWorker(cmd, cwd=self.config_manager.root_dir, parent=self)
        self.worker.log_line.connect(self._handle_orchestrator_line)
        self.worker.stage_changed.connect(self.progress_panel.set_stage)
        self.worker.progress_changed.connect(self.progress_panel.set_progress)
        self.worker.process_finished.connect(self._on_orchestrator_finished)
        self.worker.error_occurred.connect(lambda err: self.console.append_log(f"[ERROR] {err}"))
        self.worker.start()

    def _on_analyze_clicked(self) -> None:
        self._start_orchestrator(dry_run=True)

    def _on_execute_clicked(self) -> None:
        self._start_orchestrator(dry_run=False)

    def _on_cancel_clicked(self) -> None:
        if self.worker and self.worker.isRunning():
            self.console.append_log("[USER] Cancelling TV Season Orchestrator...")
            self.worker.cancel()
            self.cancel_btn.setEnabled(False)

    def _handle_orchestrator_line(self, line: str) -> None:
        self.console.append_log(line)
        clean = line.strip()

        # Parse decision signatures: e.g. [0101] Direct Mux, [0102] Frame-Perfect, etc.
        m = re.search(r'\[(\d{4})\]\s+(Frame-Perfect|Direct Mux|DTW|ERROR)', clean, re.IGNORECASE)
        if m:
            ep_code_raw = m.group(1)
            strategy = m.group(2)
            formatted_ep = f"S{ep_code_raw[:2]}E{ep_code_raw[2:]}"

            badge_type = "ok" if strategy.lower() != "error" else "missing"
            badge = StatusBadge(f"[{strategy.upper()}]", badge_type)

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setCellWidget(row, 0, badge)

            ep_item = QTableWidgetItem(formatted_ep)
            ep_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 1, ep_item)

            detail_item = QTableWidgetItem(clean)
            detail_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 2, detail_item)

            ad_item = QTableWidgetItem(strategy)
            ad_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 3, ad_item)

    def _on_orchestrator_finished(self, return_code: int, summary: str) -> None:
        self.analyze_btn.setEnabled(True)
        self.execute_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_panel.set_progress(100, summary)
        self.console.append_log(f"\n{summary}\n")
