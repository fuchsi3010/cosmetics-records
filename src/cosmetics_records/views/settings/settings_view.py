# =============================================================================
# Cosmetics Records - Settings View
# =============================================================================
# This module provides the application settings and preferences view.
#
# Key Features:
#   - Theme selection (Dark/Light/System)
#   - UI scaling (80%-200%)
#   - Language selection (English/Deutsch)
#   - Backup configuration and manual backup
#   - Export functionality (mail merge, all data)
#   - Database information display
#   - Audit log retention settings
#   - About section with version info
#
# Design Philosophy:
#   - Organized into logical sections with clear headings
#   - Immediate feedback for actions (backups, exports)
#   - Settings saved automatically on change
#   - Visual feedback for last backup time
#   - File dialogs for export destinations
#
# Layout:
#   Scrollable view with sections:
#   - Appearance (theme, UI scale)
#   - Language
#   - Backup (auto-backup, manual backup)
#   - Export (mail merge, all data)
#   - Database (path, size)
#   - Audit (retention, cleanup)
#   - About (version, copyright)
#
# Usage Example:
#   settings_view = SettingsView()
#   settings_view.settings_changed.connect(save_settings)
#   settings_view.theme_changed.connect(apply_theme)
# =============================================================================

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from cosmetics_records.config import Config
from cosmetics_records.database.connection import DatabaseConnection
from cosmetics_records.services.audit_service import AuditService
from cosmetics_records.services.backup_service import BackupService
from cosmetics_records.services.export_service import ExportService

# Configure module logger
logger = logging.getLogger(__name__)


class SectionHeader(QLabel):
    """
    Section header label with consistent styling.

    This is a reusable component for section titles in the settings view.
    """

    def __init__(self, text: str, parent: Optional[QWidget] = None):
        """
        Initialize a section header.

        Args:
            text: Header text to display
            parent: Optional parent widget
        """
        super().__init__(text, parent)
        self.setProperty("class", "section_header")  # CSS class
        self.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 16px;")


class SettingsView(QWidget):
    """
    Application settings and preferences view.

    This view provides a comprehensive settings interface organized into
    logical sections. Users can configure appearance, language, backups,
    exports, and other application preferences.

    Signals:
        settings_changed(): Emitted when any setting changes
        theme_changed(str): Emitted when theme changes (passes theme name)

    Attributes:
        config: Config singleton instance
        _backup_service: BackupService for backup operations
    """

    # Signals
    settings_changed = pyqtSignal()
    theme_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the settings view.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Get config instance
        self.config = Config.get_instance()

        # Initialize backup service
        # WHY: We need this for manual backups and displaying last backup time
        config_dir = self.config.get_config_dir()
        backup_dir = config_dir / "backups"
        db_path = config_dir / "cosmetics_records.db"
        self._backup_service = BackupService(str(db_path), str(backup_dir))

        # Set up the UI
        self._init_ui()

        # Load current settings
        self._load_settings()

        logger.debug("SettingsView initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates a scrollable view with all settings sections.
        """
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Container for all settings sections
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(32, 32, 32, 32)
        container_layout.setSpacing(24)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Page title
        title = QLabel("Settings")
        title.setProperty("class", "title")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        container_layout.addWidget(title)

        # Add all sections
        container_layout.addWidget(self._create_appearance_section())
        container_layout.addWidget(self._create_language_section())
        container_layout.addWidget(self._create_backup_section())
        container_layout.addWidget(self._create_export_section())
        container_layout.addWidget(self._create_database_section())
        container_layout.addWidget(self._create_audit_section())
        container_layout.addWidget(self._create_about_section())

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    def _create_appearance_section(self) -> QWidget:
        """
        Create the appearance settings section.

        Includes theme selector and UI scale slider.

        Returns:
            QWidget containing appearance settings
        """
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Section header
        layout.addWidget(SectionHeader("Appearance"))

        # Theme selector
        theme_label = QLabel("Theme:")
        layout.addWidget(theme_label)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(12)

        # Radio buttons for theme
        self._theme_dark = QRadioButton("Dark")
        self._theme_light = QRadioButton("Light")
        self._theme_system = QRadioButton("System")

        # Connect signals
        self._theme_dark.toggled.connect(lambda: self._on_theme_changed("dark"))
        self._theme_light.toggled.connect(lambda: self._on_theme_changed("light"))
        self._theme_system.toggled.connect(lambda: self._on_theme_changed("system"))

        theme_row.addWidget(self._theme_dark)
        theme_row.addWidget(self._theme_light)
        theme_row.addWidget(self._theme_system)
        theme_row.addStretch()

        layout.addLayout(theme_row)

        # UI Scale slider
        scale_label = QLabel("UI Scale:")
        layout.addWidget(scale_label)

        scale_row = QHBoxLayout()
        scale_row.setSpacing(12)

        # Slider for UI scale (80% - 200%)
        # WHY 80-200 range: Reasonable bounds for accessibility
        self._scale_slider = QSlider(Qt.Orientation.Horizontal)
        self._scale_slider.setMinimum(80)  # 80%
        self._scale_slider.setMaximum(200)  # 200%
        self._scale_slider.setSingleStep(10)
        self._scale_slider.setPageStep(20)
        self._scale_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._scale_slider.setTickInterval(20)

        # Connect slider to update label
        self._scale_slider.valueChanged.connect(self._on_scale_slider_changed)

        # Label showing current scale percentage
        self._scale_label = QLabel("100%")
        self._scale_label.setFixedWidth(50)

        # Apply button
        self._scale_apply_btn = QPushButton("Apply")
        self._scale_apply_btn.setFixedWidth(80)
        self._scale_apply_btn.clicked.connect(self._on_scale_apply)

        scale_row.addWidget(self._scale_slider, stretch=1)
        scale_row.addWidget(self._scale_label)
        scale_row.addWidget(self._scale_apply_btn)

        layout.addLayout(scale_row)

        return section

    def _create_language_section(self) -> QWidget:
        """
        Create the language settings section.

        Includes language selector with note about restart requirement.

        Returns:
            QWidget containing language settings
        """
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Section header
        layout.addWidget(SectionHeader("Language"))

        # Language selector
        lang_label = QLabel("Language:")
        layout.addWidget(lang_label)

        lang_row = QHBoxLayout()
        lang_row.setSpacing(12)

        # Radio buttons for language
        # WHY flag emojis: Visual identification of language
        self._lang_en = QRadioButton("English")
        self._lang_de = QRadioButton("Deutsch")

        # Connect signals
        self._lang_en.toggled.connect(lambda: self._on_language_changed("en"))
        self._lang_de.toggled.connect(lambda: self._on_language_changed("de"))

        lang_row.addWidget(self._lang_en)
        lang_row.addWidget(self._lang_de)
        lang_row.addStretch()

        layout.addLayout(lang_row)

        # Note about restart
        restart_note = QLabel("Note: Restart required for full effect")
        restart_note.setProperty("class", "secondary")
        restart_note.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(restart_note)

        return section

    def _create_backup_section(self) -> QWidget:
        """
        Create the backup settings section.

        Includes auto-backup settings, manual backup button, and backup info.

        Returns:
            QWidget containing backup settings
        """
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Section header
        layout.addWidget(SectionHeader("Backup"))

        # Auto-backup checkbox
        self._auto_backup_check = QCheckBox("Auto-backup on startup")
        self._auto_backup_check.toggled.connect(self._on_auto_backup_toggled)
        layout.addWidget(self._auto_backup_check)

        # Backup interval
        interval_row = QHBoxLayout()
        interval_row.setSpacing(12)

        interval_label = QLabel("Backup interval:")
        self._backup_interval_spin = QSpinBox()
        self._backup_interval_spin.setMinimum(1)
        self._backup_interval_spin.setMaximum(1440)  # Max 1 day
        self._backup_interval_spin.setSuffix(" minutes")
        self._backup_interval_spin.valueChanged.connect(
            self._on_backup_interval_changed
        )

        interval_row.addWidget(interval_label)
        interval_row.addWidget(self._backup_interval_spin)
        interval_row.addStretch()

        layout.addLayout(interval_row)

        # Backup retention
        retention_row = QHBoxLayout()
        retention_row.setSpacing(12)

        retention_label = QLabel("Backup retention:")
        self._backup_retention_spin = QSpinBox()
        self._backup_retention_spin.setMinimum(1)
        self._backup_retention_spin.setMaximum(100)
        self._backup_retention_spin.setSuffix(" backups")
        self._backup_retention_spin.valueChanged.connect(
            self._on_backup_retention_changed
        )

        retention_row.addWidget(retention_label)
        retention_row.addWidget(self._backup_retention_spin)
        retention_row.addStretch()

        layout.addLayout(retention_row)

        # Manual backup button and last backup time
        backup_row = QHBoxLayout()
        backup_row.setSpacing(12)

        manual_backup_btn = QPushButton("Create Backup Now")
        manual_backup_btn.setFixedWidth(150)
        manual_backup_btn.clicked.connect(self._on_manual_backup)

        self._last_backup_label = QLabel("Last backup: Never")
        self._last_backup_label.setProperty("class", "secondary")

        backup_row.addWidget(manual_backup_btn)
        backup_row.addWidget(self._last_backup_label)
        backup_row.addStretch()

        layout.addLayout(backup_row)

        # Open backups folder button
        open_folder_btn = QPushButton("Open Backups Folder")
        open_folder_btn.setFixedWidth(150)
        open_folder_btn.clicked.connect(self._on_open_backups_folder)
        layout.addWidget(open_folder_btn)

        return section

    def _create_export_section(self) -> QWidget:
        """
        Create the export settings section.

        Includes buttons for various export operations.

        Returns:
            QWidget containing export settings
        """
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Section header
        layout.addWidget(SectionHeader("Export"))

        # Export for mail merge button
        mail_merge_btn = QPushButton("Export Clients for Mail Merge")
        mail_merge_btn.setFixedWidth(220)
        mail_merge_btn.clicked.connect(self._on_export_mail_merge)
        layout.addWidget(mail_merge_btn)

        # Export all data button
        export_all_btn = QPushButton("Export All Data")
        export_all_btn.setFixedWidth(220)
        export_all_btn.clicked.connect(self._on_export_all_data)
        layout.addWidget(export_all_btn)

        return section

    def _create_database_section(self) -> QWidget:
        """
        Create the database information section.

        Displays database path and size (read-only).

        Returns:
            QWidget containing database information
        """
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Section header
        layout.addWidget(SectionHeader("Database"))

        # Database path
        path_label = QLabel("Database path:")
        layout.addWidget(path_label)

        config_dir = self.config.get_config_dir()
        db_path = config_dir / "cosmetics_records.db"

        self._db_path_label = QLabel(str(db_path))
        self._db_path_label.setProperty("class", "monospace")
        self._db_path_label.setStyleSheet("color: gray; font-family: monospace;")
        self._db_path_label.setWordWrap(True)
        layout.addWidget(self._db_path_label)

        # Database size
        self._db_size_label = QLabel("Size: Calculating...")
        self._db_size_label.setProperty("class", "secondary")
        layout.addWidget(self._db_size_label)

        # Update database size
        self._update_database_size()

        return section

    def _create_audit_section(self) -> QWidget:
        """
        Create the audit log settings section.

        Includes retention settings and cleanup button.

        Returns:
            QWidget containing audit settings
        """
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Section header
        layout.addWidget(SectionHeader("Audit Log"))

        # Audit retention
        retention_row = QHBoxLayout()
        retention_row.setSpacing(12)

        retention_label = QLabel("Audit log retention:")
        self._audit_retention_spin = QSpinBox()
        self._audit_retention_spin.setMinimum(100)
        self._audit_retention_spin.setMaximum(10000)
        self._audit_retention_spin.setValue(1000)  # Default
        self._audit_retention_spin.setSuffix(" entries")
        self._audit_retention_spin.setSingleStep(100)

        retention_row.addWidget(retention_label)
        retention_row.addWidget(self._audit_retention_spin)
        retention_row.addStretch()

        layout.addLayout(retention_row)

        # Cleanup button
        cleanup_btn = QPushButton("Clean Up Now")
        cleanup_btn.setFixedWidth(150)
        cleanup_btn.clicked.connect(self._on_audit_cleanup)
        layout.addWidget(cleanup_btn)

        return section

    def _create_about_section(self) -> QWidget:
        """
        Create the about section.

        Displays version and copyright information.

        Returns:
            QWidget containing about information
        """
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Section header
        layout.addWidget(SectionHeader("About"))

        # Version
        version_label = QLabel("Cosmetics Records v1.0")
        version_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(version_label)

        # Copyright
        copyright_label = QLabel(f"Copyright 2024")
        copyright_label.setProperty("class", "secondary")
        copyright_label.setStyleSheet("color: gray;")
        layout.addWidget(copyright_label)

        return section

    def _load_settings(self) -> None:
        """
        Load current settings from config and update UI.

        This is called on initialization to populate the UI with current values.
        """
        # Theme
        theme = self.config.theme
        if theme == "dark":
            self._theme_dark.setChecked(True)
        elif theme == "light":
            self._theme_light.setChecked(True)
        else:
            self._theme_system.setChecked(True)

        # UI Scale
        scale_percent = int(self.config.ui_scale * 100)
        self._scale_slider.setValue(scale_percent)
        self._scale_label.setText(f"{scale_percent}%")

        # Language
        language = self.config.language
        if language == "en":
            self._lang_en.setChecked(True)
        else:
            self._lang_de.setChecked(True)

        # Backup settings
        self._auto_backup_check.setChecked(self.config.auto_backup)
        self._backup_interval_spin.setValue(self.config.backup_interval_minutes)
        self._backup_retention_spin.setValue(self.config.backup_retention_count)

        # Last backup time
        self._update_last_backup_label()

    def _update_last_backup_label(self) -> None:
        """
        Update the last backup time label.

        Formats the timestamp in a human-readable way.
        """
        last_backup = self.config.last_backup_time
        if last_backup:
            # Format as relative time or absolute time
            now = datetime.now()
            delta = now - last_backup

            if delta.total_seconds() < 60:
                time_str = "just now"
            elif delta.total_seconds() < 3600:
                minutes = int(delta.total_seconds() / 60)
                time_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif delta.total_seconds() < 86400:
                hours = int(delta.total_seconds() / 3600)
                time_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                time_str = last_backup.strftime("%Y-%m-%d %H:%M")

            self._last_backup_label.setText(f"Last backup: {time_str}")
        else:
            self._last_backup_label.setText("Last backup: Never")

    def _update_database_size(self) -> None:
        """
        Update the database size label.

        Calculates and displays the database file size in a human-readable format.
        """
        try:
            config_dir = self.config.get_config_dir()
            db_path = config_dir / "cosmetics_records.db"

            if db_path.exists():
                size_bytes = db_path.stat().st_size

                # Format size in human-readable format
                if size_bytes < 1024:
                    size_str = f"{size_bytes} bytes"
                elif size_bytes < 1024 * 1024:
                    size_kb = size_bytes / 1024
                    size_str = f"{size_kb:.1f} KB"
                else:
                    size_mb = size_bytes / (1024 * 1024)
                    size_str = f"{size_mb:.1f} MB"

                self._db_size_label.setText(f"Size: {size_str}")
            else:
                self._db_size_label.setText("Size: Database not found")
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            self._db_size_label.setText("Size: Error calculating")

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_theme_changed(self, theme: str) -> None:
        """
        Handle theme selection change.

        Args:
            theme: Selected theme ("dark", "light", or "system")
        """
        # Only process if actually toggled on (not off)
        sender = self.sender()
        if not sender.isChecked():
            return

        logger.info(f"Theme changed to: {theme}")

        # Save to config
        self.config.theme = theme
        self.config.save()

        # Emit signals
        self.settings_changed.emit()
        self.theme_changed.emit(theme)

    def _on_scale_slider_changed(self, value: int) -> None:
        """
        Handle UI scale slider change.

        Updates the percentage label as user drags the slider.

        Args:
            value: Slider value (80-200 representing 80%-200%)
        """
        self._scale_label.setText(f"{value}%")

    def _on_scale_apply(self) -> None:
        """
        Handle UI scale apply button click.

        Saves the new scale and emits settings_changed signal.
        """
        scale_percent = self._scale_slider.value()
        scale_float = scale_percent / 100.0

        logger.info(f"UI scale changed to: {scale_percent}%")

        # Save to config
        self.config.ui_scale = scale_float
        self.config.save()

        # Emit signal
        self.settings_changed.emit()

        # Show confirmation
        QMessageBox.information(
            self,
            "UI Scale Changed",
            "UI scale has been changed. Please restart the application for the change to take full effect.",
        )

    def _on_language_changed(self, language: str) -> None:
        """
        Handle language selection change.

        Args:
            language: Selected language code ("en" or "de")
        """
        # Only process if actually toggled on (not off)
        sender = self.sender()
        if not sender.isChecked():
            return

        logger.info(f"Language changed to: {language}")

        # Save to config
        self.config.language = language
        self.config.save()

        # Emit signal
        self.settings_changed.emit()

    def _on_auto_backup_toggled(self, checked: bool) -> None:
        """
        Handle auto-backup checkbox toggle.

        Args:
            checked: Whether auto-backup is enabled
        """
        logger.info(f"Auto-backup toggled: {checked}")

        # Save to config
        self.config.auto_backup = checked
        self.config.save()

        # Emit signal
        self.settings_changed.emit()

    def _on_backup_interval_changed(self, value: int) -> None:
        """
        Handle backup interval change.

        Args:
            value: Interval in minutes
        """
        logger.info(f"Backup interval changed to: {value} minutes")

        # Save to config
        self.config.backup_interval_minutes = value
        self.config.save()

        # Emit signal
        self.settings_changed.emit()

    def _on_backup_retention_changed(self, value: int) -> None:
        """
        Handle backup retention change.

        Args:
            value: Number of backups to retain
        """
        logger.info(f"Backup retention changed to: {value} backups")

        # Save to config
        self.config.backup_retention_count = value
        self.config.save()

        # Emit signal
        self.settings_changed.emit()

    def _on_manual_backup(self) -> None:
        """
        Handle manual backup button click.

        Creates a backup and updates the last backup time.
        """
        try:
            logger.info("Creating manual backup...")

            # Create backup
            backup_path = self._backup_service.create_backup()

            # Update last backup time in config
            self.config.last_backup_time = datetime.now()
            self.config.save()

            # Update label
            self._update_last_backup_label()

            # Show success message
            QMessageBox.information(
                self,
                "Backup Created",
                f"Backup created successfully:\n{backup_path}",
            )

            logger.info(f"Manual backup created: {backup_path}")

        except Exception as e:
            logger.error(f"Manual backup failed: {e}")
            QMessageBox.critical(
                self,
                "Backup Failed",
                f"Failed to create backup:\n{str(e)}",
            )

    def _on_open_backups_folder(self) -> None:
        """
        Handle open backups folder button click.

        Opens the backups directory in the system file manager.
        """
        config_dir = self.config.get_config_dir()
        backup_dir = config_dir / "backups"

        # Ensure directory exists
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Open in file manager
        # WHY os.startfile/xdg-open: Platform-specific way to open folders
        try:
            import platform
            import subprocess

            system = platform.system()
            if system == "Windows":
                os.startfile(backup_dir)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(backup_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(backup_dir)])

            logger.info(f"Opened backups folder: {backup_dir}")
        except Exception as e:
            logger.error(f"Failed to open backups folder: {e}")
            QMessageBox.warning(
                self,
                "Cannot Open Folder",
                f"Could not open backups folder:\n{str(backup_dir)}",
            )

    def _on_export_mail_merge(self) -> None:
        """
        Handle export clients for mail merge button click.

        Shows file save dialog and exports client data to CSV.
        """
        # Show file save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Clients for Mail Merge",
            str(Path.home() / "clients_mailmerge.csv"),
            "CSV Files (*.csv);;All Files (*)",
        )

        if not file_path:
            return  # User cancelled

        try:
            logger.info(f"Exporting clients for mail merge to: {file_path}")

            # Export using ExportService
            with DatabaseConnection() as db:
                export_service = ExportService(db)
                count = export_service.export_clients_for_mail_merge(file_path)

            # Show success message
            QMessageBox.information(
                self,
                "Export Complete",
                f"Exported {count} clients for mail merge:\n{file_path}",
            )

            logger.info(f"Mail merge export complete: {count} clients")

        except Exception as e:
            logger.error(f"Mail merge export failed: {e}")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export clients:\n{str(e)}",
            )

    def _on_export_all_data(self) -> None:
        """
        Handle export all data button click.

        Shows directory selection dialog and exports all tables to CSV files.
        """
        # Show directory selection dialog
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            str(Path.home()),
        )

        if not directory:
            return  # User cancelled

        try:
            logger.info(f"Exporting all data to: {directory}")

            export_dir = Path(directory)

            # Export all tables using ExportService
            with DatabaseConnection() as db:
                export_service = ExportService(db)

                # Export clients
                clients_path = export_dir / "clients.csv"
                clients_count = export_service.export_all_clients(str(clients_path))

                # Export treatments
                treatments_path = export_dir / "treatments.csv"
                treatments_count = export_service.export_treatments(
                    str(treatments_path)
                )

                # Export inventory
                inventory_path = export_dir / "inventory.csv"
                inventory_count = export_service.export_inventory(str(inventory_path))

                # Export audit logs (last 90 days)
                audit_path = export_dir / "audit_logs.csv"
                audit_count = export_service.export_audit_logs(str(audit_path), days=90)

            # Show success message
            message = (
                f"All data exported successfully to:\n{directory}\n\n"
                f"- {clients_count} clients\n"
                f"- {treatments_count} treatments\n"
                f"- {inventory_count} inventory items\n"
                f"- {audit_count} audit logs (last 90 days)"
            )

            QMessageBox.information(
                self,
                "Export Complete",
                message,
            )

            logger.info(f"All data export complete")

        except Exception as e:
            logger.error(f"Export all data failed: {e}")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export data:\n{str(e)}",
            )

    def _on_audit_cleanup(self) -> None:
        """
        Handle audit cleanup button click.

        Cleans up old audit logs based on retention setting.
        """
        retention_count = self._audit_retention_spin.value()

        try:
            logger.info(f"Cleaning up audit logs (retention: {retention_count})...")

            # Cleanup using AuditService
            with DatabaseConnection() as db:
                audit_service = AuditService(db)
                deleted_count = audit_service.cleanup_old_logs(retention_count)

            # Show success message
            if deleted_count > 0:
                QMessageBox.information(
                    self,
                    "Cleanup Complete",
                    f"Deleted {deleted_count} old audit log entries.\n"
                    f"Kept {retention_count} most recent entries.",
                )
            else:
                QMessageBox.information(
                    self,
                    "Cleanup Complete",
                    "No audit logs needed cleanup.\n"
                    f"All logs are within retention limit ({retention_count} entries).",
                )

            logger.info(f"Audit cleanup complete: {deleted_count} entries deleted")

        except Exception as e:
            logger.error(f"Audit cleanup failed: {e}")
            QMessageBox.critical(
                self,
                "Cleanup Failed",
                f"Failed to cleanup audit logs:\n{str(e)}",
            )
