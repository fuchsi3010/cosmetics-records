# =============================================================================
# Cosmetics Records - Add Product Record Dialog
# =============================================================================
# This module provides a dialog for adding new product usage records.
#
# Key Features:
#   - Date picker (defaults to today)
#   - Autocomplete product input (suggests from inventory)
#   - Allows free text if product not in inventory
#   - Simple two-field form
#
# Design Philosophy:
#   - Quick data entry with autocomplete
#   - Flexibility to record unlisted products
#   - Default to today's date for convenience
#   - Minimal required fields
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
from ..components.date_picker import DatePicker

# Configure module logger
logger = logging.getLogger(__name__)


class AddProductRecordDialog(BaseDialog):
    """
    Dialog for adding a new product usage record.

    This dialog collects date and product text for a new product record.
    Product input uses autocomplete from inventory but allows free text.

    Attributes:
        _client_id: Database ID of the client this record is for
        _date_picker: DatePicker for record date
        _product_input: Autocomplete for product text
        _error_label: QLabel for displaying validation errors
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

        # Initialize base dialog
        # WHY 500x300: Compact size for simple form
        super().__init__("Add Product Record", parent, width=500, height=300)

        # Set default date to today
        self._date_picker.set_date(date.today())

        # Set autocomplete suggestions
        if self._inventory_items:
            self._product_input.set_suggestions(self._inventory_items)

        logger.debug(f"AddProductRecordDialog initialized for client {client_id}")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Adds form fields for date and product text.

        Args:
            layout: Layout to add content to
        """
        # Error message label (initially hidden)
        self._error_label = QLabel()
        self._error_label.setProperty("error_message", True)  # CSS class (red)
        self._error_label.setVisible(False)
        self._error_label.setWordWrap(True)
        layout.addWidget(self._error_label)

        # Form layout for fields
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Date (required, defaults to today)
        self._date_picker = DatePicker()
        form_layout.addRow("Date: *", self._date_picker)

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

        Validates that date and product text are provided.
        """
        # Validate date
        record_date = self._date_picker.get_date()
        if not record_date:
            self._show_error("Date is required.")
            return

        # Validate product text
        product_text = self._product_input.get_text().strip()
        if not product_text:
            self._show_error("Product is required.")
            self._product_input.set_focus()
            return

        # Validation passed
        logger.debug(
            f"Adding product record for client {self._client_id} on {record_date}"
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

    def get_product_record_data(self) -> dict:
        """
        Get the entered product record data.

        Returns:
            dict: Dictionary containing product record data with keys:
                 - client_id: int
                 - date: date
                 - product_text: str

        Note:
            This should only be called after the dialog is accepted.
        """
        return {
            "client_id": self._client_id,
            "date": self._date_picker.get_date(),
            "product_text": self._product_input.get_text().strip(),
        }
