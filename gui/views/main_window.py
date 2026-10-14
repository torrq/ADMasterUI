"""Main application window for ADMasterUI."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui.models.config_manager import ConfigManager
from gui.views.tabs import (
    QueueTab,
    SeasonTab,
    SettingsTab,
    SyncTab,
    UtilitiesTab,
)


class MainWindow(QMainWindow):
    """Main application window hosting all operational tabs."""

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager

        self.setWindowTitle("ADMasterUI - Audio Description Sync & Mastering Toolkit")
        self.resize(1150, 800)
        self.setMinimumSize(950, 650)

        self._init_ui()
        self._update_status_bar()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Tab Widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # 1. Movie Sync Tab
        self.sync_tab = SyncTab(self.config_manager)
        self.tabs.addTab(self.sync_tab, "Movie Sync")

        # 2. Batch Queue Tab
        self.queue_tab = QueueTab(self.config_manager)
        self.tabs.addTab(self.queue_tab, "Batch Queue")

        # 3. TV Season Tab
        self.season_tab = SeasonTab(self.config_manager)
        self.tabs.addTab(self.season_tab, "TV Season")

        # 4. Utilities Tab
        self.utils_tab = UtilitiesTab(self.config_manager)
        self.tabs.addTab(self.utils_tab, "Utilities")

        # 5. Settings & Diagnostics Tab
        self.settings_tab = SettingsTab(self.config_manager)
        self.tabs.addTab(self.settings_tab, "Settings & Diagnostics")

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _update_status_bar(self) -> None:
        deps = self.config_manager.probe_all_dependencies()
        all_ok = all(d.is_valid for d in deps.values())

        if all_ok:
            self.status_bar.showMessage("Ready | All core dependencies resolved [OK]")
            self.status_bar.setStyleSheet("background-color: #1b4728; color: #ffffff;")
        else:
            missing = [k for k, v in deps.items() if not v.is_valid]
            self.status_bar.showMessage(f"Warning | Missing dependencies: {', '.join(missing)}")
            self.status_bar.setStyleSheet("background-color: #4a151b; color: #ffffff;")
