# =============================================================================
# Cosmetics Records - Alphabet Filter Component
# =============================================================================
# This module provides an A-Z filter for quick navigation through lists.
#
# Key Features:
#   - Vertical layout of letter buttons A-Z
#   - Special "#" button for numbers/special characters
#   - "All" button to clear filter
#   - Active letter highlighting
#   - Signal emission on filter change
#   - Fixed width for consistent layout
#   - Arrow buttons for navigation when letters don't fit (hidden if not needed)
#
# Design Philosophy:
#   - Common pattern in contact/client lists
#   - Allows quick jumping to specific letter
#   - Visual feedback shows which filter is active
#   - Arrow buttons provide cleaner navigation than scrollbars
#
# Usage Example:
#   alphabet_filter = AlphabetFilter()
#   alphabet_filter.filter_changed.connect(handle_filter)
#   alphabet_filter.set_active("A")
# =============================================================================

import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Configure module logger
logger = logging.getLogger(__name__)


class AlphabetFilter(QWidget):
    """
    A-Z filter widget for quick list navigation.

    This widget displays a vertical list of letter buttons (A-Z) plus
    special characters and an "All" option. When a letter is clicked,
    it emits a signal that can be used to filter a list.

    Navigation is provided via UP/DOWN arrow buttons at top/bottom when
    not all letters fit. Arrows are hidden when all letters are visible.

    Signals:
        filter_changed(str): Emitted when filter selection changes.
                           Passes the selected letter, "#" for special chars,
                           or "All" for no filter.

    Attributes:
        active_letter: Currently active filter letter (or "All" or "#")
        _buttons: Dictionary of letter -> button mappings
    """

    # Signal emitted when filter changes
    filter_changed = pyqtSignal(str)

    # Widget width
    FILTER_WIDTH = 30

    # Button height
    BUTTON_HEIGHT = 26

    # Arrow button height (slightly smaller)
    ARROW_HEIGHT = 24

    # All letters/items in order
    ALL_ITEMS = ["All"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["#"]

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the alphabet filter.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # State tracking
        self.active_letter: str = "All"  # Start with no filter

        # Visible range tracking
        self._scroll_offset: int = 0  # Index of first visible item
        self._visible_count: int = 0  # Number of items that can be visible

        # Button storage for styling updates
        self._buttons: dict[str, QPushButton] = {}

        # Arrow buttons
        self._up_arrow: Optional[QPushButton] = None
        self._down_arrow: Optional[QPushButton] = None

        # Container for letter buttons
        self._letter_container: Optional[QWidget] = None
        self._letter_layout: Optional[QVBoxLayout] = None

        # Set up the UI
        self._init_ui()

        logger.debug("AlphabetFilter initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates a vertical layout with optional arrow buttons at top/bottom
        and letter buttons in between.
        """
        # Set fixed width
        self.setFixedWidth(self.FILTER_WIDTH)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 4)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # UP arrow button (hidden by default)
        self._up_arrow = QPushButton("▲")
        self._up_arrow.setFixedSize(self.FILTER_WIDTH, self.ARROW_HEIGHT)
        self._up_arrow.setCursor(Qt.CursorShape.PointingHandCursor)
        self._up_arrow.setProperty("alphabet_arrow", True)
        self._up_arrow.clicked.connect(self._scroll_up)
        self._up_arrow.setVisible(False)
        main_layout.addWidget(self._up_arrow)

        # Container for letter buttons
        self._letter_container = QWidget()
        self._letter_layout = QVBoxLayout(self._letter_container)
        self._letter_layout.setContentsMargins(0, 0, 0, 0)
        self._letter_layout.setSpacing(2)
        self._letter_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create all letter buttons (visibility managed separately)
        for item in self.ALL_ITEMS:
            self._create_filter_button(item, self._letter_layout)

        main_layout.addWidget(self._letter_container, stretch=1)

        # DOWN arrow button (hidden by default)
        self._down_arrow = QPushButton("▼")
        self._down_arrow.setFixedSize(self.FILTER_WIDTH, self.ARROW_HEIGHT)
        self._down_arrow.setCursor(Qt.CursorShape.PointingHandCursor)
        self._down_arrow.setProperty("alphabet_arrow", True)
        self._down_arrow.clicked.connect(self._scroll_down)
        self._down_arrow.setVisible(False)
        main_layout.addWidget(self._down_arrow)

        # Set "All" as initially active
        self._update_active_styling()

    def _create_filter_button(self, letter: str, layout: QVBoxLayout) -> None:
        """
        Create a filter button for the specified letter.

        Args:
            letter: The letter or special character for this button
            layout: Layout to add the button to
        """
        button = QPushButton(letter)
        button.setFixedSize(self.FILTER_WIDTH, self.BUTTON_HEIGHT)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setProperty("alphabet_filter", True)  # CSS class

        # Connect click handler
        button.clicked.connect(lambda: self._on_filter_clicked(letter))

        # Store reference for later styling updates
        self._buttons[letter] = button

        # Add to layout
        layout.addWidget(button)

    def _on_filter_clicked(self, letter: str) -> None:
        """
        Handle filter button click.

        Args:
            letter: The letter that was clicked

        Note:
            This updates the active state and emits the filter_changed signal.
        """
        logger.debug(f"Alphabet filter clicked: {letter}")

        # Update active letter
        self.set_active(letter)

        # Emit signal
        self.filter_changed.emit(letter)

    def set_active(self, letter: str) -> None:
        """
        Set the active filter letter.

        Args:
            letter: The letter to make active (or "All" or "#")

        Note:
            This updates the visual styling to highlight the active button.
        """
        # Validate letter
        if letter not in self._buttons:
            logger.warning(f"Invalid filter letter: {letter}")
            return

        # Update state
        self.active_letter = letter

        # Update button styling
        self._update_active_styling()

        logger.debug(f"Active alphabet filter set to: {letter}")

    def _update_active_styling(self) -> None:
        """
        Update button styling to reflect the active state.

        The active button gets a special property that can be styled with QSS.
        """
        for letter, button in self._buttons.items():
            is_active = letter == self.active_letter
            button.setProperty("active", is_active)

            # Force style refresh
            # WHY: Qt doesn't automatically refresh styles when properties change
            button.style().unpolish(button)
            button.style().polish(button)

    def get_active_filter(self) -> str:
        """
        Get the currently active filter.

        Returns:
            str: The active filter letter ("All", "A"-"Z", or "#")
        """
        return self.active_letter

    def clear_filter(self) -> None:
        """
        Clear the filter (set to "All").

        This is a convenience method equivalent to set_active("All").
        """
        self.set_active("All")
        self.filter_changed.emit("All")

    def resizeEvent(self, event) -> None:
        """
        Handle resize events to update visible letter buttons.

        Calculates how many letters can fit and shows/hides arrows accordingly.

        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        self._update_visible_buttons()

    def showEvent(self, event) -> None:
        """
        Handle show events to initialize visible buttons.

        Args:
            event: Show event
        """
        super().showEvent(event)
        # Defer to next event loop to ensure layout is complete
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(0, self._update_visible_buttons)

    def _calculate_visible_count(self) -> int:
        """
        Calculate how many letter buttons can fit in the available space.

        Returns:
            Number of buttons that can be displayed
        """
        # Available height = total height - arrow buttons (if shown) - margins
        available_height = self.height() - 8  # 4px top + 4px bottom margin

        # If we need arrows, reserve space for them
        total_items = len(self.ALL_ITEMS)
        items_that_fit_without_arrows = available_height // (self.BUTTON_HEIGHT + 2)

        if items_that_fit_without_arrows >= total_items:
            # All items fit, no arrows needed
            return total_items
        else:
            # Need arrows, subtract their space
            available_with_arrows = available_height - (2 * self.ARROW_HEIGHT)
            return max(1, available_with_arrows // (self.BUTTON_HEIGHT + 2))

    def _update_visible_buttons(self) -> None:
        """
        Update which letter buttons are visible based on current scroll offset.

        Also shows/hides arrow buttons as needed.
        """
        total_items = len(self.ALL_ITEMS)
        self._visible_count = self._calculate_visible_count()

        # Determine if we need arrows
        need_arrows = self._visible_count < total_items

        # Show/hide arrows
        if self._up_arrow and self._down_arrow:
            self._up_arrow.setVisible(need_arrows and self._scroll_offset > 0)
            self._down_arrow.setVisible(
                need_arrows and self._scroll_offset + self._visible_count < total_items
            )

        # Clamp scroll offset
        max_offset = max(0, total_items - self._visible_count)
        self._scroll_offset = min(self._scroll_offset, max_offset)

        # Update button visibility
        for i, item in enumerate(self.ALL_ITEMS):
            button = self._buttons.get(item)
            if button:
                is_visible = (
                    i >= self._scroll_offset
                    and i < self._scroll_offset + self._visible_count
                )
                button.setVisible(is_visible)

    def _scroll_up(self) -> None:
        """
        Scroll up to show earlier letters.
        """
        if self._scroll_offset > 0:
            self._scroll_offset -= 1
            self._update_visible_buttons()

    def _scroll_down(self) -> None:
        """
        Scroll down to show later letters.
        """
        total_items = len(self.ALL_ITEMS)
        max_offset = max(0, total_items - self._visible_count)
        if self._scroll_offset < max_offset:
            self._scroll_offset += 1
            self._update_visible_buttons()
