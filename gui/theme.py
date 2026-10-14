"""Pure ASCII Dark Theme stylesheet and color palette for ADMasterUI."""

DARK_THEME_QSS = """
/* Base Window and Widgets */
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Segoe UI", "San Francisco", "Helvetica Neue", "Ubuntu", sans-serif;
    font-size: 13px;
    selection-background-color: #007acc;
    selection-color: #ffffff;
}

QMainWindow {
    background-color: #181818;
}

/* Tab Widget & Bar */
QTabWidget::pane {
    border: 1px solid #333333;
    background-color: #1e1e1e;
    top: -1px;
}

QTabBar::tab {
    background-color: #252526;
    color: #aaaaaa;
    padding: 8px 18px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid #333333;
    border-bottom: none;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #ffffff;
    border-bottom: 2px solid #007acc;
}

QTabBar::tab:hover:!selected {
    background-color: #2d2d30;
    color: #ffffff;
}

/* Group Boxes */
QGroupBox {
    border: 1px solid #383838;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 16px;
    font-weight: bold;
    color: #4ec9b0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    background-color: #1e1e1e;
}

/* Push Buttons */
QPushButton {
    background-color: #0e639c;
    color: #ffffff;
    border: 1px solid #1177bb;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #1177bb;
}

QPushButton:pressed {
    background-color: #0d5a8d;
}

QPushButton:disabled {
    background-color: #333333;
    color: #777777;
    border-color: #444444;
}

/* Secondary / Flat Buttons */
QPushButton[secondary="true"] {
    background-color: #2d2d30;
    border: 1px solid #3e3e42;
    color: #cccccc;
}

QPushButton[secondary="true"]:hover {
    background-color: #3e3e42;
    color: #ffffff;
}

/* Line Edits & Text Inputs */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 5px 8px;
    color: #f1f1f1;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #007acc;
}

/* Combo Boxes */
QComboBox {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 5px 8px;
    color: #f1f1f1;
    min-width: 6em;
}

QComboBox:hover {
    border-color: #007acc;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #3c3c3c;
}

QComboBox QAbstractItemView {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    selection-background-color: #007acc;
    selection-color: #ffffff;
}

/* Checkboxes & Radio Buttons */
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #cccccc;
}

QCheckBox:hover, QRadioButton:hover {
    color: #ffffff;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #555555;
    background-color: #252526;
}

QCheckBox::indicator:checked {
    background-color: #007acc;
    border-color: #007acc;
}

/* Progress Bars */
QProgressBar {
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    text-align: center;
    background-color: #252526;
    color: #ffffff;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #007acc;
    border-radius: 3px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background-color: #1e1e1e;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #424242;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Status Bar */
QStatusBar {
    background-color: #007acc;
    color: #ffffff;
    font-size: 12px;
}
"""
