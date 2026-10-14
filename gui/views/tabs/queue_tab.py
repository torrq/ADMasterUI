"""Batch Queue Manager tab view for ADMasterUI."""

import glob
import os
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
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
from gui.workers.sync_worker import SyncWorker


class QueueTab(QWidget):
    """View for scanning and batch-processing full queue directories."""

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.worker: Optional[SyncWorker] = None
        self.discovered_folders: List[Path] = []

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Queue Folder Drop Zone
        self.drop_zone = DropZone(
            label_text="Select or drop top-level Queue Directory containing movie subfolders",
            is_directory=True
        )
        self.drop_zone.path_changed.connect(self._on_queue_dir_changed)
        layout.addWidget(self.drop_zone)

        # Table & Controls Header
        header_row = QHBoxLayout()
        self.scan_btn = QPushButton("Scan Queue Directory")
        self.scan_btn.clicked.connect(self.scan_queue)
        header_row.addWidget(self.scan_btn)

        self.summary_lbl = QLabel("No queue directory scanned.")
        self.summary_lbl.setStyleSheet("color: #888888; font-size: 12px;")
        header_row.addWidget(self.summary_lbl)
        header_row.addStretch()

        # Batch Options
        self.convert_main_cb = QCheckBox("Convert Main Audio (5.1/2.0)")
        self.convert_main_cb.setChecked(True)
        header_row.addWidget(self.convert_main_cb)

        self.wav_cb = QCheckBox("Fast WAV (--wav)")
        header_row.addWidget(self.wav_cb)

        self.no_night_cb = QCheckBox("Skip Night (--no-night)")
        header_row.addWidget(self.no_night_cb)

        self.overwrite_cb = QCheckBox("Force Overwrite")
        header_row.addWidget(self.overwrite_cb)

        layout.addLayout(header_row)

        # Queue Items Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Status", "Movie Folder", "Source Files", "AD Tracks (tosync/)", "Output Deliverables"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

        # Actions Bar
        actions_row = QHBoxLayout()
        self.start_btn = QPushButton("Start Batch Queue Processing")
        self.start_btn.setStyleSheet("background-color: #1b4728; border-color: #2e7d32; font-weight: bold;")
        self.start_btn.clicked.connect(self._on_start_queue)
        actions_row.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("Cancel Queue")
        self.cancel_btn.setProperty("secondary", True)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel_queue)
        actions_row.addWidget(self.cancel_btn)
        actions_row.addStretch()

        layout.addLayout(actions_row)

        # Progress & Live Console
        self.progress_panel = ProgressPanel(["Queue Batch", "Correlation", "Warping", "Final Encode"])
        layout.addWidget(self.progress_panel)

        self.console = LogConsole()
        layout.addWidget(self.console, 1)

    def _on_queue_dir_changed(self, path: str) -> None:
        if path and os.path.isdir(path):
            self.scan_queue()

    def scan_queue(self) -> None:
        queue_path = self.drop_zone.get_path()
        if not queue_path or not os.path.isdir(queue_path):
            return

        p = Path(queue_path)
        subdirs = [d for d in p.iterdir() if d.is_dir() and not d.name.startswith(".")]
        self.discovered_folders = sorted(subdirs, key=lambda x: x.name.lower())

        self.table.setRowCount(len(self.discovered_folders))

        valid_count = 0
        for row, folder in enumerate(self.discovered_folders):
            source_dir = folder / "source"
            tosync_dir = folder / "tosync"
            output_dir = folder / "output"

            source_files = list(source_dir.glob("*")) if source_dir.is_dir() else []
            tosync_files = list(tosync_dir.glob("*")) if tosync_dir.is_dir() else []
            output_files = list(output_dir.glob("*")) if output_dir.is_dir() else []

            is_ready = len(source_files) > 0 and len(tosync_files) > 0
            if is_ready:
                valid_count += 1
                badge = StatusBadge("[READY]", "ok")
            elif len(output_files) > 0:
                badge = StatusBadge("[DONE]", "neutral")
            else:
                badge = StatusBadge("[INCOMPLETE]", "warning")

            name_item = QTableWidgetItem(folder.name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            src_item = QTableWidgetItem(f"{len(source_files)} file(s)")
            src_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            ad_item = QTableWidgetItem(f"{len(tosync_files)} file(s)")
            ad_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            out_item = QTableWidgetItem(f"{len(output_files)} deliverable(s)")
            out_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            self.table.setCellWidget(row, 0, badge)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, src_item)
            self.table.setItem(row, 3, ad_item)
            self.table.setItem(row, 4, out_item)

        self.summary_lbl.setText(f"Found {len(self.discovered_folders)} folder(s) | {valid_count} ready to process")

    def _on_start_queue(self) -> None:
        queue_path = self.drop_zone.get_path()
        if not queue_path or not os.path.isdir(queue_path):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid queue directory.")
            return

        sync_script, ok = self.config_manager.resolve_core_engine()
        if not ok or not sync_script:
            QMessageBox.critical(self, "Core Engine Missing", "Cannot locate core/sync_ad_track.py.")
            return

        # Prepare batch params
        params = {
            "mode": "folder",
            "folder_path": queue_path,
            "convert_main": self.convert_main_cb.isChecked(),
            "wav_deliverables": self.wav_cb.isChecked(),
            "no_night": self.no_night_cb.isChecked(),
            "overwrite": self.overwrite_cb.isChecked(),
            "threads": int(self.config_manager.get("default_threads", 2)),
            "warp_engine": self.config_manager.get("default_warp_engine", "adsync"),
            "multiband": bool(self.config_manager.get("default_multiband", True)),
            "speed_detect": bool(self.config_manager.get("default_speed_detect", True)),
        }

        # Extra batch flag
        self.start_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.console.clear()
        self.progress_panel.reset()
        self.progress_panel.set_stage(0, "Executing batch queue sequentially...")

        self.worker = SyncWorker(sync_script, params, cwd=self.config_manager.root_dir, parent=self)
        # Ensure --batch flag is appended
        self.worker.cmd.append("--batch")

        self.worker.log_line.connect(self.console.append_log)
        self.worker.stage_changed.connect(self.progress_panel.set_stage)
        self.worker.progress_changed.connect(self.progress_panel.set_progress)
        self.worker.process_finished.connect(self._on_queue_finished)
        self.worker.error_occurred.connect(lambda err: self.console.append_log(f"[ERROR] {err}"))
        self.worker.start()

    def _on_cancel_queue(self) -> None:
        if self.worker and self.worker.isRunning():
            self.console.append_log("[USER] Cancelling batch queue...")
            self.worker.cancel()
            self.cancel_btn.setEnabled(False)

    def _on_queue_finished(self, return_code: int, summary: str) -> None:
        self.start_btn.setEnabled(True)
        self.scan_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_panel.set_progress(100, summary)
        self.console.append_log(f"\n{summary}\n")
        self.scan_queue()
