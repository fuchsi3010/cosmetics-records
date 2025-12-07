# =============================================================================
# Cosmetics Records - Add Product Record Dialog
# =============================================================================
# This module provides a dialog for adding new product usage records.
#
# Key Features:
#   - Date picker (defaults to today)
#   - Autocomplete product input (suggests from inventory)
#   - Quantity selector (1x-10x)
#   - Multi-product entry (accumulates products before saving)
#   - Prevents duplicate entries on same date
#
# Design Philosophy:
#   - Quick data entry with autocomplete
#   - Flexibility to record unlisted products
#   - Support for multiple products in one record
#   - Date picker for flexibility
#   - Prevent duplicate product records on same date
#
# Usage Example:
#   dialog = AddProductRecordDialog(client_id, inventory_items, check_date_exists_fn)
#   if dialog.exec() == QDialog.DialogCode.Accepted:
#       record_data = dialog.get_product_record_data()
#       # Save product record via controller
# =============================================================================

import logging
from datetime import date
from typing import Callable, List, Optional

from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .base_dialog import BaseDialog
from ..components.autocomplete import Autocomplete
from ..components.date_picker import DatePicker
from cosmetics_records.utils.localization import _

# Configure module logger
logger = logging.getLogger(__name__)


class AddProductRecordDialog(BaseDialog):
    """
    Dialog for adding a new product usage record.

    This dialog collects date and product text for a new product record.
    Includes date picker defaulting to today.
    Product input uses autocomplete from inventory but allows free text.
    Supports adding multiple products with quantities.

    Attributes:
        _client_id: Database ID of the client this record is for
        _date_picker: DatePicker for selecting record date
        _product_input: Autocomplete for product text
        _quantity_combo: ComboBox for quantity selection
        _products_text: QTextEdit showing accumulated products
        _check_date_exists: Callback to check if entry exists for date
        _existing_record_id: If set, edit existing record instead
    """

    def __init__(
        self,
        client_id: int,
        inventory_items: Optional[List[str]] = None,
        check_date_exists: Optional[Callable[[date], bool]] = None,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the add product record dialog.

        Args:
            client_id: Database ID of the client
            inventory_items: List of product names for autocomplete (optional)
            check_date_exists: Optional callback that returns True if a
                              product record already exists for the given date
            parent: Optional parent widget
        """
        self._client_id = client_id
        self._inventory_items = inventory_items or []
        self._check_date_exists = check_date_exists
        self._existing_record_id: Optional[int] = None

        # Initialize base dialog - larger to fit suggestions
        super().__init__(_("Add Product Record"), parent, width=550, height=500)

        # Set autocomplete suggestions
        if self._inventory_items:
            self._product_input.set_suggestions(self._inventory_items)

        logger.debug(f"AddProductRecordDialog initialized for client {client_id}")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Adds form field for date, product text with quantity selector and
        accumulated products text area.

        Args:
            layout: Layout to add content to
        """
        # Error message label (initially hidden)
        # WHY use BaseDialog method: Ensures consistent styling across all dialogs
        self.create_error_label(layout)

        # Form layout for date
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Date picker (defaults to today)
        self._date_picker = DatePicker()
        self._date_picker.set_date(date.today())
        form_layout.addRow(_("Date") + ": *", self._date_picker)

        layout.addLayout(form_layout)

        # Product entry row: [Quantity] [Product input] [Add button]
        entry_row = QHBoxLayout()
        entry_row.setSpacing(8)

        # Quantity selector (1x-10x)
        self._quantity_combo = QComboBox()
        for i in range(1, 11):
            self._quantity_combo.addItem(f"{i}x")
        self._quantity_combo.setFixedWidth(60)
        entry_row.addWidget(self._quantity_combo)

        # Product autocomplete input
        self._product_input = Autocomplete()
        self._product_input.set_placeholder(_("Type product name..."))
        entry_row.addWidget(self._product_input, stretch=1)

        # Add button
        add_btn = QPushButton(_("Add"))
        add_btn.setMinimumWidth(60)
        add_btn.clicked.connect(self._on_add_product)
        entry_row.addWidget(add_btn)

        layout.addLayout(entry_row)

        # Info note about free text
        info_note = QLabel(_("Type to search inventory, or enter custom product name"))
        info_note.setProperty("form_note", True)
        info_note.setWordWrap(True)
        layout.addWidget(info_note)

        # Accumulated products text area
        products_label = QLabel(_("Products:"))
        layout.addWidget(products_label)

        self._products_text = QTextEdit()
        self._products_text.setPlaceholderText(_("Added products will appear here..."))
        self._products_text.setMinimumHeight(150)
        layout.addWidget(self._products_text)

        # Save/Cancel buttons
        button_row = self.create_button_row(_("Save"), _("Cancel"))
        layout.addLayout(button_row)

    def _on_add_product(self) -> None:
        """
        Handle Add button click.

        Adds the current product with quantity to the products text area.
        """
        product_name = self._product_input.get_text().strip()
        if not product_name:
            self.show_error(_("Please enter a product name."))
            self._product_input.set_focus()
            return

        # Get quantity
        quantity = self._quantity_combo.currentText()

        # Add to products text
        current_text = self._products_text.toPlainText()
        new_line = f"{quantity} {product_name}"

        if current_text:
            self._products_text.setPlainText(f"{current_text}\n{new_line}")
        else:
            self._products_text.setPlainText(new_line)

        # Clear input for next product
        self._product_input.clear()
        self._quantity_combo.setCurrentIndex(0)
        self._product_input.set_focus()

        # Hide error if showing
        self.hide_error()

        logger.debug(f"Added product: {new_line}")

    def accept(self) -> None:
        """
        Accept the dialog after validating input.

        Validates that date is selected, at least one product is in the list,
        and no duplicate entry exists for the selected date.
        """
        # Validate date
        selected_date = self._date_picker.get_date()
        if not selected_date:
            self.show_error(_("Date is required."))
            return

        # Check for duplicate entry (only for new entries, not edits)
        if (
            self._check_date_exists
            and not self._existing_record_id
            and self._check_date_exists(selected_date)
        ):
            self.show_error(_("A product record already exists for this date."))
            return

        # Check if there's content in the products text
        products_text = self._products_text.toPlainText().strip()

        # Also check if there's something in the input field that wasn't added
        pending_product = self._product_input.get_text().strip()
        if pending_product and not products_text:
            # Auto-add the pending product
            self._on_add_product()
            products_text = self._products_text.toPlainText().strip()

        if not products_text:
            self.show_error(_("Please add at least one product."))
            self._product_input.set_focus()
            return

        # Validation passed
        logger.debug(
            f"Adding product record for client {self._client_id} on {selected_date}"
        )

        # Hide error if it was showing
        self.hide_error()

        # Accept dialog
        super().accept()

    def set_existing_record(
        self, record_id: int, record_date: date, product_text: str
    ) -> None:
        """
        Set up dialog to edit an existing product record.

        Args:
            record_id: ID of existing record to edit
            record_date: Date of the existing record
            product_text: Existing product text to pre-fill
        """
        self._existing_record_id = record_id
        self._date_picker.set_date(record_date)
        self._products_text.setPlainText(product_text)
        self.setWindowTitle(_("Edit Product Record"))
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
                 - date: date (selected date)
                 - product_text: str (all added products)

        Note:
            This should only be called after the dialog is accepted.
        """
        return {
            "client_id": self._client_id,
            "date": self._date_picker.get_date(),
            "product_text": self._products_text.toPlainText().strip(),
        }
