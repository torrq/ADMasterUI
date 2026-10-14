"""Application entry point and lifecycle manager for ADMasterUI."""

import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from gui.models.config_manager import ConfigManager
from gui.theme import DARK_THEME_QSS
from gui.views.main_window import MainWindow


def run() -> int:
    """Launch the ADMasterUI PyQt6 desktop application."""
    # Ensure High-DPI support on modern displays
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("ADMasterUI")
    app.setOrganizationName("ADMaster")

    # Load configuration
    config_mgr = ConfigManager()

    # Apply dark theme
    app.setStyleSheet(DARK_THEME_QSS)

    window = MainWindow(config_mgr)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
