# =============================================================================
# Cosmetics Records - Edit Treatment Dialog
# =============================================================================
# This module provides a dialog for editing existing treatment records.
#
# Key Features:
#   - Pre-populated date and notes
#   - Delete button with confirmation
#   - Same validation as add dialog
#
# Design Philosophy:
#   - Consistent with add dialog
#   - Delete button for quick access
#   - Confirmation prevents accidents
#
# Usage Example:
#   dialog = EditTreatmentDialog(treatment_id, treatment_data)
#   result = dialog.exec()
#   if result == QDialog.DialogCode.Accepted:
#       if dialog.was_deleted():
#           # Delete treatment via controller
#       else:
#           updated_data = dialog.get_treatment_data()
#           # Update treatment via controller
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
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from .base_dialog import BaseDialog, ConfirmDialog
from ..components.date_picker import DatePicker

# Configure module logger
logger = logging.getLogger(__name__)


class EditTreatmentDialog(BaseDialog):
    """
    Dialog for editing an existing treatment record.

    This dialog allows editing treatment date and notes, and includes
    a delete button for removing the treatment.

    Attributes:
        _treatment_id: Database ID of the treatment being edited
        _treatment_data: Dictionary containing current treatment data
        _deleted: Flag indicating if treatment was deleted
        _date_picker: DatePicker for treatment date
        _notes_input: QTextEdit for treatment notes
        _error_label: QLabel for displaying validation errors
    """

    def __init__(
        self, treatment_id: int, treatment_data: dict, parent: Optional = None
    ):
        """
        Initialize the edit treatment dialog.

        Args:
            treatment_id: Database ID of the treatment to edit
            treatment_data: Dictionary with current treatment data containing:
                          - date: date
                          - notes: str
            parent: Optional parent widget
        """
        self._treatment_id = treatment_id
        self._treatment_data = treatment_data
        self._deleted = False

        # Initialize base dialog
        super().__init__("Edit Treatment", parent, width=500, height=450)

        # Populate fields with existing data
        self._populate_fields()

        logger.debug(f"EditTreatmentDialog initialized for treatment {treatment_id}")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Adds form fields for date and notes plus delete button.

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

        # Date (required)
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
        Populate form fields with existing treatment data.

        This is called after the UI is created to fill in current values.
        """
        # Set date
        treatment_date = self._treatment_data.get("date")
        if treatment_date:
            self._date_picker.set_date(treatment_date)

        # Set notes
        notes = self._treatment_data.get("notes", "")
        self._notes_input.setPlainText(notes)

    def accept(self) -> None:
        """
        Accept the dialog after validating input.

        Validates that date and notes are provided.
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

        # Validation passed
        logger.debug(f"Saving changes to treatment {self._treatment_id}")

        # Hide error if it was showing
        self._error_label.setVisible(False)

        # Accept dialog
        super().accept()

    def _on_delete_clicked(self) -> None:
        """
        Handle delete button click.

        Shows confirmation dialog before marking treatment for deletion.
        """
        # Get treatment date for confirmation message
        treatment_date = self._treatment_data.get("date")
        if isinstance(treatment_date, date):
            date_str = treatment_date.strftime("%B %d, %Y")
        else:
            date_str = str(treatment_date)

        # Show confirmation dialog
        confirm = ConfirmDialog(
            "Delete Treatment",
            f"Are you sure you want to delete the treatment from {date_str}?\n\n"
            f"This action cannot be undone.",
            ok_text="Delete",
            cancel_text="Cancel",
            parent=self,
            width=450,
            height=200,
        )

        if confirm.exec() == QDialog.DialogCode.Accepted:
            # User confirmed deletion
            logger.debug(f"Treatment {self._treatment_id} marked for deletion")
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
        Check if the treatment was marked for deletion.

        Returns:
            bool: True if delete button was clicked and confirmed

        Note:
            After accepting the dialog, check this to determine if the
            treatment should be deleted or updated.
        """
        return self._deleted

    def get_treatment_data(self) -> dict:
        """
        Get the updated treatment data.

        Returns:
            dict: Dictionary containing updated treatment data with keys:
                 - date: date
                 - notes: str

        Note:
            This should only be called after the dialog is accepted
            and was_deleted() returns False.
        """
        return {
            "date": self._date_picker.get_date(),
            "notes": self._notes_input.toPlainText().strip(),
        }
