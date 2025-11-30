# =============================================================================
# Cosmetics Records - Add Treatment Dialog
# =============================================================================
# This module provides a dialog for adding new treatment records.
#
# Key Features:
#   - Always uses today's date (no date picker)
#   - Notes text area (required)
#   - Auto-redirects to edit if treatment exists for today
#
# Design Philosophy:
#   - Simple form with minimal required fields
#   - Uses current date automatically for convenience
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

# Configure module logger
logger = logging.getLogger(__name__)


class AddTreatmentDialog(BaseDialog):
    """
    Dialog for adding a new treatment record.

    This dialog collects notes for a new treatment record.
    Always uses today's date - no date picker shown.

    Attributes:
        _client_id: Database ID of the client this treatment is for
        _notes_input: QTextEdit for treatment notes
        _error_label: QLabel for displaying validation errors
        _existing_treatment_id: If set, edit existing treatment instead
    """

    def __init__(self, client_id: int, parent: Optional = None):
        """
        Initialize the add treatment dialog.

        Args:
            client_id: Database ID of the client
            parent: Optional parent widget
        """
        self._client_id = client_id
        self._existing_treatment_id: Optional[int] = None

        # Initialize base dialog
        # WHY 500x350: Compact size for simple form (smaller without date picker)
        super().__init__("Add Treatment", parent, width=500, height=350)

        logger.debug(f"AddTreatmentDialog initialized for client {client_id}")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Adds form field for notes. Date is always today.

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

        # Notes (required)
        notes_label = QLabel("Notes: *")
        layout.addWidget(notes_label)

        self._notes_input = QTextEdit()
        self._notes_input.setPlaceholderText("Enter treatment notes...")
        self._notes_input.setMinimumHeight(150)
        layout.addWidget(self._notes_input)

        # Add stretch to push buttons to bottom
        layout.addStretch()

        # Save/Cancel buttons
        button_row = self.create_button_row("Save", "Cancel")
        layout.addLayout(button_row)

    def accept(self) -> None:
        """
        Accept the dialog after validating input.

        Validates that notes are provided.
        """
        # Validate notes
        notes = self._notes_input.toPlainText().strip()
        if not notes:
            self._show_error("Notes are required.")
            self._notes_input.setFocus()
            return

        # Validation passed
        logger.debug(
            f"Adding treatment for client {self._client_id} on {date.today()}"
        )

        # Hide error if it was showing
        self._error_label.setVisible(False)

        # Accept dialog
        super().accept()

    def set_existing_treatment(self, treatment_id: int, notes: str) -> None:
        """
        Set up dialog to edit an existing treatment.

        Called when a treatment already exists for today's date.

        Args:
            treatment_id: ID of existing treatment to edit
            notes: Existing notes to pre-fill
        """
        self._existing_treatment_id = treatment_id
        self._notes_input.setPlainText(notes)
        self.setWindowTitle("Edit Treatment")
        logger.debug(f"Editing existing treatment {treatment_id}")

    def is_editing_existing(self) -> bool:
        """
        Check if dialog is editing an existing treatment.

        Returns:
            bool: True if editing existing, False if creating new
        """
        return self._existing_treatment_id is not None

    def get_existing_treatment_id(self) -> Optional[int]:
        """
        Get the ID of the existing treatment being edited.

        Returns:
            Optional[int]: Treatment ID if editing, None if creating new
        """
        return self._existing_treatment_id

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
                 - date: date (always today)
                 - notes: str

        Note:
            This should only be called after the dialog is accepted.
        """
        return {
            "client_id": self._client_id,
            "date": date.today(),
            "notes": self._notes_input.toPlainText().strip(),
        }
