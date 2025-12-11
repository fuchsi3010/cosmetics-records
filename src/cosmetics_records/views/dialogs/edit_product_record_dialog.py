# =============================================================================
# Cosmetics Records - Edit Product Record Dialog
# =============================================================================
# This module provides a dialog for editing existing product usage records.
#
# Key Features:
#   - Pre-populated date and product text
#   - Delete button with confirmation
#   - Same fields as add dialog
#
# Design Philosophy:
#   - Consistent with add dialog
#   - Delete button for quick access
#   - Confirmation prevents accidents
#
# Usage Example:
#   dialog = EditProductRecordDialog(record_id, record_data, inventory_items)
#   result = dialog.exec()
#   if result == QDialog.DialogCode.Accepted:
#       if dialog.was_deleted():
#           # Delete record via controller
#       else:
#           updated_data = dialog.get_product_record_data()
#           # Update record via controller
# =============================================================================

import logging
from datetime import date
from typing import List, Optional

from cosmetics_records.utils.time_utils import format_date_localized

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .base_dialog import BaseDialog, ConfirmDialog
from ..components.autocomplete import Autocomplete
from ..components.date_picker import DatePicker
from cosmetics_records.utils.localization import _

# Configure module logger
logger = logging.getLogger(__name__)


class EditProductRecordDialog(BaseDialog):
    """
    Dialog for editing an existing product usage record.

    This dialog allows editing record date and product text, and includes
    a delete button for removing the record.

    Attributes:
        _record_id: Database ID of the record being edited
        _record_data: Dictionary containing current record data
        _deleted: Flag indicating if record was deleted
        _date_picker: DatePicker for record date
        _product_input: Autocomplete for product text
        _error_label: QLabel for displaying validation errors
    """

    def __init__(
        self,
        record_id: int,
        record_data: dict,
        inventory_items: Optional[List[str]] = None,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the edit product record dialog.

        Args:
            record_id: Database ID of the record to edit
            record_data: Dictionary with current record data containing:
                        - date: date
                        - product_text: str
            inventory_items: List of product names for autocomplete (optional)
            parent: Optional parent widget
        """
        self._record_id = record_id
        self._record_data = record_data
        self._inventory_items = inventory_items or []
        self._deleted = False

        # Initialize base dialog
        super().__init__(_("Edit Product Sale"), parent, width=500, height=350)

        # Set autocomplete suggestions
        if self._inventory_items:
            self._product_input.set_suggestions(self._inventory_items)

        # Populate fields with existing data
        self._populate_fields()

        logger.debug(f"EditProductRecordDialog initialized for record {record_id}")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Adds form fields for date and product text plus delete button.

        Args:
            layout: Layout to add content to
        """
        # Error message label (initially hidden)
        # WHY use BaseDialog method: Ensures consistent styling across all dialogs
        self.create_error_label(layout)

        # Form layout for fields
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Date (required)
        self._date_picker = DatePicker()
        form_layout.addRow(_("Date: *"), self._date_picker)

        # Product (autocomplete from inventory, but allows free text)
        self._product_input = Autocomplete()
        self._product_input.set_placeholder(_("Type product name..."))
        form_layout.addRow(_("Products:") + " *", self._product_input)

        layout.addLayout(form_layout)

        # Add stretch to push buttons to bottom
        layout.addStretch()

        # Info note about free text
        info_note = QLabel(_("Type to search inventory, or enter custom product name"))
        info_note.setProperty("form_note", True)  # CSS class (small, gray)
        info_note.setWordWrap(True)
        layout.addWidget(info_note)

        # Required fields note
        required_note = QLabel(_("* Required fields"))
        required_note.setProperty("form_note", True)  # CSS class (small, gray)
        layout.addWidget(required_note)

        # Button row: Delete + Save/Cancel
        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        # Delete button (left side)
        delete_btn = QPushButton(_("Delete"))
        delete_btn.setProperty("class", "danger")  # Danger button styling
        delete_btn.setMinimumWidth(100)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(self._on_delete_clicked)
        button_row.addWidget(delete_btn)

        # Spacer
        button_row.addStretch()

        # Cancel button
        cancel_btn = QPushButton(_("Cancel"))
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(cancel_btn)

        # Save button
        save_btn = QPushButton(_("Save"))
        save_btn.setMinimumWidth(100)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)  # Enter key triggers this
        button_row.addWidget(save_btn)

        layout.addLayout(button_row)

    def _populate_fields(self) -> None:
        """
        Populate form fields with existing record data.

        This is called after the UI is created to fill in current values.
        """
        # Set date
        record_date = self._record_data.get("date")
        if record_date:
            self._date_picker.set_date(record_date)

        # Set product text
        product_text = self._record_data.get("product_text", "")
        self._product_input.set_text(product_text)

    def accept(self) -> None:
        """
        Accept the dialog after validating input.

        Validates that date and product text are provided.
        """
        # Validate date
        record_date = self._date_picker.get_date()
        if not record_date:
            self.show_error(_("Date is required."))
            return

        # Validate product text
        product_text = self._product_input.get_text().strip()
        if not product_text:
            self.show_error(_("Please enter a product name."))
            self._product_input.set_focus()
            return

        # Validation passed
        logger.debug(f"Saving changes to product record {self._record_id}")

        # Hide error if it was showing
        self.hide_error()

        # Accept dialog
        super().accept()

    def _on_delete_clicked(self) -> None:
        """
        Handle delete button click.

        Shows confirmation dialog before marking record for deletion.
        """
        # Get record date for confirmation message
        record_date = self._record_data.get("date")
        if isinstance(record_date, date):
            date_str = format_date_localized(record_date)
        else:
            date_str = str(record_date)

        product_text = self._record_data.get("product_text", "product")

        # Show confirmation dialog
        confirm = ConfirmDialog(
            _("Delete Product Sale"),
            _("Are you sure you want to delete '{name}'?").format(name=product_text)
            + f" ({date_str})\n\n"
            + _("This action cannot be undone."),
            ok_text=_("Delete"),
            cancel_text=_("Cancel"),
            parent=self,
            width=450,
            height=200,
        )

        if confirm.exec() == QDialog.DialogCode.Accepted:
            # User confirmed deletion
            logger.debug(f"Product record {self._record_id} marked for deletion")
            self._deleted = True

            # Close this dialog with Accepted status
            super().accept()

    def was_deleted(self) -> bool:
        """
        Check if the record was marked for deletion.

        Returns:
            bool: True if delete button was clicked and confirmed

        Note:
            After accepting the dialog, check this to determine if the
            record should be deleted or updated.
        """
        return self._deleted

    def get_product_record_data(self) -> dict:
        """
        Get the updated product record data.

        Returns:
            dict: Dictionary containing updated record data with keys:
                 - date: date
                 - product_text: str

        Note:
            This should only be called after the dialog is accepted
            and was_deleted() returns False.
        """
        return {
            "date": self._date_picker.get_date(),
            "product_text": self._product_input.get_text().strip(),
        }
