# =============================================================================
# Cosmetics Records - Audit Log View
# =============================================================================
# This module provides the audit history browsing view.
#
# Key Features:
#   - Filterable audit log list (by table and action)
#   - Pagination (50 entries per page)
#   - Color-coded action icons (green=CREATE, blue=UPDATE, red=DELETE)
#   - Human-readable descriptions
#   - Relative timestamps ("2 hours ago", "Yesterday at 14:32")
#   - UI location badges showing where changes were made
#   - Page navigation with jump-to-page
#
# Design Philosophy:
#   - Clarity: Visual icons and colors make scanning easy
#   - Context: Descriptions include what changed and where
#   - Performance: Pagination prevents loading entire audit history
#   - Navigation: Jump to specific pages quickly
#
# Layout:
#   ┌──────────────────────────────────────────────┐
#   │ Table: [All ▼] Action: [All ▼] [Refresh]    │
#   ├──────────────────────────────────────────────┤
#   │ ✓ New client created                         │
#   │   2 hours ago | ClientListView               │
#   ├──────────────────────────────────────────────┤
#   │ ✎ Client updated: email changed...           │
#   │   Yesterday at 14:32 | ClientEditView        │
#   ├──────────────────────────────────────────────┤
#   │ ✗ Treatment record deleted                   │
#   │   Jan 15, 2024 10:30 | TreatmentHistoryView  │
#   ├──────────────────────────────────────────────┤
#   │ [< Previous] Page 1 of 10 [Next >] Go to: [_]│
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
    QComboBox,
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
from cosmetics_records.utils.time_utils import format_relative_time

# Configure module logger
logger = logging.getLogger(__name__)


class AuditEntryWidget(QFrame):
    """
    Single audit log entry display.

    Shows an icon, description, timestamp, and UI location for one audit entry.

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

        Creates a layout with icon, description, timestamp, and location.
        """
        # Main horizontal layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Icon based on action type
        # WHY visual icons: Quick identification of action type
        icon_label = QLabel()
        icon_label.setFixedWidth(24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.audit_log.action == AuditAction.CREATE:
            # Green checkmark for CREATE
            icon_label.setText("✓")
            icon_label.setStyleSheet(
                "color: #4CAF50; font-size: 20px; font-weight: bold;"
            )
        elif self.audit_log.action == AuditAction.UPDATE:
            # Blue pencil for UPDATE
            icon_label.setText("✎")
            icon_label.setStyleSheet(
                "color: #2196F3; font-size: 20px; font-weight: bold;"
            )
        else:  # DELETE
            # Red X for DELETE
            icon_label.setText("✗")
            icon_label.setStyleSheet(
                "color: #F44336; font-size: 20px; font-weight: bold;"
            )

        layout.addWidget(icon_label)

        # Content column (description, timestamp, location)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        # Description (human-readable)
        description = self.audit_log.get_description()
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 14px;")
        content_layout.addWidget(desc_label)

        # Metadata row (timestamp and UI location)
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(8)

        # Timestamp (relative format)
        if self.audit_log.created_at:
            timestamp_str = format_relative_time(self.audit_log.created_at)
        else:
            timestamp_str = "Unknown time"

        timestamp_label = QLabel(timestamp_str)
        timestamp_label.setProperty("class", "secondary")
        timestamp_label.setStyleSheet("color: gray; font-size: 12px;")
        meta_layout.addWidget(timestamp_label)

        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("color: gray; font-size: 12px;")
        meta_layout.addWidget(separator)

        # UI location badge
        location_label = QLabel(self.audit_log.ui_location)
        location_label.setProperty("class", "badge")
        location_label.setStyleSheet(
            "color: #2196F3; background-color: rgba(33, 150, 243, 0.1); "
            "padding: 2px 8px; border-radius: 4px; font-size: 11px;"
        )
        meta_layout.addWidget(location_label)

        meta_layout.addStretch()

        content_layout.addLayout(meta_layout)

        layout.addLayout(content_layout, stretch=1)


class AuditLogView(QWidget):
    """
    Audit history browsing view.

    This view provides a filterable, paginated list of audit log entries.
    Users can filter by table and action type, navigate between pages,
    and jump to specific pages.

    Attributes:
        _current_table_filter: Current table filter selection
        _current_action_filter: Current action filter selection
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
        self._current_table_filter: Optional[str] = None  # None = "All"
        self._current_action_filter: Optional[str] = None  # None = "All"
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

        Creates the layout with filters, audit entries, and pagination.
        """
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar: filters and refresh button
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)

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
        self._entries_layout.setContentsMargins(0, 0, 0, 0)
        self._entries_layout.setSpacing(0)
        self._entries_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll_area.setWidget(self._entries_container)
        main_layout.addWidget(self._scroll_area, stretch=1)

        # Bottom bar: pagination controls
        bottom_bar = self._create_bottom_bar()
        main_layout.addWidget(bottom_bar)

    def _create_top_bar(self) -> QWidget:
        """
        Create the top bar with filters and refresh button.

        Returns:
            QWidget containing filter controls
        """
        top_bar = QWidget()
        top_bar.setFixedHeight(60)
        top_bar.setProperty("top_bar", True)  # CSS class

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # Table filter
        table_label = QLabel("Table:")
        layout.addWidget(table_label)

        self._table_filter = QComboBox()
        self._table_filter.addItems(
            [
                "All",
                "clients",
                "treatment_records",
                "product_records",
                "inventory_items",
            ]
        )
        self._table_filter.currentTextChanged.connect(self._on_filter_changed)
        self._table_filter.setFixedWidth(180)
        layout.addWidget(self._table_filter)

        # Action filter
        action_label = QLabel("Action:")
        layout.addWidget(action_label)

        self._action_filter = QComboBox()
        self._action_filter.addItems(["All", "CREATE", "UPDATE", "DELETE"])
        self._action_filter.currentTextChanged.connect(self._on_filter_changed)
        self._action_filter.setFixedWidth(120)
        layout.addWidget(self._action_filter)

        layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)

        return top_bar

    def _create_bottom_bar(self) -> QWidget:
        """
        Create the bottom bar with pagination controls.

        Returns:
            QWidget containing pagination controls
        """
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(60)
        bottom_bar.setProperty("bottom_bar", True)  # CSS class

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

    def _on_filter_changed(self) -> None:
        """
        Handle filter selection change.

        Resets to first page and reloads audit logs with new filters.
        """
        # Get selected filters
        table_filter = self._table_filter.currentText()
        action_filter = self._action_filter.currentText()

        # Convert "All" to None for database query
        self._current_table_filter = None if table_filter == "All" else table_filter
        self._current_action_filter = None if action_filter == "All" else action_filter

        logger.debug(
            f"Filters changed: table={self._current_table_filter}, "
            f"action={self._current_action_filter}"
        )

        # Reset to first page and reload
        self._current_page = 1
        self._load_audit_logs()

    def _on_previous_page(self) -> None:
        """
        Handle previous page button click.

        Loads the previous page of audit logs.
        """
        if self._current_page > 1:
            self._current_page -= 1
            self._load_audit_logs()
            logger.debug(f"Navigated to page {self._current_page}")

    def _on_next_page(self) -> None:
        """
        Handle next page button click.

        Loads the next page of audit logs.
        """
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._load_audit_logs()
            logger.debug(f"Navigated to page {self._current_page}")

    def _on_jump_to_page(self, page: int) -> None:
        """
        Handle jump to page spinbox change.

        Loads the specified page of audit logs.

        Args:
            page: Page number to jump to
        """
        if 1 <= page <= self._total_pages and page != self._current_page:
            self._current_page = page
            self._load_audit_logs()
            logger.debug(f"Jumped to page {self._current_page}")

    def _load_audit_logs(self) -> None:
        """
        Load audit logs from database with current filters and pagination.

        Updates the UI with loaded entries and pagination state.
        """
        try:
            logger.debug(
                f"Loading audit logs: page={self._current_page}, "
                f"table={self._current_table_filter}, "
                f"action={self._current_action_filter}"
            )

            # Calculate offset for pagination
            offset = (self._current_page - 1) * self.ENTRIES_PER_PAGE

            # Load audit logs from database
            with DatabaseConnection() as db:
                audit_service = AuditService(db)

                # Get total count for pagination
                total_count = audit_service.get_audit_log_count(
                    table_filter=self._current_table_filter,
                    action_filter=self._current_action_filter,
                )

                # Calculate total pages
                # WHY max(1, ...): Always show at least 1 page even if empty
                self._total_pages = max(
                    1,
                    (total_count + self.ENTRIES_PER_PAGE - 1) // self.ENTRIES_PER_PAGE,
                )

                # Ensure current page is within bounds
                # WHY: If filters change and reduce total pages, we might be on invalid page
                if self._current_page > self._total_pages:
                    self._current_page = self._total_pages

                # Recalculate offset after potential page adjustment
                offset = (self._current_page - 1) * self.ENTRIES_PER_PAGE

                # Get audit logs for current page
                audit_logs = audit_service.get_audit_logs(
                    limit=self.ENTRIES_PER_PAGE,
                    offset=offset,
                    table_filter=self._current_table_filter,
                    action_filter=self._current_action_filter,
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
            # Clear entries on error
            self._clear_entries()
            # Show error in UI
            error_label = QLabel(f"Error loading audit logs: {str(e)}")
            error_label.setProperty("class", "error")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._entries_layout.addWidget(error_label)

    def _display_audit_logs(self, audit_logs: List[AuditLog]) -> None:
        """
        Display audit logs in the UI.

        Clears existing entries and creates new widgets for each log.

        Args:
            audit_logs: List of AuditLog instances to display
        """
        # Clear existing entries
        self._clear_entries()

        # If no logs, show message
        if not audit_logs:
            empty_label = QLabel("No audit logs found")
            empty_label.setProperty("class", "secondary")
            empty_label.setStyleSheet("color: gray; padding: 20px; font-style: italic;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._entries_layout.addWidget(empty_label)
            return

        # Create widget for each audit log
        for audit_log in audit_logs:
            entry_widget = AuditEntryWidget(audit_log)
            self._entries_layout.addWidget(entry_widget)

    def _clear_entries(self) -> None:
        """
        Remove all audit entry widgets from the UI.
        """
        # Remove all widgets from layout
        while self._entries_layout.count():
            item = self._entries_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _update_pagination_controls(self) -> None:
        """
        Update pagination controls based on current state.

        Updates button states, page label, and jump spinbox.
        """
        # Update page label
        self._page_label.setText(f"Page {self._current_page} of {self._total_pages}")

        # Update button states
        self._prev_btn.setEnabled(self._current_page > 1)
        self._next_btn.setEnabled(self._current_page < self._total_pages)

        # Update jump spinbox
        self._jump_spin.setMaximum(self._total_pages)
        # WHY blockSignals: Prevent triggering valueChanged during programmatic update
        self._jump_spin.blockSignals(True)
        self._jump_spin.setValue(self._current_page)
        self._jump_spin.blockSignals(False)

    def refresh(self) -> None:
        """
        Refresh the audit log view.

        Reloads audit logs from the database with current filters and pagination.
        This should be called after database changes.
        """
        logger.debug("Refreshing audit log view")
        self._load_audit_logs()
