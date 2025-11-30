# =============================================================================
# Cosmetics Records - Add Treatment Dialog
# =============================================================================
# This module provides a dialog for adding new treatment records.
#
# Key Features:
#   - Date picker (defaults to today)
#   - Notes text area (required)
#   - Check for existing treatment on same date
#   - Offer to edit existing treatment instead
#
# Design Philosophy:
#   - Simple form with minimal required fields
#   - Default to today's date for convenience
#   - Prevent duplicate treatments on same date
#   - Clear validation messages
#
# Usage Example:
#   dialog = AddTreatmentDialog(client_id)
#   if dialog.exec() == QDialog.DialogCode.Accepted:
#       treatment_data = dialog.get_treatment_data()
#       # Save treatment via controller
# =============================================================================

import logging
from datetime import date
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)

from .base_dialog import BaseDialog, SimpleMessageDialog
from ..components.date_picker import DatePicker

# Configure module logger
logger = logging.getLogger(__name__)


class AddTreatmentDialog(BaseDialog):
    """
    Dialog for adding a new treatment record.

    This dialog collects date and notes for a new treatment record.
    It checks for existing treatments on the selected date.

    Attributes:
        _client_id: Database ID of the client this treatment is for
        _date_picker: DatePicker for treatment date
        _notes_input: QTextEdit for treatment notes
        _error_label: QLabel for displaying validation errors
    """

    def __init__(self, client_id: int, parent: Optional = None):
        """
        Initialize the add treatment dialog.

        Args:
            client_id: Database ID of the client
            parent: Optional parent widget
        """
        self._client_id = client_id

        # Initialize base dialog
        # WHY 500x400: Compact size for simple form
        super().__init__("Add Treatment", parent, width=500, height=400)

        # Set default date to today
        self._date_picker.set_date(date.today())

        logger.debug(f"AddTreatmentDialog initialized for client {client_id}")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Adds form fields for date and notes.

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

        # Notes (required)
        self._notes_input = QTextEdit()
        self._notes_input.setPlaceholderText("Enter treatment notes...")
        self._notes_input.setMinimumHeight(150)
        form_layout.addRow("Notes: *", self._notes_input)

        layout.addLayout(form_layout)

        # Add stretch to push buttons to bottom
        layout.addStretch()

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

        Validates that date and notes are provided, and checks for
        existing treatment on the same date.
        """
        # Validate date
        treatment_date = self._date_picker.get_date()
        if not treatment_date:
            self._show_error("Date is required.")
            return

        # Validate notes
        notes = self._notes_input.toPlainText().strip()
        if not notes:
            self._show_error("Notes are required.")
            self._notes_input.setFocus()
            return

        # PLACEHOLDER: Check for existing treatment on this date
        # In real implementation, this would query the controller
        existing_treatment = self._check_existing_treatment(treatment_date)

        if existing_treatment:
            # Offer to edit existing treatment instead
            self._offer_edit_existing()
            return

        # Validation passed
        logger.debug(
            f"Adding treatment for client {self._client_id} on {treatment_date}"
        )

        # Hide error if it was showing
        self._error_label.setVisible(False)

        # Accept dialog
        super().accept()

    def _check_existing_treatment(self, treatment_date: date) -> bool:
        """
        Check if a treatment already exists on the given date.

        Args:
            treatment_date: Date to check

        Returns:
            bool: True if treatment exists, False otherwise

        Note:
            PLACEHOLDER: This will be implemented by the controller.
        """
        # PLACEHOLDER: Controller method will be called here
        # For now, return False (no existing treatment)
        return False

    def _offer_edit_existing(self) -> None:
        """
        Show a message offering to edit the existing treatment.

        This is called when a treatment already exists on the selected date.
        """
        treatment_date = self._date_picker.get_date()
        date_str = treatment_date.strftime("%B %d, %Y") if treatment_date else ""

        message_dialog = SimpleMessageDialog(
            "Treatment Already Exists",
            f"A treatment record already exists for {date_str}.\n\n"
            f"Please edit the existing treatment or choose a different date.",
            parent=self,
            width=450,
            height=200,
        )

        message_dialog.exec()

    def _show_error(self, message: str) -> None:
        """
        Show an error message to the user.

        Args:
            message: Error message to display
        """
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def get_treatment_data(self) -> dict:
        """
        Get the entered treatment data.

        Returns:
            dict: Dictionary containing treatment data with keys:
                 - client_id: int
                 - date: date
                 - notes: str

        Note:
            This should only be called after the dialog is accepted.
        """
        return {
            "client_id": self._client_id,
            "date": self._date_picker.get_date(),
            "notes": self._notes_input.toPlainText().strip(),
        }
