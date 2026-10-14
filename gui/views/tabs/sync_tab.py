"""Movie Sync and Fast Preview tab view for ADMasterUI."""

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from gui.models.config_manager import ConfigManager
from gui.models.stream_info import AudioStream, StreamProber
from gui.views.components.drop_zone import DropZone
from gui.views.components.log_console import LogConsole
from gui.views.components.progress_panel import ProgressPanel
from gui.workers.sync_worker import SyncWorker


class SyncTab(QWidget):
    """View for single-movie acoustic alignment, warping, downmixing, and previewing."""

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.worker: Optional[SyncWorker] = None

        self._init_ui()
        self._on_mode_toggled()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top scrollable configuration area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget()
        top_layout = QVBoxLayout(container)
        top_layout.setSpacing(12)

        # 1. Input Media Selection Group
        input_box = QGroupBox("Input Media & Directory Configuration")
        input_layout = QVBoxLayout(input_box)
        input_layout.setSpacing(10)

        mode_row = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        self.radio_folder = QRadioButton("Movie Directory Auto-Discovery (source/ and tosync/)")
        self.radio_explicit = QRadioButton("Explicit File Pairing (Reference Video/Audio + AD File)")
        self.radio_folder.setChecked(True)
        self.mode_group.addButton(self.radio_folder, 1)
        self.mode_group.addButton(self.radio_explicit, 2)
        self.radio_folder.toggled.connect(self._on_mode_toggled)
        self.radio_explicit.toggled.connect(self._on_mode_toggled)
        mode_row.addWidget(self.radio_folder)
        mode_row.addWidget(self.radio_explicit)
        mode_row.addStretch()
        input_layout.addLayout(mode_row)

        # Folder Drop Zone
        self.folder_drop = DropZone(
            label_text="Drop Movie Folder here (must contain 'source/' and 'tosync/')",
            is_directory=True
        )
        input_layout.addWidget(self.folder_drop)

        # Explicit File Drop Zones Container
        self.explicit_widget = QWidget()
        explicit_layout = QVBoxLayout(self.explicit_widget)
        explicit_layout.setContentsMargins(0, 0, 0, 0)
        explicit_layout.setSpacing(8)

        self.ref_drop = DropZone(
            label_text="Reference Video or Master Audio (MKV, MP4, DTS-HD, TrueHD, AC3, FLAC, WAV)",
            is_directory=False,
            allowed_extensions=[".mkv", ".mp4", ".dts", ".dtshd", ".thd", ".ac3", ".eac3", ".flac", ".wav", ".m4a"]
        )
        self.ref_drop.path_changed.connect(self._on_ref_file_changed)
        explicit_layout.addWidget(self.ref_drop)

        # Stream Selector Row
        stream_row = QHBoxLayout()
        stream_row.addWidget(QLabel("Reference Audio Stream:"))
        self.stream_combo = QComboBox()
        self.stream_combo.addItem("0:a:0 (Default / Auto-selected)", "0:a:0")
        stream_row.addWidget(self.stream_combo, 1)
        self.probe_btn = QPushButton("Probe Streams")
        self.probe_btn.setProperty("secondary", True)
        self.probe_btn.clicked.connect(self._probe_ref_streams)
        stream_row.addWidget(self.probe_btn)
        explicit_layout.addLayout(stream_row)

        self.ad_drop = DropZone(
            label_text="Candidate Audio Description Track to Sync (MP3, M4A, AC3, AAC, FLAC, WAV)",
            is_directory=False,
            allowed_extensions=[".mp3", ".m4a", ".ac3", ".aac", ".flac", ".wav", ".dts"]
        )
        explicit_layout.addWidget(self.ad_drop)

        input_layout.addWidget(self.explicit_widget)
        top_layout.addWidget(input_box)

        # 2. Alignment & Output Settings
        settings_row = QHBoxLayout()
        settings_row.setSpacing(10)

        # Warp & Alignment Options
        warp_box = QGroupBox("Acoustic Alignment & Warp Settings")
        warp_layout = QVBoxLayout(warp_box)

        engine_row = QHBoxLayout()
        engine_row.addWidget(QLabel("Warp Engine:"))
        self.warp_combo = QComboBox()
        self.warp_combo.addItems(["adsync (Default -- High Speed Viterbi DP)", "describealign (Legacy DTW)"])
        engine_row.addWidget(self.warp_combo, 1)
        warp_layout.addLayout(engine_row)

        self.multiband_cb = QCheckBox("3-Band Speech Suppression (narration downweighting)")
        self.multiband_cb.setChecked(bool(self.config_manager.get("default_multiband", True)))
        warp_layout.addWidget(self.multiband_cb)

        self.speed_detect_cb = QCheckBox("Automatic PAL Speed Detection (25fps vs 23.976fps)")
        self.speed_detect_cb.setChecked(bool(self.config_manager.get("default_speed_detect", True)))
        warp_layout.addWidget(self.speed_detect_cb)

        self.no_pal_cb = QCheckBox("Force Native 1.0x Speed (Disable PAL slowdown)")
        warp_layout.addWidget(self.no_pal_cb)

        self.force_dtw_cb = QCheckBox("Force Non-Linear Warp (Skip 100-anchor search)")
        warp_layout.addWidget(self.force_dtw_cb)

        # Anchors Slider
        anchors_row = QHBoxLayout()
        anchors_row.addWidget(QLabel("Correlation Anchors:"))
        self.anchors_slider = QSlider(Qt.Orientation.Horizontal)
        self.anchors_slider.setRange(10, 200)
        self.anchors_spin = QSpinBox()
        self.anchors_spin.setRange(10, 200)
        cur_anchors = int(self.config_manager.get("default_anchors", 100))
        self.anchors_slider.setValue(cur_anchors)
        self.anchors_spin.setValue(cur_anchors)
        self.anchors_slider.valueChanged.connect(self.anchors_spin.setValue)
        self.anchors_spin.valueChanged.connect(self.anchors_slider.setValue)
        anchors_row.addWidget(self.anchors_slider)
        anchors_row.addWidget(self.anchors_spin)
        warp_layout.addLayout(anchors_row)

        settings_row.addWidget(warp_box, 1)

        # Deliverables & Processing Options
        deliv_box = QGroupBox("Deliverables & Output Preferences")
        deliv_layout = QVBoxLayout(deliv_box)

        self.convert_main_cb = QCheckBox("Convert Main Audio (5.1 AC3 + True 2.0 Stereo + Night Mode)")
        self.convert_main_cb.setChecked(True)
        deliv_layout.addWidget(self.convert_main_cb)

        self.wav_cb = QCheckBox("Fast PCM WAV Deliverables (--wav: bypass AAC encoding)")
        deliv_layout.addWidget(self.wav_cb)

        self.no_night_cb = QCheckBox("Skip Night Mode (--no-night: bypass slow loudnorm filter)")
        deliv_layout.addWidget(self.no_night_cb)

        self.clean_scratch_cb = QCheckBox("Clean Scratch Directory Before Execution")
        deliv_layout.addWidget(self.clean_scratch_cb)

        self.overwrite_cb = QCheckBox("Overwrite Existing Deliverables")
        self.overwrite_cb.setChecked(bool(self.config_manager.get("default_overwrite", False)))
        deliv_layout.addWidget(self.overwrite_cb)

        # CPU Threads
        threads_row = QHBoxLayout()
        threads_row.addWidget(QLabel("FFmpeg Threads:"))
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 16)
        self.threads_spin.setValue(int(self.config_manager.get("default_threads", 2)))
        threads_row.addWidget(self.threads_spin)
        threads_row.addStretch()
        deliv_layout.addLayout(threads_row)

        settings_row.addWidget(deliv_box, 1)
        top_layout.addLayout(settings_row)

        scroll.setWidget(container)
        main_layout.addWidget(scroll, 2)

        # 3. Action Buttons Row
        actions_box = QHBoxLayout()
        actions_box.setSpacing(10)

        self.preview_btn = QPushButton("Test Preview (3 min)")
        self.preview_btn.clicked.connect(self._on_preview_clicked)
        actions_box.addWidget(self.preview_btn)

        self.preview_mux_cb = QCheckBox("Mux Video with Preview Sample")
        self.preview_mux_cb.setChecked(True)
        actions_box.addWidget(self.preview_mux_cb)

        actions_box.addStretch()

        self.run_btn = QPushButton("Run Full Sync & Encode")
        self.run_btn.setStyleSheet("background-color: #1b4728; border-color: #2e7d32; font-weight: bold;")
        self.run_btn.clicked.connect(self._on_run_clicked)
        actions_box.addWidget(self.run_btn)

        self.cancel_btn = QPushButton("Cancel Execution")
        self.cancel_btn.setProperty("secondary", True)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        actions_box.addWidget(self.cancel_btn)

        main_layout.addLayout(actions_box)

        # 4. Progress Panel
        self.progress_panel = ProgressPanel()
        main_layout.addWidget(self.progress_panel)

        # 5. Real-Time Log Console
        self.console = LogConsole()
        main_layout.addWidget(self.console, 1)

    def _on_mode_toggled(self) -> None:
        is_folder = self.radio_folder.isChecked()
        self.folder_drop.setVisible(is_folder)
        self.explicit_widget.setVisible(not is_folder)

    def _on_ref_file_changed(self, file_path: str) -> None:
        if file_path and os.path.isfile(file_path):
            self._probe_ref_streams()

    def _probe_ref_streams(self) -> None:
        ref_file = self.ref_drop.get_path()
        if not ref_file or not os.path.isfile(ref_file):
            return

        ffprobe_path = self.config_manager.resolve_executable("ffprobe_path", "ffprobe")
        if not ffprobe_path:
            self.console.append_log("[WARNING] Cannot probe audio streams: ffprobe executable not found.")
            return

        prober = StreamProber(ffprobe_path)
        streams = prober.probe_audio_streams(ref_file)

        self.stream_combo.clear()
        if streams:
            for s in streams:
                self.stream_combo.addItem(s.display_label, s.stream_specifier)
            self.console.append_log(f"[INFO] Discovered {len(streams)} audio stream(s) in {Path(ref_file).name}")
        else:
            self.stream_combo.addItem("0:a:0 (Default)", "0:a:0")

    def _build_params(self, preview_sec: int = 0) -> dict:
        is_folder = self.radio_folder.isChecked()
        warp_selection = "adsync" if "adsync" in self.warp_combo.currentText() else "describealign"

        params = {
            "mode": "folder" if is_folder else "explicit",
            "folder_path": self.folder_drop.get_path(),
            "ref_path": self.ref_drop.get_path(),
            "ref_stream": self.stream_combo.currentData() or "0:a:0",
            "ad_path": self.ad_drop.get_path(),
            "warp_engine": warp_selection,
            "multiband": self.multiband_cb.isChecked(),
            "speed_detect": self.speed_detect_cb.isChecked(),
            "no_pal": self.no_pal_cb.isChecked(),
            "force_dtw": self.force_dtw_cb.isChecked(),
            "anchors": self.anchors_spin.value(),
            "convert_main": self.convert_main_cb.isChecked(),
            "wav_deliverables": self.wav_cb.isChecked(),
            "no_night": self.no_night_cb.isChecked(),
            "clean_scratch": self.clean_scratch_cb.isChecked(),
            "overwrite": self.overwrite_cb.isChecked(),
            "threads": self.threads_spin.value(),
            "preview_sec": preview_sec,
            "preview_mux": self.preview_mux_cb.isChecked(),
        }
        return params

    def _on_preview_clicked(self) -> None:
        self._start_execution(preview_sec=180)

    def _on_run_clicked(self) -> None:
        self._start_execution(preview_sec=0)

    def _start_execution(self, preview_sec: int = 0) -> None:
        # Validate inputs
        is_folder = self.radio_folder.isChecked()
        if is_folder:
            folder = self.folder_drop.get_path()
            if not folder or not os.path.isdir(folder):
                QMessageBox.warning(self, "Invalid Directory", "Please select a valid movie directory.")
                return
        else:
            ref = self.ref_drop.get_path()
            ad = self.ad_drop.get_path()
            if not ref or not os.path.isfile(ref):
                QMessageBox.warning(self, "Missing Reference Media", "Please select a valid reference video/audio file.")
                return
            if not ad or not os.path.isfile(ad):
                QMessageBox.warning(self, "Missing AD Track", "Please select a candidate Audio Description track.")
                return

        sync_script, ok = self.config_manager.resolve_core_engine()
        if not ok or not sync_script:
            QMessageBox.critical(self, "Core Engine Missing", "Cannot locate core/sync_ad_track.py.")
            return

        params = self._build_params(preview_sec=preview_sec)

        # UI State updates
        self.run_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_panel.reset()
        self.progress_panel.set_stage(0, "Launching pipeline subprocess...")
        self.console.clear()

        # Start worker thread
        self.worker = SyncWorker(sync_script, params, cwd=self.config_manager.root_dir, parent=self)
        self.worker.log_line.connect(self.console.append_log)
        self.worker.stage_changed.connect(self.progress_panel.set_stage)
        self.worker.progress_changed.connect(self.progress_panel.set_progress)
        self.worker.process_finished.connect(self._on_process_finished)
        self.worker.error_occurred.connect(lambda err: self.console.append_log(f"[ERROR] {err}"))
        self.worker.start()

    def _on_cancel_clicked(self) -> None:
        if self.worker and self.worker.isRunning():
            self.console.append_log("[USER] Cancellation requested.")
            self.worker.cancel()
            self.cancel_btn.setEnabled(False)

    def _on_process_finished(self, return_code: int, summary: str) -> None:
        self.run_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        if return_code == 0:
            self.progress_panel.set_progress(100, summary)
            self.progress_panel.set_stage(3, summary)
        else:
            self.progress_panel.set_progress(self.progress_panel.bar.value(), summary)

        self.console.append_log(f"\n{summary}\n")
