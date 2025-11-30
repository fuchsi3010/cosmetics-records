# =============================================================================
# Cosmetics Records - Add Product Record Dialog
# =============================================================================
# This module provides a dialog for adding new product usage records.
#
# Key Features:
#   - Always uses today's date (no date picker)
#   - Autocomplete product input (suggests from inventory)
#   - Allows free text if product not in inventory
#   - Auto-redirects to edit if product record exists for today
#
# Design Philosophy:
#   - Quick data entry with autocomplete
#   - Flexibility to record unlisted products
#   - Uses current date automatically for convenience
#   - Prevent duplicate records on same date
#
# Usage Example:
#   dialog = AddProductRecordDialog(client_id, inventory_items)
#   if dialog.exec() == QDialog.DialogCode.Accepted:
#       record_data = dialog.get_product_record_data()
#       # Save product record via controller
# =============================================================================

import logging
from datetime import date
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

from .base_dialog import BaseDialog
from ..components.autocomplete import Autocomplete

# Configure module logger
logger = logging.getLogger(__name__)


class AddProductRecordDialog(BaseDialog):
    """
    Dialog for adding a new product usage record.

    This dialog collects product text for a new product record.
    Always uses today's date - no date picker shown.
    Product input uses autocomplete from inventory but allows free text.

    Attributes:
        _client_id: Database ID of the client this record is for
        _product_input: Autocomplete for product text
        _error_label: QLabel for displaying validation errors
        _existing_record_id: If set, edit existing record instead
    """

    def __init__(
        self, client_id: int, inventory_items: List[str] = None, parent: Optional = None
    ):
        """
        Initialize the add product record dialog.

        Args:
            client_id: Database ID of the client
            inventory_items: List of product names for autocomplete (optional)
            parent: Optional parent widget
        """
        self._client_id = client_id
        self._inventory_items = inventory_items or []
        self._existing_record_id: Optional[int] = None

        # Initialize base dialog
        # WHY 500x300: Compact size for simple form
        super().__init__("Add Product Record", parent, width=500, height=300)

        # Set autocomplete suggestions
        if self._inventory_items:
            self._product_input.set_suggestions(self._inventory_items)

        logger.debug(f"AddProductRecordDialog initialized for client {client_id}")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Adds form field for product text. Date is always today.

        Args:
            layout: Layout to add content to
        """
        # Error message label (initially hidden)
        self._error_label = QLabel()
        self._error_label.setProperty("error_message", True)  # CSS class (red)
        self._error_label.setVisible(False)
        self._error_label.setWordWrap(True)
        layout.addWidget(self._error_label)

        # Date display (read-only, always today)
        today_str = date.today().strftime("%B %d, %Y")
        date_label = QLabel(f"Date: {today_str}")
        date_label.setProperty("form_note", True)
        layout.addWidget(date_label)

        # Form layout for fields
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Product (autocomplete from inventory, but allows free text)
        self._product_input = Autocomplete()
        self._product_input.set_placeholder("Type product name...")
        form_layout.addRow("Product: *", self._product_input)

        layout.addLayout(form_layout)

        # Add stretch to push buttons to bottom
        layout.addStretch()

        # Info note about free text
        info_note = QLabel("Type to search inventory, or enter custom product name")
        info_note.setProperty("form_note", True)  # CSS class (small, gray)
        info_note.setWordWrap(True)
        layout.addWidget(info_note)

        # Required fields note
        required_note = QLabel("* Required fields")
        required_note.setProperty("form_note", True)  # CSS class (small, gray)
        layout.addWidget(required_note)

        # Save/Cancel buttons
        button_row = self.create_button_row("Save", "Cancel")
        layout.addLayout(button_row)

    def accept(self) -> None:
        """
        Accept the dialog after validating input.

        Validates that product text is provided.
        """
        # Validate product text
        product_text = self._product_input.get_text().strip()
        if not product_text:
            self._show_error("Product is required.")
            self._product_input.set_focus()
            return

        # Validation passed
        logger.debug(
            f"Adding product record for client {self._client_id} on {date.today()}"
        )

        # Hide error if it was showing
        self._error_label.setVisible(False)

        # Accept dialog
        super().accept()

    def _show_error(self, message: str) -> None:
        """
        Show an error message to the user.

        Args:
            message: Error message to display
        """
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def set_existing_record(self, record_id: int, product_text: str) -> None:
        """
        Set up dialog to edit an existing product record.

        Called when a product record already exists for today's date.

        Args:
            record_id: ID of existing record to edit
            product_text: Existing product text to pre-fill
        """
        self._existing_record_id = record_id
        self._product_input.set_text(product_text)
        self.setWindowTitle("Edit Product Record")
        logger.debug(f"Editing existing product record {record_id}")

    def is_editing_existing(self) -> bool:
        """
        Check if dialog is editing an existing record.

        Returns:
            bool: True if editing existing, False if creating new
        """
        return self._existing_record_id is not None

    def get_existing_record_id(self) -> Optional[int]:
        """
        Get the ID of the existing record being edited.

        Returns:
            Optional[int]: Record ID if editing, None if creating new
        """
        return self._existing_record_id

    def get_product_record_data(self) -> dict:
        """
        Get the entered product record data.

        Returns:
            dict: Dictionary containing product record data with keys:
                 - client_id: int
                 - date: date (always today)
                 - product_text: str

        Note:
            This should only be called after the dialog is accepted.
        """
        return {
            "client_id": self._client_id,
            "date": date.today(),
            "product_text": self._product_input.get_text().strip(),
        }
