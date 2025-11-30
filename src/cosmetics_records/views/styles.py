# =============================================================================
# Cosmetics Records - QSS Stylesheets
# =============================================================================
# This module provides comprehensive QSS (Qt Style Sheets) for the application.
#
# Key Features:
#   - Complete dark and light themes
#   - Consistent color palette across themes
#   - Typography hierarchy (titles, headers, body, secondary)
#   - Proper hover/focus/pressed states for all widgets
#   - System theme detection
#
# Color Philosophy:
#   - Primary Blue: Professional, medical association
#   - Dark theme: Reduced eye strain for long sessions
#   - Light theme: Traditional, clean appearance
#   - Semantic colors (error, success, warning) consistent across themes
#
# Usage Example:
#   stylesheet = get_theme("dark")
#   app.setStyleSheet(stylesheet)
# =============================================================================

import logging
from typing import Literal

# Configure module logger
logger = logging.getLogger(__name__)

# Try to import darkdetect for system theme detection
# This is optional - if not available, we'll default to dark theme
try:
    import darkdetect

    DARKDETECT_AVAILABLE = True
except ImportError:
    DARKDETECT_AVAILABLE = False
    logger.warning("darkdetect not available - system theme detection disabled")


# =============================================================================
# Color Palette
# =============================================================================
# These colors are used consistently throughout the application.
# Keeping them as constants makes it easy to adjust the entire color scheme.

# Primary Colors - Used for interactive elements and branding
PRIMARY_BLUE = "#3B8ED0"  # Main brand color for buttons, links, accents
HOVER_BLUE = "#1F6AA5"  # Darker blue for hover states

# Dark Theme Colors
DARK_BG = "#2b2b2b"  # Main background - dark gray
DARK_SURFACE = "#333333"  # Elevated surfaces (cards, inputs)
DARK_BORDER = "#444444"  # Subtle borders and dividers
DARK_TEXT = "#E0E0E0"  # Primary text color - light gray
DARK_TEXT_SECONDARY = "#A0A0A0"  # Secondary text - medium gray
DARK_HOVER = "#3a3a3a"  # Hover state for clickable elements

# Light Theme Colors
LIGHT_BG = "#f5f5f5"  # Main background - off-white
LIGHT_SURFACE = "#ffffff"  # Elevated surfaces (cards, inputs)
LIGHT_BORDER = "#e0e0e0"  # Borders and dividers
LIGHT_TEXT = "#1a1a1a"  # Primary text - near black
LIGHT_TEXT_SECONDARY = "#666666"  # Secondary text - gray
LIGHT_HOVER = "#e8e8e8"  # Hover state for clickable elements

# Semantic Colors - Same across both themes for consistency
ERROR_RED = "#e74c3c"  # Error states, delete actions
SUCCESS_GREEN = "#27ae60"  # Success states, confirmations
WARNING_ORANGE = "#f39c12"  # Warning states, caution

# Base Typography Sizes (in points, will be scaled)
# These are the base sizes at 100% scale
BASE_SIZE_TITLE = 24  # Page titles
BASE_SIZE_HEADER = 18  # Section headers
BASE_SIZE_NAV = 14  # Navigation items
BASE_SIZE_BODY = 13  # Body text, inputs
BASE_SIZE_SECONDARY = 12  # Secondary text, captions

# Border Radius
BORDER_RADIUS = "8px"  # Consistent rounded corners


def get_scaled_sizes(scale: float = 1.0) -> dict:
    """
    Get font sizes scaled by the given factor.

    Args:
        scale: Scale factor (1.0 = 100%, 1.5 = 150%, etc.)

    Returns:
        Dictionary with scaled size strings (e.g., {"title": "24pt"})
    """
    return {
        "title": f"{int(BASE_SIZE_TITLE * scale)}pt",
        "header": f"{int(BASE_SIZE_HEADER * scale)}pt",
        "nav": f"{int(BASE_SIZE_NAV * scale)}pt",
        "body": f"{int(BASE_SIZE_BODY * scale)}pt",
        "secondary": f"{int(BASE_SIZE_SECONDARY * scale)}pt",
    }


# =============================================================================
# Theme Stylesheet Generation Functions
# =============================================================================


def generate_dark_theme(scale: float = 1.0) -> str:
    """
    Generate the dark theme stylesheet with optional scaling.

    Args:
        scale: Scale factor for font sizes (1.0 = 100%)

    Returns:
        Complete QSS stylesheet for dark theme
    """
    sizes = get_scaled_sizes(scale)
    return f"""
/* ==========================================================================
   Global Application Styles
   ========================================================================== */

QMainWindow {{
    background-color: {DARK_BG};
    color: {DARK_TEXT};
}}

/* Base widget styling - applies to all widgets unless overridden */
QWidget {{
    background-color: {DARK_BG};
    color: {DARK_TEXT};
    font-size: {sizes["body"]};
    font-family: "Segoe UI", "Ubuntu", "Arial", sans-serif;
}}

/* ==========================================================================
   Typography Styles
   ========================================================================== */

/* Page titles - used for main page headings */
.title {{
    font-size: {sizes["title"]};
    font-weight: bold;
    color: {DARK_TEXT};
}}

/* Section headers - used for subsections within pages */
.header {{
    font-size: {sizes["header"]};
    font-weight: 600;
    color: {DARK_TEXT};
}}

/* Secondary text - used for captions, hints, metadata */
.secondary {{
    font-size: {sizes["secondary"]};
    color: {DARK_TEXT_SECONDARY};
}}

/* ==========================================================================
   Labels
   ========================================================================== */

QLabel {{
    background-color: transparent;
    color: {DARK_TEXT};
    font-size: {sizes["body"]};
}}

/* ==========================================================================
   Buttons
   ========================================================================== */

QPushButton {{
    background-color: {PRIMARY_BLUE};
    color: white;
    border: none;
    border-radius: {BORDER_RADIUS};
    padding: 8px 16px;
    font-size: {sizes["body"]};
    font-weight: 500;
}}

/* Hover state - darker blue to indicate interactivity */
QPushButton:hover {{
    background-color: {HOVER_BLUE};
}}

/* Pressed state - even darker to provide click feedback */
QPushButton:pressed {{
    background-color: #164d7a;
}}

/* Disabled state - grayed out to indicate non-interactivity */
QPushButton:disabled {{
    background-color: #555555;
    color: #888888;
}}

/* Secondary button variant - less prominent than primary */
QPushButton[class="secondary"] {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER};
}}

QPushButton[class="secondary"]:hover {{
    background-color: {DARK_HOVER};
}}

/* Danger button variant - for delete/destructive actions */
QPushButton[class="danger"] {{
    background-color: {ERROR_RED};
    color: white;
}}

QPushButton[class="danger"]:hover {{
    background-color: #c0392b;
}}

/* ==========================================================================
   Text Input Fields
   ========================================================================== */

QLineEdit {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER};
    border-radius: {BORDER_RADIUS};
    padding: 8px 12px;
    font-size: {sizes["body"]};
}}

/* Focus state - blue border to indicate active input */
QLineEdit:focus {{
    border: 1px solid {PRIMARY_BLUE};
}}

/* Disabled state - grayed out */
QLineEdit:disabled {{
    background-color: #3a3a3a;
    color: #888888;
}}

/* ==========================================================================
   Text Edit (Multi-line)
   ========================================================================== */

QTextEdit {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER};
    border-radius: {BORDER_RADIUS};
    padding: 8px;
    font-size: {sizes["body"]};
}}

QTextEdit:focus {{
    border: 1px solid {PRIMARY_BLUE};
}}

/* ==========================================================================
   List Widgets
   ========================================================================== */

QListWidget {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER};
    border-radius: {BORDER_RADIUS};
    font-size: {sizes["body"]};
    outline: none;  /* Remove focus outline - we use selection color instead */
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 4px;
}}

/* Hover state - subtle highlight */
QListWidget::item:hover {{
    background-color: {DARK_HOVER};
}}

/* Selected state - primary color highlight */
QListWidget::item:selected {{
    background-color: {PRIMARY_BLUE};
    color: white;
}}

/* ==========================================================================
   Scroll Areas
   ========================================================================== */

QScrollArea {{
    background-color: transparent;
    border: none;
}}

/* Scrollbar styling for vertical scrollbars */
QScrollBar:vertical {{
    background-color: {DARK_BG};
    width: 12px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {DARK_BORDER};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #555555;
}}

/* Remove arrows from scrollbar */
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Horizontal scrollbar styling */
QScrollBar:horizontal {{
    background-color: {DARK_BG};
    height: 12px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background-color: {DARK_BORDER};
    border-radius: 6px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: #555555;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ==========================================================================
   Frames and Containers
   ========================================================================== */

QFrame {{
    background-color: {DARK_SURFACE};
    border: 1px solid {DARK_BORDER};
    border-radius: {BORDER_RADIUS};
}}

/* Frameless variant - no border */
QFrame[frameShape="0"] {{
    border: none;
}}

/* ==========================================================================
   Client/Inventory List Rows
   ========================================================================== */

QFrame[client_row="true"], QFrame[inventory_row="true"] {{
    background-color: #3a3a3a;
    border: none;
    border-radius: 6px;
}}

QFrame[client_row="true"]:hover, QFrame[inventory_row="true"]:hover {{
    background-color: #454545;
}}

QLabel[client_name="true"] {{
    background-color: transparent;
}}

/* ==========================================================================
   Tag Chips (Small)
   ========================================================================== */

QLabel[tag_chip_small="true"] {{
    background-color: #444444;
    color: {DARK_TEXT};
    border-radius: 4px;
    padding: 2px 8px;
    font-size: {sizes["secondary"]};
}}

QLabel[tag_more="true"] {{
    color: {DARK_TEXT_SECONDARY};
    font-size: {sizes["secondary"]};
}}

/* ==========================================================================
   Client Detail Header
   ========================================================================== */

QWidget[detail_header="true"] {{
    background-color: transparent;
}}

QLabel[client_detail_name="true"] {{
    background-color: transparent;
    font-size: 24px;
    font-weight: bold;
    color: {DARK_TEXT};
}}

QLabel[client_age="true"] {{
    background-color: transparent;
    font-size: 18px;
    color: {DARK_TEXT_SECONDARY};
}}

QLabel[allergies_warning="true"] {{
    background-color: transparent;
    font-size: 14px;
    color: #cc3333;
    font-weight: 500;
}}

/* ==========================================================================
   History Section
   ========================================================================== */

QScrollArea[history_section="true"] {{
    background-color: transparent;
    border: 1px solid {DARK_BORDER};
    border-radius: {BORDER_RADIUS};
}}

QFrame[history_item="true"] {{
    background-color: #1e1e1e;
    border: none;
    border-radius: 6px;
}}

QFrame[history_item="true"]:hover {{
    background-color: #282828;
}}

QLabel[history_date="true"] {{
    background-color: transparent;
    font-size: 11px;
    color: {DARK_TEXT_SECONDARY};
}}

QLabel[history_notes="true"] {{
    background-color: transparent;
    color: {DARK_TEXT};
}}

QLabel[history_timestamp="true"] {{
    background-color: transparent;
    font-size: 10px;
    color: {DARK_TEXT_SECONDARY};
}}

QLabel[history_end_message="true"] {{
    background-color: transparent;
    font-size: 12px;
    color: {DARK_TEXT_SECONDARY};
    padding: 8px;
}}

/* ==========================================================================
   Dialog Styling
   ========================================================================== */

QFrame[dialog_frame="true"] {{
    background-color: {DARK_SURFACE};
    border: 1px solid {DARK_BORDER};
    border-radius: 12px;
}}

QWidget[dialog_title_bar="true"] {{
    background-color: transparent;
    border: none;
}}

QLabel[dialog_title="true"] {{
    background-color: transparent;
    font-size: 20px;
    font-weight: bold;
    color: {DARK_TEXT};
}}

QPushButton[dialog_close="true"] {{
    background-color: transparent;
    color: {DARK_TEXT_SECONDARY};
    border: none;
    border-radius: 15px;
    font-size: 20px;
    font-weight: bold;
}}

QPushButton[dialog_close="true"]:hover {{
    background-color: {DARK_HOVER};
    color: {DARK_TEXT};
}}

/* ==========================================================================
   Combo Box (Dropdown)
   ========================================================================== */

QComboBox {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER};
    border-radius: {BORDER_RADIUS};
    padding: 8px 12px;
    font-size: {sizes["body"]};
}}

QComboBox:hover {{
    border: 1px solid {PRIMARY_BLUE};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;  /* Use Unicode arrow in code instead */
    border: none;
}}

/* Dropdown list styling */
QComboBox QAbstractItemView {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER};
    selection-background-color: {PRIMARY_BLUE};
}}

/* ==========================================================================
   Table Widget
   ========================================================================== */

QTableWidget {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER};
    gridline-color: {DARK_BORDER};
    font-size: {sizes["body"]};
}}

QTableWidget::item {{
    padding: 4px;
}}

QTableWidget::item:selected {{
    background-color: {PRIMARY_BLUE};
    color: white;
}}

QHeaderView::section {{
    background-color: {DARK_BG};
    color: {DARK_TEXT};
    border: none;
    border-bottom: 1px solid {DARK_BORDER};
    padding: 8px;
    font-weight: 600;
}}

/* ==========================================================================
   Calendar Widget
   ========================================================================== */

QCalendarWidget {{
    background-color: {DARK_SURFACE};
}}

QCalendarWidget QToolButton {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
    border: none;
    border-radius: 4px;
    padding: 4px;
}}

QCalendarWidget QToolButton:hover {{
    background-color: {DARK_HOVER};
}}

QCalendarWidget QMenu {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
}}

QCalendarWidget QSpinBox {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER};
}}

/* Calendar grid */
QCalendarWidget QAbstractItemView {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
    selection-background-color: {PRIMARY_BLUE};
    selection-color: white;
}}

/* ==========================================================================
   Checkboxes and Radio Buttons
   ========================================================================== */

QCheckBox {{
    color: {DARK_TEXT};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {DARK_BORDER};
    border-radius: 4px;
    background-color: {DARK_SURFACE};
}}

QCheckBox::indicator:checked {{
    background-color: {PRIMARY_BLUE};
    border-color: {PRIMARY_BLUE};
}}

QRadioButton {{
    color: {DARK_TEXT};
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {DARK_BORDER};
    border-radius: 9px;
    background-color: {DARK_SURFACE};
}}

QRadioButton::indicator:checked {{
    background-color: {PRIMARY_BLUE};
    border-color: {PRIMARY_BLUE};
}}

/* ==========================================================================
   Tab Widget
   ========================================================================== */

QTabWidget::pane {{
    border: 1px solid {DARK_BORDER};
    background-color: {DARK_SURFACE};
}}

QTabBar::tab {{
    background-color: {DARK_BG};
    color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER};
    padding: 8px 16px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {DARK_SURFACE};
    border-bottom-color: {DARK_SURFACE};
}}

QTabBar::tab:hover {{
    background-color: {DARK_HOVER};
}}

/* ==========================================================================
   Tooltips
   ========================================================================== */

QToolTip {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER};
    padding: 4px;
    border-radius: 4px;
}}

/* ==========================================================================
   Navigation Bar Buttons
   ========================================================================== */

QPushButton[nav_item="true"] {{
    background-color: transparent;
    color: {DARK_TEXT};
    border: none;
    border-radius: 4px;
    font-size: {sizes["nav"]};
    text-align: left;
    padding-left: 16px;
}}

QPushButton[nav_item="true"]:hover {{
    background-color: {DARK_HOVER};
}}

QPushButton[nav_item="true"][active="true"] {{
    background-color: {PRIMARY_BLUE};
    color: white;
}}

/* ==========================================================================
   Navigation Toggle Button
   ========================================================================== */

QPushButton[toggle_nav="true"] {{
    background-color: #555555;
    color: white;
    border: 1px solid {DARK_BORDER};
    border-radius: 4px;
    font-size: 14px;
    font-weight: bold;
    padding: 0px;
}}

QPushButton[toggle_nav="true"]:hover {{
    background-color: #666666;
    border-color: #777777;
}}

QPushButton[toggle_nav="true"]:pressed {{
    background-color: #444444;
}}

/* ==========================================================================
   Alphabet Filter Buttons
   ========================================================================== */

QPushButton[alphabet_filter="true"] {{
    background-color: transparent;
    color: #888888;
    border: none;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    padding: 2px;
}}

QPushButton[alphabet_filter="true"]:hover {{
    background-color: {DARK_HOVER};
    color: {DARK_TEXT};
}}

QPushButton[alphabet_filter="true"][active="true"] {{
    background-color: #555555;
    color: white;
}}

/* ==========================================================================
   Alphabet Filter Arrow Buttons
   ========================================================================== */

QPushButton[alphabet_arrow="true"] {{
    background-color: transparent;
    color: #888888;
    border: none;
    border-radius: 4px;
    font-size: 10px;
    padding: 2px;
}}

QPushButton[alphabet_arrow="true"]:hover {{
    background-color: {DARK_HOVER};
    color: {DARK_TEXT};
}}

QPushButton[alphabet_arrow="true"]:pressed {{
    background-color: #555555;
}}
"""


def generate_light_theme(scale: float = 1.0) -> str:
    """
    Generate the light theme stylesheet with optional scaling.

    Args:
        scale: Scale factor for font sizes (1.0 = 100%)

    Returns:
        Complete QSS stylesheet for light theme
    """
    sizes = get_scaled_sizes(scale)
    return f"""
/* ==========================================================================
   Global Application Styles
   ========================================================================== */

QMainWindow {{
    background-color: {LIGHT_BG};
    color: {LIGHT_TEXT};
}}

QWidget {{
    background-color: {LIGHT_BG};
    color: {LIGHT_TEXT};
    font-size: {sizes["body"]};
    font-family: "Segoe UI", "Ubuntu", "Arial", sans-serif;
}}

/* ==========================================================================
   Typography Styles
   ========================================================================== */

.title {{
    font-size: {sizes["title"]};
    font-weight: bold;
    color: {LIGHT_TEXT};
}}

.header {{
    font-size: {sizes["header"]};
    font-weight: 600;
    color: {LIGHT_TEXT};
}}

.secondary {{
    font-size: {sizes["secondary"]};
    color: {LIGHT_TEXT_SECONDARY};
}}

/* ==========================================================================
   Labels
   ========================================================================== */

QLabel {{
    background-color: transparent;
    color: {LIGHT_TEXT};
    font-size: {sizes["body"]};
}}

/* ==========================================================================
   Buttons
   ========================================================================== */

QPushButton {{
    background-color: {PRIMARY_BLUE};
    color: white;
    border: none;
    border-radius: {BORDER_RADIUS};
    padding: 8px 16px;
    font-size: {sizes["body"]};
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {HOVER_BLUE};
}}

QPushButton:pressed {{
    background-color: #164d7a;
}}

QPushButton:disabled {{
    background-color: #cccccc;
    color: #888888;
}}

QPushButton[class="secondary"] {{
    background-color: {LIGHT_SURFACE};
    color: {LIGHT_TEXT};
    border: 1px solid {LIGHT_BORDER};
}}

QPushButton[class="secondary"]:hover {{
    background-color: {LIGHT_HOVER};
}}

QPushButton[class="danger"] {{
    background-color: {ERROR_RED};
    color: white;
}}

QPushButton[class="danger"]:hover {{
    background-color: #c0392b;
}}

/* ==========================================================================
   Text Input Fields
   ========================================================================== */

QLineEdit {{
    background-color: {LIGHT_SURFACE};
    color: {LIGHT_TEXT};
    border: 1px solid {LIGHT_BORDER};
    border-radius: {BORDER_RADIUS};
    padding: 8px 12px;
    font-size: {sizes["body"]};
}}

QLineEdit:focus {{
    border: 1px solid {PRIMARY_BLUE};
}}

QLineEdit:disabled {{
    background-color: #f0f0f0;
    color: #888888;
}}

/* ==========================================================================
   Text Edit (Multi-line)
   ========================================================================== */

QTextEdit {{
    background-color: {LIGHT_SURFACE};
    color: {LIGHT_TEXT};
    border: 1px solid {LIGHT_BORDER};
    border-radius: {BORDER_RADIUS};
    padding: 8px;
    font-size: {sizes["body"]};
}}

QTextEdit:focus {{
    border: 1px solid {PRIMARY_BLUE};
}}

/* ==========================================================================
   List Widgets
   ========================================================================== */

QListWidget {{
    background-color: {LIGHT_SURFACE};
    color: {LIGHT_TEXT};
    border: 1px solid {LIGHT_BORDER};
    border-radius: {BORDER_RADIUS};
    font-size: {sizes["body"]};
    outline: none;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 4px;
}}

QListWidget::item:hover {{
    background-color: {LIGHT_HOVER};
}}

QListWidget::item:selected {{
    background-color: {PRIMARY_BLUE};
    color: white;
}}

/* ==========================================================================
   Scroll Areas
   ========================================================================== */

QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background-color: {LIGHT_BG};
    width: 12px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {LIGHT_BORDER};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #c0c0c0;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {LIGHT_BG};
    height: 12px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background-color: {LIGHT_BORDER};
    border-radius: 6px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: #c0c0c0;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ==========================================================================
   Frames and Containers
   ========================================================================== */

QFrame {{
    background-color: {LIGHT_SURFACE};
    border: 1px solid {LIGHT_BORDER};
    border-radius: {BORDER_RADIUS};
}}

QFrame[frameShape="0"] {{
    border: none;
}}

/* ==========================================================================
   Client/Inventory List Rows
   ========================================================================== */

QFrame[client_row="true"], QFrame[inventory_row="true"] {{
    background-color: #e8e8e8;
    border: none;
    border-radius: 6px;
}}

QFrame[client_row="true"]:hover, QFrame[inventory_row="true"]:hover {{
    background-color: #d8d8d8;
}}

QLabel[client_name="true"] {{
    background-color: transparent;
}}

/* ==========================================================================
   Tag Chips (Small)
   ========================================================================== */

QLabel[tag_chip_small="true"] {{
    background-color: #e0e0e0;
    color: #333333;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: {sizes["secondary"]};
}}

QLabel[tag_more="true"] {{
    color: {LIGHT_TEXT_SECONDARY};
    font-size: {sizes["secondary"]};
}}

/* ==========================================================================
   Client Detail Header
   ========================================================================== */

QWidget[detail_header="true"] {{
    background-color: transparent;
}}

QLabel[client_detail_name="true"] {{
    background-color: transparent;
    font-size: 24px;
    font-weight: bold;
    color: {LIGHT_TEXT};
}}

QLabel[client_age="true"] {{
    background-color: transparent;
    font-size: 18px;
    color: {LIGHT_TEXT_SECONDARY};
}}

QLabel[allergies_warning="true"] {{
    background-color: transparent;
    font-size: 14px;
    color: #aa0000;
    font-weight: 500;
}}

/* ==========================================================================
   History Section
   ========================================================================== */

QScrollArea[history_section="true"] {{
    background-color: transparent;
    border: 1px solid {LIGHT_BORDER};
    border-radius: {BORDER_RADIUS};
}}

QFrame[history_item="true"] {{
    background-color: #ffffff;
    border: none;
    border-radius: 6px;
}}

QFrame[history_item="true"]:hover {{
    background-color: #f5f5f5;
}}

QLabel[history_date="true"] {{
    background-color: transparent;
    font-size: 11px;
    color: {LIGHT_TEXT_SECONDARY};
}}

QLabel[history_notes="true"] {{
    background-color: transparent;
    color: {LIGHT_TEXT};
}}

QLabel[history_timestamp="true"] {{
    background-color: transparent;
    font-size: 10px;
    color: {LIGHT_TEXT_SECONDARY};
}}

QLabel[history_end_message="true"] {{
    background-color: transparent;
    font-size: 12px;
    color: {LIGHT_TEXT_SECONDARY};
    padding: 8px;
}}

/* ==========================================================================
   Dialog Styling
   ========================================================================== */

QFrame[dialog_frame="true"] {{
    background-color: {LIGHT_SURFACE};
    border: 1px solid {LIGHT_BORDER};
    border-radius: 12px;
}}

QWidget[dialog_title_bar="true"] {{
    background-color: transparent;
    border: none;
}}

QLabel[dialog_title="true"] {{
    background-color: transparent;
    font-size: 20px;
    font-weight: bold;
    color: {LIGHT_TEXT};
}}

QPushButton[dialog_close="true"] {{
    background-color: transparent;
    color: {LIGHT_TEXT_SECONDARY};
    border: none;
    border-radius: 15px;
    font-size: 20px;
    font-weight: bold;
}}

QPushButton[dialog_close="true"]:hover {{
    background-color: {LIGHT_HOVER};
    color: {LIGHT_TEXT};
}}

/* ==========================================================================
   Combo Box (Dropdown)
   ========================================================================== */

QComboBox {{
    background-color: {LIGHT_SURFACE};
    color: {LIGHT_TEXT};
    border: 1px solid {LIGHT_BORDER};
    border-radius: {BORDER_RADIUS};
    padding: 8px 12px;
    font-size: {sizes["body"]};
}}

QComboBox:hover {{
    border: 1px solid {PRIMARY_BLUE};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border: none;
}}

QComboBox QAbstractItemView {{
    background-color: {LIGHT_SURFACE};
    color: {LIGHT_TEXT};
    border: 1px solid {LIGHT_BORDER};
    selection-background-color: {PRIMARY_BLUE};
}}

/* ==========================================================================
   Table Widget
   ========================================================================== */

QTableWidget {{
    background-color: {LIGHT_SURFACE};
    color: {LIGHT_TEXT};
    border: 1px solid {LIGHT_BORDER};
    gridline-color: {LIGHT_BORDER};
    font-size: {sizes["body"]};
}}

QTableWidget::item {{
    padding: 4px;
}}

QTableWidget::item:selected {{
    background-color: {PRIMARY_BLUE};
    color: white;
}}

QHeaderView::section {{
    background-color: {LIGHT_BG};
    color: {LIGHT_TEXT};
    border: none;
    border-bottom: 1px solid {LIGHT_BORDER};
    padding: 8px;
    font-weight: 600;
}}

/* ==========================================================================
   Calendar Widget
   ========================================================================== */

QCalendarWidget {{
    background-color: {LIGHT_SURFACE};
}}

QCalendarWidget QToolButton {{
    background-color: {LIGHT_SURFACE};
    color: {LIGHT_TEXT};
    border: none;
    border-radius: 4px;
    padding: 4px;
}}

QCalendarWidget QToolButton:hover {{
    background-color: {LIGHT_HOVER};
}}

QCalendarWidget QMenu {{
    background-color: {LIGHT_SURFACE};
    color: {LIGHT_TEXT};
}}

QCalendarWidget QSpinBox {{
    background-color: {LIGHT_SURFACE};
    color: {LIGHT_TEXT};
    border: 1px solid {LIGHT_BORDER};
}}

QCalendarWidget QAbstractItemView {{
    background-color: {LIGHT_SURFACE};
    color: {LIGHT_TEXT};
    selection-background-color: {PRIMARY_BLUE};
    selection-color: white;
}}

/* ==========================================================================
   Checkboxes and Radio Buttons
   ========================================================================== */

QCheckBox {{
    color: {LIGHT_TEXT};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {LIGHT_BORDER};
    border-radius: 4px;
    background-color: {LIGHT_SURFACE};
}}

QCheckBox::indicator:checked {{
    background-color: {PRIMARY_BLUE};
    border-color: {PRIMARY_BLUE};
}}

QRadioButton {{
    color: {LIGHT_TEXT};
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {LIGHT_BORDER};
    border-radius: 9px;
    background-color: {LIGHT_SURFACE};
}}

QRadioButton::indicator:checked {{
    background-color: {PRIMARY_BLUE};
    border-color: {PRIMARY_BLUE};
}}

/* ==========================================================================
   Tab Widget
   ========================================================================== */

QTabWidget::pane {{
    border: 1px solid {LIGHT_BORDER};
    background-color: {LIGHT_SURFACE};
}}

QTabBar::tab {{
    background-color: {LIGHT_BG};
    color: {LIGHT_TEXT};
    border: 1px solid {LIGHT_BORDER};
    padding: 8px 16px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {LIGHT_SURFACE};
    border-bottom-color: {LIGHT_SURFACE};
}}

QTabBar::tab:hover {{
    background-color: {LIGHT_HOVER};
}}

/* ==========================================================================
   Tooltips
   ========================================================================== */

QToolTip {{
    background-color: {LIGHT_SURFACE};
    color: {LIGHT_TEXT};
    border: 1px solid {LIGHT_BORDER};
    padding: 4px;
    border-radius: 4px;
}}

/* ==========================================================================
   Navigation Bar Buttons
   ========================================================================== */

QPushButton[nav_item="true"] {{
    background-color: transparent;
    color: {LIGHT_TEXT};
    border: none;
    border-radius: 4px;
    font-size: {sizes["nav"]};
    text-align: left;
    padding-left: 16px;
}}

QPushButton[nav_item="true"]:hover {{
    background-color: {LIGHT_HOVER};
}}

QPushButton[nav_item="true"][active="true"] {{
    background-color: {PRIMARY_BLUE};
    color: white;
}}

/* ==========================================================================
   Navigation Toggle Button
   ========================================================================== */

QPushButton[toggle_nav="true"] {{
    background-color: #888888;
    color: white;
    border: 1px solid {LIGHT_BORDER};
    border-radius: 4px;
    font-size: 14px;
    font-weight: bold;
    padding: 0px;
}}

QPushButton[toggle_nav="true"]:hover {{
    background-color: #777777;
    border-color: #666666;
}}

QPushButton[toggle_nav="true"]:pressed {{
    background-color: #666666;
}}

/* ==========================================================================
   Alphabet Filter Buttons
   ========================================================================== */

QPushButton[alphabet_filter="true"] {{
    background-color: transparent;
    color: #666666;
    border: none;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    padding: 2px;
}}

QPushButton[alphabet_filter="true"]:hover {{
    background-color: {LIGHT_HOVER};
    color: {LIGHT_TEXT};
}}

QPushButton[alphabet_filter="true"][active="true"] {{
    background-color: #888888;
    color: white;
}}

/* ==========================================================================
   Alphabet Filter Arrow Buttons
   ========================================================================== */

QPushButton[alphabet_arrow="true"] {{
    background-color: transparent;
    color: #666666;
    border: none;
    border-radius: 4px;
    font-size: 10px;
    padding: 2px;
}}

QPushButton[alphabet_arrow="true"]:hover {{
    background-color: {LIGHT_HOVER};
    color: {LIGHT_TEXT};
}}

QPushButton[alphabet_arrow="true"]:pressed {{
    background-color: #888888;
}}
"""


# =============================================================================
# Theme Functions
# =============================================================================


def get_theme(theme_name: Literal["dark", "light", "system"], scale: float = 1.0) -> str:
    """
    Get the QSS stylesheet for the specified theme with optional scaling.

    Args:
        theme_name: The theme to load - "dark", "light", or "system"
        scale: Scale factor for UI elements (1.0 = 100%, 1.5 = 150%, etc.)

    Returns:
        str: The complete QSS stylesheet with scaled font sizes

    Note:
        If "system" is specified, this will detect the system theme
        and return the appropriate stylesheet.
    """
    if theme_name == "system":
        # Detect system theme
        system_theme = detect_system_theme()
        logger.info(f"System theme detected: {system_theme}")
        if system_theme == "dark":
            return generate_dark_theme(scale)
        else:
            return generate_light_theme(scale)

    elif theme_name == "dark":
        return generate_dark_theme(scale)

    elif theme_name == "light":
        return generate_light_theme(scale)

    else:
        logger.warning(f"Unknown theme '{theme_name}', defaulting to dark")
        return generate_dark_theme(scale)


def detect_system_theme() -> Literal["dark", "light"]:
    """
    Detect the system's current theme preference.

    Returns:
        str: "dark" or "light" based on system settings

    Note:
        This uses the darkdetect library if available. If darkdetect is not
        installed or fails to detect the theme, it defaults to "dark".

        System theme detection works on:
        - Windows 10+ (reads registry for app theme)
        - macOS 10.14+ (reads system defaults)
        - Linux (reads GTK theme settings)
    """
    if not DARKDETECT_AVAILABLE:
        logger.debug("darkdetect not available, defaulting to dark theme")
        return "dark"

    try:
        # darkdetect.theme() returns "Dark" or "Light" (capitalized)
        # or None if it can't detect
        system_theme = darkdetect.theme()

        if system_theme is None:
            logger.debug("Could not detect system theme, defaulting to dark")
            return "dark"

        # Convert to lowercase for consistency
        return "dark" if system_theme.lower() == "dark" else "light"

    except Exception as e:
        logger.warning(f"Error detecting system theme: {e}, defaulting to dark")
        return "dark"
