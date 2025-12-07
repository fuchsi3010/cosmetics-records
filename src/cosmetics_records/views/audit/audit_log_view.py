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
from PyQt6.QtGui import QShowEvent
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
from cosmetics_records.utils.localization import _

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

    def __init__(
        self,
        audit_log: AuditLog,
        client_name: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize an audit entry widget.

        Args:
            audit_log: The AuditLog instance to display
            client_name: Optional client name for client-related entries
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.audit_log = audit_log
        self.client_name = client_name

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

        # Header row: timestamp on left, description on right
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Timestamp (left side)
        if self.audit_log.created_at:
            timestamp_str = self.audit_log.created_at.strftime("%Y-%m-%d %H:%M")
        else:
            timestamp_str = _("Unknown time")

        timestamp_label = QLabel(timestamp_str)
        timestamp_label.setStyleSheet("color: gray; font-size: 12px;")
        header_layout.addWidget(timestamp_label)

        # Description (right side)
        header_text = self._build_header_text()
        header_label = QLabel(header_text)
        header_label.setWordWrap(True)
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label, stretch=1)

        layout.addLayout(header_layout)

        # Side-by-side old/new state boxes (if applicable)
        if self.audit_log.action == AuditAction.UPDATE:
            # Show old and new values side by side
            comparison_layout = QHBoxLayout()
            comparison_layout.setSpacing(8)

            # Old value box
            old_box = self._create_state_box(
                _("Old"), self.audit_log.old_value or _("(empty)")
            )
            comparison_layout.addWidget(old_box, stretch=1)

            # New value box
            new_box = self._create_state_box(
                _("New"), self.audit_log.new_value or _("(empty)")
            )
            comparison_layout.addWidget(new_box, stretch=1)

            layout.addLayout(comparison_layout)

        elif self.audit_log.action == AuditAction.CREATE:
            # Just show the new value
            if self.audit_log.new_value:
                value_box = self._create_state_box(
                    _("Created"), self.audit_log.new_value
                )
                layout.addWidget(value_box)

        elif self.audit_log.action == AuditAction.DELETE:
            # Just show the old (deleted) value
            if self.audit_log.old_value:
                value_box = self._create_state_box(
                    _("Deleted"), self.audit_log.old_value
                )
                layout.addWidget(value_box)

    def _build_header_text(self) -> str:
        """
        Build the header text describing the change.

        Returns:
            A formatted header string like "Treatment record for Jon Doe updated"
        """
        # Map table names to human-readable names
        table_names = {
            "clients": _("Client"),
            "treatment_records": _("Treatment record"),
            "product_records": _("Product sale record"),
            "inventory": _("Inventory item"),
        }

        # Map actions to verbs
        action_verbs = {
            AuditAction.CREATE: _("created"),
            AuditAction.UPDATE: _("updated"),
            AuditAction.DELETE: _("deleted"),
        }

        table_name = table_names.get(
            self.audit_log.table_name, self.audit_log.table_name
        )
        action_verb = action_verbs.get(self.audit_log.action, _("changed"))

        # Build base description
        if self.audit_log.action == AuditAction.UPDATE and self.audit_log.field_name:
            description = f"{table_name} {self.audit_log.field_name} {action_verb}"
        else:
            description = f"{table_name} {action_verb}"

        # Add client name if available (for treatment/product records)
        if self.client_name:
            return f"{description} ({self.client_name})"

        return description

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
        box.setFrameShape(QFrame.Shape.NoFrame)
        # Simplified styling - transparent background, no border
        box.setStyleSheet("QFrame { background-color: transparent; border: none; }")

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

        # Title row (no background, just title and refresh button)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(16, 16, 16, 8)

        title_label = QLabel(_("Audit Log"))
        title_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; background: transparent;"
        )
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton(_("Refresh"))
        refresh_btn.setMinimumWidth(100)
        refresh_btn.clicked.connect(self.refresh)
        title_layout.addWidget(refresh_btn)

        main_layout.addLayout(title_layout)

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
        self._prev_btn = QPushButton(_("< Previous"))
        self._prev_btn.setMinimumWidth(100)
        self._prev_btn.clicked.connect(self._on_previous_page)
        layout.addWidget(self._prev_btn)

        # Page indicator
        self._page_label = QLabel(_("Page 1 of 1"))
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setMinimumWidth(120)
        layout.addWidget(self._page_label)

        # Next button
        self._next_btn = QPushButton(_("Next >"))
        self._next_btn.setMinimumWidth(100)
        self._next_btn.clicked.connect(self._on_next_page)
        layout.addWidget(self._next_btn)

        layout.addStretch()

        # Jump to page
        jump_label = QLabel(_("Go to page:"))
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
            error_label = QLabel(_("Error loading audit logs: %s") % str(e))
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._entries_layout.addWidget(error_label)

    def _display_audit_logs(self, audit_logs: List[AuditLog]) -> None:
        """Display audit logs in the UI."""
        # Clear existing entries
        self._clear_entries()

        # If no logs, show message
        if not audit_logs:
            empty_label = QLabel(_("No audit logs found"))
            empty_label.setStyleSheet("color: gray; padding: 20px; font-style: italic;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._entries_layout.addWidget(empty_label)
            return

        # Fetch client names for client-related audit logs
        client_names = self._fetch_client_names(audit_logs)

        # Create widget for each audit log
        for audit_log in audit_logs:
            # Get client name if available
            client_name = client_names.get((audit_log.table_name, audit_log.record_id))
            entry_widget = AuditEntryWidget(audit_log, client_name=client_name)
            self._entries_layout.addWidget(entry_widget)

    def _fetch_client_names(
        self, audit_logs: List[AuditLog]
    ) -> dict[tuple[str, int], str]:
        """
        Fetch client names for audit log entries using stored client_id.

        Args:
            audit_logs: List of audit logs to fetch client names for

        Returns:
            Dictionary mapping (table_name, record_id) to client full name
        """
        client_names: dict[tuple[str, int], str] = {}

        # Collect unique client IDs from audit logs
        client_ids = set()
        log_to_client: dict[tuple[str, int], int] = {}

        for log in audit_logs:
            if log.client_id is not None:
                client_ids.add(log.client_id)
                log_to_client[(log.table_name, log.record_id)] = log.client_id

        if not client_ids:
            return client_names

        try:
            with DatabaseConnection() as db:
                # Fetch client names for all referenced clients
                placeholders = ",".join("?" * len(client_ids))
                db.execute(
                    f"""
                    SELECT id,
                           first_name || ' ' || last_name as client_name
                    FROM clients
                    WHERE id IN ({placeholders})
                    """,
                    tuple(client_ids),
                )

                # Build client_id -> name mapping
                id_to_name: dict[int, str] = {}
                for row in db.fetchall():
                    id_to_name[row["id"]] = row["client_name"]

                # Map (table_name, record_id) to client name
                for key, client_id in log_to_client.items():
                    if client_id in id_to_name:
                        client_names[key] = id_to_name[client_id]

        except Exception as e:
            logger.error(f"Failed to fetch client names for audit logs: {e}")

        return client_names

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
        self._page_label.setText(
            _("Page %d of %d") % (self._current_page, self._total_pages)
        )

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

    def showEvent(self, event: Optional[QShowEvent]) -> None:
        """
        Handle show events to refresh audit logs.

        This ensures the view always shows the latest data when navigated to.

        Args:
            event: Show event (can be None)
        """
        super().showEvent(event)
        # Refresh to show latest audit logs when view becomes visible
        self.refresh()
        logger.debug("AuditLogView shown, refreshed data")
