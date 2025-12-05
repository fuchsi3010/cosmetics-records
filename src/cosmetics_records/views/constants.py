# =============================================================================
# Cosmetics Records - UI Constants
# =============================================================================
# This module defines layout constants for consistent styling across the UI.
#
# Key Features:
#   - Spacing scale following design system (5/10/20/30px)
#   - Standard component heights for consistency
#   - Dialog size presets for different content types
#   - Button sizing standards
#
# Design Philosophy:
#   - Use these constants instead of hardcoded values
#   - Ensures visual consistency across the application
#   - Makes it easy to adjust spacing globally
#   - Follows CLAUDE.md design system guidelines
#
# Usage Example:
#   from cosmetics_records.views.constants import Spacing, DialogSize
#
#   layout.setContentsMargins(Spacing.MEDIUM, Spacing.MEDIUM, ...)
#   dialog = BaseDialog("Title", width=DialogSize.NORMAL_WIDTH)
# =============================================================================


class Spacing:
    """
    Spacing scale constants following the design system.

    Based on CLAUDE.md design guidelines:
    - MICRO (5px): Button padding, tight spacing
    - SMALL (10px): Related elements, compact layouts
    - MEDIUM (20px): Section padding, default spacing
    - LARGE (30px): Page margins, section separation
    """

    # Micro spacing - for tight areas like button padding
    MICRO = 5

    # Small spacing - between related elements
    SMALL = 10

    # Medium spacing - default section padding
    MEDIUM = 20

    # Large spacing - page margins, major sections
    LARGE = 30

    # Form-specific spacing
    FORM_ROW_SPACING = 12  # Between form rows
    FORM_LABEL_SPACING = 8  # Between label and input


class ComponentHeight:
    """
    Standard heights for UI components.

    Ensures consistent sizing across different views.
    """

    # List item rows
    LIST_ROW = 50  # Standard list row (client/inventory rows)
    LIST_ROW_TALL = 60  # Tall list row (with subtitle)

    # Input fields
    TEXTAREA_SMALL = 60  # Single-line text areas
    TEXTAREA_MEDIUM = 80  # Multi-line text areas
    TEXTAREA_LARGE = 150  # Large text areas (e.g., notes)

    # Headers and bars
    TOP_BAR = 60  # Top bar with search/buttons
    TITLE_BAR = 50  # Dialog title bar
    HEADER = 70  # View header with client info

    # Buttons
    BUTTON_SMALL = 24  # Icon buttons
    BUTTON_NORMAL = 36  # Standard buttons


class DialogSize:
    """
    Standard dialog dimensions for different content types.

    Presets ensure dialogs are appropriately sized for their content
    while maintaining visual consistency.
    """

    # Compact dialogs (confirmations, simple messages)
    COMPACT_WIDTH = 400
    COMPACT_HEIGHT = 200

    # Normal dialogs (simple forms)
    NORMAL_WIDTH = 500
    NORMAL_HEIGHT = 400

    # Large dialogs (complex forms like client edit)
    LARGE_WIDTH = 600
    LARGE_HEIGHT = 700

    # Extra large dialogs (very detailed forms)
    XL_WIDTH = 700
    XL_HEIGHT = 800


class ButtonWidth:
    """
    Standard button minimum widths.

    Ensures buttons are large enough to be easily clickable
    while maintaining consistent proportions.
    """

    # Minimum widths
    SMALL = 80  # Icon + short text (e.g., "Edit")
    NORMAL = 100  # Standard action buttons
    LARGE = 150  # Primary action buttons
    XL = 220  # Full-width buttons


class FontSize:
    """
    Typography scale following the design system.

    Based on CLAUDE.md typography guidelines:
    - Level 1: 24pt bold (page titles)
    - Level 2: 18pt bold (dialog/section headers)
    - Level 3: 16pt bold (subsections)
    - Level 4: 14pt (navigation, primary actions)
    - Level 5: 13pt (body text, forms)
    """

    # Heading sizes
    H1 = 24  # Page titles
    H2 = 18  # Dialog/section headers
    H3 = 16  # Subsections

    # Body sizes
    BODY = 13  # Standard body text
    NAV = 14  # Navigation, primary actions

    # Small text
    SMALL = 11  # Captions, hints
    TINY = 10  # Status indicators
