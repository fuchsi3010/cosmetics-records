# =============================================================================
# Cosmetics Records - Backup Management Dialog
# =============================================================================
# Dialog for managing database backups: view, verify, restore, and delete.
#
# Key Features:
#   - List all available backups with date and size
#   - Verify backup integrity (ZIP structure and CRC check)
#   - Restore database from a selected backup
#   - Delete individual backups
#
# UI Layout:
#   +------------------------------------------+
#   | Manage Backups                       [X] |
#   +------------------------------------------+
#   | +--------------------------------------+ |
#   | | Filename          | Date    | Size   | |
#   | | backup_20241...   | Nov 30  | 1.2 MB | |
#   | | backup_20241...   | Nov 29  | 1.1 MB | |
#   | +--------------------------------------+ |
#   |                                          |
#   | Selected: backup_20241130_143000.zip     |
#   | Status: Valid                            |
#   |                                          |
#   |    [Verify] [Restore] [Delete]   [Close] |
#   +------------------------------------------+
#
# Usage Example:
#   dialog = BackupManagementDialog(parent=main_window)
#   dialog.exec()
# =============================================================================

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cosmetics_records.config import Config
from cosmetics_records.services.backup_service import BackupService
from cosmetics_records.utils.localization import _
from .base_dialog import BaseDialog

# Configure module logger
logger = logging.getLogger(__name__)


class BackupManagementDialog(BaseDialog):
    """
    Dialog for managing database backups.

    Allows users to:
    - View all available backups with date and size
    - Verify backup integrity
    - Restore from a selected backup
    - Delete individual backups

    Attributes:
        _config: Application configuration instance
        _backup_service: Service for backup operations
        _selected_backup: Currently selected backup info dict
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the backup management dialog.

        Args:
            parent: Optional parent widget
        """
        # Initialize services before calling super().__init__
        # which will call _create_content()
        self._config = Config.get_instance()
        config_dir = self._config.get_config_dir()
        backup_dir = config_dir / "backups"
        db_path = config_dir / "cosmetics_records.db"
        self._backup_service = BackupService(str(db_path), str(backup_dir))
        self._selected_backup: Optional[dict] = None

        super().__init__(
            title=_("Manage Backups"),
            parent=parent,
            width=650,
            height=500,
        )

        logger.debug("BackupManagementDialog initialized")

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        Args:
            layout: Layout to add content to
        """
        # Backup table
        self._create_backup_table(layout)

        # Selection info
        self._create_selection_info(layout)

        # Button row
        self._create_buttons(layout)

        # Load backups
        self._refresh_backup_list()

    def _create_backup_table(self, layout: QVBoxLayout) -> None:
        """
        Create the backup list table.

        Args:
            layout: Parent layout
        """
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(
            [
                _("Filename"),
                _("Date"),
                _("Size"),
            ]
        )

        # Configure table
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)

        # Column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        # Connect selection
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self._table)

    def _create_selection_info(self, layout: QVBoxLayout) -> None:
        """
        Create the selection info area.

        Args:
            layout: Parent layout
        """
        self._selection_label = QLabel(_("No backup selected"))
        self._selection_label.setStyleSheet("color: #888888;")
        layout.addWidget(self._selection_label)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #888888;")
        layout.addWidget(self._status_label)

    def _create_buttons(self, layout: QVBoxLayout) -> None:
        """
        Create the button row.

        Args:
            layout: Parent layout
        """
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        # Action buttons (left side)
        self._verify_btn = QPushButton(_("Verify"))
        self._verify_btn.setMinimumWidth(80)
        self._verify_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._verify_btn.setEnabled(False)
        self._verify_btn.clicked.connect(self._on_verify)
        button_layout.addWidget(self._verify_btn)

        self._restore_btn = QPushButton(_("Restore"))
        self._restore_btn.setMinimumWidth(80)
        self._restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._restore_btn.setEnabled(False)
        self._restore_btn.clicked.connect(self._on_restore)
        button_layout.addWidget(self._restore_btn)

        self._delete_btn = QPushButton(_("Delete"))
        self._delete_btn.setMinimumWidth(80)
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.setEnabled(False)
        self._delete_btn.setProperty("class", "danger")
        self._delete_btn.clicked.connect(self._on_delete)
        button_layout.addWidget(self._delete_btn)

        button_layout.addStretch()

        # Close button (right side)
        close_btn = QPushButton(_("Close"))
        close_btn.setMinimumWidth(80)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _refresh_backup_list(self) -> None:
        """Refresh the backup list from disk."""
        backups = self._backup_service.get_backups()

        self._table.setRowCount(len(backups))

        for row, backup in enumerate(backups):
            # Filename
            filename_item = QTableWidgetItem(backup["filename"])
            filename_item.setData(Qt.ItemDataRole.UserRole, backup)
            self._table.setItem(row, 0, filename_item)

            # Date
            date_str = backup["created"].strftime("%Y-%m-%d %H:%M")
            self._table.setItem(row, 1, QTableWidgetItem(date_str))

            # Size
            size_str = self._format_size(backup["size"])
            self._table.setItem(row, 2, QTableWidgetItem(size_str))

        # Reset selection state
        self._selected_backup = None
        self._update_buttons()
        self._selection_label.setText(_("No backup selected"))
        self._status_label.setText("")

    def _format_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable form.

        Args:
            size_bytes: Size in bytes

        Returns:
            Human-readable size string (e.g., "1.2 MB")
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def _on_selection_changed(self) -> None:
        """Handle table selection change."""
        selected = self._table.selectedItems()
        if selected:
            row = selected[0].row()
            item = self._table.item(row, 0)
            self._selected_backup = item.data(Qt.ItemDataRole.UserRole)
            self._selection_label.setText(
                _("Selected:") + f" {self._selected_backup['filename']}"
            )
            self._status_label.setText("")
            self._status_label.setStyleSheet("color: #888888;")
        else:
            self._selected_backup = None
            self._selection_label.setText(_("No backup selected"))
            self._status_label.setText("")

        self._update_buttons()

    def _update_buttons(self) -> None:
        """Update button enabled states based on selection."""
        has_selection = self._selected_backup is not None
        self._verify_btn.setEnabled(has_selection)
        self._restore_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)

    def _on_verify(self) -> None:
        """Handle Verify button click."""
        if not self._selected_backup:
            return

        logger.info(f"Verifying backup: {self._selected_backup['filename']}")

        is_valid, message = self._backup_service.verify_backup(
            self._selected_backup["path"]
        )

        if is_valid:
            self._status_label.setText(_("Status:") + f" {_('Valid')}")
            self._status_label.setStyleSheet("color: #66ff66;")
            logger.info("Backup verification passed")
        else:
            self._status_label.setText(_("Status:") + f" {message}")
            self._status_label.setStyleSheet("color: #ff6666;")
            logger.warning(f"Backup verification failed: {message}")

    def _on_restore(self) -> None:
        """Handle Restore button click."""
        if not self._selected_backup:
            return

        # Confirm restore
        reply = QMessageBox.warning(
            self,
            _("Confirm Restore"),
            _("Are you sure you want to restore from this backup?")
            + "\n\n"
            + self._selected_backup["filename"]
            + "\n\n"
            + _(
                "This will replace the current database. "
                "A pre-restore backup will be created automatically."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        logger.info(f"Restoring backup: {self._selected_backup['filename']}")

        # Perform restore
        success = self._backup_service.restore_backup(self._selected_backup["path"])

        if success:
            QMessageBox.information(
                self,
                _("Restore Complete"),
                _("Database restored successfully.")
                + "\n\n"
                + _("Please restart the application for changes to take effect."),
            )
            logger.info("Backup restore completed successfully")
            self.accept()
        else:
            QMessageBox.critical(
                self,
                _("Restore Failed"),
                _("Failed to restore database from backup."),
            )
            logger.error("Backup restore failed")

    def _on_delete(self) -> None:
        """Handle Delete button click."""
        if not self._selected_backup:
            return

        # Confirm delete
        reply = QMessageBox.warning(
            self,
            _("Confirm Delete"),
            _("Are you sure you want to delete this backup?")
            + "\n\n"
            + self._selected_backup["filename"]
            + "\n\n"
            + _("This action cannot be undone."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        logger.info(f"Deleting backup: {self._selected_backup['filename']}")

        # Perform delete
        success = self._backup_service.delete_backup(self._selected_backup["path"])

        if success:
            self._refresh_backup_list()
            self._status_label.setText(_("Backup deleted"))
            self._status_label.setStyleSheet("color: #66ff66;")
            logger.info("Backup deleted successfully")
        else:
            QMessageBox.critical(
                self,
                _("Delete Failed"),
                _("Failed to delete backup."),
            )
            logger.error("Backup deletion failed")
