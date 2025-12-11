# =============================================================================
# Cosmetics Records - Add Inventory Dialog
# =============================================================================
# This module provides a dialog for adding new inventory items.
#
# Key Features:
#   - Required fields: name, capacity, unit
#   - Optional field: description
#   - Capacity as QSpinBox for numeric input
#   - Unit dropdown: ml/g/Pc.
#   - Field validation
#
# Design Philosophy:
#   - Simple form with clear field types
#   - Dropdown prevents invalid units
#   - SpinBox ensures valid capacity values
#   - Description optional for quick entry
#
# Usage Example:
#   dialog = AddInventoryDialog()
#   if dialog.exec() == QDialog.DialogCode.Accepted:
#       item_data = dialog.get_inventory_data()
#       # Save inventory item via controller
# =============================================================================

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .base_dialog import BaseDialog
from cosmetics_records.config import Config
from cosmetics_records.utils.localization import _

# Configure module logger
logger = logging.getLogger(__name__)

# Unit options by measurement system
METRIC_UNITS = ["ml", "g"]
IMPERIAL_UNITS = ["fl oz", "oz"]


def get_units_for_system() -> list:
    """
    Get the available units based on the configured measurement system.

    Returns:
        List of unit strings for the current system, plus localized "Pc."
    """
    config = Config.get_instance()
    if config.units_system == "imperial":
        base_units = IMPERIAL_UNITS.copy()
    else:
        base_units = METRIC_UNITS.copy()

    # Add localized "Pc." (pieces) which is the same in both systems
    base_units.append(_("Pc."))
    return base_units


class AddInventoryDialog(BaseDialog):
    """
    Dialog for adding a new inventory item.

    This dialog collects all necessary information to create a new inventory
    item. Name, capacity, and unit are required.

    Attributes:
        _name_input: QLineEdit for item name
        _description_input: QTextEdit for description
        _capacity_input: QSpinBox for capacity
        _unit_input: QComboBox for unit
        _error_label: QLabel for displaying validation errors
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the add inventory dialog.

        Args:
            parent: Optional parent widget
        """
        # Initialize base dialog
        super().__init__(_("Add Inventory Item"), parent, width=500, height=500)

        logger.debug("AddInventoryDialog initialized")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Adds form fields for all inventory attributes.

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

        # Name (required)
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText(_("Enter item name..."))
        form_layout.addRow(_("Name") + ": *", self._name_input)

        # Description (optional)
        self._description_input = QTextEdit()
        self._description_input.setPlaceholderText(_("Enter description..."))
        self._description_input.setFixedHeight(80)
        form_layout.addRow(_("Description") + ":", self._description_input)

        # Capacity and Unit on same row: [Capacity input] [Unit dropdown]
        capacity_row = QHBoxLayout()
        capacity_row.setSpacing(8)

        # Capacity (required, numeric)
        self._capacity_input = QSpinBox()
        self._capacity_input.setMinimum(1)  # Must be at least 1
        self._capacity_input.setMaximum(999999)  # Reasonable max
        self._capacity_input.setValue(30)  # Default value
        self._capacity_input.setSuffix("")  # No suffix, unit is separate
        capacity_row.addWidget(self._capacity_input, stretch=1)

        # Unit (required, dropdown)
        self._unit_input = QComboBox()
        self._unit_input.addItems(get_units_for_system())
        # Default to first unit (ml for metric, fl oz for imperial)
        self._unit_input.setCurrentIndex(0)
        self._unit_input.setFixedWidth(80)
        capacity_row.addWidget(self._unit_input)

        form_layout.addRow(_("Capacity") + ": *", capacity_row)

        layout.addLayout(form_layout)

        # Add stretch to push buttons to bottom
        layout.addStretch()

        # Required fields note
        required_note = QLabel(_("* Required fields"))
        required_note.setProperty("form_note", True)  # CSS class (small, gray)
        layout.addWidget(required_note)

        # Save/Cancel buttons
        button_row = self.create_button_row("Save", "Cancel")
        layout.addLayout(button_row)

    def accept(self) -> None:
        """
        Accept the dialog after validating input.

        Validates that required fields are filled before accepting.
        Shows error message if validation fails.
        """
        # Validate name
        name = self._name_input.text().strip()
        if not name:
            self.show_error(_("Name is required."))
            self._name_input.setFocus()
            return

        # Validate capacity
        capacity = self._capacity_input.value()
        if capacity <= 0:
            self.show_error(_("Capacity must be greater than 0."))
            self._capacity_input.setFocus()
            return

        # Validation passed
        logger.debug(f"Adding new inventory item: {name}")

        # Hide error if it was showing
        self.hide_error()

        # Accept dialog
        super().accept()

    def get_inventory_data(self) -> dict:
        """
        Get the entered inventory data.

        Returns:
            dict: Dictionary containing inventory data with keys:
                 - name: str
                 - description: str
                 - capacity: int
                 - unit: str

        Note:
            This should only be called after the dialog is accepted.
        """
        return {
            "name": self._name_input.text().strip(),
            "description": self._description_input.toPlainText().strip(),
            "capacity": self._capacity_input.value(),
            "unit": self._unit_input.currentText(),
        }
