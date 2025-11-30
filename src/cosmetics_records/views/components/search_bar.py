# =============================================================================
# Cosmetics Records - Search Bar Component
# =============================================================================
# This module provides a search input field with debouncing and clear button.
#
# Key Features:
#   - Search icon for visual clarity
#   - Placeholder text
#   - Clear button (X) when text is present
#   - Debounced text change events (300ms delay)
#   - Fixed height for consistent layout
#
# Design Philosophy:
#   - Debouncing prevents excessive search queries while typing
#   - Clear button provides quick way to reset search
#   - Search icon makes purpose immediately obvious
#
# Usage Example:
#   search_bar = SearchBar()
#   search_bar.search_changed.connect(handle_search)
#   search_bar.set_placeholder("Search clients...")
# =============================================================================

import logging
from typing import Optional

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

# Configure module logger
logger = logging.getLogger(__name__)


class SearchBar(QWidget):
    """
    Search input field with debouncing and clear functionality.

    This widget provides a user-friendly search input that delays emitting
    search events until the user has stopped typing for 300ms. This prevents
    excessive search operations while the user is still typing.

    Signals:
        search_changed(str): Emitted when search text changes (debounced).
                           Passes the current search text.

    Attributes:
        _debounce_timer: QTimer for debouncing text changes
        _line_edit: The actual QLineEdit input field
        _clear_btn: Button to clear the search text
    """

    # Signal emitted when search text changes (after debounce delay)
    search_changed = pyqtSignal(str)

    # Debounce delay in milliseconds
    # WHY 300ms: Long enough to avoid triggering while typing, short enough
    # to feel responsive when the user pauses
    DEBOUNCE_DELAY = 300

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the search bar.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Create debounce timer
        # WHY setSingleShot(True): Timer fires once per start(), which is perfect
        # for debouncing - we restart it on each keystroke
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_search_changed)

        # Set up the UI
        self._init_ui()

        logger.debug("SearchBar initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates the search input, search icon, and clear button.
        """
        # Set fixed height for consistent layout
        self.setFixedHeight(40)

        # Horizontal layout: [input field] [X clear button]
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Main search input field
        self._line_edit = QLineEdit()
        self._line_edit.setPlaceholderText("Search...")
        self._line_edit.setClearButtonEnabled(False)  # We'll use custom clear button

        # Connect text change to debounce timer
        # WHY textChanged not textEdited: textChanged fires even when text is
        # set programmatically, which is what we want for consistency
        self._line_edit.textChanged.connect(self._on_text_changed)

        layout.addWidget(self._line_edit, stretch=1)  # Take remaining space

        # Clear button (X)
        # Initially hidden - only shown when there's text
        self._clear_btn = QPushButton("×")  # Multiplication sign looks like X
        self._clear_btn.setFixedSize(36, 36)
        self._clear_btn.setProperty("clear_button", True)  # CSS class
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.clicked.connect(self.clear)
        self._clear_btn.setVisible(False)  # Hidden by default
        layout.addWidget(self._clear_btn)

    def _on_text_changed(self, text: str) -> None:
        """
        Handle text change in the input field.

        This method:
        1. Shows/hides the clear button based on whether there's text
        2. Restarts the debounce timer

        Args:
            text: The current text in the search field

        Note:
            The actual search_changed signal is emitted after the debounce
            delay expires, not immediately.
        """
        # Show clear button only when there's text
        self._clear_btn.setVisible(bool(text))

        # Restart debounce timer
        # WHY restart: Each keystroke resets the timer, so the signal only
        # fires when the user stops typing for 300ms
        self._debounce_timer.stop()
        self._debounce_timer.start(self.DEBOUNCE_DELAY)

    def _emit_search_changed(self) -> None:
        """
        Emit the search_changed signal with current text.

        This is called by the debounce timer after the delay expires.
        """
        text = self._line_edit.text()
        logger.debug(f"Search changed: '{text}'")
        self.search_changed.emit(text)

    def clear(self) -> None:
        """
        Clear the search text.

        This is called when the clear button is clicked, but can also be
        called programmatically to reset the search.
        """
        self._line_edit.clear()
        self._line_edit.setFocus()  # Keep focus for immediate re-typing
        logger.debug("Search cleared")

    def set_placeholder(self, text: str) -> None:
        """
        Set the placeholder text.

        Args:
            text: Placeholder text to display when field is empty

        Example:
            search_bar.set_placeholder("Search clients by name...")
        """
        self._line_edit.setPlaceholderText(text)

    def get_text(self) -> str:
        """
        Get the current search text.

        Returns:
            str: Current text in the search field
        """
        return self._line_edit.text()

    def set_text(self, text: str) -> None:
        """
        Set the search text programmatically.

        Args:
            text: Text to set in the search field

        Note:
            This will trigger the search_changed signal after the debounce delay.
        """
        self._line_edit.setText(text)

    def set_focus(self) -> None:
        """
        Set keyboard focus to the search input.

        Useful for auto-focusing the search when a view is displayed.
        """
        self._line_edit.setFocus()
