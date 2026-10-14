"""Specialized utilities tab view for ADMasterUI."""

import os
from pathlib import Path
import sys
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui.models.config_manager import ConfigManager
from gui.views.components.drop_zone import DropZone
from gui.views.components.log_console import LogConsole
from gui.workers.base_worker import BaseSubprocessWorker


class UtilitiesTab(QWidget):
    """View hosting secondary audio/video and media server utilities."""

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.worker: Optional[BaseSubprocessWorker] = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Sub-tabs for utilities
        self.subtabs = QTabWidget()
        layout.addWidget(self.subtabs, 1)

        # 1. MKV Commentary Tagger
        self.tagger_tab = self._create_tagger_tab()
        self.subtabs.addTab(self.tagger_tab, "Commentary Tagger")

        # 2. Commercial Break Scanner
        self.commercial_tab = self._create_commercial_tab()
        self.subtabs.addTab(self.commercial_tab, "Commercial Breaks")

        # 3. Surround Downmixer & Normalizer
        self.audio_tab = self._create_audio_tab()
        self.subtabs.addTab(self.audio_tab, "Downmixing & Normalization")

        # 4. Gemini Video Chunker
        self.chunker_tab = self._create_chunker_tab()
        self.subtabs.addTab(self.chunker_tab, "Gemini Video Chunker")

        # 5. Plex Sync
        self.plex_tab = self._create_plex_tab()
        self.subtabs.addTab(self.plex_tab, "Plex Sync")

        # Shared Live Log Console
        console_box = QGroupBox("Tool Execution Logs")
        console_layout = QVBoxLayout(console_box)
        self.console = LogConsole()
        console_layout.addWidget(self.console)
        layout.addWidget(console_box, 1)

    # =========================================================================
    # Sub-Tab 1: MKV Commentary Tagger
    # =========================================================================
    def _create_tagger_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        desc = QLabel(
            "Scans MKV files in a folder and applies flag-commentary=1 in-place in ~10ms "
            "using mkvpropedit for tracks matching commentary keywords."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #aaaaaa; margin-bottom: 5px;")
        layout.addWidget(desc)

        self.tagger_drop = DropZone("Select directory of MKV files to scan and flag", is_directory=True)
        layout.addWidget(self.tagger_drop)

        btn_row = QHBoxLayout()
        run_btn = QPushButton("Scan & Flag Commentary Tracks In-Place")
        run_btn.setStyleSheet("background-color: #0e639c; font-weight: bold;")
        run_btn.clicked.connect(self._run_commentary_tagger)
        btn_row.addWidget(run_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addStretch()
        return widget

    def _run_commentary_tagger(self) -> None:
        target = self.tagger_drop.get_path()
        if not target or not os.path.isdir(target):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid directory.")
            return

        script = self.config_manager.core_dir / "set_commentary_flags.py"
        cmd = [sys.executable, str(script), target]
        self._launch_worker(cmd, "Running in-place MKV commentary tagger...")

    # =========================================================================
    # Sub-Tab 2: Commercial Break Scanner
    # =========================================================================
    def _create_commercial_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        desc = QLabel(
            "Detects simultaneous video black frames and audio silence to output exact commercial cut intervals."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #aaaaaa; margin-bottom: 5px;")
        layout.addWidget(desc)

        self.comm_drop = DropZone(
            "Select MKV video file to scan for commercial breaks",
            is_directory=False,
            allowed_extensions=[".mkv", ".mp4"]
        )
        layout.addWidget(self.comm_drop)

        btn_row = QHBoxLayout()
        scan_btn = QPushButton("Scan Commercial Breaks (Black & Silence Detect)")
        scan_btn.clicked.connect(self._run_commercial_scan)
        btn_row.addWidget(scan_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addStretch()
        return widget

    def _run_commercial_scan(self) -> None:
        file_path = self.comm_drop.get_path()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.warning(self, "Invalid File", "Please select an MKV/MP4 file.")
            return

        script = self.config_manager.core_dir / "remove_commercial_breaks.py"
        cmd = [sys.executable, str(script), file_path]
        self._launch_worker(cmd, f"Scanning commercial breaks on {Path(file_path).name}...")

    # =========================================================================
    # Sub-Tab 3: Surround Downmixing & Loudness Normalization
    # =========================================================================
    def _create_audio_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        desc = QLabel(
            "Extracts surround masters (5.1/7.1) into 5.1 AC3, true 2.0 Stereo (alimiter), "
            "and Night Mode (loudnorm -16 LUFS), or normalizes standalone tracks via 2-pass EBU R128."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #aaaaaa; margin-bottom: 5px;")
        layout.addWidget(desc)

        self.downmix_drop = DropZone("Select media file or directory to downmix / normalize", is_directory=True)
        layout.addWidget(self.downmix_drop)

        btn_row = QHBoxLayout()
        downmix_btn = QPushButton("Downmix 5.1/7.1 to Stereo & Night Mode")
        downmix_btn.clicked.connect(self._run_downmix)
        btn_row.addWidget(downmix_btn)

        norm_btn = QPushButton("Run 2-Pass EBU R128 Loudness Normalizer")
        norm_btn.setProperty("secondary", True)
        norm_btn.clicked.connect(self._run_loudnorm)
        btn_row.addWidget(norm_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addStretch()
        return widget

    def _run_downmix(self) -> None:
        target = self.downmix_drop.get_path()
        if not target or not (os.path.isdir(target) or os.path.isfile(target)):
            QMessageBox.warning(self, "Invalid Target", "Please select a valid media file or folder.")
            return

        script = self.config_manager.core_dir / "convert_main_tracks.py"
        cmd = [sys.executable, str(script), target]
        self._launch_worker(cmd, "Executing ITU-R BS.775 2.0 surround downmixing...")

    def _run_loudnorm(self) -> None:
        target = self.downmix_drop.get_path()
        if not target or not os.path.isfile(target):
            QMessageBox.warning(self, "Invalid Target", "Please select an audio file for 2-pass normalization.")
            return

        script = self.config_manager.core_dir / "convert_ad_2pass.py"
        cmd = [sys.executable, str(script), target]
        self._launch_worker(cmd, "Executing 2-pass EBU R128 loudness normalization...")

    # =========================================================================
    # Sub-Tab 4: Gemini Video Chunker
    # =========================================================================
    def _create_chunker_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        desc = QLabel(
            "Slices long-form media into balanced 1 FPS MP4 chunks with structured JSON manifests "
            "optimized for Gemini multimodal ingestion."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #aaaaaa; margin-bottom: 5px;")
        layout.addWidget(desc)

        self.chunk_drop = DropZone(
            "Select movie video file to chunk for Gemini",
            is_directory=False,
            allowed_extensions=[".mkv", ".mp4"]
        )
        layout.addWidget(self.chunk_drop)

        opts_row = QHBoxLayout()
        opts_row.addWidget(QLabel("Max Chunk Duration (min):"))
        self.chunk_max_spin = QSpinBox()
        self.chunk_max_spin.setRange(5, 120)
        self.chunk_max_spin.setValue(45)
        opts_row.addWidget(self.chunk_max_spin)

        opts_row.addWidget(QLabel("Resolution Profile:"))
        self.chunk_res_combo = QComboBox()
        self.chunk_res_combo.addItems(["720p", "480p"])
        opts_row.addWidget(self.chunk_res_combo)

        self.chunk_dry_run_cb = QCheckBox("Dry Run (analyze boundaries without transcoding)")
        opts_row.addWidget(self.chunk_dry_run_cb)
        opts_row.addStretch()
        layout.addLayout(opts_row)

        btn_row = QHBoxLayout()
        chunk_btn = QPushButton("Chunk Video for Gemini")
        chunk_btn.setStyleSheet("background-color: #0e639c; font-weight: bold;")
        chunk_btn.clicked.connect(self._run_chunker)
        btn_row.addWidget(chunk_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addStretch()
        return widget

    def _run_chunker(self) -> None:
        video_path = self.chunk_drop.get_path()
        if not video_path or not os.path.isfile(video_path):
            QMessageBox.warning(self, "Invalid Video", "Please select a valid video file.")
            return

        script = self.config_manager.core_dir / "chunk_ad_video.py"
        cmd = [
            sys.executable,
            str(script),
            video_path,
            "--max-duration", str(self.chunk_max_spin.value()),
            "--resolution", self.chunk_res_combo.currentText(),
        ]
        if self.chunk_dry_run_cb.isChecked():
            cmd.append("--dry-run")

        self._launch_worker(cmd, f"Chunking video {Path(video_path).name} for Gemini...")

    # =========================================================================
    # Sub-Tab 5: Plex Sync
    # =========================================================================
    def _create_plex_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        desc = QLabel(
            "Maintains static collections in Plex for items containing Audio Description "
            "or Director/Commentary audio tracks."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #aaaaaa; margin-bottom: 5px;")
        layout.addWidget(desc)

        btn_row = QHBoxLayout()
        dry_run_btn = QPushButton("Inspect Plex Collections (Dry Run)")
        dry_run_btn.clicked.connect(lambda: self._run_plex(dry_run=True))
        btn_row.addWidget(dry_run_btn)

        sync_btn = QPushButton("Sync Plex Collections")
        sync_btn.clicked.connect(lambda: self._run_plex(dry_run=False))
        btn_row.addWidget(sync_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addStretch()
        return widget

    def _run_plex(self, dry_run: bool) -> None:
        script = self.config_manager.core_dir / "plex_ad_commentary_collections.py"
        cmd = [sys.executable, str(script)]
        if dry_run:
            cmd.append("--dry-run")
        self._launch_worker(cmd, "Connecting to Plex server...")

    # =========================================================================
    # Worker Lifecycle
    # =========================================================================
    def _launch_worker(self, cmd: list, initial_msg: str) -> None:
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Job In Progress", "A task is already executing. Please wait for it to finish.")
            return

        self.console.clear()
        self.console.append_log(f"[START] {initial_msg}")

        self.worker = BaseSubprocessWorker(cmd, cwd=self.config_manager.root_dir, parent=self)
        self.worker.log_line.connect(self.console.append_log)
        self.worker.process_finished.connect(
            lambda rc, summary: self.console.append_log(f"\n{summary}\n")
        )
        self.worker.error_occurred.connect(lambda err: self.console.append_log(f"[ERROR] {err}"))
        self.worker.start()
