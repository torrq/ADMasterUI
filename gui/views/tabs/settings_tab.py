"""Settings and Diagnostics tab for ADMasterUI."""

from pathlib import Path
from typing import Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.models.config_manager import ConfigManager, BinaryStatus
from gui.views.components.status_badge import StatusBadge


class SettingsTab(QWidget):
    """View for inspecting dependency binaries and tuning pipeline configurations."""

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.badges: Dict[str, StatusBadge] = {}

        self._init_ui()
        self.refresh_diagnostics()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Scroll area to handle smaller monitor resolutions comfortably
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)

        # 1. Dependency Diagnostics Group
        diag_box = QGroupBox("System Dependencies & External Tool Diagnostics")
        diag_layout = QVBoxLayout(diag_box)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Status", "Component", "Resolved Path", "Version / Details"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setMinimumHeight(210)
        diag_layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.rescan_btn = QPushButton("Re-scan Dependencies")
        self.rescan_btn.clicked.connect(self.refresh_diagnostics)
        btn_row.addWidget(self.rescan_btn)
        btn_row.addStretch()
        diag_layout.addLayout(btn_row)

        layout.addWidget(diag_box)

        # 2. Pipeline Preferences Group
        pref_box = QGroupBox("Default Pipeline & Audio Encoding Preferences")
        pref_grid = QGridLayout(pref_box)
        pref_grid.setVerticalSpacing(10)
        pref_grid.setHorizontalSpacing(15)

        # Default Warp Engine
        pref_grid.addWidget(QLabel("Default Non-Linear Warp Engine:"), 0, 0)
        self.warp_combo = QComboBox()
        self.warp_combo.addItems(["adsync", "describealign"])
        cur_engine = self.config_manager.get("default_warp_engine", "adsync")
        idx = self.warp_combo.findText(cur_engine)
        if idx >= 0:
            self.warp_combo.setCurrentIndex(idx)
        pref_grid.addWidget(self.warp_combo, 0, 1)

        # CPU Encoding Threads
        pref_grid.addWidget(QLabel("FFmpeg Encoding Threads:"), 1, 0)
        threads_box = QHBoxLayout()
        self.threads_slider = QSlider(Qt.Orientation.Horizontal)
        self.threads_slider.setRange(1, 16)
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 16)
        cur_threads = int(self.config_manager.get("default_threads", 2))
        self.threads_slider.setValue(cur_threads)
        self.threads_spin.setValue(cur_threads)
        self.threads_slider.valueChanged.connect(self.threads_spin.setValue)
        self.threads_spin.valueChanged.connect(self.threads_slider.setValue)
        threads_box.addWidget(self.threads_slider)
        threads_box.addWidget(self.threads_spin)
        pref_grid.addLayout(threads_box, 1, 1)

        # Correlation Anchors
        pref_grid.addWidget(QLabel("Correlation Timeline Anchors:"), 2, 0)
        anchors_box = QHBoxLayout()
        self.anchors_slider = QSlider(Qt.Orientation.Horizontal)
        self.anchors_slider.setRange(10, 200)
        self.anchors_spin = QSpinBox()
        self.anchors_spin.setRange(10, 200)
        cur_anchors = int(self.config_manager.get("default_anchors", 100))
        self.anchors_slider.setValue(cur_anchors)
        self.anchors_spin.setValue(cur_anchors)
        self.anchors_slider.valueChanged.connect(self.anchors_spin.setValue)
        self.anchors_spin.valueChanged.connect(self.anchors_slider.setValue)
        anchors_box.addWidget(self.anchors_slider)
        anchors_box.addWidget(self.anchors_spin)
        pref_grid.addLayout(anchors_box, 2, 1)

        # Target Loudness LUFS
        pref_grid.addWidget(QLabel("Night Mode Target Loudness (LUFS):"), 3, 0)
        self.lufs_spin = QDoubleSpinBox()
        self.lufs_spin.setRange(-30.0, -10.0)
        self.lufs_spin.setSingleStep(0.5)
        self.lufs_spin.setValue(float(self.config_manager.get("default_target_i", -16.0)))
        pref_grid.addWidget(self.lufs_spin, 3, 1)

        # Target True Peak dB
        pref_grid.addWidget(QLabel("Night Mode True Peak Ceiling (dB):"), 4, 0)
        self.tp_spin = QDoubleSpinBox()
        self.tp_spin.setRange(-6.0, 0.0)
        self.tp_spin.setSingleStep(0.1)
        self.tp_spin.setValue(float(self.config_manager.get("default_target_tp", -1.5)))
        pref_grid.addWidget(self.tp_spin, 4, 1)

        # Toggles Row
        pref_grid.addWidget(QLabel("Acoustic Features:"), 5, 0)
        toggles_row = QHBoxLayout()
        self.multiband_cb = QCheckBox("Multiband Speech Suppression")
        self.multiband_cb.setChecked(bool(self.config_manager.get("default_multiband", True)))
        self.speed_detect_cb = QCheckBox("Automatic PAL Speed Detection")
        self.speed_detect_cb.setChecked(bool(self.config_manager.get("default_speed_detect", True)))
        self.overwrite_cb = QCheckBox("Overwrite Existing Outputs")
        self.overwrite_cb.setChecked(bool(self.config_manager.get("default_overwrite", False)))
        toggles_row.addWidget(self.multiband_cb)
        toggles_row.addWidget(self.speed_detect_cb)
        toggles_row.addWidget(self.overwrite_cb)
        toggles_row.addStretch()
        pref_grid.addLayout(toggles_row, 5, 1)

        layout.addWidget(pref_box)

        # 3. Custom Binary Overrides Group
        paths_box = QGroupBox("Custom Binary Path Overrides (Optional)")
        paths_grid = QGridLayout(paths_box)
        paths_grid.setVerticalSpacing(8)

        self.path_edits: Dict[str, QLineEdit] = {}
        path_fields = [
            ("ffmpeg_path", "FFmpeg Path:"),
            ("ffprobe_path", "FFprobe Path:"),
            ("mkvmerge_path", "MKVMerge Path:"),
            ("mkvpropedit_path", "MKVPropEdit Path:"),
            ("mkvextract_path", "MKVExtract Path:"),
            ("adsync_path", "ADSync Path:"),
            ("describealign_path", "DescribeAlign Path:"),
        ]

        for row, (key, label) in enumerate(path_fields):
            paths_grid.addWidget(QLabel(label), row, 0)
            edit = QLineEdit(str(self.config_manager.get(key, "")))
            paths_grid.addWidget(edit, row, 1)
            browse_btn = QPushButton("Browse...")
            browse_btn.setProperty("secondary", True)
            browse_btn.clicked.connect(lambda checked, e=edit: self._browse_file(e))
            paths_grid.addWidget(browse_btn, row, 2)
            self.path_edits[key] = edit

        layout.addWidget(paths_box)

        # Bottom Actions Bar
        actions_bar = QHBoxLayout()
        self.save_btn = QPushButton("Save Settings to config.json")
        self.save_btn.clicked.connect(self.save_settings)
        self.status_msg = QLabel("")
        actions_bar.addWidget(self.save_btn)
        actions_bar.addWidget(self.status_msg)
        actions_bar.addStretch()
        layout.addLayout(actions_bar)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _browse_file(self, target_edit: QLineEdit) -> None:
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Executable File")
        if filepath:
            target_edit.setText(filepath)

    def refresh_diagnostics(self) -> None:
        """Scan and populate the diagnostics table."""
        deps = self.config_manager.probe_all_dependencies()
        self.table.setRowCount(len(deps))

        for row, (key, item) in enumerate(deps.items()):
            badge_type = "ok" if item.is_valid else "missing"
            badge = StatusBadge(item.status_badge, badge_type)

            name_item = QTableWidgetItem(item.display_name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            path_text = item.path if item.path else "(Not resolved)"
            path_item = QTableWidgetItem(path_text)
            path_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            ver_item = QTableWidgetItem(item.version_str)
            ver_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            self.table.setCellWidget(row, 0, badge)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, path_item)
            self.table.setItem(row, 3, ver_item)

    def save_settings(self) -> None:
        """Persist user adjustments back to config.json and reload."""
        self.config_manager.set("default_warp_engine", self.warp_combo.currentText())
        self.config_manager.set("default_threads", self.threads_spin.value())
        self.config_manager.set("default_anchors", self.anchors_spin.value())
        self.config_manager.set("default_target_i", self.lufs_spin.value())
        self.config_manager.set("default_target_tp", self.tp_spin.value())
        self.config_manager.set("default_multiband", self.multiband_cb.isChecked())
        self.config_manager.set("default_speed_detect", self.speed_detect_cb.isChecked())
        self.config_manager.set("default_overwrite", self.overwrite_cb.isChecked())

        for key, edit in self.path_edits.items():
            self.config_manager.set(key, edit.text().strip())

        saved_path = self.config_manager.save("config.json")
        self.status_msg.setText(f"[OK] Settings successfully saved to {saved_path.name}")
        self.status_msg.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        self.refresh_diagnostics()
