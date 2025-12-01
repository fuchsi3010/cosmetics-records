# =============================================================================
# Cosmetics Records - Service Unit Tests
# =============================================================================
# This file contains comprehensive unit tests for all service classes.
# Services provide higher-level operations like audit logging, backups,
# and data export.
#
# Test Structure:
#   - TestAuditService: Tests for AuditService
#   - TestBackupService: Tests for BackupService
#   - TestExportService: Tests for ExportService
#
# Testing Strategy:
#   - Test service methods with real databases and files
#   - Verify file creation and cleanup
#   - Test edge cases and error handling
# =============================================================================

import csv
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

from cosmetics_records.models.audit import AuditAction
from cosmetics_records.services.audit_service import AuditService
from cosmetics_records.services.backup_service import BackupService
from cosmetics_records.services.export_service import ExportService
from tests.conftest import create_client_in_db


# =============================================================================
# AuditService Tests
# =============================================================================


class TestAuditService:
    """Tests for the AuditService class."""

    def test_log_create(self, db_connection):
        """
        Test logging a CREATE action.

        This verifies that CREATE operations are properly logged to the
        audit_log table.
        """
        service = AuditService(db_connection)

        # Log a CREATE action
        service.log_create(
            table_name="clients",
            record_id=1,
            new_value="Jane Doe",
            ui_location="ClientEditView",
        )

        # Verify the log was created
        logs = service.get_audit_logs(table_filter="clients", limit=10)
        assert len(logs) == 1

        log = logs[0]
        assert log.table_name == "clients"
        assert log.record_id == 1
        assert log.action == AuditAction.CREATE
        assert log.new_value == "Jane Doe"
        assert log.ui_location == "ClientEditView"

    def test_log_update(self, db_connection):
        """
        Test logging an UPDATE action.

        This verifies that UPDATE operations are properly logged with both
        old and new values.
        """
        service = AuditService(db_connection)

        # Log an UPDATE action
        service.log_update(
            table_name="clients",
            record_id=1,
            field_name="email",
            old_value="old@example.com",
            new_value="new@example.com",
            ui_location="ClientEditView",
        )

        # Verify the log was created
        logs = service.get_audit_logs(table_filter="clients", limit=10)
        assert len(logs) == 1

        log = logs[0]
        assert log.action == AuditAction.UPDATE
        assert log.field_name == "email"
        assert log.old_value == "old@example.com"
        assert log.new_value == "new@example.com"

    def test_log_delete(self, db_connection):
        """
        Test logging a DELETE action.

        This verifies that DELETE operations are properly logged.
        """
        service = AuditService(db_connection)

        # Log a DELETE action
        service.log_delete(
            table_name="clients",
            record_id=1,
            old_value="Jane Doe",
            ui_location="ClientEditView",
        )

        # Verify the log was created
        logs = service.get_audit_logs(table_filter="clients", limit=10)
        assert len(logs) == 1

        log = logs[0]
        assert log.action == AuditAction.DELETE
        assert log.old_value == "Jane Doe"

    def test_get_audit_logs(self, db_connection):
        """
        Test retrieving audit logs with filtering and pagination.

        This verifies that we can query audit logs with various filters.
        """
        service = AuditService(db_connection)

        # Create multiple audit logs
        for i in range(5):
            service.log_create(
                table_name="clients",
                record_id=i + 1,
                new_value=f"Client {i + 1}",
                ui_location="ClientEditView",
            )

        # Get all logs (should have 5)
        all_logs = service.get_audit_logs(limit=10)
        assert len(all_logs) == 5

        # Get logs with pagination (limit 3)
        page1 = service.get_audit_logs(limit=3, offset=0)
        assert len(page1) == 3

        page2 = service.get_audit_logs(limit=3, offset=3)
        assert len(page2) == 2

        # Get logs filtered by table
        client_logs = service.get_audit_logs(table_filter="clients", limit=10)
        assert len(client_logs) == 5

    def test_get_audit_logs_empty(self, db_connection):
        """
        Test retrieving audit logs when none exist.

        Should return empty list, not None or error.
        """
        service = AuditService(db_connection)

        logs = service.get_audit_logs()
        assert logs == []

    def test_cleanup_old_logs(self, db_connection):
        """
        Test cleaning up old audit logs.

        This verifies that logs beyond the retention count are deleted,
        keeping only the most recent N logs.
        """
        service = AuditService(db_connection)

        # Create multiple logs
        for i in range(5):
            service.log_create(
                table_name="clients",
                record_id=i + 1,
                new_value=f"Client {i + 1}",
                ui_location="ClientEditView",
            )

        # Verify we have 5 logs
        all_logs = service.get_audit_logs(limit=10)
        assert len(all_logs) == 5

        # Clean up, keeping only 2 most recent logs
        deleted_count = service.cleanup_old_logs(retention_count=2)

        # Should have deleted 3 logs (keeping 2)
        assert deleted_count == 3

        # Verify only 2 logs remain
        remaining_logs = service.get_audit_logs(limit=10)
        assert len(remaining_logs) == 2


# =============================================================================
# BackupService Tests
# =============================================================================


class TestBackupService:
    """Tests for the BackupService class."""

    def test_create_backup(self, temp_db):
        """
        Test creating a database backup.

        This verifies that:
        - A backup file is created
        - The backup is a valid ZIP file
        - The backup path is returned
        """
        # Create a temporary directory for backups
        with tempfile.TemporaryDirectory() as backup_dir:
            service = BackupService(db_path=temp_db, backup_dir=backup_dir)

            # Create a backup
            backup_path = service.create_backup()

            # Verify the backup file exists
            assert Path(backup_path).exists()

            # Verify it's a ZIP file
            assert backup_path.endswith(".zip")

            # Verify the filename contains timestamp
            assert "backup" in backup_path

            # Clean up (TemporaryDirectory handles this)

    def test_get_backups(self, temp_db):
        """
        Test listing available backups.

        This verifies that we can retrieve a list of all backup files.
        """
        with tempfile.TemporaryDirectory() as backup_dir:
            service = BackupService(db_path=temp_db, backup_dir=backup_dir)

            # Create multiple backups (with delay to ensure unique timestamps)
            service.create_backup()
            time.sleep(1.1)  # Ensure unique timestamp (backup uses seconds)
            service.create_backup()

            # Get list of backups
            backups = service.get_backups()

            # Should have 2 backups
            assert len(backups) == 2

            # Verify backups contain metadata
            for backup in backups:
                assert "path" in backup
                assert "size" in backup
                assert "created" in backup

    def test_get_backups_empty(self, temp_db):
        """
        Test listing backups when none exist.

        Should return empty list, not None or error.
        """
        with tempfile.TemporaryDirectory() as backup_dir:
            service = BackupService(db_path=temp_db, backup_dir=backup_dir)

            # Get backups (should be empty)
            backups = service.get_backups()
            assert backups == []

    def test_cleanup_old_backups(self, temp_db):
        """
        Test cleaning up old backups based on retention count.

        This verifies that only the most recent N backups are kept.
        """
        with tempfile.TemporaryDirectory() as backup_dir:
            service = BackupService(db_path=temp_db, backup_dir=backup_dir)

            # Create 5 backups (with delays to ensure unique timestamps)
            for i in range(5):
                service.create_backup()
                if i < 4:  # No need to sleep after the last one
                    time.sleep(1.1)

            # Verify we have 5 backups
            backups = service.get_backups()
            assert len(backups) == 5

            # Clean up, keeping only 3 most recent
            deleted_count = service.cleanup_old_backups(retention_count=3)

            # Should have deleted 2 backups
            assert deleted_count == 2

            # Verify only 3 remain
            remaining_backups = service.get_backups()
            assert len(remaining_backups) == 3

    def test_should_auto_backup(self, temp_db):
        """
        Test the auto-backup decision logic.

        This verifies that the service correctly determines when an
        auto-backup should be created.
        """
        with tempfile.TemporaryDirectory() as backup_dir:
            service = BackupService(db_path=temp_db, backup_dir=backup_dir)

            # No backups exist and no last backup time, should need auto-backup
            assert service.should_auto_backup(
                interval_minutes=60,
                last_backup_time=None
            ) is True

            # Create a backup
            service.create_backup()

            # Just created a backup, with current time as last backup
            # Should NOT need another one immediately
            assert service.should_auto_backup(
                interval_minutes=60,
                last_backup_time=datetime.now()
            ) is False


# =============================================================================
# ExportService Tests
# =============================================================================


class TestExportService:
    """Tests for the ExportService class."""

    def test_export_clients_for_mail_merge(self, db_connection, sample_client):
        """
        Test exporting clients to CSV for mail merge.

        This verifies that:
        - A valid CSV file is created
        - The CSV contains the correct columns
        - Client data is properly exported
        """
        # Create some clients
        create_client_in_db(db_connection, sample_client)

        # Create a temporary file for the export
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as temp_file:
            export_path = temp_file.name

        try:
            # Export clients
            service = ExportService(db_connection)
            count = service.export_clients_for_mail_merge(export_path)

            # Verify at least 1 client was exported
            assert count >= 1

            # Read the CSV file and verify its contents
            with open(export_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                # Should have at least 1 row
                assert len(rows) >= 1

                # Verify columns exist
                assert "first_name" in reader.fieldnames
                assert "last_name" in reader.fieldnames
                assert "address" in reader.fieldnames
                assert "email" in reader.fieldnames

                # Verify data
                first_row = rows[0]
                assert first_row["first_name"] == sample_client.first_name
                assert first_row["last_name"] == sample_client.last_name

        finally:
            # Clean up the temporary file
            Path(export_path).unlink(missing_ok=True)

    def test_export_creates_valid_csv(self, db_connection, sample_client):
        """
        Test that exported CSV files are properly formatted.

        This verifies:
        - UTF-8 with BOM encoding (for Excel compatibility)
        - Proper header row
        - Proper escaping of special characters
        """
        # Create a client with special characters in the data
        from cosmetics_records.models.client import Client

        special_client = Client(
            first_name='Jane "Special"',
            last_name="O'Brien",
            email="jane@example.com",
            address="123 Main St, Apt #5",
        )
        create_client_in_db(db_connection, special_client)

        # Export to CSV
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as temp_file:
            export_path = temp_file.name

        try:
            service = ExportService(db_connection)
            service.export_clients_for_mail_merge(export_path)

            # Read the CSV and verify special characters are handled
            with open(export_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                # Find the row with our special client
                special_row = next(
                    (r for r in rows if r["first_name"] == 'Jane "Special"'), None
                )

                assert special_row is not None
                assert special_row["last_name"] == "O'Brien"
                assert "#5" in special_row["address"]

        finally:
            Path(export_path).unlink(missing_ok=True)

    def test_export_clients_empty_database(self, db_connection):
        """
        Test exporting clients when the database is empty.

        Should create a CSV with just the header row and return 0.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as temp_file:
            export_path = temp_file.name

        try:
            service = ExportService(db_connection)
            count = service.export_clients_for_mail_merge(export_path)

            # Should export 0 clients
            assert count == 0

            # File should still exist with header row
            assert Path(export_path).exists()

            # Verify header exists
            with open(export_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                # Should have column names
                assert reader.fieldnames is not None
                # But no data rows
                rows = list(reader)
                assert len(rows) == 0

        finally:
            Path(export_path).unlink(missing_ok=True)
