# =============================================================================
# Cosmetics Records - Inventory View
# =============================================================================
# This module provides the inventory catalog management view.
#
# Key Features:
#   - Searchable inventory list (by name)
#   - Alphabet filter for quick navigation (including #)
#   - Infinite scroll pagination (20 items per load)
#   - Item rows with name, capacity/unit, and description preview
#   - Click to edit item details
#   - Add new item button
#
# Design Philosophy:
#   - Performance: Load items in batches to handle large catalogs
#   - UX: Fuzzy search for quick finding
#   - Visual clarity: Show capacity/unit with name, truncated descriptions
#   - Navigation: Alphabet filter including # for items starting with numbers
#
# Layout:
#   ┌─────────────────────────────────────────┐
#   │ [Search Bar]              [+ Add Item]  │
#   ├───┬─────────────────────────────────────┤
#   │ A │ Item Rows (scrollable)              │
#   │ B │ - Hyaluronic Serum (30 ml)         │
#   │ C │ - Description preview...            │
#   │...│                                      │
#   │ # │                                      │
#   └───┴─────────────────────────────────────┘
#
# Usage Example:
#   inventory_view = InventoryView()
#   inventory_view.item_updated.connect(refresh_autocomplete)
# =============================================================================

import logging
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..components.alphabet_filter import AlphabetFilter
from ..components.search_bar import SearchBar

# Configure module logger
logger = logging.getLogger(__name__)


class InventoryRow(QFrame):
    """
    Single inventory item row in the list.

    Displays item name with capacity/unit and description preview.

    Signals:
        clicked(): Emitted when the row is clicked

    Attributes:
        item_id: Database ID of this inventory item
        item_data: Dictionary containing item information
    """

    # Signal emitted when row is clicked
    clicked = pyqtSignal()

    # Fixed row height for consistent layout
    ROW_HEIGHT = 60

    def __init__(self, item_id: int, item_data: dict, parent: Optional[QWidget] = None):
        """
        Initialize an inventory row.

        Args:
            item_id: Database ID of the inventory item
            item_data: Dictionary with keys:
                      - name: Item name
                      - capacity: Numeric capacity
                      - unit: Unit string (ml/g/Pc.)
                      - description: Item description (optional)
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.item_id = item_id
        self.item_data = item_data

        # Set fixed height for consistent rows
        self.setFixedHeight(self.ROW_HEIGHT)

        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("inventory_row", True)  # CSS class

        # Set up the UI
        self._init_ui()

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates a layout with name/capacity and description preview.
        """
        # Main vertical layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Item name with capacity/unit: "Hyaluronic Serum (30 ml)"
        name = self.item_data.get("name", "")
        capacity = self.item_data.get("capacity", 0)
        unit = self.item_data.get("unit", "")

        # Format: "Name (capacity unit)"
        name_with_capacity = f"{name} ({capacity} {unit})"

        name_label = QLabel(name_with_capacity)
        name_label.setProperty("inventory_name", True)  # CSS class (bold)
        layout.addWidget(name_label)

        # Description preview (truncated)
        description = self.item_data.get("description", "")
        if description:
            # WHY 80 chars: Fits in row without wrapping in most cases
            truncated_desc = (
                description[:80] + "..." if len(description) > 80 else description
            )

            desc_label = QLabel(truncated_desc)
            desc_label.setProperty("inventory_description", True)  # CSS class (gray)
            layout.addWidget(desc_label)

    def mousePressEvent(self, event):
        """
        Handle mouse press event to emit clicked signal.

        Args:
            event: Mouse press event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class InventoryView(QWidget):
    """
    Inventory catalog management view.

    This view provides a searchable, filterable list of inventory items with
    infinite scroll pagination. Users can search by name, filter by alphabet,
    and click items to edit them.

    Signals:
        item_updated(): Emitted when any inventory item changes

    Attributes:
        _current_search: Current search query
        _current_filter: Current alphabet filter
        _loaded_items: List of currently loaded item IDs
        _has_more: Whether more items are available to load
        _loading: Whether items are currently being loaded
    """

    # Signal
    item_updated = pyqtSignal()

    # Pagination settings
    ITEMS_PER_PAGE = 20

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the inventory view.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # State tracking
        self._current_search: str = ""
        self._current_filter: str = "All"
        self._loaded_items: List[int] = []
        self._has_more: bool = True
        self._loading: bool = False

        # Set up the UI
        self._init_ui()

        # Initial load
        # NOTE: This will be connected to a controller method later
        self._load_initial_items()

        logger.debug("InventoryView initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates the layout with search bar, alphabet filter, and item list.
        """
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar: search + add button
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)

        # Content area: filter sidebar + item list
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Left sidebar: alphabet filter (including #)
        self._alphabet_filter = AlphabetFilter()
        self._alphabet_filter.filter_changed.connect(self._on_filter_changed)
        content_layout.addWidget(self._alphabet_filter)

        # Item list (scrollable)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        # Connect scroll event for infinite scroll
        self._scroll_area.verticalScrollBar().valueChanged.connect(
            self._on_scroll_changed
        )

        # Container for item rows
        self._item_container = QWidget()
        self._item_layout = QVBoxLayout(self._item_container)
        self._item_layout.setContentsMargins(0, 0, 0, 0)
        self._item_layout.setSpacing(0)
        self._item_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll_area.setWidget(self._item_container)
        content_layout.addWidget(self._scroll_area, stretch=1)

        main_layout.addLayout(content_layout)

    def _create_top_bar(self) -> QWidget:
        """
        Create the top bar with search and add button.

        Returns:
            QWidget containing search bar and add button
        """
        top_bar = QWidget()
        top_bar.setFixedHeight(60)
        top_bar.setProperty("top_bar", True)  # CSS class

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # Search bar
        self._search_bar = SearchBar()
        self._search_bar.set_placeholder("Search inventory by name...")
        self._search_bar.search_changed.connect(self._on_search_changed)
        layout.addWidget(self._search_bar, stretch=1)

        # Add item button
        add_btn = QPushButton("+ Add Item")
        add_btn.setProperty("class", "primary")  # Primary button styling
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add_item)
        add_btn.setFixedWidth(120)
        layout.addWidget(add_btn)

        return top_bar

    def _on_search_changed(self, query: str) -> None:
        """
        Handle search query change.

        Resets to first page and loads items matching the search.

        Args:
            query: Search query string (already debounced by SearchBar)
        """
        logger.debug(f"Search changed: '{query}'")

        self._current_search = query

        # Reset and reload
        self._reset_and_reload()

    def _on_filter_changed(self, letter: str) -> None:
        """
        Handle alphabet filter change.

        Resets to first page and loads items starting with the selected letter.

        Args:
            letter: Selected letter ("All", "A"-"Z", or "#")
        """
        logger.debug(f"Filter changed: {letter}")

        self._current_filter = letter

        # Reset and reload
        self._reset_and_reload()

    def _reset_and_reload(self) -> None:
        """
        Reset the item list and reload from the beginning.

        Clears all loaded items and loads the first page with current filters.
        """
        # Clear current items
        self._clear_item_list()

        # Reset state
        self._loaded_items.clear()
        self._has_more = True

        # Load first page
        self._load_more_items()

    def _clear_item_list(self) -> None:
        """
        Remove all item rows from the UI.
        """
        # Remove all widgets from layout
        while self._item_layout.count():
            item = self._item_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _on_scroll_changed(self, value: int) -> None:
        """
        Handle scroll position change.

        Loads more items when scrolling near the bottom (infinite scroll).

        Args:
            value: Current scroll position
        """
        # Check if we're near the bottom
        scrollbar = self._scroll_area.verticalScrollBar()
        max_value = scrollbar.maximum()

        # Load more when within 100 pixels of bottom
        if value >= max_value - 100 and not self._loading and self._has_more:
            self._load_more_items()

    def _load_initial_items(self) -> None:
        """
        Load the initial page of items.

        This is called when the view is first created.
        """
        self._load_more_items()

    def _load_more_items(self) -> None:
        """
        Load the next page of items.

        This method will be connected to a controller later. For now,
        it contains placeholder logic.

        Note:
            Sets _loading flag to prevent duplicate requests.
            Updates _has_more flag based on results.
        """
        if self._loading:
            return

        self._loading = True
        logger.debug(
            f"Loading items (offset: {len(self._loaded_items)}, "
            f"search: '{self._current_search}', filter: '{self._current_filter}')"
        )

        # PLACEHOLDER: Controller method will be called here
        # For now, we'll simulate with a timer
        QTimer.singleShot(100, self._on_items_loaded_placeholder)

    def _on_items_loaded_placeholder(self) -> None:
        """
        Placeholder for when items are loaded.

        In real implementation, this will be called by the controller
        with actual item data.
        """
        # PLACEHOLDER: This simulates no items loaded
        # Real implementation will call add_items() with actual data
        self._loading = False
        self._has_more = False

        logger.debug("Placeholder: No items loaded (controller not connected)")

    def add_items(self, items: List[dict]) -> None:
        """
        Add loaded items to the view.

        This method should be called by the controller with loaded item data.

        Args:
            items: List of item dictionaries, each containing:
                  - id: Item database ID
                  - name: Item name
                  - capacity: Numeric capacity
                  - unit: Unit string (ml/g/Pc.)
                  - description: Item description (optional)

        Note:
            This method updates _has_more based on whether a full page was loaded.
        """
        for item_data in items:
            item_id = item_data["id"]

            # Create item row
            item_row = InventoryRow(item_id, item_data)
            item_row.clicked.connect(lambda iid=item_id: self._on_item_clicked(iid))

            # Add to layout
            self._item_layout.addWidget(item_row)

            # Track loaded item
            self._loaded_items.append(item_id)

        # Update pagination state
        # WHY: If we got fewer than a full page, we've reached the end
        self._has_more = len(items) >= self.ITEMS_PER_PAGE
        self._loading = False

        logger.debug(f"Added {len(items)} items (total: {len(self._loaded_items)})")

    def _on_item_clicked(self, item_id: int) -> None:
        """
        Handle item row click.

        Opens the edit inventory dialog.

        Args:
            item_id: Database ID of the clicked item
        """
        logger.debug(f"Item clicked: {item_id}")

        # PLACEHOLDER: Will show EditInventoryDialog
        # For now, just log it

    def _on_add_item(self) -> None:
        """
        Handle add item button click.

        Opens the add inventory dialog.
        """
        logger.debug("Add item clicked")

        # PLACEHOLDER: Will show AddInventoryDialog

    def refresh(self) -> None:
        """
        Refresh the inventory list.

        Reloads items from the beginning with current search and filter.
        This should be called after adding/editing/deleting an item.
        """
        logger.debug("Refreshing inventory list")
        self._reset_and_reload()

    def get_current_search(self) -> str:
        """
        Get the current search query.

        Returns:
            str: Current search query
        """
        return self._current_search

    def get_current_filter(self) -> str:
        """
        Get the current alphabet filter.

        Returns:
            str: Current filter letter ("All", "A"-"Z", or "#")
        """
        return self._current_filter

    def get_loaded_count(self) -> int:
        """
        Get the number of currently loaded items.

        Returns:
            int: Number of loaded items
        """
        return len(self._loaded_items)
