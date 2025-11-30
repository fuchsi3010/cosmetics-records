# =============================================================================
# Cosmetics Records - Autocomplete Input Component
# =============================================================================
# This module provides an autocomplete input with fuzzy matching suggestions.
#
# Key Features:
#   - Dropdown suggestions as user types
#   - Fuzzy matching using thefuzz library
#   - Arrow keys to navigate suggestions
#   - Enter or click to select
#   - Configurable suggestion list
#   - Signal emission on selection
#
# Design Philosophy:
#   - Helps users find items quickly without exact typing
#   - Fuzzy matching handles typos and partial matches
#   - Keyboard navigation for power users
#   - Mouse support for casual users
#
# Usage Example:
#   autocomplete = Autocomplete()
#   autocomplete.set_suggestions(["Botox", "Filler", "Microneedling"])
#   autocomplete.item_selected.connect(handle_selection)
# =============================================================================

import logging
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Try to import thefuzz for fuzzy matching
try:
    from thefuzz import fuzz

    FUZZ_AVAILABLE = True
except ImportError:
    FUZZ_AVAILABLE = False
    logging.warning("thefuzz not available - autocomplete will use exact matching")

# Configure module logger
logger = logging.getLogger(__name__)


class Autocomplete(QWidget):
    """
    Autocomplete input with fuzzy matching suggestions.

    This widget provides a text input with a dropdown list of suggestions.
    As the user types, it filters suggestions using fuzzy matching.

    Signals:
        item_selected(str): Emitted when a suggestion is selected.
                          Passes the selected item text.
        text_changed(str): Emitted when input text changes.
                         Passes the current text.

    Attributes:
        _suggestions: Full list of available suggestions
        _line_edit: The input field
        _suggestions_list: The dropdown suggestions list
    """

    # Signals
    item_selected = pyqtSignal(str)
    text_changed = pyqtSignal(str)

    # Fuzzy match score threshold
    # WHY 60: Requires reasonable similarity while allowing some typos
    MATCH_THRESHOLD = 60

    # Maximum suggestions to show
    MAX_SUGGESTIONS = 10

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the autocomplete input.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # State tracking
        self._suggestions: List[str] = []

        # Set up the UI
        self._init_ui()

        logger.debug("Autocomplete initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates the input field and suggestions dropdown.
        """
        # Main vertical layout: [input field] [suggestions list]
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Input field
        self._line_edit = QLineEdit()
        self._line_edit.setPlaceholderText("Type to search...")
        self._line_edit.textChanged.connect(self._on_text_changed)
        self._line_edit.returnPressed.connect(self._on_return_pressed)

        # Install event filter to handle arrow key navigation
        self._line_edit.installEventFilter(self)

        layout.addWidget(self._line_edit)

        # Suggestions list (initially hidden)
        self._suggestions_list = QListWidget()
        self._suggestions_list.setVisible(False)
        self._suggestions_list.itemClicked.connect(self._on_item_clicked)

        # Install event filter to handle Enter key in list
        self._suggestions_list.installEventFilter(self)

        layout.addWidget(self._suggestions_list)

    def eventFilter(self, obj, event):
        """
        Event filter for keyboard navigation.

        Handles arrow keys to navigate suggestions and Enter to select.

        Args:
            obj: Object that received the event
            event: The event

        Returns:
            bool: True if event was handled, False otherwise
        """
        # Handle key presses in the line edit
        if obj == self._line_edit and event.type() == event.Type.KeyPress:
            key = event.key()

            # Down arrow: move focus to suggestions list
            if key == Qt.Key.Key_Down and self._suggestions_list.isVisible():
                self._suggestions_list.setFocus()
                self._suggestions_list.setCurrentRow(0)
                return True

        # Handle key presses in the suggestions list
        elif obj == self._suggestions_list and event.type() == event.Type.KeyPress:
            key = event.key()

            # Up arrow on first item: return to input
            if key == Qt.Key.Key_Up and self._suggestions_list.currentRow() == 0:
                self._line_edit.setFocus()
                return True

            # Enter: select current item
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                current_item = self._suggestions_list.currentItem()
                if current_item:
                    self._select_item(current_item.text())
                return True

        return super().eventFilter(obj, event)

    def _on_text_changed(self, text: str) -> None:
        """
        Handle text change in the input field.

        Filters suggestions based on the input text.

        Args:
            text: Current text in the input field
        """
        # Emit text changed signal
        self.text_changed.emit(text)

        # Filter and show suggestions
        if text.strip():
            filtered = self._filter_suggestions(text)

            if filtered:
                self._show_suggestions(filtered)
            else:
                self._hide_suggestions()
        else:
            self._hide_suggestions()

    def _filter_suggestions(self, query: str) -> List[str]:
        """
        Filter suggestions based on query using fuzzy matching.

        Args:
            query: The search query

        Returns:
            List[str]: Filtered and sorted suggestions

        Note:
            Uses thefuzz for fuzzy matching if available, otherwise falls
            back to simple substring matching.
        """
        if not self._suggestions:
            return []

        query = query.lower().strip()

        if FUZZ_AVAILABLE:
            # Use fuzzy matching with scoring
            scored_suggestions = []

            for suggestion in self._suggestions:
                # Calculate fuzzy match score
                score = fuzz.partial_ratio(query, suggestion.lower())

                # Only include if score meets threshold
                if score >= self.MATCH_THRESHOLD:
                    scored_suggestions.append((score, suggestion))

            # Sort by score (descending) and take top N
            scored_suggestions.sort(reverse=True, key=lambda x: x[0])
            filtered = [s for _, s in scored_suggestions[: self.MAX_SUGGESTIONS]]

        else:
            # Fallback: simple substring matching
            filtered = [s for s in self._suggestions if query in s.lower()][
                : self.MAX_SUGGESTIONS
            ]

        return filtered

    def _show_suggestions(self, suggestions: List[str]) -> None:
        """
        Show the suggestions dropdown with filtered items.

        Args:
            suggestions: List of suggestions to display
        """
        # Clear existing items
        self._suggestions_list.clear()

        # Add new suggestions
        for suggestion in suggestions:
            QListWidgetItem(suggestion, self._suggestions_list)

        # Show the list
        self._suggestions_list.setVisible(True)

        # Adjust height based on number of items
        # WHY 30: Approximate height per item
        item_height = 30
        list_height = min(len(suggestions) * item_height, 300)  # Max 300px
        self._suggestions_list.setFixedHeight(list_height)

    def _hide_suggestions(self) -> None:
        """
        Hide the suggestions dropdown.
        """
        self._suggestions_list.setVisible(False)
        self._suggestions_list.clear()

    def _on_return_pressed(self) -> None:
        """
        Handle Enter key press in the input field.

        If there are suggestions showing, select the first one.
        """
        if self._suggestions_list.isVisible():
            # Select first suggestion
            item = self._suggestions_list.item(0)
            if item:
                self._select_item(item.text())

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """
        Handle suggestion item click.

        Args:
            item: The clicked list item
        """
        self._select_item(item.text())

    def _select_item(self, text: str) -> None:
        """
        Handle item selection.

        Sets the input text to the selected item, hides suggestions,
        and emits the item_selected signal.

        Args:
            text: The selected item text
        """
        # Set input text
        self._line_edit.setText(text)

        # Hide suggestions
        self._hide_suggestions()

        # Emit signal
        self.item_selected.emit(text)

        logger.debug(f"Autocomplete item selected: {text}")

    def set_suggestions(self, items: List[str]) -> None:
        """
        Set the list of available suggestions.

        Args:
            items: List of suggestion strings

        Example:
            autocomplete.set_suggestions(["Botox", "Filler", "Microneedling"])
        """
        self._suggestions = items
        logger.debug(f"Autocomplete suggestions set: {len(items)} items")

    def get_text(self) -> str:
        """
        Get the current input text.

        Returns:
            str: Current text in the input field
        """
        return self._line_edit.text()

    def set_text(self, text: str) -> None:
        """
        Set the input text programmatically.

        Args:
            text: Text to set
        """
        self._line_edit.setText(text)

    def clear(self) -> None:
        """
        Clear the input text and hide suggestions.
        """
        self._line_edit.clear()
        self._hide_suggestions()

    def set_placeholder(self, text: str) -> None:
        """
        Set the placeholder text.

        Args:
            text: Placeholder text to display when field is empty
        """
        self._line_edit.setPlaceholderText(text)
