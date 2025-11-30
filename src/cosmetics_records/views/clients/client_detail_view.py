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
from typing import List, Optional

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

    Displays date, notes preview, and edit/delete buttons on hover.

    Signals:
        edit_clicked(): Emitted when edit button is clicked
        delete_clicked(): Emitted when delete button is clicked

    Attributes:
        item_id: Database ID of this history item
        item_data: Dictionary containing item information
    """

    # Signals
    edit_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()

    # Fixed height for consistent layout
    ITEM_HEIGHT = 60

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

        self.setFixedHeight(self.ITEM_HEIGHT)
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

        # Date label
        item_date = self.item_data.get("date")
        if isinstance(item_date, date):
            date_str = item_date.strftime("%b %d, %Y")
        else:
            date_str = str(item_date)

        date_label = QLabel(date_str)
        date_label.setProperty("history_date", True)  # CSS class
        top_row.addWidget(date_label)

        top_row.addStretch()

        # Action buttons (initially hidden, shown on hover)
        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setProperty("class", "secondary")
        self._edit_btn.setFixedWidth(60)
        self._edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._edit_btn.clicked.connect(self.edit_clicked.emit)
        self._edit_btn.setVisible(False)
        top_row.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setProperty("class", "danger")
        self._delete_btn.setFixedWidth(60)
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.clicked.connect(self.delete_clicked.emit)
        self._delete_btn.setVisible(False)
        top_row.addWidget(self._delete_btn)

        layout.addLayout(top_row)

        # Notes preview (truncated)
        notes = self.item_data.get("notes", "")
        # WHY 100 chars: Enough to give context without taking too much space
        truncated_notes = notes[:100] + "..." if len(notes) > 100 else notes

        notes_label = QLabel(truncated_notes)
        notes_label.setProperty("history_notes", True)  # CSS class
        notes_label.setWordWrap(True)
        layout.addWidget(notes_label)

        # Timestamp info (created/edited)
        timestamp_text = self._format_timestamp()
        if timestamp_text:
            timestamp_label = QLabel(timestamp_text)
            timestamp_label.setProperty("history_timestamp", True)  # CSS class
            layout.addWidget(timestamp_label)

    def _format_timestamp(self) -> str:
        """
        Format the timestamp text showing created and edited times.

        Returns:
            str: Formatted timestamp text (e.g., "Created: 14:32 (Edited: 14:35)")
        """
        created_at = self.item_data.get("created_at")
        updated_at = self.item_data.get("updated_at")

        if not created_at:
            return ""

        # Format created time
        if isinstance(created_at, datetime):
            created_str = created_at.strftime("%H:%M")
        else:
            created_str = str(created_at)

        result = f"Created: {created_str}"

        # Add edited time if different from created
        if updated_at and updated_at != created_at:
            if isinstance(updated_at, datetime):
                updated_str = updated_at.strftime("%H:%M")
            else:
                updated_str = str(updated_at)
            result += f" (Edited: {updated_str})"

        return result

    def enterEvent(self, event):
        """
        Show action buttons when mouse enters the widget.

        Args:
            event: Enter event
        """
        self._edit_btn.setVisible(True)
        self._delete_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """
        Hide action buttons when mouse leaves the widget.

        Args:
            event: Leave event
        """
        self._edit_btn.setVisible(False)
        self._delete_btn.setVisible(False)
        super().leaveEvent(event)


class HistoryList(QWidget):
    """
    List of history items with add and pagination buttons.

    Displays treatment or product history with load more functionality.

    Signals:
        add_clicked(): Emitted when Add button is clicked
        load_more_clicked(): Emitted when Show More button is clicked
        edit_item(int): Emitted when item edit is clicked (passes item_id)
        delete_item(int): Emitted when item delete is clicked (passes item_id)

    Attributes:
        _title: Title for this history list
        _items: List of loaded item IDs
    """

    # Signals
    add_clicked = pyqtSignal()
    load_more_clicked = pyqtSignal()
    edit_item = pyqtSignal(int)  # Passes item_id
    delete_item = pyqtSignal(int)  # Passes item_id

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

        # Set up the UI
        self._init_ui()

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates layout with title, items list, and action buttons.
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

        add_btn = QPushButton(f"+ Add")
        add_btn.setProperty("class", "primary")
        add_btn.setFixedWidth(80)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.add_clicked.emit)
        title_row.addWidget(add_btn)

        layout.addLayout(title_row)

        # Scrollable items list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        self._items_container = QWidget()
        self._items_layout = QVBoxLayout(self._items_container)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(4)
        self._items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(self._items_container)
        layout.addWidget(scroll_area, stretch=1)

        # Show More button
        self._show_more_btn = QPushButton("Show More")
        self._show_more_btn.setProperty("class", "secondary")
        self._show_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._show_more_btn.clicked.connect(self.load_more_clicked.emit)
        layout.addWidget(self._show_more_btn)

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
        for item_data in items:
            item_id = item_data["id"]

            # Create history item
            history_item = HistoryItem(item_id, item_data)
            history_item.edit_clicked.connect(
                lambda iid=item_id: self.edit_item.emit(iid)
            )
            history_item.delete_clicked.connect(
                lambda iid=item_id: self.delete_item.emit(iid)
            )

            # Add to layout
            self._items_layout.addWidget(history_item)

            # Track loaded item
            self._items.append(item_id)

        # Update Show More button visibility
        self._has_more = len(items) >= self.ITEMS_PER_PAGE
        self._show_more_btn.setVisible(self._has_more)

    def clear_items(self) -> None:
        """
        Remove all items from the list.
        """
        while self._items_layout.count():
            item = self._items_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self._items.clear()


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
        self._treatment_history.delete_item.connect(self._on_delete_treatment)
        grid.addWidget(self._treatment_history, 1, 0)

        # Bottom-right: Product History
        self._product_history = HistoryList("Product History")
        self._product_history.add_clicked.connect(self._on_add_product)
        self._product_history.load_more_clicked.connect(self._on_load_more_products)
        self._product_history.edit_item.connect(self._on_edit_product)
        self._product_history.delete_item.connect(self._on_delete_product)
        grid.addWidget(self._product_history, 1, 1)

        main_layout.addLayout(grid)

    def _create_header(self) -> QWidget:
        """
        Create the header section with client info and action buttons.

        Returns:
            QWidget containing header elements
        """
        header = QWidget()
        header.setFixedHeight(100)
        header.setProperty("detail_header", True)  # CSS class

        layout = QVBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Top row: name and buttons
        top_row = QHBoxLayout()

        self._name_label = QLabel("Client Name")
        self._name_label.setProperty("client_detail_name", True)  # CSS class
        top_row.addWidget(self._name_label)

        self._age_label = QLabel("(Age: --)")
        self._age_label.setProperty("client_age", True)  # CSS class
        top_row.addWidget(self._age_label)

        top_row.addStretch()

        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("class", "secondary")
        edit_btn.setFixedWidth(80)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(self._on_edit_client)
        top_row.addWidget(edit_btn)

        # Back button
        back_btn = QPushButton("Back")
        back_btn.setProperty("class", "secondary")
        back_btn.setFixedWidth(80)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_to_list.emit)
        top_row.addWidget(back_btn)

        layout.addLayout(top_row)

        # Allergies warning (if present)
        self._allergies_label = QLabel()
        self._allergies_label.setProperty("allergies_warning", True)  # CSS class (red)
        self._allergies_label.setVisible(False)
        layout.addWidget(self._allergies_label)

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
        Load and display client details.

        This method will be connected to a controller later.

        Args:
            client_id: Database ID of the client to load
        """
        self._client_id = client_id

        logger.debug(f"Loading client: {client_id}")

        # PLACEHOLDER: Controller method will be called here
        # For now, set placeholder data
        self._client_data = {
            "id": client_id,
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": None,
            "allergies": "",
            "planned_treatment": "",
            "personal_notes": "",
        }

        self._update_ui()

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

        # Update age (calculated from DOB)
        dob = self._client_data.get("date_of_birth")
        if dob and isinstance(dob, date):
            age = self._calculate_age(dob)
            self._age_label.setText(f"(Age: {age})")
        else:
            self._age_label.setText("(Age: --)")

        # Update allergies
        allergies = self._client_data.get("allergies", "").strip()
        if allergies:
            self._allergies_label.setText(f"⚠ Allergies: {allergies}")
            self._allergies_label.setVisible(True)
        else:
            self._allergies_label.setVisible(False)

        # Update planned treatment
        planned = self._client_data.get("planned_treatment", "")
        self._planned_treatment_edit.setPlainText(planned)

        # Update personal notes
        notes = self._client_data.get("personal_notes", "")
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

    def _on_planned_treatment_saved(self, text: str) -> None:
        """
        Handle planned treatment auto-save.

        Args:
            text: Updated planned treatment text
        """
        logger.debug("Saving planned treatment")
        # PLACEHOLDER: Controller method will be called here
        self.client_updated.emit()

    def _on_personal_notes_saved(self, text: str) -> None:
        """
        Handle personal notes auto-save.

        Args:
            text: Updated personal notes text
        """
        logger.debug("Saving personal notes")
        # PLACEHOLDER: Controller method will be called here
        self.client_updated.emit()

    def _on_edit_client(self) -> None:
        """
        Handle edit client button click.

        Opens the edit client dialog (to be implemented).
        """
        logger.debug("Edit client clicked")
        # PLACEHOLDER: Will show EditClientDialog

    def _on_add_treatment(self) -> None:
        """
        Handle add treatment button click.

        Opens the add treatment dialog (to be implemented).
        """
        logger.debug("Add treatment clicked")
        # PLACEHOLDER: Will show AddTreatmentDialog

    def _on_load_more_treatments(self) -> None:
        """
        Handle load more treatments button click.
        """
        logger.debug("Load more treatments clicked")
        # PLACEHOLDER: Controller method will be called here

    def _on_edit_treatment(self, treatment_id: int) -> None:
        """
        Handle edit treatment button click.

        Args:
            treatment_id: Database ID of the treatment to edit
        """
        logger.debug(f"Edit treatment clicked: {treatment_id}")
        # PLACEHOLDER: Will show EditTreatmentDialog

    def _on_delete_treatment(self, treatment_id: int) -> None:
        """
        Handle delete treatment button click.

        Args:
            treatment_id: Database ID of the treatment to delete
        """
        logger.debug(f"Delete treatment clicked: {treatment_id}")
        # PLACEHOLDER: Will show confirmation dialog and delete

    def _on_add_product(self) -> None:
        """
        Handle add product button click.

        Opens the add product dialog (to be implemented).
        """
        logger.debug("Add product clicked")
        # PLACEHOLDER: Will show AddProductRecordDialog

    def _on_load_more_products(self) -> None:
        """
        Handle load more products button click.
        """
        logger.debug("Load more products clicked")
        # PLACEHOLDER: Controller method will be called here

    def _on_edit_product(self, product_id: int) -> None:
        """
        Handle edit product button click.

        Args:
            product_id: Database ID of the product record to edit
        """
        logger.debug(f"Edit product clicked: {product_id}")
        # PLACEHOLDER: Will show EditProductRecordDialog

    def _on_delete_product(self, product_id: int) -> None:
        """
        Handle delete product button click.

        Args:
            product_id: Database ID of the product record to delete
        """
        logger.debug(f"Delete product clicked: {product_id}")
        # PLACEHOLDER: Will show confirmation dialog and delete
