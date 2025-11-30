# =============================================================================
# Cosmetics Records - Edit Client Dialog
# =============================================================================
# This module provides a dialog for editing existing clients.
#
# Key Features:
#   - Pre-populated fields with existing client data
#   - Same fields as add dialog
#   - Delete button with confirmation
#   - Field validation before saving
#
# Design Philosophy:
#   - Reuses layout from add dialog for consistency
#   - Delete button for quick access to deletion
#   - Confirmation prevents accidental deletion
#   - Validation ensures data integrity
#
# Usage Example:
#   dialog = EditClientDialog(client_id, client_data)
#   result = dialog.exec()
#   if result == QDialog.DialogCode.Accepted:
#       updated_data = dialog.get_client_data()
#       # Update client via controller
#   elif dialog.was_deleted():
#       # Delete client via controller
# =============================================================================

import logging
from datetime import date
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from .base_dialog import BaseDialog, ConfirmDialog
from ..components.date_picker import DatePicker
from ..components.tag_input import TagInput

# Configure module logger
logger = logging.getLogger(__name__)


class EditClientDialog(BaseDialog):
    """
    Dialog for editing an existing client.

    This dialog allows editing all client information and includes a
    delete button for removing the client.

    Attributes:
        _client_id: Database ID of the client being edited
        _client_data: Dictionary containing current client data
        _deleted: Flag indicating if client was deleted
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

    def __init__(self, client_id: int, client_data: dict, parent: Optional = None):
        """
        Initialize the edit client dialog.

        Args:
            client_id: Database ID of the client to edit
            client_data: Dictionary with current client data containing:
                        - first_name: str
                        - last_name: str
                        - email: str (optional)
                        - phone: str (optional)
                        - address: str (optional)
                        - date_of_birth: date or None
                        - allergies: str (optional)
                        - tags: list of str (optional)
            parent: Optional parent widget
        """
        self._client_id = client_id
        self._client_data = client_data
        self._deleted = False

        # Initialize base dialog
        super().__init__("Edit Client", parent, width=600, height=750)

        # Populate fields with existing data
        self._populate_fields()

        logger.debug(f"EditClientDialog initialized for client {client_id}")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Adds form fields for all client attributes plus delete button.

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

        # First Name (required)
        self._first_name_input = QLineEdit()
        self._first_name_input.setPlaceholderText("Enter first name...")
        form_layout.addRow("First Name: *", self._first_name_input)

        # Last Name (required)
        self._last_name_input = QLineEdit()
        self._last_name_input.setPlaceholderText("Enter last name...")
        form_layout.addRow("Last Name: *", self._last_name_input)

        # Email (optional)
        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("Enter email address...")
        form_layout.addRow("Email:", self._email_input)

        # Phone (optional)
        self._phone_input = QLineEdit()
        self._phone_input.setPlaceholderText("Enter phone number...")
        form_layout.addRow("Phone:", self._phone_input)

        # Address (optional)
        self._address_input = QTextEdit()
        self._address_input.setPlaceholderText("Enter address...")
        self._address_input.setFixedHeight(60)
        form_layout.addRow("Address:", self._address_input)

        # Date of Birth (optional)
        self._dob_picker = DatePicker()
        form_layout.addRow("Date of Birth:", self._dob_picker)

        # Allergies (optional)
        self._allergies_input = QTextEdit()
        self._allergies_input.setPlaceholderText("Enter any allergies...")
        self._allergies_input.setFixedHeight(60)
        form_layout.addRow("Allergies:", self._allergies_input)

        # Tags (optional)
        self._tag_input = TagInput()
        form_layout.addRow("Tags:", self._tag_input)

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
        delete_btn.setFixedWidth(100)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(self._on_delete_clicked)
        button_row.addWidget(delete_btn)

        # Spacer
        button_row.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setFixedWidth(100)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(cancel_btn)

        # Save button
        save_btn = QPushButton("Save")
        save_btn.setFixedWidth(100)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)  # Enter key triggers this
        button_row.addWidget(save_btn)

        layout.addLayout(button_row)

    def _populate_fields(self) -> None:
        """
        Populate form fields with existing client data.

        This is called after the UI is created to fill in current values.
        """
        # Set text fields
        self._first_name_input.setText(self._client_data.get("first_name", ""))
        self._last_name_input.setText(self._client_data.get("last_name", ""))
        self._email_input.setText(self._client_data.get("email", ""))
        self._phone_input.setText(self._client_data.get("phone", ""))
        self._address_input.setPlainText(self._client_data.get("address", ""))
        self._allergies_input.setPlainText(self._client_data.get("allergies", ""))

        # Set date of birth
        dob = self._client_data.get("date_of_birth")
        if dob:
            self._dob_picker.set_date(dob)

        # Set tags
        tags = self._client_data.get("tags", [])
        if tags:
            self._tag_input.set_tags(tags)

    def accept(self) -> None:
        """
        Accept the dialog after validating input.

        Validates that required fields are filled before accepting.
        Shows error message if validation fails.
        """
        # Validate required fields
        first_name = self._first_name_input.text().strip()
        last_name = self._last_name_input.text().strip()

        if not first_name:
            self._show_error("First name is required.")
            self._first_name_input.setFocus()
            return

        if not last_name:
            self._show_error("Last name is required.")
            self._last_name_input.setFocus()
            return

        # Validation passed
        logger.debug(f"Saving changes to client {self._client_id}")

        # Hide error if it was showing
        self._error_label.setVisible(False)

        # Accept dialog
        super().accept()

    def _on_delete_clicked(self) -> None:
        """
        Handle delete button click.

        Shows confirmation dialog before marking client for deletion.
        """
        # Get client name for confirmation message
        first_name = self._client_data.get("first_name", "")
        last_name = self._client_data.get("last_name", "")
        client_name = f"{first_name} {last_name}".strip()

        # Show confirmation dialog
        confirm = ConfirmDialog(
            "Delete Client",
            f"Are you sure you want to delete {client_name}?\n\n"
            f"This will also delete all associated treatment and product history.\n\n"
            f"This action cannot be undone.",
            ok_text="Delete",
            cancel_text="Cancel",
            parent=self,
            width=450,
            height=250,
        )

        if confirm.exec() == QDialog.DialogCode.Accepted:
            # User confirmed deletion
            logger.debug(f"Client {self._client_id} marked for deletion")
            self._deleted = True

            # Close this dialog with Accepted status
            # WHY Accepted not Rejected: We want to signal that an action was taken
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
        Check if the client was marked for deletion.

        Returns:
            bool: True if delete button was clicked and confirmed

        Note:
            After accepting the dialog, check this to determine if the
            client should be deleted or updated.
        """
        return self._deleted

    def get_client_data(self) -> dict:
        """
        Get the updated client data.

        Returns:
            dict: Dictionary containing updated client data with keys:
                 - first_name: str
                 - last_name: str
                 - email: str
                 - phone: str
                 - address: str
                 - date_of_birth: date or None
                 - allergies: str
                 - tags: list of str

        Note:
            This should only be called after the dialog is accepted
            and was_deleted() returns False.
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
