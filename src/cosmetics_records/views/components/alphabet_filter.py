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
#
# Design Philosophy:
#   - Common pattern in contact/client lists
#   - Allows quick jumping to specific letter
#   - Visual feedback shows which filter is active
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
    QScrollArea,
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

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the alphabet filter.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # State tracking
        self.active_letter: str = "All"  # Start with no filter

        # Button storage for styling updates
        self._buttons: dict[str, QPushButton] = {}

        # Set up the UI
        self._init_ui()

        logger.debug("AlphabetFilter initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates a scrollable vertical list of letter buttons.
        """
        # Set fixed width
        self.setFixedWidth(self.FILTER_WIDTH)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area for the buttons
        # WHY scroll area: On small screens, 28 buttons might not fit vertically
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        # Container widget for buttons
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(2)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # "All" button at the top - clears filter
        self._create_filter_button("All", button_layout)

        # Add separator visual spacing
        button_layout.addSpacing(4)

        # A-Z buttons
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self._create_filter_button(letter, button_layout)

        # Add separator visual spacing
        button_layout.addSpacing(4)

        # "#" button for numbers and special characters
        self._create_filter_button("#", button_layout)

        # Set the container as the scroll area's widget
        scroll_area.setWidget(button_container)

        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)

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
        button.setFixedSize(self.FILTER_WIDTH, self.FILTER_WIDTH)
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
