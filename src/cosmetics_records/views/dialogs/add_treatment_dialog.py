# =============================================================================
# Cosmetics Records - Add Treatment Dialog
# =============================================================================
# This module provides a dialog for adding new treatment records.
#
# Key Features:
#   - Date picker (defaults to today)
#   - Notes text area (required)
#   - Prevents duplicate entries on same date
#
# Design Philosophy:
#   - Simple form with minimal required fields
#   - Date picker for flexibility
#   - Prevent duplicate treatments on same date
#   - Clear validation messages
#
# Usage Example:
#   dialog = AddTreatmentDialog(client_id, check_date_exists_fn)
#   if dialog.exec() == QDialog.DialogCode.Accepted:
#       treatment_data = dialog.get_treatment_data()
#       # Save treatment via controller
# =============================================================================

import logging
from datetime import date
from typing import Callable, Optional

from PyQt6.QtWidgets import (
    QFormLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .base_dialog import BaseDialog
from ..components.date_picker import DatePicker
from cosmetics_records.utils.localization import _

# Configure module logger
logger = logging.getLogger(__name__)


class AddTreatmentDialog(BaseDialog):
    """
    Dialog for adding a new treatment record.

    This dialog collects date and notes for a new treatment record.
    Includes date picker defaulting to today.

    Attributes:
        _client_id: Database ID of the client this treatment is for
        _date_picker: DatePicker for selecting treatment date
        _notes_input: QTextEdit for treatment notes
        _check_date_exists: Callback to check if entry exists for date
        _existing_treatment_id: If set, edit existing treatment instead
    """

    def __init__(
        self,
        client_id: int,
        check_date_exists: Optional[Callable[[date], bool]] = None,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the add treatment dialog.

        Args:
            client_id: Database ID of the client
            check_date_exists: Optional callback that returns True if a
                              treatment already exists for the given date
            parent: Optional parent widget
        """
        self._client_id = client_id
        self._check_date_exists = check_date_exists
        self._existing_treatment_id: Optional[int] = None

        # Initialize base dialog
        super().__init__(_("Add Treatment"), parent, width=500, height=400)

        logger.debug(f"AddTreatmentDialog initialized for client {client_id}")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Adds form fields for date and notes.

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

        # Notes (required)
        notes_label = QLabel(_("Notes: *"))
        layout.addWidget(notes_label)

        self._notes_input = QTextEdit()
        self._notes_input.setPlaceholderText(_("Enter treatment notes..."))
        self._notes_input.setMinimumHeight(150)
        layout.addWidget(self._notes_input)

        # Add stretch to push buttons to bottom
        layout.addStretch()

        # Save/Cancel buttons
        button_row = self.create_button_row(_("Save"), _("Cancel"))
        layout.addLayout(button_row)

    def accept(self) -> None:
        """
        Accept the dialog after validating input.

        Validates that date is selected, notes are provided, and no
        duplicate entry exists for the selected date.
        """
        # Validate date
        selected_date = self._date_picker.get_date()
        if not selected_date:
            self.show_error(_("Date is required."))
            return

        # Check for duplicate entry (only for new entries, not edits)
        if (
            self._check_date_exists
            and not self._existing_treatment_id
            and self._check_date_exists(selected_date)
        ):
            self.show_error(_("A treatment entry already exists for this date."))
            return

        # Validate notes
        notes = self._notes_input.toPlainText().strip()
        if not notes:
            self.show_error(_("Notes are required."))
            self._notes_input.setFocus()
            return

        # Validation passed
        logger.debug(
            f"Adding treatment for client {self._client_id} on {selected_date}"
        )

        # Hide error if it was showing
        self.hide_error()

        # Accept dialog
        super().accept()

    def set_existing_treatment(
        self, treatment_id: int, treatment_date: date, notes: str
    ) -> None:
        """
        Set up dialog to edit an existing treatment.

        Args:
            treatment_id: ID of existing treatment to edit
            treatment_date: Date of the existing treatment
            notes: Existing notes to pre-fill
        """
        self._existing_treatment_id = treatment_id
        self._date_picker.set_date(treatment_date)
        self._notes_input.setPlainText(notes)
        self.setWindowTitle(_("Edit Treatment"))
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

    def get_treatment_data(self) -> dict:
        """
        Get the entered treatment data.

        Returns:
            dict: Dictionary containing treatment data with keys:
                 - client_id: int
                 - date: date (selected date)
                 - notes: str

        Note:
            This should only be called after the dialog is accepted.
        """
        return {
            "client_id": self._client_id,
            "date": self._date_picker.get_date(),
            "notes": self._notes_input.toPlainText().strip(),
        }
