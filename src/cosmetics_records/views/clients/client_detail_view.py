# =============================================================================
# Cosmetics Records - Client Detail View
# =============================================================================
# This module provides the detailed client view with treatment and product history.
#
# Key Features:
#   - Client header with name, age, allergies
#   - Edit button to modify client details
#   - 2x2 grid layout for information sections
#   - Auto-saving text fields (1 second debounce)
#   - Treatment history with timestamps and edit/delete
#   - Product history with timestamps and edit/delete
#   - Pagination for history lists
#
# Design Philosophy:
#   - Auto-save: No explicit save button needed, changes persist automatically
#   - Timestamps: Show creation time and edit time for full audit trail
#   - Hover actions: Edit/delete buttons appear on hover for clean UI
#   - Pagination: Load history in chunks for performance
#
# Layout:
#   ┌─────────────────────────────────────────────┐
#   │ John Smith (Age: 35)         [Edit] [Back] │
#   │ ⚠ Allergies: Latex, Aspirin                │
#   ├─────────────────────┬───────────────────────┤
#   │ Planned Treatment   │ Personal Notes        │
#   │ (auto-save text)    │ (auto-save text)      │
#   ├─────────────────────┼───────────────────────┤
#   │ Treatment History   │ Product History       │
#   │ [+ Add] [Show More] │ [+ Add] [Show More]   │
#   └─────────────────────┴───────────────────────┘
#
# Usage Example:
#   detail_view = ClientDetailView()
#   detail_view.load_client(client_id)
#   detail_view.client_updated.connect(refresh_list)
#   detail_view.back_to_list.connect(show_list_view)
# =============================================================================

import logging
from datetime import datetime, date

from cosmetics_records.utils.time_utils import format_date_localized
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtCore import QEvent
    from PyQt6.QtGui import QEnterEvent

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QGridLayout,
)

# Configure module logger
logger = logging.getLogger(__name__)


class HistoryItem(QFrame):
    """
    Single history item (treatment or product record).

    Displays date, notes preview, and edit button on hover.
    Delete is handled in the edit dialog.

    Signals:
        edit_clicked(): Emitted when edit button is clicked

    Attributes:
        item_id: Database ID of this history item
        item_data: Dictionary containing item information
    """

    # Signals
    edit_clicked = pyqtSignal()

    def __init__(self, item_id: int, item_data: dict, parent: Optional[QWidget] = None):
        """
        Initialize a history item.

        Args:
            item_id: Database ID of the history item
            item_data: Dictionary with keys:
                      - date: Date of the treatment/product
                      - notes: Text content
                      - created_at: Creation timestamp (optional)
                      - updated_at: Last update timestamp (optional)
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.item_id = item_id
        self.item_data = item_data

        self.setProperty("history_item", True)  # CSS class

        # Set up the UI
        self._init_ui()

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates layout with date, notes, and action buttons.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Top row: date and action buttons
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Date label - format according to user's date format preference
        item_date = self.item_data.get("date")
        created_at = self.item_data.get("created_at")

        if isinstance(item_date, date):
            date_str = format_date_localized(item_date)
            # Add time from created_at if available
            if isinstance(created_at, datetime):
                date_str += f" {created_at.strftime('%H:%M')}"
        else:
            date_str = str(item_date)

        date_label = QLabel(date_str)
        date_label.setProperty("history_date", True)  # CSS class
        top_row.addWidget(date_label)

        top_row.addStretch()

        # Edit button (hidden via CSS property, shown on hover)
        # Delete is handled in the edit dialog
        # Using "Edit" text for reliability across fonts
        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setProperty("class", "history_edit_button")
        self._edit_btn.setProperty("visible_state", "hidden")
        self._edit_btn.setFixedSize(50, 24)  # Fixed size to prevent layout shifts
        self._edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._edit_btn.clicked.connect(self.edit_clicked.emit)
        top_row.addWidget(self._edit_btn)

        layout.addLayout(top_row)

        # Notes content (full text with word wrap)
        notes = self.item_data.get("notes", "")

        notes_label = QLabel(notes)
        notes_label.setProperty("history_notes", True)  # CSS class
        notes_label.setWordWrap(True)
        layout.addWidget(notes_label)

    def enterEvent(self, event: Optional["QEnterEvent"]) -> None:
        """
        Show edit button when mouse enters the widget.

        Args:
            event: Enter event
        """
        self._edit_btn.setProperty("visible_state", "visible")
        # Refresh stylesheet to apply new property state
        style = self._edit_btn.style()
        if style:
            style.unpolish(self._edit_btn)
            style.polish(self._edit_btn)
        super().enterEvent(event)

    def leaveEvent(self, event: Optional["QEvent"]) -> None:
        """
        Hide edit button when mouse leaves the widget.

        Args:
            event: Leave event
        """
        self._edit_btn.setProperty("visible_state", "hidden")
        # Refresh stylesheet to apply new property state
        style = self._edit_btn.style()
        if style:
            style.unpolish(self._edit_btn)
            style.polish(self._edit_btn)
        super().leaveEvent(event)


class HistoryList(QWidget):
    """
    List of history items with auto-load on scroll.

    Displays treatment or product history with infinite scroll functionality.
    Automatically loads more items when scrolling near the bottom.

    Signals:
        add_clicked(): Emitted when Add button is clicked
        load_more_clicked(): Emitted when more items need to be loaded
        edit_item(int): Emitted when item edit is clicked (passes item_id)

    Attributes:
        _title: Title for this history list
        _items: List of loaded item IDs
        _loading: Whether items are currently being loaded
    """

    # Signals
    add_clicked = pyqtSignal()
    load_more_clicked = pyqtSignal()
    edit_item = pyqtSignal(int)  # Passes item_id

    # Items per page
    ITEMS_PER_PAGE = 20

    def __init__(self, title: str, parent: Optional[QWidget] = None):
        """
        Initialize a history list.

        Args:
            title: Title for this list (e.g., "Treatment History")
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._title = title
        self._items: List[int] = []
        self._has_more: bool = True
        self._loading: bool = False

        # Set up the UI
        self._init_ui()

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates layout with title, scrollable items list with auto-load,
        and end-of-list message.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Title and Add button
        title_row = QHBoxLayout()
        title_label = QLabel(self._title)
        title_label.setProperty("section_title", True)  # CSS class
        title_row.addWidget(title_label)

        title_row.addStretch()

        add_btn = QPushButton("+ Add")
        add_btn.setProperty("class", "primary")
        add_btn.setMinimumWidth(80)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.add_clicked.emit)
        title_row.addWidget(add_btn)

        layout.addLayout(title_row)

        # Scrollable items list
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll_area.setProperty("history_section", True)  # CSS class

        # Connect scroll event for auto-load
        self._scroll_area.verticalScrollBar().valueChanged.connect(
            self._on_scroll_changed
        )

        self._items_container = QWidget()
        self._items_container.setProperty("history_container", True)  # CSS class
        self._items_layout = QVBoxLayout(self._items_container)
        self._items_layout.setContentsMargins(8, 8, 8, 8)
        self._items_layout.setSpacing(8)  # Gap between history items
        self._items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # End of list message (inside scroll area, hidden by default)
        self._end_label = QFrame()
        self._end_label.setProperty("history_item", True)  # Same style as entries
        self._end_label_layout = QVBoxLayout(self._end_label)
        self._end_label_layout.setContentsMargins(12, 12, 12, 12)
        self._end_label_text = QLabel()
        self._end_label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._end_label_text.setProperty("history_notes", True)
        self._end_label_layout.addWidget(self._end_label_text)
        self._end_label.setVisible(False)
        self._items_layout.addWidget(self._end_label)

        self._scroll_area.setWidget(self._items_container)
        layout.addWidget(self._scroll_area, stretch=1)

    def _on_scroll_changed(self, value: int) -> None:
        """
        Handle scroll position change for auto-loading.

        Loads more items when scrolling near the bottom.

        Args:
            value: Current scroll position
        """
        if self._loading or not self._has_more:
            return

        scrollbar = self._scroll_area.verticalScrollBar()
        max_value = scrollbar.maximum()

        # Load more when within 50 pixels of bottom
        if value >= max_value - 50:
            self._loading = True
            self.load_more_clicked.emit()

    def add_items(self, items: List[dict]) -> None:
        """
        Add history items to the list.

        Args:
            items: List of item dictionaries, each containing:
                  - id: Item database ID
                  - date: Date of the treatment/product
                  - notes: Text content
                  - created_at: Creation timestamp (optional)
                  - updated_at: Last update timestamp (optional)
        """
        # Find the position before the end label (end label should always be last)
        end_label_index = self._items_layout.indexOf(self._end_label)
        insert_position = (
            end_label_index if end_label_index >= 0 else self._items_layout.count()
        )

        for item_data in items:
            item_id = item_data["id"]

            # Create history item
            history_item = HistoryItem(item_id, item_data)
            history_item.edit_clicked.connect(
                lambda iid=item_id: self.edit_item.emit(iid)
            )

            # Insert before the end label
            self._items_layout.insertWidget(insert_position, history_item)
            insert_position += 1

            # Track loaded item
            self._items.append(item_id)

        # Update state
        self._has_more = len(items) >= self.ITEMS_PER_PAGE
        self._loading = False

        # Show end message when no more items
        self._update_end_message()

    def _update_end_message(self) -> None:
        """
        Update the end-of-list message visibility and text.

        Only shows when scrollbar is visible and all items are loaded.
        """
        scrollbar = self._scroll_area.verticalScrollBar()
        scrollbar_visible = scrollbar.isVisible() and scrollbar.maximum() > 0

        if not self._has_more and len(self._items) > 0 and scrollbar_visible:
            # Determine message based on title
            if "Treatment" in self._title:
                self._end_label_text.setText("No more treatments")
            elif "Product" in self._title:
                self._end_label_text.setText("No more products")
            else:
                self._end_label_text.setText("No more items")
            self._end_label.setVisible(True)
        else:
            self._end_label.setVisible(False)

    def clear_items(self) -> None:
        """
        Remove all items from the list.

        Preserves the end label widget which is always at the end of the layout.
        """
        # Remove items in reverse order, skipping the end_label
        for i in reversed(range(self._items_layout.count())):
            item = self._items_layout.itemAt(i)
            widget = item.widget()
            if widget and widget != self._end_label:
                self._items_layout.takeAt(i)
                widget.deleteLater()

        self._items.clear()
        self._has_more = True
        self._loading = False
        self._end_label.setVisible(False)


class AutoSaveTextEdit(QTextEdit):
    """
    Text edit widget with auto-save functionality.

    Saves changes after 1 second of inactivity.

    Signals:
        content_saved(str): Emitted when content is auto-saved (passes text)

    Attributes:
        _save_timer: QTimer for debouncing saves
    """

    # Signal emitted when content is saved
    content_saved = pyqtSignal(str)

    # Auto-save delay in milliseconds
    # WHY 1000ms (1 second): Long enough to avoid saving on every keystroke,
    # short enough to feel automatic
    AUTOSAVE_DELAY = 1000

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize an auto-save text edit.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Create save timer
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_content)

        # Connect text change to timer
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self) -> None:
        """
        Handle text change by restarting the save timer.

        The timer restarts on each change, so saving only happens
        after the user stops typing for 1 second.
        """
        self._save_timer.stop()
        self._save_timer.start(self.AUTOSAVE_DELAY)

    def _save_content(self) -> None:
        """
        Save the current content.

        Emits the content_saved signal with the current text.
        """
        text = self.toPlainText()
        self.content_saved.emit(text)
        logger.debug("Auto-save triggered")


class ClientDetailView(QWidget):
    """
    Detailed client view with treatment and product history.

    This view displays full client information including demographics,
    planned treatment, personal notes, and complete treatment/product history.

    Signals:
        client_updated(): Emitted when any client data changes
        back_to_list(): Emitted when back button is clicked

    Attributes:
        _client_id: Currently displayed client ID
        _client_data: Dictionary containing client information
    """

    # Signals
    client_updated = pyqtSignal()
    back_to_list = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the client detail view.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # State tracking
        self._client_id: Optional[int] = None
        self._client_data: Optional[dict] = None

        # Set up the UI
        self._init_ui()

        logger.debug("ClientDetailView initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates the layout with header, grid sections, and history lists.
        """
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header section
        header = self._create_header()
        main_layout.addWidget(header)

        # 2x2 Grid layout for main content
        grid = QGridLayout()
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setSpacing(16)

        # Top-left: Planned Treatment
        planned_frame = self._create_section_frame("Planned Treatment")
        self._planned_treatment_edit = AutoSaveTextEdit()
        self._planned_treatment_edit.setPlaceholderText(
            "Enter planned treatment details..."
        )
        self._planned_treatment_edit.content_saved.connect(
            self._on_planned_treatment_saved
        )
        planned_frame.layout().addWidget(self._planned_treatment_edit)
        grid.addWidget(planned_frame, 0, 0)

        # Top-right: Personal Notes
        notes_frame = self._create_section_frame("Personal Notes")
        self._personal_notes_edit = AutoSaveTextEdit()
        self._personal_notes_edit.setPlaceholderText("Enter personal notes...")
        self._personal_notes_edit.content_saved.connect(self._on_personal_notes_saved)
        notes_frame.layout().addWidget(self._personal_notes_edit)
        grid.addWidget(notes_frame, 0, 1)

        # Bottom-left: Treatment History
        self._treatment_history = HistoryList("Treatment History")
        self._treatment_history.add_clicked.connect(self._on_add_treatment)
        self._treatment_history.load_more_clicked.connect(self._on_load_more_treatments)
        self._treatment_history.edit_item.connect(self._on_edit_treatment)
        grid.addWidget(self._treatment_history, 1, 0)

        # Bottom-right: Product History
        self._product_history = HistoryList("Product History")
        self._product_history.add_clicked.connect(self._on_add_product)
        self._product_history.load_more_clicked.connect(self._on_load_more_products)
        self._product_history.edit_item.connect(self._on_edit_product)
        grid.addWidget(self._product_history, 1, 1)

        # Set row stretch: row 0 (freetext) = 1, row 1 (history) = 2
        # WHY 1:2 ratio: User requested 1/3 for freetext, 2/3 for history
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 2)

        main_layout.addLayout(grid)

    def _create_header(self) -> QWidget:
        """
        Create the header section with client info and action buttons.

        Returns:
            QWidget containing header elements
        """
        header = QWidget()
        header.setFixedHeight(70)  # Reduced height since allergies moved inline
        header.setProperty("detail_header", True)  # CSS class

        layout = QVBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Single row: name, age, allergies, and edit button
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # Client name - larger font via QSS
        self._name_label = QLabel("Client Name")
        self._name_label.setProperty("client_detail_name", True)  # CSS class
        top_row.addWidget(self._name_label)

        # Age - slightly smaller than name
        self._age_label = QLabel("(Age: --)")
        self._age_label.setProperty("client_age", True)  # CSS class
        top_row.addWidget(self._age_label)

        # Allergies warning - inline with age, red text
        self._allergies_label = QLabel()
        self._allergies_label.setProperty("allergies_warning", True)  # CSS class (red)
        self._allergies_label.setVisible(False)
        top_row.addWidget(self._allergies_label)

        top_row.addStretch()

        # Edit button (back button removed - navigation via navbar)
        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("class", "secondary")
        edit_btn.setMinimumWidth(80)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(self._on_edit_client)
        top_row.addWidget(edit_btn)

        layout.addLayout(top_row)

        return header

    def _create_section_frame(self, title: str) -> QFrame:
        """
        Create a framed section with title.

        Args:
            title: Section title

        Returns:
            QFrame with vertical layout for content
        """
        frame = QFrame()
        frame.setProperty("section_frame", True)  # CSS class

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setProperty("section_title", True)  # CSS class
        layout.addWidget(title_label)

        return frame

    def load_client(self, client_id: int) -> None:
        """
        Load and display client details from the database.

        Args:
            client_id: Database ID of the client to load
        """
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.client_controller import ClientController

        self._client_id = client_id

        logger.debug(f"Loading client: {client_id}")

        try:
            with DatabaseConnection() as db:
                controller = ClientController(db)
                client = controller.get_client(client_id)

                if client:
                    self._client_data = {
                        "id": client.id,
                        "first_name": client.first_name,
                        "last_name": client.last_name,
                        "date_of_birth": client.date_of_birth,
                        "allergies": client.allergies or "",
                        "planned_treatment": client.planned_treatment or "",
                        "notes": client.notes or "",
                    }
                    logger.debug(f"Loaded client: {client.full_name()}")
                else:
                    logger.error(f"Client not found: {client_id}")
                    self._client_data = None

        except Exception as e:
            logger.error(f"Failed to load client {client_id}: {e}")
            self._client_data = None

        self._update_ui()
        self._load_history()

    def _update_ui(self) -> None:
        """
        Update the UI with current client data.

        Populates all fields with data from _client_data.
        """
        if not self._client_data:
            return

        # Update name
        first_name = self._client_data.get("first_name", "")
        last_name = self._client_data.get("last_name", "")
        self._name_label.setText(f"{first_name} {last_name}")

        # Update age (calculated from DOB) - show just the number in parentheses
        dob = self._client_data.get("date_of_birth")
        if dob and isinstance(dob, date):
            age = self._calculate_age(dob)
            self._age_label.setText(f"({age})")
            self._age_label.setVisible(True)
        else:
            # Hide age label if no DOB
            self._age_label.setVisible(False)

        # Update allergies (shown in red, no prefix)
        allergies = self._client_data.get("allergies", "").strip()
        if allergies:
            self._allergies_label.setText(allergies)
            self._allergies_label.setVisible(True)
        else:
            self._allergies_label.setVisible(False)

        # Update planned treatment
        planned = self._client_data.get("planned_treatment", "")
        self._planned_treatment_edit.setPlainText(planned)

        # Update personal notes
        notes = self._client_data.get("notes", "")
        self._personal_notes_edit.setPlainText(notes)

    def _calculate_age(self, birth_date: date) -> int:
        """
        Calculate age from birth date.

        Args:
            birth_date: Date of birth

        Returns:
            int: Age in years
        """
        today = date.today()
        age = today.year - birth_date.year

        # Adjust if birthday hasn't occurred yet this year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1

        return age

    def _load_history(self) -> None:
        """
        Load treatment and product history from the database.

        Clears existing history and loads fresh data for the current client.
        """
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.treatment_controller import (
            TreatmentController,
        )
        from cosmetics_records.controllers.product_controller import ProductController

        if not self._client_id:
            return

        # Clear existing items
        self._treatment_history.clear_items()
        self._product_history.clear_items()

        try:
            with DatabaseConnection() as db:
                # Load treatments
                treatment_controller = TreatmentController(db)
                treatments = treatment_controller.get_treatments_for_client(
                    self._client_id, limit=20
                )

                # Convert to format expected by HistoryList
                treatment_items = []
                for t in treatments:
                    treatment_items.append(
                        {
                            "id": t.id,
                            "date": t.treatment_date,
                            "notes": t.treatment_notes,
                            "created_at": t.created_at,
                            "updated_at": t.updated_at,
                        }
                    )

                self._treatment_history.add_items(treatment_items)
                logger.debug(f"Loaded {len(treatment_items)} treatments")

                # Load products
                product_controller = ProductController(db)
                products = product_controller.get_product_records_for_client(
                    self._client_id, limit=20
                )

                # Convert to format expected by HistoryList
                product_items = []
                for p in products:
                    product_items.append(
                        {
                            "id": p.id,
                            "date": p.product_date,
                            "notes": p.product_text,
                            "created_at": p.created_at,
                            "updated_at": p.updated_at,
                        }
                    )

                self._product_history.add_items(product_items)
                logger.debug(f"Loaded {len(product_items)} products")

        except Exception as e:
            logger.error(f"Failed to load history: {e}")

    def _on_planned_treatment_saved(self, text: str) -> None:
        """
        Handle planned treatment auto-save.

        Args:
            text: Updated planned treatment text
        """
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.client_controller import ClientController

        if not self._client_id:
            return

        logger.debug("Saving planned treatment")

        try:
            with DatabaseConnection() as db:
                controller = ClientController(db)
                client = controller.get_client(self._client_id)
                if client:
                    client.planned_treatment = text
                    controller.update_client(client)
                    logger.debug("Planned treatment saved")
                    self.client_updated.emit()
        except Exception as e:
            logger.error(f"Failed to save planned treatment: {e}")

    def _on_personal_notes_saved(self, text: str) -> None:
        """
        Handle personal notes auto-save.

        Args:
            text: Updated personal notes text
        """
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.client_controller import ClientController

        if not self._client_id:
            return

        logger.debug("Saving personal notes")

        try:
            with DatabaseConnection() as db:
                controller = ClientController(db)
                client = controller.get_client(self._client_id)
                if client:
                    client.notes = text
                    controller.update_client(client)
                    logger.debug("Personal notes saved")
                    self.client_updated.emit()
        except Exception as e:
            logger.error(f"Failed to save personal notes: {e}")

    def _on_edit_client(self) -> None:
        """
        Handle edit client button click.

        Opens the edit client dialog and saves changes to database.
        """
        from cosmetics_records.views.dialogs.edit_client_dialog import EditClientDialog
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.client_controller import ClientController

        if not self._client_id or not self._client_data:
            logger.error("Cannot edit client: no client loaded")
            return

        logger.debug("Edit client clicked")

        try:
            # Prepare client data for dialog
            dialog_data = {
                "first_name": self._client_data.get("first_name", ""),
                "last_name": self._client_data.get("last_name", ""),
                "email": "",  # Need to load from database
                "phone": "",
                "address": "",
                "date_of_birth": self._client_data.get("date_of_birth"),
                "allergies": self._client_data.get("allergies", ""),
                "tags": [],
            }

            # Load full client data from database
            with DatabaseConnection() as db:
                controller = ClientController(db)
                client = controller.get_client(self._client_id)
                if client:
                    dialog_data = {
                        "first_name": client.first_name,
                        "last_name": client.last_name,
                        "email": client.email or "",
                        "phone": client.phone or "",
                        "address": client.address or "",
                        "date_of_birth": client.date_of_birth,
                        "allergies": client.allergies or "",
                        "tags": client.tags,
                    }

            dialog = EditClientDialog(self._client_id, dialog_data, self)
            result = dialog.exec()

            if dialog.was_deleted():
                # Client was deleted - go back to list
                with DatabaseConnection() as db:
                    controller = ClientController(db)
                    controller.delete_client(self._client_id)
                    logger.info(f"Client deleted: {self._client_id}")
                self.back_to_list.emit()

            elif result:
                # Client was updated
                updated_data = dialog.get_client_data()

                with DatabaseConnection() as db:
                    controller = ClientController(db)
                    client = controller.get_client(self._client_id)
                    if client:
                        client.first_name = updated_data["first_name"]
                        client.last_name = updated_data["last_name"]
                        client.email = updated_data.get("email") or None
                        client.phone = updated_data.get("phone") or None
                        client.address = updated_data.get("address") or None
                        client.date_of_birth = updated_data.get("date_of_birth")
                        client.allergies = updated_data.get("allergies") or None
                        client.tags = updated_data.get("tags", [])
                        controller.update_client(client)
                        logger.info(f"Client updated: {client.full_name()}")

                # Reload to show updated data
                self.load_client(self._client_id)
                self.client_updated.emit()

        except Exception as e:
            logger.error(f"Failed to edit client: {e}")

    def _on_add_treatment(self) -> None:
        """
        Handle add treatment button click.

        Opens the add treatment dialog and saves the treatment to database.
        If a treatment already exists for today, opens it for editing instead.
        """
        from cosmetics_records.views.dialogs.add_treatment_dialog import (
            AddTreatmentDialog,
        )
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.treatment_controller import (
            TreatmentController,
        )
        from cosmetics_records.models.treatment import TreatmentRecord

        if not self._client_id:
            logger.error("Cannot add treatment: no client loaded")
            return

        logger.debug("Add treatment clicked")

        try:
            dialog = AddTreatmentDialog(self._client_id, self)

            # Check if treatment exists for today
            with DatabaseConnection() as db:
                controller = TreatmentController(db)
                existing = controller.get_treatment_for_date(
                    self._client_id, date.today()
                )
                if existing and existing.id is not None:
                    # Edit existing treatment instead of creating new
                    dialog.set_existing_treatment(existing.id, existing.treatment_notes)
                    logger.debug(f"Found existing treatment for today: {existing.id}")

            if dialog.exec():
                # Get treatment data from dialog
                treatment_data = dialog.get_treatment_data()

                with DatabaseConnection() as db:
                    controller = TreatmentController(db)

                    if dialog.is_editing_existing():
                        # Update existing treatment
                        existing_id = dialog.get_existing_treatment_id()
                        if existing_id is None:
                            logger.error("Cannot update treatment: ID is None")
                            return
                        treatment = controller.get_treatment(existing_id)
                        if treatment:
                            treatment.treatment_notes = treatment_data["notes"]
                            controller.update_treatment(treatment)
                            logger.info(f"Treatment {existing_id} updated")
                    else:
                        # Create new treatment
                        treatment = TreatmentRecord(
                            client_id=treatment_data["client_id"],
                            treatment_date=treatment_data["date"],
                            treatment_notes=treatment_data["notes"],
                        )
                        treatment_id = controller.create_treatment(treatment)
                        logger.info(f"Treatment created with ID: {treatment_id}")

                # Reload history to show changes
                self._load_history()
                self.client_updated.emit()

        except Exception as e:
            logger.error(f"Failed to add treatment: {e}")

    def _on_load_more_treatments(self) -> None:
        """
        Handle load more treatments button click.

        Loads the next page of treatments from the database and appends
        them to the treatment history list.
        """
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.treatment_controller import (
            TreatmentController,
        )

        if not self._client_id:
            return

        # Calculate offset based on already loaded items
        offset = len(self._treatment_history._items)
        logger.debug(f"Loading more treatments (offset: {offset})")

        try:
            with DatabaseConnection() as db:
                controller = TreatmentController(db)
                treatments = controller.get_treatments_for_client(
                    self._client_id,
                    limit=HistoryList.ITEMS_PER_PAGE,
                    offset=offset,
                )

                # Convert to format expected by HistoryList
                treatment_items = []
                for t in treatments:
                    treatment_items.append(
                        {
                            "id": t.id,
                            "date": t.treatment_date,
                            "notes": t.treatment_notes,
                            "created_at": t.created_at,
                            "updated_at": t.updated_at,
                        }
                    )

                # Add items to list (this will update _has_more and _loading)
                self._treatment_history.add_items(treatment_items)
                logger.debug(f"Loaded {len(treatment_items)} more treatments")

        except Exception as e:
            logger.error(f"Failed to load more treatments: {e}")
            # Reset loading state on error so user can retry
            self._treatment_history._loading = False

    def _on_edit_treatment(self, treatment_id: int) -> None:
        """
        Handle edit treatment button click.

        Opens the edit treatment dialog and updates/deletes the treatment.

        Args:
            treatment_id: Database ID of the treatment to edit
        """
        from PyQt6.QtWidgets import QDialog
        from cosmetics_records.views.dialogs.edit_treatment_dialog import (
            EditTreatmentDialog,
        )
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.treatment_controller import (
            TreatmentController,
        )

        logger.debug(f"Edit treatment clicked: {treatment_id}")

        try:
            # Get current treatment data
            with DatabaseConnection() as db:
                controller = TreatmentController(db)
                treatment = controller.get_treatment(treatment_id)

                if not treatment:
                    logger.error(f"Treatment not found: {treatment_id}")
                    return

                treatment_data = {
                    "date": treatment.treatment_date,
                    "notes": treatment.treatment_notes,
                }

            # Show edit dialog
            dialog = EditTreatmentDialog(treatment_id, treatment_data, parent=self)
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                with DatabaseConnection() as db:
                    controller = TreatmentController(db)

                    if dialog.was_deleted():
                        # Delete the treatment
                        controller.delete_treatment(treatment_id)
                        logger.info(f"Treatment {treatment_id} deleted")
                    else:
                        # Update the treatment
                        updated_data = dialog.get_treatment_data()
                        treatment.treatment_date = updated_data["date"]
                        treatment.treatment_notes = updated_data["notes"]
                        controller.update_treatment(treatment)
                        logger.info(f"Treatment {treatment_id} updated")

                # Refresh the history
                self._load_history()

        except Exception as e:
            logger.error(f"Failed to edit treatment {treatment_id}: {e}")

    def _on_delete_treatment(self, treatment_id: int) -> None:
        """
        Handle delete treatment button click.

        Shows confirmation dialog and deletes the treatment if confirmed.

        Args:
            treatment_id: Database ID of the treatment to delete
        """
        from PyQt6.QtWidgets import QDialog
        from cosmetics_records.views.dialogs.base_dialog import ConfirmDialog
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.treatment_controller import (
            TreatmentController,
        )

        logger.debug(f"Delete treatment clicked: {treatment_id}")

        try:
            # Get treatment data for confirmation message
            with DatabaseConnection() as db:
                controller = TreatmentController(db)
                treatment = controller.get_treatment(treatment_id)

                if not treatment:
                    logger.error(f"Treatment not found: {treatment_id}")
                    return

                date_str = treatment.treatment_date.strftime("%B %d, %Y")

            # Show confirmation dialog
            confirm = ConfirmDialog(
                "Delete Treatment",
                f"Are you sure you want to delete the treatment from {date_str}?\n\n"
                f"This action cannot be undone.",
                ok_text="Delete",
                cancel_text="Cancel",
                parent=self,
                width=450,
                height=200,
            )

            if confirm.exec() == QDialog.DialogCode.Accepted:
                # Delete the treatment
                with DatabaseConnection() as db:
                    controller = TreatmentController(db)
                    controller.delete_treatment(treatment_id)
                    logger.info(f"Treatment {treatment_id} deleted")

                # Refresh the history
                self._load_history()

        except Exception as e:
            logger.error(f"Failed to delete treatment {treatment_id}: {e}")

    def _on_add_product(self) -> None:
        """
        Handle add product button click.

        Opens the add product dialog and saves the product record to database.
        If a product record already exists for today, opens it for editing instead.
        """
        from cosmetics_records.views.dialogs.add_product_record_dialog import (
            AddProductRecordDialog,
        )
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.product_controller import ProductController
        from cosmetics_records.controllers.inventory_controller import (
            InventoryController,
        )
        from cosmetics_records.models.product import ProductRecord

        if not self._client_id:
            logger.error("Cannot add product: no client loaded")
            return

        logger.debug("Add product clicked")

        try:
            # Get inventory items for autocomplete
            inventory_names = []
            with DatabaseConnection() as db:
                inv_controller = InventoryController(db)
                inventory_names = inv_controller.get_all_names()

            dialog = AddProductRecordDialog(self._client_id, inventory_names, self)

            # Check if product record exists for today
            with DatabaseConnection() as db:
                controller = ProductController(db)
                existing = controller.get_product_for_date(
                    self._client_id, date.today()
                )
                if existing and existing.id is not None:
                    # Edit existing product record instead of creating new
                    dialog.set_existing_record(existing.id, existing.product_text)
                    logger.debug(
                        f"Found existing product record for today: {existing.id}"
                    )

            if dialog.exec():
                # Get product data from dialog
                product_data = dialog.get_product_record_data()

                with DatabaseConnection() as db:
                    controller = ProductController(db)

                    if dialog.is_editing_existing():
                        # Update existing product record
                        existing_id = dialog.get_existing_record_id()
                        if existing_id is None:
                            logger.error("Cannot update product record: ID is None")
                            return
                        product = controller.get_product_record(existing_id)
                        if product:
                            product.product_text = product_data["product_text"]
                            controller.update_product_record(product)
                            logger.info(f"Product record {existing_id} updated")
                    else:
                        # Create new product record
                        product = ProductRecord(
                            client_id=product_data["client_id"],
                            product_date=product_data["date"],
                            product_text=product_data["product_text"],
                        )
                        product_id = controller.create_product_record(product)
                        logger.info(f"Product record created with ID: {product_id}")

                # Reload history to show changes
                self._load_history()
                self.client_updated.emit()

        except Exception as e:
            logger.error(f"Failed to add product: {e}")

    def _on_load_more_products(self) -> None:
        """
        Handle load more products button click.

        Loads the next page of product records from the database and appends
        them to the product history list.
        """
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.product_controller import ProductController

        if not self._client_id:
            return

        # Calculate offset based on already loaded items
        offset = len(self._product_history._items)
        logger.debug(f"Loading more products (offset: {offset})")

        try:
            with DatabaseConnection() as db:
                controller = ProductController(db)
                products = controller.get_product_records_for_client(
                    self._client_id,
                    limit=HistoryList.ITEMS_PER_PAGE,
                    offset=offset,
                )

                # Convert to format expected by HistoryList
                product_items = []
                for p in products:
                    product_items.append(
                        {
                            "id": p.id,
                            "date": p.product_date,
                            "notes": p.product_text,
                            "created_at": p.created_at,
                            "updated_at": p.updated_at,
                        }
                    )

                # Add items to list (this will update _has_more and _loading)
                self._product_history.add_items(product_items)
                logger.debug(f"Loaded {len(product_items)} more products")

        except Exception as e:
            logger.error(f"Failed to load more products: {e}")
            # Reset loading state on error so user can retry
            self._product_history._loading = False

    def _on_edit_product(self, product_id: int) -> None:
        """
        Handle edit product button click.

        Opens the edit product dialog and updates/deletes the product record.

        Args:
            product_id: Database ID of the product record to edit
        """
        from PyQt6.QtWidgets import QDialog
        from cosmetics_records.views.dialogs.add_product_record_dialog import (
            AddProductRecordDialog,
        )
        from cosmetics_records.views.dialogs.base_dialog import ConfirmDialog
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.product_controller import ProductController
        from cosmetics_records.controllers.inventory_controller import (
            InventoryController,
        )

        logger.debug(f"Edit product clicked: {product_id}")

        try:
            # Get current product data and inventory names
            with DatabaseConnection() as db:
                controller = ProductController(db)
                product = controller.get_product_record(product_id)

                if not product:
                    logger.error(f"Product record not found: {product_id}")
                    return

                inv_controller = InventoryController(db)
                inventory_names = inv_controller.get_all_names()

            # Show edit dialog (reusing AddProductRecordDialog)
            if self._client_id is None:
                logger.error("Cannot edit product record: client_id is None")
                return
            dialog = AddProductRecordDialog(
                self._client_id, inventory_names, parent=self
            )
            dialog.setWindowTitle("Edit Product Sale")
            dialog.set_existing_record(product_id, product.product_text)

            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                with DatabaseConnection() as db:
                    controller = ProductController(db)

                    # Check if user wants to delete (empty text)
                    product_data = dialog.get_product_record_data()
                    if not product_data["product_text"].strip():
                        # Show delete confirmation
                        confirm = ConfirmDialog(
                            "Delete Product Sale",
                            "The product text is empty. Delete this record?",
                            ok_text="Delete",
                            cancel_text="Cancel",
                            parent=self,
                        )
                        if confirm.exec() == QDialog.DialogCode.Accepted:
                            controller.delete_product_record(product_id)
                            logger.info(f"Product record {product_id} deleted")
                    else:
                        # Update the product record
                        product.product_text = product_data["product_text"]
                        controller.update_product_record(product)
                        logger.info(f"Product record {product_id} updated")

                # Refresh the history
                self._load_history()

        except Exception as e:
            logger.error(f"Failed to edit product record {product_id}: {e}")

    def _on_delete_product(self, product_id: int) -> None:
        """
        Handle delete product button click.

        Args:
            product_id: Database ID of the product record to delete
        """
        logger.debug(f"Delete product clicked: {product_id}")
        # PLACEHOLDER: Will show confirmation dialog and delete
