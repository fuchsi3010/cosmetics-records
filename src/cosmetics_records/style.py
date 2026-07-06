"""Theme layer reproducing the 1.x look: blue accent, dark/light palettes,
8px radii, 24/18/14/13 type scale. QPalette carries the base colors (Fusion
renders from it), the stylesheet adds spacing, radii and the sidebar."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

# Salon-warm palette: dusty rose accent, warm-tinted neutrals.
# The 1.x blue was ACCENT "#3B8ED0" / HOVER "#1F6AA5" with plain gray neutrals.
ACCENT = "#B85C79"
ACCENT_HOVER = "#9C4762"
ERROR = "#D93A2B"

DARK = {
    "bg": "#2e2a28",
    "surface": "#38322f",
    "sidebar": "#262220",
    "border": "#4a423e",
    "text": "#EAE4E0",
    "muted": "#A89C94",
    "hover": "#403935",
}
LIGHT = {
    "bg": "#f8f4f1",
    "surface": "#fffdfb",
    "sidebar": "#f0e8e3",
    "border": "#e3d8d1",
    "text": "#332b27",
    "muted": "#8a7a71",
    "hover": "#efe5df",
}


def _palette(c: dict) -> QPalette:
    p = QPalette()
    for role, color in {
        QPalette.ColorRole.Window: c["bg"],
        QPalette.ColorRole.WindowText: c["text"],
        QPalette.ColorRole.Base: c["surface"],
        QPalette.ColorRole.AlternateBase: c["hover"],
        QPalette.ColorRole.Text: c["text"],
        QPalette.ColorRole.Button: c["surface"],
        QPalette.ColorRole.ButtonText: c["text"],
        QPalette.ColorRole.Highlight: ACCENT,
        QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.PlaceholderText: c["muted"],
        QPalette.ColorRole.ToolTipBase: c["surface"],
        QPalette.ColorRole.ToolTipText: c["text"],
    }.items():
        p.setColor(role, QColor(color))
    for role in (
        QPalette.ColorRole.Text,
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.ButtonText,
    ):
        p.setColor(QPalette.ColorGroup.Disabled, role, QColor(c["muted"]))
    return p


def _stylesheet(c: dict) -> str:
    return f"""
QWidget {{ font-size: 13px; }}

QLineEdit, QPlainTextEdit, QTextBrowser, QSpinBox, QDoubleSpinBox,
QDateEdit, QComboBox {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QDateEdit:focus, QComboBox:focus {{ border-color: {ACCENT}; }}

QComboBox QAbstractItemView {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    selection-background-color: {ACCENT};
}}

QPushButton {{
    background: {ACCENT};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}}
QPushButton:hover {{ background: {ACCENT_HOVER}; }}
QPushButton:pressed {{ background: {ACCENT_HOVER}; padding-top: 9px; }}
QPushButton:disabled {{ background: {c["hover"]}; color: {c["muted"]}; }}

QListWidget {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: 8px;
    padding: 4px;
    outline: 0;
    /* let the QSS item background be the only selection paint */
    selection-background-color: transparent;
}}
QListWidget::item {{ padding: 8px; border-radius: 5px; }}
QListWidget::item:selected {{ background: {ACCENT}; color: white; }}
QListWidget::item:hover:!selected {{ background: {c["hover"]}; }}

QGroupBox {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: 8px;
    padding: 24px 12px 12px 12px;
    margin-top: 8px;
    font-weight: bold;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; color: {ACCENT}; }}

QWidget#Sidebar {{ background: {c["sidebar"]}; }}
QLabel#AppTitle {{
    font-size: 15px;
    font-weight: bold;
    padding: 18px 12px 10px 12px;
    background: transparent;
}}
QListWidget#Nav {{
    background: {c["sidebar"]};
    border: none;
    border-radius: 0;
    font-size: 14px;
    padding: 6px;
}}
QListWidget#Nav::item {{ padding: 10px 12px; border-radius: 6px; margin: 2px 4px; }}

QLabel#PageTitle {{ font-size: 24px; font-weight: bold; }}
QLabel#DetailTitle {{ font-size: 18px; font-weight: bold; }}
QLabel#SectionTitle {{ font-size: 14px; font-weight: bold; }}
QLabel#Allergy {{ color: {ERROR}; font-weight: bold; }}
QLabel#Muted, QStatusBar {{ color: {c["muted"]}; }}

QSplitter::handle {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{
    background: {c["border"]}; border-radius: 5px; min-height: 30px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
"""


def apply_theme(mode: str) -> None:
    """mode: 'system' | 'light' | 'dark' — applies palette + stylesheet."""
    app = QApplication.instance()
    if mode == "system":
        dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    else:
        dark = mode == "dark"
    c = DARK if dark else LIGHT
    app.setPalette(_palette(c))
    app.setStyleSheet(_stylesheet(c))
