# =============================================================================
# Cosmetics Records - Tag Input Component
# =============================================================================
# This module provides a tag/chip input widget for managing multiple labels.
#
# Key Features:
#   - Visual tag chips with remove buttons
#   - Enter or comma to create new tags
#   - Click X on chip to remove
#   - Duplicate prevention
#   - Signal emission when tags change
#   - Clean, modern appearance
#
# Design Philosophy:
#   - Common pattern for categorization and labeling
#   - Visual chips make it clear what tags are active
#   - Easy to add and remove tags
#   - Prevents accidental duplicates
#
# Usage Example:
#   tag_input = TagInput()
#   tag_input.tags_changed.connect(handle_tags_change)
#   tag_input.set_tags(["Botox", "Filler"])
# =============================================================================

import logging
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QObject
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Configure module logger
logger = logging.getLogger(__name__)


class TagChip(QFrame):
    """
    A single tag chip with label and remove button.

    This widget represents one tag as a pill-shaped chip with a remove button.
    Uses QFrame instead of QWidget so background styling works properly.

    Signals:
        remove_clicked: Emitted when the X button is clicked

    Attributes:
        tag_text: The text content of this tag
    """

    # Signal emitted when remove button is clicked
    remove_clicked = pyqtSignal()

    def __init__(self, tag_text: str, parent: Optional[QWidget] = None):
        """
        Initialize a tag chip.

        Args:
            tag_text: The text to display in the chip
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.tag_text = tag_text

        # Set up the UI
        self._init_ui()

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates a horizontal layout with tag text and remove button.
        """
        # Horizontal layout for tag text and X button
        layout = QHBoxLayout(self)
        # WHY small margins: The chip background needs to wrap tightly around content
        layout.setContentsMargins(10, 4, 6, 4)
        layout.setSpacing(6)

        # Tag text label - using QLabel for proper text display
        self._label = QLabel(self.tag_text)
        self._label.setProperty("tag_label", True)  # CSS class
        layout.addWidget(self._label)

        # Remove button (X)
        self._remove_btn = QPushButton("×")
        self._remove_btn.setFixedSize(18, 18)
        self._remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._remove_btn.setProperty("tag_remove", True)  # CSS class
        self._remove_btn.clicked.connect(self.remove_clicked.emit)
        layout.addWidget(self._remove_btn)

        # Style the chip itself - QFrame picks up background styles properly
        self.setProperty("tag_chip", True)  # CSS class
        self.setFrameShape(QFrame.Shape.NoFrame)  # No default frame border


class TagInput(QWidget):
    """
    Tag input widget with visual chips.

    This widget allows users to add and remove tags. Tags are displayed as
    blue pill-shaped chips above an input field.

    Signals:
        tags_changed(list): Emitted when tags are added or removed.
                          Passes the current list of tags.

    Attributes:
        _tags: List of current tags
        _chips: Dictionary mapping tag text to TagChip widgets
    """

    # Signal emitted when tags change
    tags_changed = pyqtSignal(list)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the tag input.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # State tracking
        self._tags: List[str] = []
        self._chips: dict[str, TagChip] = {}

        # Set up the UI
        self._init_ui()

        logger.debug("TagInput initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates a layout with chip display area and input field.
        """
        # Main vertical layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Chips container - horizontal flow layout
        # WHY QWidget instead of QHBoxLayout: We'll manually manage chip positioning
        # for better wrapping behavior
        self._chips_container = QWidget()
        self._chips_container.setProperty("chips_container", True)  # CSS class
        self._chips_layout = QHBoxLayout(self._chips_container)
        self._chips_layout.setContentsMargins(4, 4, 4, 4)
        self._chips_layout.setSpacing(4)
        self._chips_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._chips_container)

        # Input field for adding new tags
        self._line_edit = QLineEdit()
        self._line_edit.setPlaceholderText("Type tag and press Enter, Tab, or comma...")
        # Don't connect returnPressed - we handle Enter in eventFilter to prevent
        # dialog from closing when user just wants to add a tag
        self._line_edit.textChanged.connect(self._on_text_changed)
        # Install event filter to intercept Tab and Enter keys
        self._line_edit.installEventFilter(self)
        layout.addWidget(self._line_edit)

    def eventFilter(self, obj: Optional[QObject], event: Optional[QEvent]) -> bool:
        """
        Event filter to intercept Tab and Enter keys in the line edit.

        When Tab or Enter is pressed with text in the input, add it as a tag
        instead of navigating to the next widget or triggering dialog buttons.

        Args:
            obj: The object that triggered the event
            event: The event

        Returns:
            bool: True if event was handled, False otherwise
        """
        # Only filter key press events on the line edit
        if (
            obj == self._line_edit
            and event is not None
            and event.type() == QEvent.Type.KeyPress
            and isinstance(event, QKeyEvent)
        ):
            if event.key() == Qt.Key.Key_Tab:
                # If there's text, add it as a tag
                if self._line_edit.text().strip():
                    self._add_tag_from_input()
                    return True  # Consume the event

            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # Always consume Enter to prevent dialog from closing
                # Add tag if there's text, otherwise just consume the event
                if self._line_edit.text().strip():
                    self._add_tag_from_input()
                return True  # Always consume Enter key

        # Let other events pass through
        return super().eventFilter(obj, event)

    def _on_text_changed(self, text: str) -> None:
        """
        Handle text change in the input field.

        Detects comma as a tag separator and adds the tag.

        Args:
            text: Current text in the input field
        """
        # Check if user typed a comma (tag separator)
        if "," in text:
            # Extract tag before the comma
            tag = text.split(",")[0].strip()

            # Add the tag if it's not empty
            if tag:
                self._add_tag(tag)

            # Clear the input (remove everything before and including the comma)
            remaining = text.split(",", 1)[1] if "," in text else ""
            self._line_edit.setText(remaining.strip())

    def _add_tag_from_input(self) -> None:
        """
        Add a tag from the input field when Enter is pressed.

        This extracts the text from the input, adds it as a tag,
        and clears the input.
        """
        tag = self._line_edit.text().strip()

        if tag:
            self._add_tag(tag)
            self._line_edit.clear()

    def _add_tag(self, tag: str) -> None:
        """
        Add a tag to the collection.

        Args:
            tag: The tag text to add

        Note:
            Duplicates are ignored (case-insensitive comparison).
        """
        # Normalize tag (strip whitespace, capitalize first letter)
        tag = tag.strip()

        if not tag:
            return

        # Check for duplicates (case-insensitive)
        if any(t.lower() == tag.lower() for t in self._tags):
            logger.debug(f"Duplicate tag ignored: {tag}")
            return

        # Add to tags list
        self._tags.append(tag)

        # Create chip widget
        chip = TagChip(tag)
        chip.remove_clicked.connect(lambda: self._remove_tag(tag))
        self._chips[tag] = chip

        # Add to layout
        self._chips_layout.addWidget(chip)

        # Emit signal
        self.tags_changed.emit(self._tags.copy())

        logger.debug(f"Tag added: {tag}")

    def _remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the collection.

        Args:
            tag: The tag text to remove
        """
        if tag not in self._tags:
            return

        # Remove from list
        self._tags.remove(tag)

        # Remove and delete chip widget
        if tag in self._chips:
            chip = self._chips[tag]
            self._chips_layout.removeWidget(chip)
            chip.deleteLater()
            del self._chips[tag]

        # Emit signal
        self.tags_changed.emit(self._tags.copy())

        logger.debug(f"Tag removed: {tag}")

    def get_tags(self) -> List[str]:
        """
        Get the current list of tags.

        Returns:
            List[str]: Copy of the current tags list
        """
        return self._tags.copy()

    def set_tags(self, tags: List[str]) -> None:
        """
        Set the tags programmatically.

        This clears existing tags and replaces them with the provided list.

        Args:
            tags: List of tag strings

        Example:
            tag_input.set_tags(["Botox", "Filler", "Consultation"])
        """
        # Clear existing tags
        self.clear()

        # Add new tags
        for tag in tags:
            self._add_tag(tag)

    def clear(self) -> None:
        """
        Remove all tags.

        This clears the tags list and removes all chip widgets.
        """
        # Remove all chip widgets
        for chip in self._chips.values():
            self._chips_layout.removeWidget(chip)
            chip.deleteLater()

        # Clear tracking
        self._chips.clear()
        self._tags.clear()

        # Emit signal
        self.tags_changed.emit([])

        logger.debug("All tags cleared")
