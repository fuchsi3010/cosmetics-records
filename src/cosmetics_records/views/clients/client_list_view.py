# =============================================================================
# Cosmetics Records - Client List View
# =============================================================================
# This module provides the main client listing view with search and filtering.
#
# Key Features:
#   - Searchable client list (by name and tags)
#   - Alphabet filter for quick navigation
#   - Infinite scroll pagination (20 clients per load)
#   - Client rows with name formatting and tags
#   - Click to view client details
#   - Add new client button
#
# Design Philosophy:
#   - Performance: Load clients in batches to handle large datasets
#   - UX: Debounced search prevents excessive queries
#   - Visual clarity: Bold last names, tag chips for matched searches
#   - Navigation: Alphabet filter provides quick jumping
#
# Layout:
#   ┌─────────────────────────────────────────┐
#   │ [Search Bar]             [+ Add Client] │
#   ├─────────────────────────────────────┬───┤
#   │ Client Rows (scrollable)            │ A │
#   │ - LastName, FirstName               │ B │
#   │ - Tags (if matched)                 │ C │
#   │                                      │...│
#   │                                      │ # │
#   └─────────────────────────────────────┴───┘
#
# Usage Example:
#   client_list = ClientListView()
#   client_list.client_selected.connect(show_client_detail)
#   client_list.add_client_clicked.connect(show_add_dialog)
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

from cosmetics_records.utils.localization import _
from cosmetics_records.database.connection import DatabaseConnection
from cosmetics_records.controllers.client_controller import ClientController
from ..components.alphabet_filter import AlphabetFilter
from ..components.search_bar import SearchBar

# Configure module logger
logger = logging.getLogger(__name__)


class ClientRow(QFrame):
    """
    Single client row in the list.

    Displays client name in "LastName, FirstName" format with bold last name.
    Shows tags as blue chips only when they match the search query.

    Signals:
        clicked(): Emitted when the row is clicked

    Attributes:
        client_id: Database ID of this client
        client_data: Dictionary containing client information
        _tags_widget: Widget containing tag chips (hidden by default)
    """

    # Signal emitted when row is clicked
    clicked = pyqtSignal()

    # Fixed row height for consistent layout
    ROW_HEIGHT = 50

    def __init__(
        self, client_id: int, client_data: dict, parent: Optional[QWidget] = None
    ):
        """
        Initialize a client row.

        Args:
            client_id: Database ID of the client
            client_data: Dictionary with keys: first_name, last_name, tags (list)
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.client_id = client_id
        self.client_data = client_data

        # Tags widget reference for visibility control
        self._tags_widget: Optional[QWidget] = None

        # Set fixed height for consistent rows
        self.setFixedHeight(self.ROW_HEIGHT)

        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("client_row", True)  # CSS class

        # Set up the UI
        self._init_ui()

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates a layout with name label and optional tag chips.
        Tags are hidden by default and shown only when search matches.
        """
        # Main horizontal layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Client name: "LastName, FirstName" (bold last name)
        # WHY this format: Common in professional contexts, easy to scan alphabetically
        last_name = self.client_data.get("last_name", "")
        first_name = self.client_data.get("first_name", "")

        name_label = QLabel(f"<b>{last_name}</b>, {first_name}")
        name_label.setProperty("client_name", True)  # CSS class
        layout.addWidget(name_label)

        # Add stretch to push tags to the right
        layout.addStretch()

        # Tags (if present) - hidden by default, shown when search matches
        tags = self.client_data.get("tags", [])
        if tags:
            self._tags_widget = self._create_tags_widget(tags)
            self._tags_widget.setVisible(False)  # Hidden by default
            layout.addWidget(self._tags_widget)

    def _create_tags_widget(self, tags: List[str]) -> QWidget:
        """
        Create a widget displaying tag chips.

        Args:
            tags: List of tag strings

        Returns:
            QWidget containing tag chips in horizontal layout
        """
        tags_container = QWidget()
        tags_layout = QHBoxLayout(tags_container)
        tags_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.setSpacing(4)

        # Create small tag chips
        for tag in tags[:3]:  # Limit to 3 tags to avoid overflow
            tag_chip = QLabel(tag)
            tag_chip.setProperty(
                "tag_chip_small", True
            )  # CSS class for small blue chips
            tags_layout.addWidget(tag_chip)

        # If more than 3 tags, show "+N more"
        if len(tags) > 3:
            more_label = QLabel(f"+{len(tags) - 3} more")
            more_label.setProperty("tag_more", True)  # CSS class
            tags_layout.addWidget(more_label)

        return tags_container

    def set_search_query(self, query: str) -> None:
        """
        Update tag visibility based on search query.

        Tags are shown only if the query matches any of the client's tags.

        Args:
            query: Current search query (empty string shows no tags)
        """
        if not self._tags_widget:
            return

        # No query = hide tags
        if not query:
            self._tags_widget.setVisible(False)
            return

        # Check if query matches any tag (case-insensitive)
        tags = self.client_data.get("tags", [])
        query_lower = query.lower()
        matches_tag = any(query_lower in tag.lower() for tag in tags)

        self._tags_widget.setVisible(matches_tag)

    def mousePressEvent(self, event):
        """
        Handle mouse press event to emit clicked signal.

        Args:
            event: Mouse press event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ClientListView(QWidget):
    """
    Main view showing all clients with search and filtering.

    This view provides a searchable, filterable list of clients with
    infinite scroll pagination. Users can search by name and tags,
    filter by alphabet, and click clients to view details.

    Signals:
        client_selected(int): Emitted when a client is clicked (passes client_id)
        add_client_clicked(): Emitted when the Add Client button is clicked

    Attributes:
        _current_search: Current search query
        _current_filter: Current alphabet filter
        _loaded_clients: List of currently loaded client IDs
        _has_more: Whether more clients are available to load
        _loading: Whether clients are currently being loaded
    """

    # Signals
    client_selected = pyqtSignal(int)  # Passes client_id
    add_client_clicked = pyqtSignal()

    # Pagination settings
    CLIENTS_PER_PAGE = 20

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the client list view.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # State tracking
        self._current_search: str = ""
        self._current_filter: str = "All"
        self._loaded_clients: List[int] = []
        self._has_more: bool = True
        self._loading: bool = False

        # Set up the UI
        self._init_ui()

        # Initial load
        # NOTE: This will be connected to a controller method later
        self._load_initial_clients()

        logger.debug("ClientListView initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates the layout with search bar, alphabet filter, and client list.
        """
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar: search + add button
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)

        # Content area: client list + filter sidebar
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 12, 0)  # Right margin for alphabet filter
        content_layout.setSpacing(8)

        # Client list (scrollable) - takes most of the space
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        # Connect scroll event for infinite scroll
        # WHY verticalScrollBar: We need to detect when user scrolls near bottom
        self._scroll_area.verticalScrollBar().valueChanged.connect(
            self._on_scroll_changed
        )

        # Container for client rows
        self._client_container = QWidget()
        self._client_layout = QVBoxLayout(self._client_container)
        self._client_layout.setContentsMargins(8, 8, 8, 8)
        self._client_layout.setSpacing(8)  # Gap between list entries
        self._client_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll_area.setWidget(self._client_container)
        content_layout.addWidget(self._scroll_area, stretch=1)

        # Right sidebar: alphabet filter
        self._alphabet_filter = AlphabetFilter()
        self._alphabet_filter.filter_changed.connect(self._on_filter_changed)
        content_layout.addWidget(self._alphabet_filter)

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
        self._search_bar.set_placeholder(_("Search clients by name or tags..."))
        self._search_bar.search_changed.connect(self._on_search_changed)
        layout.addWidget(self._search_bar, stretch=1)

        # Add client button
        add_btn = QPushButton("+ " + _("Add Client"))
        add_btn.setProperty("class", "primary")  # Primary button styling
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.add_client_clicked.emit)
        add_btn.setMinimumWidth(120)
        layout.addWidget(add_btn)

        return top_bar

    def _on_search_changed(self, query: str) -> None:
        """
        Handle search query change.

        Resets to first page and loads clients matching the search.

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

        Resets to first page and loads clients starting with the selected letter.

        Args:
            letter: Selected letter ("All", "A"-"Z", or "#")
        """
        logger.debug(f"Filter changed: {letter}")

        self._current_filter = letter

        # Reset and reload
        self._reset_and_reload()

    def _reset_and_reload(self) -> None:
        """
        Reset the client list and reload from the beginning.

        Clears all loaded clients and loads the first page with current filters.
        """
        # Clear current clients
        self._clear_client_list()

        # Reset state
        self._loaded_clients.clear()
        self._has_more = True

        # Load first page
        self._load_more_clients()

    def _clear_client_list(self) -> None:
        """
        Remove all client rows from the UI.
        """
        # Remove all widgets from layout
        while self._client_layout.count():
            item = self._client_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _on_scroll_changed(self, value: int) -> None:
        """
        Handle scroll position change.

        Loads more clients when scrolling near the bottom (infinite scroll).

        Args:
            value: Current scroll position
        """
        # Check if we're near the bottom
        # WHY 100 pixels: Provides smooth UX - loads before reaching absolute bottom
        scrollbar = self._scroll_area.verticalScrollBar()
        max_value = scrollbar.maximum()

        # Load more when within 100 pixels of bottom
        if value >= max_value - 100 and not self._loading and self._has_more:
            self._load_more_clients()

    def _load_initial_clients(self) -> None:
        """
        Load the initial page of clients.

        This is called when the view is first created.
        """
        self._load_more_clients()

    def _load_more_clients(self) -> None:
        """
        Load the next page of clients from the database.

        Uses the ClientController to fetch clients based on current
        search query and alphabet filter.

        Note:
            Sets _loading flag to prevent duplicate requests.
            Updates _has_more flag based on results.
        """
        if self._loading:
            return

        self._loading = True
        offset = len(self._loaded_clients)
        logger.debug(
            f"Loading clients (offset: {offset}, "
            f"search: '{self._current_search}', filter: '{self._current_filter}')"
        )

        try:
            # Load clients from database
            # WHY context manager: Ensures database connection is properly closed
            with DatabaseConnection() as db:
                controller = ClientController(db)

                # Determine which method to call based on search/filter state
                if self._current_search:
                    # Search mode: fuzzy search across name and tags
                    # NOTE: Search doesn't support pagination, returns all matches
                    clients = controller.search_clients(
                        self._current_search, limit=self.CLIENTS_PER_PAGE
                    )
                    # Since search returns all at once, no more to load
                    self._has_more = False
                elif self._current_filter != "All":
                    # Filter mode: filter by first letter of last name
                    if self._current_filter == "#":
                        # Special case: non-alphabetic first characters
                        # WHY not implemented yet: Complex query, rare use case
                        clients = []
                        self._has_more = False
                    else:
                        clients = controller.filter_by_letter(
                            self._current_filter,
                            limit=self.CLIENTS_PER_PAGE,
                            offset=offset
                        )
                        self._has_more = len(clients) >= self.CLIENTS_PER_PAGE
                else:
                    # Default mode: all clients, paginated
                    clients = controller.get_all_clients(
                        limit=self.CLIENTS_PER_PAGE, offset=offset
                    )
                    self._has_more = len(clients) >= self.CLIENTS_PER_PAGE

            # Convert Client models to dictionaries for display
            client_dicts = []
            for client in clients:
                client_dicts.append({
                    "id": client.id,
                    "first_name": client.first_name,
                    "last_name": client.last_name,
                    "tags": client.tags,
                })

            # Add clients to the view
            self.add_clients(client_dicts)

            logger.debug(f"Loaded {len(clients)} clients from database")

        except Exception as e:
            logger.error(f"Failed to load clients: {e}")
            self._has_more = False

        self._loading = False

    def add_clients(self, clients: List[dict]) -> None:
        """
        Add loaded clients to the view.

        This method should be called by the controller with loaded client data.

        Args:
            clients: List of client dictionaries, each containing:
                    - id: Client database ID
                    - first_name: Client's first name
                    - last_name: Client's last name
                    - tags: List of tag strings (optional)

        Note:
            This method updates _has_more based on whether a full page was loaded.
        """
        for client_data in clients:
            client_id = client_data["id"]

            # Create client row
            client_row = ClientRow(client_id, client_data)
            client_row.clicked.connect(
                lambda cid=client_id: self._on_client_clicked(cid)
            )

            # Update tag visibility based on current search query
            # Tags are only shown when search matches a tag
            client_row.set_search_query(self._current_search)

            # Add to layout
            self._client_layout.addWidget(client_row)

            # Track loaded client
            self._loaded_clients.append(client_id)

        # Update pagination state
        # WHY: If we got fewer than a full page, we've reached the end
        self._has_more = len(clients) >= self.CLIENTS_PER_PAGE
        self._loading = False

        logger.debug(
            f"Added {len(clients)} clients (total: {len(self._loaded_clients)})"
        )

    def _on_client_clicked(self, client_id: int) -> None:
        """
        Handle client row click.

        Emits the client_selected signal with the client ID.

        Args:
            client_id: Database ID of the clicked client
        """
        logger.debug(f"Client clicked: {client_id}")
        self.client_selected.emit(client_id)

    def refresh(self) -> None:
        """
        Refresh the client list.

        Reloads clients from the beginning with current search and filter.
        This should be called after adding/editing/deleting a client.
        """
        logger.debug("Refreshing client list")
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
        Get the number of currently loaded clients.

        Returns:
            int: Number of loaded clients
        """
        return len(self._loaded_clients)
