# =============================================================================
# Cosmetics Records - Mail Merge Export Dialog
# =============================================================================
# This module provides a dialog for configuring mail merge export options.
#
# Key Features:
#   - Option to sort by recent activity (most recent first)
#   - Option to limit number of exported clients
#   - Simple, focused interface
# =============================================================================

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .base_dialog import BaseDialog
from cosmetics_records.utils.localization import _

# Configure module logger
logger = logging.getLogger(__name__)


class MailMergeExportDialog(BaseDialog):
    """
    Dialog for configuring mail merge export options.

    Allows user to:
    - Sort clients by recent activity (most recent treatment/sale first)
    - Limit the number of clients exported

    Attributes:
        _sort_by_activity: Checkbox for sorting option
        _limit_enabled: Checkbox to enable/disable limit
        _limit_spinbox: Spinbox for limit value
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the mail merge export dialog.

        Args:
            parent: Optional parent widget
        """
        super().__init__(_("Export Options"), parent, width=400, height=250)
        logger.debug("MailMergeExportDialog initialized")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Args:
            layout: Layout to add content to
        """
        # Form layout for options
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Sort by recent activity checkbox
        self._sort_by_activity = QCheckBox(_("Sort by most recent activity"))
        self._sort_by_activity.setToolTip(
            _("Clients with recent treatments or sales appear first")
        )
        form_layout.addRow(self._sort_by_activity)

        # Limit checkbox and spinbox
        self._limit_enabled = QCheckBox(_("Limit number of clients"))
        self._limit_enabled.toggled.connect(self._on_limit_toggled)
        form_layout.addRow(self._limit_enabled)

        self._limit_spinbox = QSpinBox()
        self._limit_spinbox.setRange(1, 10000)
        self._limit_spinbox.setValue(100)
        self._limit_spinbox.setEnabled(False)
        self._limit_spinbox.setToolTip(_("Maximum number of clients to export"))
        form_layout.addRow(_("Maximum clients:"), self._limit_spinbox)

        layout.addLayout(form_layout)
        layout.addStretch()

        # Export/Cancel buttons
        button_row = self.create_button_row(_("Export"), _("Cancel"))
        layout.addLayout(button_row)

    def _on_limit_toggled(self, checked: bool) -> None:
        """
        Handle limit checkbox toggle.

        Args:
            checked: Whether the checkbox is checked
        """
        self._limit_spinbox.setEnabled(checked)

    def get_sort_by_recent_activity(self) -> bool:
        """
        Get whether to sort by recent activity.

        Returns:
            True if clients should be sorted by recent activity
        """
        return self._sort_by_activity.isChecked()

    def get_limit(self) -> Optional[int]:
        """
        Get the limit value if enabled.

        Returns:
            The limit value, or None if limit is not enabled
        """
        if self._limit_enabled.isChecked():
            return self._limit_spinbox.value()
        return None
