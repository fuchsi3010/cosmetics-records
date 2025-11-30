# =============================================================================
# Cosmetics Records - Edit Inventory Dialog
# =============================================================================
# This module provides a dialog for editing existing inventory items.
#
# Key Features:
#   - Pre-populated fields with existing item data
#   - Same fields as add dialog
#   - Delete button with confirmation
#   - Field validation
#
# Design Philosophy:
#   - Consistent with add dialog
#   - Delete button for quick access
#   - Confirmation prevents accidents
#   - Validation ensures data integrity
#
# Usage Example:
#   dialog = EditInventoryDialog(item_id, item_data)
#   result = dialog.exec()
#   if result == QDialog.DialogCode.Accepted:
#       if dialog.was_deleted():
#           # Delete item via controller
#       else:
#           updated_data = dialog.get_inventory_data()
#           # Update item via controller
# =============================================================================

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .base_dialog import BaseDialog, ConfirmDialog

# Configure module logger
logger = logging.getLogger(__name__)


class EditInventoryDialog(BaseDialog):
    """
    Dialog for editing an existing inventory item.

    This dialog allows editing all inventory item information and includes
    a delete button for removing the item.

    Attributes:
        _item_id: Database ID of the item being edited
        _item_data: Dictionary containing current item data
        _deleted: Flag indicating if item was deleted
        _name_input: QLineEdit for item name
        _description_input: QTextEdit for description
        _capacity_input: QSpinBox for capacity
        _unit_input: QComboBox for unit
        _error_label: QLabel for displaying validation errors
    """

    # Available units
    UNITS = ["ml", "g", "Pc."]

    def __init__(self, item_id: int, item_data: dict, parent: Optional[QWidget] = None):
        """
        Initialize the edit inventory dialog.

        Args:
            item_id: Database ID of the item to edit
            item_data: Dictionary with current item data containing:
                      - name: str
                      - description: str (optional)
                      - capacity: int
                      - unit: str
            parent: Optional parent widget
        """
        self._item_id = item_id
        self._item_data = item_data
        self._deleted = False

        # Initialize base dialog
        super().__init__("Edit Inventory Item", parent, width=500, height=550)

        # Populate fields with existing data
        self._populate_fields()

        logger.debug(f"EditInventoryDialog initialized for item {item_id}")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Adds form fields for all inventory attributes plus delete button.

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

        # Name (required)
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Enter item name...")
        form_layout.addRow("Name: *", self._name_input)

        # Description (optional)
        self._description_input = QTextEdit()
        self._description_input.setPlaceholderText("Enter description...")
        self._description_input.setFixedHeight(80)
        form_layout.addRow("Description:", self._description_input)

        # Capacity and Unit on same row: [Capacity input] [Unit dropdown]
        capacity_row = QHBoxLayout()
        capacity_row.setSpacing(8)

        # Capacity (required, numeric)
        self._capacity_input = QSpinBox()
        self._capacity_input.setMinimum(1)  # Must be at least 1
        self._capacity_input.setMaximum(999999)  # Reasonable max
        self._capacity_input.setSuffix("")  # No suffix, unit is separate
        capacity_row.addWidget(self._capacity_input, stretch=1)

        # Unit (required, dropdown)
        self._unit_input = QComboBox()
        self._unit_input.addItems(self.UNITS)
        self._unit_input.setFixedWidth(80)
        capacity_row.addWidget(self._unit_input)

        form_layout.addRow("Capacity: *", capacity_row)

        layout.addLayout(form_layout)

        # Add stretch to push buttons to bottom
        layout.addStretch()

        # Required fields note
        required_note = QLabel("* Required fields")
        required_note.setProperty("form_note", True)  # CSS class (small, gray)
        layout.addWidget(required_note)

        # Button row: Delete + Save/Cancel
        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        # Delete button (left side)
        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("class", "danger")  # Danger button styling
        delete_btn.setMinimumWidth(100)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(self._on_delete_clicked)
        button_row.addWidget(delete_btn)

        # Spacer
        button_row.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(cancel_btn)

        # Save button
        save_btn = QPushButton("Save")
        save_btn.setMinimumWidth(100)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)  # Enter key triggers this
        button_row.addWidget(save_btn)

        layout.addLayout(button_row)

    def _populate_fields(self) -> None:
        """
        Populate form fields with existing item data.

        This is called after the UI is created to fill in current values.
        """
        # Set name
        self._name_input.setText(self._item_data.get("name", ""))

        # Set description
        description = self._item_data.get("description", "")
        self._description_input.setPlainText(description)

        # Set capacity
        capacity = self._item_data.get("capacity", 0)
        self._capacity_input.setValue(capacity)

        # Set unit
        unit = self._item_data.get("unit", "ml")
        if unit in self.UNITS:
            self._unit_input.setCurrentText(unit)

    def accept(self) -> None:
        """
        Accept the dialog after validating input.

        Validates that required fields are filled before accepting.
        Shows error message if validation fails.
        """
        # Validate name
        name = self._name_input.text().strip()
        if not name:
            self._show_error("Name is required.")
            self._name_input.setFocus()
            return

        # Validate capacity
        capacity = self._capacity_input.value()
        if capacity <= 0:
            self._show_error("Capacity must be greater than 0.")
            self._capacity_input.setFocus()
            return

        # Validation passed
        logger.debug(f"Saving changes to inventory item {self._item_id}")

        # Hide error if it was showing
        self._error_label.setVisible(False)

        # Accept dialog
        super().accept()

    def _on_delete_clicked(self) -> None:
        """
        Handle delete button click.

        Shows confirmation dialog before marking item for deletion.
        """
        # Get item name for confirmation message
        item_name = self._item_data.get("name", "this item")

        # Show confirmation dialog
        confirm = ConfirmDialog(
            "Delete Inventory Item",
            f"Are you sure you want to delete '{item_name}'?\n\n"
            f"This action cannot be undone.",
            ok_text="Delete",
            cancel_text="Cancel",
            parent=self,
            width=450,
            height=200,
        )

        if confirm.exec() == QDialog.DialogCode.Accepted:
            # User confirmed deletion
            logger.debug(f"Inventory item {self._item_id} marked for deletion")
            self._deleted = True

            # Close this dialog with Accepted status
            super().accept()

    def _show_error(self, message: str) -> None:
        """
        Show an error message to the user.

        Args:
            message: Error message to display
        """
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def was_deleted(self) -> bool:
        """
        Check if the item was marked for deletion.

        Returns:
            bool: True if delete button was clicked and confirmed

        Note:
            After accepting the dialog, check this to determine if the
            item should be deleted or updated.
        """
        return self._deleted

    def get_inventory_data(self) -> dict:
        """
        Get the updated inventory data.

        Returns:
            dict: Dictionary containing updated inventory data with keys:
                 - name: str
                 - description: str
                 - capacity: int
                 - unit: str

        Note:
            This should only be called after the dialog is accepted
            and was_deleted() returns False.
        """
        return {
            "name": self._name_input.text().strip(),
            "description": self._description_input.toPlainText().strip(),
            "capacity": self._capacity_input.value(),
            "unit": self._unit_input.currentText(),
        }
