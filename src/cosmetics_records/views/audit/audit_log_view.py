# =============================================================================
# Cosmetics Records - Audit Log View
# =============================================================================
# This module provides the audit history browsing view.
#
# Key Features:
#   - Displays all changes made in the application
#   - Each entry shows header with timestamp
#   - Side-by-side old/new state comparison
#   - Pagination (50 entries per page)
#
# Layout:
#   ┌──────────────────────────────────────────────┐
#   │ Treatment Plan for Jon Doe updated           │
#   │ 2025-11-12 16:25                             │
#   │ ┌─────────────────┬─────────────────────────┐│
#   │ │ Old             │ New                     ││
#   │ │ asdasdasd       │ acute acne, referred... ││
#   │ └─────────────────┴─────────────────────────┘│
#   ├──────────────────────────────────────────────┤
#   │ [< Previous] Page 1 of 10 [Next >]           │
#   └──────────────────────────────────────────────┘
#
# Usage Example:
#   audit_view = AuditLogView()
#   audit_view.refresh()  # Reload audit logs
# =============================================================================

import logging
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from cosmetics_records.database.connection import DatabaseConnection
from cosmetics_records.models.audit import AuditAction, AuditLog
from cosmetics_records.services.audit_service import AuditService
from cosmetics_records.utils.time_utils import format_date_localized

# Configure module logger
logger = logging.getLogger(__name__)


class AuditEntryWidget(QFrame):
    """
    Single audit log entry display.

    Shows a header with description and timestamp, plus side-by-side
    old/new state comparison boxes.

    Attributes:
        audit_log: The AuditLog instance to display
    """

    def __init__(self, audit_log: AuditLog, parent: Optional[QWidget] = None):
        """
        Initialize an audit entry widget.

        Args:
            audit_log: The AuditLog instance to display
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.audit_log = audit_log

        # Set frame properties
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setProperty("audit_entry", True)  # CSS class

        # Set up the UI
        self._init_ui()

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates a layout with header and side-by-side old/new state boxes.
        """
        # Main vertical layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Header: description with timestamp
        header_text = self._build_header_text()
        header_label = QLabel(header_text)
        header_label.setWordWrap(True)
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header_label)

        # Timestamp
        if self.audit_log.created_at:
            timestamp_str = self.audit_log.created_at.strftime("%Y-%m-%d %H:%M")
        else:
            timestamp_str = "Unknown time"

        timestamp_label = QLabel(timestamp_str)
        timestamp_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(timestamp_label)

        # Side-by-side old/new state boxes (if applicable)
        if self.audit_log.action == AuditAction.UPDATE:
            # Show old and new values side by side
            comparison_layout = QHBoxLayout()
            comparison_layout.setSpacing(8)

            # Old value box
            old_box = self._create_state_box("Old", self.audit_log.old_value or "(empty)")
            comparison_layout.addWidget(old_box, stretch=1)

            # New value box
            new_box = self._create_state_box("New", self.audit_log.new_value or "(empty)")
            comparison_layout.addWidget(new_box, stretch=1)

            layout.addLayout(comparison_layout)

        elif self.audit_log.action == AuditAction.CREATE:
            # Just show the new value
            if self.audit_log.new_value:
                value_box = self._create_state_box("Created", self.audit_log.new_value)
                layout.addWidget(value_box)

        elif self.audit_log.action == AuditAction.DELETE:
            # Just show the old (deleted) value
            if self.audit_log.old_value:
                value_box = self._create_state_box("Deleted", self.audit_log.old_value)
                layout.addWidget(value_box)

    def _build_header_text(self) -> str:
        """
        Build the header text describing the change.

        Returns:
            A formatted header string like "Treatment Plan for Jon Doe updated"
        """
        # Map table names to human-readable names
        table_names = {
            "clients": "Client",
            "treatment_records": "Treatment record",
            "product_records": "Product sale record",
            "inventory_items": "Inventory item",
        }

        # Map actions to verbs
        action_verbs = {
            AuditAction.CREATE: "created",
            AuditAction.UPDATE: "updated",
            AuditAction.DELETE: "deleted",
        }

        table_name = table_names.get(self.audit_log.table_name, self.audit_log.table_name)
        action_verb = action_verbs.get(self.audit_log.action, "changed")

        # Include field name for updates
        if self.audit_log.action == AuditAction.UPDATE and self.audit_log.field_name:
            return f"{table_name} {self.audit_log.field_name} {action_verb}"
        else:
            return f"{table_name} {action_verb}"

    def _create_state_box(self, label: str, content: str) -> QFrame:
        """
        Create a labeled box showing state content.

        Args:
            label: Label for the box (e.g., "Old", "New", "Deleted")
            content: The content to display

        Returns:
            QFrame containing the labeled state box
        """
        box = QFrame()
        box.setFrameShape(QFrame.Shape.StyledPanel)
        box.setStyleSheet(
            "QFrame { background-color: rgba(100, 100, 100, 0.1); "
            "border: 1px solid rgba(100, 100, 100, 0.3); border-radius: 4px; }"
        )

        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(8, 6, 8, 6)
        box_layout.setSpacing(4)

        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-weight: bold; font-size: 11px; color: gray;")
        box_layout.addWidget(label_widget)

        # Content (allow wrapping for long text)
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("font-size: 13px;")
        box_layout.addWidget(content_label)

        return box


class AuditLogView(QWidget):
    """
    Audit history browsing view.

    This view provides a paginated list of audit log entries showing all
    changes made in the application with old/new state comparison.

    Attributes:
        _current_page: Current page number (1-indexed)
        _total_pages: Total number of pages
        _entries_per_page: Number of entries per page (50)
    """

    # Pagination settings
    ENTRIES_PER_PAGE = 50

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the audit log view.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # State tracking
        self._current_page: int = 1
        self._total_pages: int = 1

        # Set up the UI
        self._init_ui()

        # Initial load
        self.refresh()

        logger.debug("AuditLogView initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates the layout with title and audit entries list.
        """
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(60)
        title_bar.setProperty("top_bar", True)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 10, 16, 10)

        title_label = QLabel("Audit Log")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self.refresh)
        title_layout.addWidget(refresh_btn)

        main_layout.addWidget(title_bar)

        # Scrollable audit entries list
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Container for audit entries
        self._entries_container = QWidget()
        self._entries_layout = QVBoxLayout(self._entries_container)
        self._entries_layout.setContentsMargins(8, 8, 8, 8)
        self._entries_layout.setSpacing(8)
        self._entries_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll_area.setWidget(self._entries_container)
        main_layout.addWidget(self._scroll_area, stretch=1)

        # Bottom bar: pagination controls
        bottom_bar = self._create_bottom_bar()
        main_layout.addWidget(bottom_bar)

    def _create_bottom_bar(self) -> QWidget:
        """
        Create the bottom bar with pagination controls.

        Returns:
            QWidget containing pagination controls
        """
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(60)
        bottom_bar.setProperty("bottom_bar", True)

        layout = QHBoxLayout(bottom_bar)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # Previous button
        self._prev_btn = QPushButton("< Previous")
        self._prev_btn.setFixedWidth(100)
        self._prev_btn.clicked.connect(self._on_previous_page)
        layout.addWidget(self._prev_btn)

        # Page indicator
        self._page_label = QLabel("Page 1 of 1")
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setMinimumWidth(120)
        layout.addWidget(self._page_label)

        # Next button
        self._next_btn = QPushButton("Next >")
        self._next_btn.setFixedWidth(100)
        self._next_btn.clicked.connect(self._on_next_page)
        layout.addWidget(self._next_btn)

        layout.addStretch()

        # Jump to page
        jump_label = QLabel("Go to page:")
        layout.addWidget(jump_label)

        self._jump_spin = QSpinBox()
        self._jump_spin.setMinimum(1)
        self._jump_spin.setMaximum(1)
        self._jump_spin.setFixedWidth(80)
        self._jump_spin.valueChanged.connect(self._on_jump_to_page)
        layout.addWidget(self._jump_spin)

        return bottom_bar

    def _on_previous_page(self) -> None:
        """Navigate to the previous page."""
        if self._current_page > 1:
            self._current_page -= 1
            self._load_audit_logs()

    def _on_next_page(self) -> None:
        """Navigate to the next page."""
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._load_audit_logs()

    def _on_jump_to_page(self, page: int) -> None:
        """Jump to a specific page."""
        if 1 <= page <= self._total_pages and page != self._current_page:
            self._current_page = page
            self._load_audit_logs()

    def _load_audit_logs(self) -> None:
        """
        Load audit logs from database with pagination.
        """
        try:
            # Calculate offset for pagination
            offset = (self._current_page - 1) * self.ENTRIES_PER_PAGE

            # Load audit logs from database
            with DatabaseConnection() as db:
                audit_service = AuditService(db)

                # Get total count for pagination
                total_count = audit_service.get_audit_log_count()

                # Calculate total pages
                self._total_pages = max(
                    1,
                    (total_count + self.ENTRIES_PER_PAGE - 1) // self.ENTRIES_PER_PAGE,
                )

                # Ensure current page is within bounds
                if self._current_page > self._total_pages:
                    self._current_page = self._total_pages

                # Recalculate offset
                offset = (self._current_page - 1) * self.ENTRIES_PER_PAGE

                # Get audit logs for current page
                audit_logs = audit_service.get_audit_logs(
                    limit=self.ENTRIES_PER_PAGE,
                    offset=offset,
                )

            # Update UI
            self._display_audit_logs(audit_logs)
            self._update_pagination_controls()

            logger.debug(
                f"Loaded {len(audit_logs)} audit logs "
                f"(page {self._current_page} of {self._total_pages})"
            )

        except Exception as e:
            logger.error(f"Failed to load audit logs: {e}")
            self._clear_entries()
            error_label = QLabel(f"Error loading audit logs: {str(e)}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._entries_layout.addWidget(error_label)

    def _display_audit_logs(self, audit_logs: List[AuditLog]) -> None:
        """Display audit logs in the UI."""
        # Clear existing entries
        self._clear_entries()

        # If no logs, show message
        if not audit_logs:
            empty_label = QLabel("No audit logs found")
            empty_label.setStyleSheet("color: gray; padding: 20px; font-style: italic;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._entries_layout.addWidget(empty_label)
            return

        # Create widget for each audit log
        for audit_log in audit_logs:
            entry_widget = AuditEntryWidget(audit_log)
            self._entries_layout.addWidget(entry_widget)

    def _clear_entries(self) -> None:
        """Remove all audit entry widgets from the UI."""
        while self._entries_layout.count():
            item = self._entries_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _update_pagination_controls(self) -> None:
        """Update pagination controls based on current state."""
        # Update page label
        self._page_label.setText(f"Page {self._current_page} of {self._total_pages}")

        # Update button states
        self._prev_btn.setEnabled(self._current_page > 1)
        self._next_btn.setEnabled(self._current_page < self._total_pages)

        # Update jump spinbox
        self._jump_spin.setMaximum(self._total_pages)
        self._jump_spin.blockSignals(True)
        self._jump_spin.setValue(self._current_page)
        self._jump_spin.blockSignals(False)

    def refresh(self) -> None:
        """Refresh the audit log view."""
        logger.debug("Refreshing audit log view")
        self._load_audit_logs()
