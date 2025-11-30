# =============================================================================
# Cosmetics Records - Import Dialog
# =============================================================================
# This module provides the ImportDialog for importing data from CSV files.
# The dialog guides users through the import process: file selection,
# validation, preview, and import.
#
# Key Features:
#   - File selection for 4 CSV types (clients required, others optional)
#   - Browse buttons with file dialogs
#   - Validation with detailed error display
#   - Preview of data to be imported
#   - Import with progress indication
#
# UI Layout:
#   ┌─────────────────────────────────────────────────┐
#   │ Import Data from CSV                        [X] │
#   ├─────────────────────────────────────────────────┤
#   │                                                 │
#   │ Clients (required):  [path display    ] [Browse]│
#   │ Treatments:          [path display    ] [Browse]│
#   │ Product Sales:       [path display    ] [Browse]│
#   │ Inventory:           [path display    ] [Browse]│
#   │                                                 │
#   │ ─────────────────────────────────────────────── │
#   │ Status/Preview:                                 │
#   │ • Ready to validate                             │
#   │ OR                                              │
#   │ • 150 clients, 423 treatments, ...              │
#   │ OR                                              │
#   │ • Error list (scrollable)                       │
#   │                                                 │
#   │              [Cancel]  [Validate]  [Import]     │
#   └─────────────────────────────────────────────────┘
#
# Usage Example:
#   dialog = ImportDialog(parent=main_window)
#   if dialog.exec() == QDialog.DialogCode.Accepted:
#       # Import was successful
#       refresh_data()
# =============================================================================

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from cosmetics_records.utils.localization import _
from cosmetics_records.services.import_service import ImportService
from .base_dialog import BaseDialog

# Configure module logger
logger = logging.getLogger(__name__)


class ImportDialog(BaseDialog):
    """
    Dialog for importing data from CSV files.

    This dialog guides users through the import process:
    1. Select CSV files (clients required, others optional)
    2. Validate files (check format and data integrity)
    3. Preview what will be imported
    4. Perform the import

    Attributes:
        _import_service: Service for validation and import
        _clients_path: Selected clients CSV path
        _treatments_path: Selected treatments CSV path
        _products_path: Selected products CSV path
        _inventory_path: Selected inventory CSV path
        _validated: Whether validation has passed
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the import dialog.

        Args:
            parent: Optional parent widget
        """
        # Initialize state before calling super().__init__
        # which will call _create_content()
        self._import_service = ImportService()
        self._clients_path: Optional[str] = None
        self._treatments_path: Optional[str] = None
        self._products_path: Optional[str] = None
        self._inventory_path: Optional[str] = None
        self._validated: bool = False

        # Call base class constructor (larger size for this dialog)
        super().__init__(
            title=_("Import Data from CSV"),
            parent=parent,
            width=600,
            height=580,
        )

        logger.debug("ImportDialog initialized")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Args:
            layout: Layout to add content to
        """
        # File selection section
        self._create_file_selection(layout)

        # Horizontal line separator
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #444444;")
        layout.addWidget(separator)

        # Status/Preview section
        self._create_status_section(layout)

        # Button row
        self._create_button_row(layout)

    def _create_file_selection(self, layout: QVBoxLayout) -> None:
        """
        Create the file selection section.

        Creates four rows for selecting CSV files:
        - Clients (required)
        - Treatments (optional)
        - Products (optional)
        - Inventory (optional)

        Args:
            layout: Parent layout
        """
        # Instruction label
        instruction = QLabel(_("Select CSV files to import:"))
        instruction.setProperty("dialog_label", True)
        layout.addWidget(instruction)

        # Clients row (required)
        clients_row, self._clients_input = self._create_file_row(
            _("Clients (required):"), self._browse_clients
        )
        layout.addLayout(clients_row)

        # Treatments row
        treatments_row, self._treatments_input = self._create_file_row(
            _("Treatments:"), self._browse_treatments
        )
        layout.addLayout(treatments_row)

        # Product Sales row
        products_row, self._products_input = self._create_file_row(
            _("Product Sales:"), self._browse_products
        )
        layout.addLayout(products_row)

        # Inventory row
        inventory_row, self._inventory_input = self._create_file_row(
            _("Inventory:"), self._browse_inventory
        )
        layout.addLayout(inventory_row)

    def _create_file_row(self, label_text: str, browse_callback) -> tuple:
        """
        Create a single file selection row.

        Args:
            label_text: Label for the row
            browse_callback: Function to call when Browse is clicked

        Returns:
            Tuple of (QHBoxLayout, QLineEdit) for the row
        """
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)

        # Label (fixed width for alignment)
        label = QLabel(label_text)
        label.setFixedWidth(140)
        row_layout.addWidget(label)

        # Path input (read-only display)
        path_input = QLineEdit()
        path_input.setReadOnly(True)
        path_input.setPlaceholderText(_("No file selected"))
        row_layout.addWidget(path_input, stretch=1)

        # Browse button
        browse_btn = QPushButton(_("Browse"))
        browse_btn.setMinimumWidth(80)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(browse_callback)
        row_layout.addWidget(browse_btn)

        return row_layout, path_input

    def _create_status_section(self, layout: QVBoxLayout) -> None:
        """
        Create the status/preview section.

        This section shows:
        - Initial instruction to validate
        - Validation errors (scrollable)
        - Preview counts after successful validation

        Args:
            layout: Parent layout
        """
        # Status label
        status_label = QLabel(_("Status:"))
        status_label.setProperty("dialog_label", True)
        layout.addWidget(status_label)

        # Scrollable area for status/errors
        self._status_scroll = QScrollArea()
        self._status_scroll.setWidgetResizable(True)
        self._status_scroll.setFixedHeight(150)
        self._status_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Container for status content
        self._status_container = QWidget()
        self._status_layout = QVBoxLayout(self._status_container)
        self._status_layout.setContentsMargins(8, 8, 8, 8)
        self._status_layout.setSpacing(4)
        self._status_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._status_scroll.setWidget(self._status_container)
        layout.addWidget(self._status_scroll)

        # Initial status message
        self._update_status_initial()

    def _create_button_row(self, layout: QVBoxLayout) -> None:
        """
        Create the button row at the bottom.

        Buttons: Cancel, Validate, Import

        Args:
            layout: Parent layout
        """
        # Add stretch to push buttons to bottom
        layout.addStretch()

        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        # Spacer
        button_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton(_("Cancel"))
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        # Validate button
        self._validate_btn = QPushButton(_("Validate"))
        self._validate_btn.setMinimumWidth(100)
        self._validate_btn.clicked.connect(self._on_validate_clicked)
        button_layout.addWidget(self._validate_btn)

        # Import button (disabled until validation passes)
        self._import_btn = QPushButton(_("Import"))
        self._import_btn.setProperty("class", "primary")
        self._import_btn.setMinimumWidth(100)
        self._import_btn.setEnabled(False)
        self._import_btn.clicked.connect(self._on_import_clicked)
        button_layout.addWidget(self._import_btn)

        layout.addLayout(button_layout)

    # =========================================================================
    # File Browse Handlers
    # =========================================================================

    def _browse_clients(self) -> None:
        """Open file dialog for clients CSV."""
        path = self._open_file_dialog(_("Select Clients CSV"))
        if path:
            self._clients_path = path
            self._clients_input.setText(path)
            self._reset_validation()

    def _browse_treatments(self) -> None:
        """Open file dialog for treatments CSV."""
        path = self._open_file_dialog(_("Select Treatments CSV"))
        if path:
            self._treatments_path = path
            self._treatments_input.setText(path)
            self._reset_validation()

    def _browse_products(self) -> None:
        """Open file dialog for product_sales CSV."""
        path = self._open_file_dialog(_("Select Product Sales CSV"))
        if path:
            self._products_path = path
            self._products_input.setText(path)
            self._reset_validation()

    def _browse_inventory(self) -> None:
        """Open file dialog for inventory CSV."""
        path = self._open_file_dialog(_("Select Inventory CSV"))
        if path:
            self._inventory_path = path
            self._inventory_input.setText(path)
            self._reset_validation()

    def _open_file_dialog(self, title: str) -> Optional[str]:
        """
        Open a file dialog for CSV file selection.

        Args:
            title: Dialog title

        Returns:
            Selected file path, or None if cancelled
        """
        path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        return path if path else None

    def _reset_validation(self) -> None:
        """Reset validation state when files change."""
        self._validated = False
        self._import_btn.setEnabled(False)
        self._update_status_initial()

    # =========================================================================
    # Validation and Import
    # =========================================================================

    def _on_validate_clicked(self) -> None:
        """Handle Validate button click."""
        # Check that clients file is selected
        if not self._clients_path:
            self._update_status_error(
                [_("Please select a clients CSV file (required)")]
            )
            return

        logger.info("Starting validation...")

        # Run validation
        errors = self._import_service.validate_files(
            clients_path=self._clients_path,
            treatments_path=self._treatments_path,
            products_path=self._products_path,
            inventory_path=self._inventory_path,
        )

        if errors:
            # Show errors
            error_messages = [str(e) for e in errors]
            self._update_status_error(error_messages)
            self._validated = False
            self._import_btn.setEnabled(False)
            logger.info(f"Validation failed with {len(errors)} errors")
        else:
            # Show preview
            preview = self._import_service.get_preview()
            self._update_status_preview(preview)
            self._validated = True
            self._import_btn.setEnabled(True)
            logger.info("Validation passed")

    def _on_import_clicked(self) -> None:
        """Handle Import button click."""
        if not self._validated:
            return

        logger.info("Starting import...")

        # Disable buttons during import
        self._import_btn.setEnabled(False)
        self._validate_btn.setEnabled(False)

        # Perform import
        result = self._import_service.import_data()

        if result.success:
            # Show success message
            self._update_status_success(result)
            logger.info("Import completed successfully")

            # Accept dialog (closes it)
            self.accept()
        else:
            # Show error
            self._update_status_error([result.error_message or _("Import failed")])
            self._validate_btn.setEnabled(True)
            logger.error(f"Import failed: {result.error_message}")

    # =========================================================================
    # Status Display Updates
    # =========================================================================

    def _clear_status(self) -> None:
        """Clear all status messages."""
        # Remove all widgets from status layout
        while self._status_layout.count():
            item = self._status_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _update_status_initial(self) -> None:
        """Show initial status message."""
        self._clear_status()

        label = QLabel(_("Select files and click 'Validate' to check them."))
        label.setWordWrap(True)
        label.setStyleSheet("color: #888888;")
        self._status_layout.addWidget(label)

    def _update_status_error(self, errors: list) -> None:
        """
        Show validation errors.

        Args:
            errors: List of error messages
        """
        self._clear_status()

        # Error count header
        header = QLabel(
            _("Validation failed ({count} errors):").format(count=len(errors))
        )
        header.setStyleSheet("color: #ff6666; font-weight: bold;")
        self._status_layout.addWidget(header)

        # Error list
        for error in errors:
            error_label = QLabel(f"• {error}")
            error_label.setWordWrap(True)
            error_label.setStyleSheet("color: #ff6666;")
            self._status_layout.addWidget(error_label)

    def _update_status_preview(self, preview) -> None:
        """
        Show import preview.

        Args:
            preview: ImportPreview with counts
        """
        self._clear_status()

        # Success header
        header = QLabel(_("Validation passed! Ready to import:"))
        header.setStyleSheet("color: #66ff66; font-weight: bold;")
        self._status_layout.addWidget(header)

        # Counts
        if preview.clients_count > 0:
            label = QLabel(f"• {preview.clients_count} " + _("clients"))
            label.setStyleSheet("color: #cccccc;")
            self._status_layout.addWidget(label)

        if preview.treatments_count > 0:
            label = QLabel(f"• {preview.treatments_count} " + _("treatments"))
            label.setStyleSheet("color: #cccccc;")
            self._status_layout.addWidget(label)

        if preview.products_count > 0:
            label = QLabel(f"• {preview.products_count} " + _("product sales"))
            label.setStyleSheet("color: #cccccc;")
            self._status_layout.addWidget(label)

        if preview.inventory_count > 0:
            label = QLabel(f"• {preview.inventory_count} " + _("inventory items"))
            label.setStyleSheet("color: #cccccc;")
            self._status_layout.addWidget(label)

        # Warning
        warning = QLabel(_("Warning: This will add data to your database."))
        warning.setStyleSheet("color: #ffcc00; margin-top: 8px;")
        self._status_layout.addWidget(warning)

    def _update_status_success(self, result) -> None:
        """
        Show import success message.

        Args:
            result: ImportResult with counts
        """
        self._clear_status()

        # Success header
        header = QLabel(_("Import completed successfully!"))
        header.setStyleSheet("color: #66ff66; font-weight: bold;")
        self._status_layout.addWidget(header)

        # Counts
        total = (
            result.clients_imported
            + result.treatments_imported
            + result.products_imported
            + result.inventory_imported
        )

        summary = QLabel(_("Imported {total} records total:").format(total=total))
        summary.setStyleSheet("color: #cccccc;")
        self._status_layout.addWidget(summary)

        if result.clients_imported > 0:
            label = QLabel(f"• {result.clients_imported} " + _("clients"))
            label.setStyleSheet("color: #cccccc;")
            self._status_layout.addWidget(label)

        if result.treatments_imported > 0:
            label = QLabel(f"• {result.treatments_imported} " + _("treatments"))
            label.setStyleSheet("color: #cccccc;")
            self._status_layout.addWidget(label)

        if result.products_imported > 0:
            label = QLabel(f"• {result.products_imported} " + _("product sales"))
            label.setStyleSheet("color: #cccccc;")
            self._status_layout.addWidget(label)

        if result.inventory_imported > 0:
            label = QLabel(f"• {result.inventory_imported} " + _("inventory items"))
            label.setStyleSheet("color: #cccccc;")
            self._status_layout.addWidget(label)
