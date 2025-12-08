# =============================================================================
# Cosmetics Records - Add Client Dialog
# =============================================================================
# This module provides a dialog for adding new clients.
#
# Key Features:
#   - Required fields: first_name, last_name
#   - Optional fields: email, phone, address, date_of_birth, allergies, tags
#   - Field validation before saving
#   - DatePicker component for date of birth
#   - TagInput component for tags
#   - Clear error messages
#
# Design Philosophy:
#   - Simple form layout with clear labels
#   - Validation prevents invalid data entry
#   - Optional fields allow quick entry of basic info
#   - Components provide rich UI for complex inputs
#
# Usage Example:
#   dialog = AddClientDialog()
#   if dialog.exec() == QDialog.DialogCode.Accepted:
#       client_data = dialog.get_client_data()
#       # Save client via controller
# =============================================================================

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .base_dialog import BaseDialog
from ..components.date_picker import DatePicker
from ..components.tag_input import TagInput
from ..constants import DialogSize, ComponentHeight
from cosmetics_records.utils.validators import is_valid_email
from cosmetics_records.utils.localization import _

# Configure module logger
logger = logging.getLogger(__name__)


class AddClientDialog(BaseDialog):
    """
    Dialog for adding a new client.

    This dialog collects all necessary information to create a new client
    record. First and last names are required; all other fields are optional.

    Attributes:
        _first_name_input: QLineEdit for first name
        _last_name_input: QLineEdit for last name
        _email_input: QLineEdit for email
        _phone_input: QLineEdit for phone
        _address_input: QTextEdit for address
        _dob_picker: DatePicker for date of birth
        _allergies_input: QTextEdit for allergies
        _tag_input: TagInput for tags
        _error_label: QLabel for displaying validation errors
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the add client dialog.

        Args:
            parent: Optional parent widget
        """
        # Initialize base dialog with appropriate size
        # WHY LARGE: Tall enough for all client fields without scrolling
        super().__init__(
            _("Add New Client"),
            parent,
            width=DialogSize.LARGE_WIDTH,
            height=DialogSize.LARGE_HEIGHT,
        )

        logger.debug("AddClientDialog initialized")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Adds form fields for all client attributes.

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

        # First Name (required)
        self._first_name_input = QLineEdit()
        self._first_name_input.setPlaceholderText(_("Enter first name..."))
        form_layout.addRow(_("First Name") + ": *", self._first_name_input)

        # Last Name (required)
        self._last_name_input = QLineEdit()
        self._last_name_input.setPlaceholderText(_("Enter last name..."))
        form_layout.addRow(_("Last Name") + ": *", self._last_name_input)

        # Email (optional)
        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText(_("Enter email address..."))
        form_layout.addRow(_("Email") + ":", self._email_input)

        # Phone (optional)
        self._phone_input = QLineEdit()
        self._phone_input.setPlaceholderText(_("Enter phone number..."))
        form_layout.addRow(_("Phone") + ":", self._phone_input)

        # Address (optional)
        self._address_input = QTextEdit()
        self._address_input.setPlaceholderText(_("Enter address..."))
        self._address_input.setFixedHeight(ComponentHeight.TEXTAREA_SMALL)
        form_layout.addRow(_("Address") + ":", self._address_input)

        # Date of Birth (optional)
        self._dob_picker = DatePicker()
        form_layout.addRow(_("Date of Birth") + ":", self._dob_picker)

        # Allergies (optional)
        self._allergies_input = QTextEdit()
        self._allergies_input.setPlaceholderText(_("Enter any allergies..."))
        self._allergies_input.setFixedHeight(ComponentHeight.TEXTAREA_SMALL)
        form_layout.addRow(_("Allergies") + ":", self._allergies_input)

        # Tags (optional)
        self._tag_input = TagInput()
        form_layout.addRow(_("Tags") + ":", self._tag_input)

        layout.addLayout(form_layout)

        # Add stretch to push buttons to bottom
        layout.addStretch()

        # Required fields note
        required_note = QLabel(_("* Required fields"))
        required_note.setProperty("form_note", True)  # CSS class (small, gray)
        layout.addWidget(required_note)

        # Save/Cancel buttons
        button_row = self.create_button_row(_("Save"), _("Cancel"))
        layout.addLayout(button_row)

    def accept(self) -> None:
        """
        Accept the dialog after validating input.

        Validates that required fields are filled and email format is valid
        before accepting. Shows error message if validation fails.
        """
        # Validate required fields
        first_name = self._first_name_input.text().strip()
        last_name = self._last_name_input.text().strip()

        if not first_name:
            self.show_error(_("First name is required."))
            self._first_name_input.setFocus()
            return

        if not last_name:
            self.show_error(_("Last name is required."))
            self._last_name_input.setFocus()
            return

        # Validate email format if provided
        # WHY shared validator: Ensures consistent validation across model and UI
        email = self._email_input.text().strip()
        if email and not is_valid_email(email):
            self.show_error(
                _(
                    "Invalid email format. Please enter a valid email "
                    "(e.g., user@example.com)."
                )
            )
            self._email_input.setFocus()
            return

        # Validation passed
        logger.debug(f"Adding new client: {first_name} {last_name}")

        # Hide error if it was showing
        self.hide_error()

        # Accept dialog
        super().accept()

    def get_client_data(self) -> dict:
        """
        Get the entered client data.

        Returns:
            dict: Dictionary containing client data with keys:
                 - first_name: str
                 - last_name: str
                 - email: str
                 - phone: str
                 - address: str
                 - date_of_birth: date or None
                 - allergies: str
                 - tags: list of str

        Note:
            This should only be called after the dialog is accepted.
        """
        return {
            "first_name": self._first_name_input.text().strip(),
            "last_name": self._last_name_input.text().strip(),
            "email": self._email_input.text().strip(),
            "phone": self._phone_input.text().strip(),
            "address": self._address_input.toPlainText().strip(),
            "date_of_birth": self._dob_picker.get_date(),
            "allergies": self._allergies_input.toPlainText().strip(),
            "tags": self._tag_input.get_tags(),
        }
