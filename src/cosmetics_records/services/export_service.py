# =============================================================================
# Cosmetics Records - Export Service
# =============================================================================
# This module provides the ExportService class, which handles exporting data
# to CSV format. The primary use case is exporting client data for mail merge
# operations, but it also supports exporting other data types.
#
# Key Features:
#   - Export client data for mail merge (first_name, last_name, address, email)
#   - Export full client data with all fields
#   - Export treatment records (all or filtered by client)
#   - Export inventory items
#   - Export audit logs (with date filtering)
#   - UTF-8 with BOM encoding for Excel compatibility
#
# CSV Format:
#   - UTF-8-sig encoding (UTF-8 with BOM) for Excel compatibility
#   - Header row with column names
#   - One record per row
#   - Proper escaping of special characters (quotes, commas, newlines)
#
# Usage Example:
#   export_service = ExportService(db)
#   count = export_service.export_clients_for_mail_merge(
#       "/path/to/clients.csv"
#   )
#   print(f"Exported {count} clients")
#
# Design Decisions:
#   - UTF-8-sig encoding ensures Excel opens files with correct encoding
#   - CSV module handles proper escaping of special characters
#   - Return count of exported records for user feedback
#   - Query database directly (no model conversion) for efficiency
# =============================================================================

import csv
import logging
from datetime import datetime, timedelta
from typing import Optional

from cosmetics_records.database.connection import DatabaseConnection

# Configure module logger for debugging export operations
logger = logging.getLogger(__name__)


class ExportService:
    """
    Service for exporting data to various formats (primarily CSV).

    This class provides methods for exporting different types of data from
    the database to CSV files. The most common use case is exporting client
    data for mail merge operations in word processors.

    All CSV files use UTF-8 encoding with BOM (utf-8-sig) for maximum
    compatibility with Microsoft Excel, which has issues with plain UTF-8.

    Attributes:
        db: DatabaseConnection instance for querying data
    """

    def __init__(self, db: DatabaseConnection):
        """
        Initialize the export service with a database connection.

        Args:
            db: DatabaseConnection instance (must be used within a context
                manager - the service does NOT manage connection lifecycle)

        Note:
            The caller is responsible for managing the database connection
            lifecycle (opening/closing via context manager).
        """
        self.db = db
        logger.debug("ExportService initialized")

    def export_clients_for_mail_merge(self, file_path: str) -> int:
        """
        Export client data to CSV for mail merge.

        This creates a CSV file with the essential client information needed
        for mail merge operations: first_name, last_name, address, and email.
        This is the most common export format for sending letters, labels, etc.

        The CSV includes only clients that have all required fields populated
        (first_name and last_name are required by the model, but we filter
        for address or email since mail merge typically needs contact info).

        Args:
            file_path: Path where the CSV file will be created
                      (will overwrite if exists)

        Returns:
            Number of client records exported

        Raises:
            PermissionError: If we don't have permission to write the file
            OSError: If the file write fails for other reasons

        Example:
            >>> count = export_service.export_clients_for_mail_merge(
            ...     "/home/user/Documents/clients_mailmerge.csv"
            ... )
            >>> print(f"Exported {count} clients for mail merge")
        """
        try:
            # Query clients with relevant mail merge fields
            # We export all clients, even if some fields are empty
            # (users can filter in their mail merge application)
            self.db.execute(
                """
                SELECT
                    first_name,
                    last_name,
                    address,
                    email
                FROM clients
                ORDER BY last_name, first_name
                """
            )

            rows = self.db.fetchall()

            # Write to CSV file
            # UTF-8-sig (UTF-8 with BOM) ensures Excel opens with correct encoding
            # The BOM (Byte Order Mark) tells Excel this is UTF-8 encoded
            with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
                # Create CSV writer
                # We use DictWriter for easier column management
                fieldnames = ["first_name", "last_name", "address", "email"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header row
                writer.writeheader()

                # Write each client row
                for row in rows:
                    writer.writerow(
                        {
                            "first_name": row["first_name"] or "",
                            "last_name": row["last_name"] or "",
                            "address": row["address"] or "",
                            "email": row["email"] or "",
                        }
                    )

            record_count = len(rows)
            logger.info(
                f"Exported {record_count} clients for mail merge to: {file_path}"
            )

            return record_count

        except Exception as e:
            logger.error(f"Failed to export clients for mail merge: {e}")
            raise

    def export_all_clients(self, file_path: str) -> int:
        """
        Export all client data to CSV (full export).

        This creates a comprehensive CSV file with ALL client fields, not just
        the mail merge subset. This is useful for backups, data migration, or
        detailed analysis.

        Args:
            file_path: Path where the CSV file will be created

        Returns:
            Number of client records exported

        Raises:
            PermissionError: If we don't have permission to write the file
            OSError: If the file write fails for other reasons

        Example:
            >>> count = export_service.export_all_clients(
            ...     "/home/user/Documents/clients_full.csv"
            ... )
            >>> print(f"Exported {count} clients (full data)")
        """
        try:
            # Query all client fields
            self.db.execute(
                """
                SELECT
                    id,
                    first_name,
                    last_name,
                    email,
                    phone,
                    address,
                    date_of_birth,
                    allergies,
                    tags,
                    planned_treatment,
                    notes,
                    created_at,
                    updated_at
                FROM clients
                ORDER BY last_name, first_name
                """
            )

            rows = self.db.fetchall()

            # Write to CSV file
            with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
                fieldnames = [
                    "id",
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                    "address",
                    "date_of_birth",
                    "allergies",
                    "tags",
                    "planned_treatment",
                    "notes",
                    "created_at",
                    "updated_at",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header row
                writer.writeheader()

                # Write each client row
                for row in rows:
                    # Convert Row object to dict and handle None values
                    row_dict = {}
                    for field in fieldnames:
                        value = row[field]
                        # Convert None to empty string for CSV
                        # Convert dates/timestamps to ISO format strings
                        if value is None:
                            row_dict[field] = ""
                        else:
                            row_dict[field] = str(value)

                    writer.writerow(row_dict)

            record_count = len(rows)
            logger.info(f"Exported {record_count} clients (full data) to: {file_path}")

            return record_count

        except Exception as e:
            logger.error(f"Failed to export all clients: {e}")
            raise

    def export_treatments(self, file_path: str, client_id: Optional[int] = None) -> int:
        """
        Export treatment records to CSV.

        This exports treatment records with all their fields. If a client_id
        is provided, only exports treatments for that specific client. Otherwise,
        exports all treatments across all clients.

        Args:
            file_path: Path where the CSV file will be created
            client_id: Optional client ID to filter by (exports only that
                      client's treatments). If None, exports all treatments.

        Returns:
            Number of treatment records exported

        Raises:
            PermissionError: If we don't have permission to write the file
            OSError: If the file write fails for other reasons

        Example:
            >>> # Export all treatments
            >>> count = export_service.export_treatments(
            ...     "/home/user/Documents/all_treatments.csv"
            ... )
            >>>
            >>> # Export treatments for a specific client
            >>> count = export_service.export_treatments(
            ...     "/home/user/Documents/client_42_treatments.csv",
            ...     client_id=42
            ... )
        """
        try:
            # Build query with optional client filter
            if client_id is not None:
                query = """
                    SELECT
                        t.id,
                        t.client_id,
                        c.first_name,
                        c.last_name,
                        t.treatment_date,
                        t.treatment_notes,
                        t.created_at,
                        t.updated_at
                    FROM treatment_records t
                    LEFT JOIN clients c ON t.client_id = c.id
                    WHERE t.client_id = ?
                    ORDER BY t.treatment_date DESC, t.id DESC
                """
                parameters: tuple[int, ...] = (client_id,)
            else:
                query = """
                    SELECT
                        t.id,
                        t.client_id,
                        c.first_name,
                        c.last_name,
                        t.treatment_date,
                        t.treatment_notes,
                        t.created_at,
                        t.updated_at
                    FROM treatment_records t
                    LEFT JOIN clients c ON t.client_id = c.id
                    ORDER BY t.treatment_date DESC, t.id DESC
                """
                parameters = ()

            self.db.execute(query, parameters)
            rows = self.db.fetchall()

            # Write to CSV file
            with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
                fieldnames = [
                    "id",
                    "client_id",
                    "client_first_name",
                    "client_last_name",
                    "treatment_date",
                    "treatment_notes",
                    "created_at",
                    "updated_at",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header row
                writer.writeheader()

                # Write each treatment row
                for row in rows:
                    writer.writerow(
                        {
                            "id": row["id"],
                            "client_id": row["client_id"],
                            "client_first_name": row["first_name"] or "",
                            "client_last_name": row["last_name"] or "",
                            "treatment_date": row["treatment_date"] or "",
                            "treatment_notes": row["treatment_notes"] or "",
                            "created_at": row["created_at"] or "",
                            "updated_at": row["updated_at"] or "",
                        }
                    )

            record_count = len(rows)
            if client_id is not None:
                logger.info(
                    f"Exported {record_count} treatments for client {client_id} "
                    f"to: {file_path}"
                )
            else:
                logger.info(
                    f"Exported {record_count} treatments (all clients) to: {file_path}"
                )

            return record_count

        except Exception as e:
            logger.error(f"Failed to export treatments: {e}")
            raise

    def export_inventory(self, file_path: str) -> int:
        """
        Export inventory items to CSV.

        This exports all inventory items with their complete information:
        name, description, capacity, unit, and timestamps.

        Args:
            file_path: Path where the CSV file will be created

        Returns:
            Number of inventory items exported

        Raises:
            PermissionError: If we don't have permission to write the file
            OSError: If the file write fails for other reasons

        Example:
            >>> count = export_service.export_inventory(
            ...     "/home/user/Documents/inventory.csv"
            ... )
            >>> print(f"Exported {count} inventory items")
        """
        try:
            # Query all inventory items
            self.db.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    capacity,
                    unit,
                    created_at,
                    updated_at
                FROM inventory_items
                ORDER BY name
                """
            )

            rows = self.db.fetchall()

            # Write to CSV file
            with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
                fieldnames = [
                    "id",
                    "name",
                    "description",
                    "capacity",
                    "unit",
                    "created_at",
                    "updated_at",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header row
                writer.writeheader()

                # Write each inventory row
                for row in rows:
                    writer.writerow(
                        {
                            "id": row["id"],
                            "name": row["name"] or "",
                            "description": row["description"] or "",
                            "capacity": row["capacity"] or "",
                            "unit": row["unit"] or "",
                            "created_at": row["created_at"] or "",
                            "updated_at": row["updated_at"] or "",
                        }
                    )

            record_count = len(rows)
            logger.info(f"Exported {record_count} inventory items to: {file_path}")

            return record_count

        except Exception as e:
            logger.error(f"Failed to export inventory: {e}")
            raise

    def export_audit_logs(self, file_path: str, days: int = 30) -> int:
        """
        Export recent audit logs to CSV.

        This exports audit log entries from the last N days. This is useful
        for compliance reporting or analysis of recent changes.

        Args:
            file_path: Path where the CSV file will be created
            days: Number of days of history to export (default: 30)
                 Set to 0 to export ALL audit logs (be careful with large logs!)

        Returns:
            Number of audit log entries exported

        Raises:
            PermissionError: If we don't have permission to write the file
            OSError: If the file write fails for other reasons

        Example:
            >>> # Export last 30 days of audit logs
            >>> count = export_service.export_audit_logs(
            ...     "/home/user/Documents/audit_logs.csv"
            ... )
            >>>
            >>> # Export last 7 days
            >>> count = export_service.export_audit_logs(
            ...     "/home/user/Documents/audit_logs_week.csv",
            ...     days=7
            ... )
            >>>
            >>> # Export ALL audit logs
            >>> count = export_service.export_audit_logs(
            ...     "/home/user/Documents/audit_logs_all.csv",
            ...     days=0
            ... )
        """
        try:
            # Build query with optional date filter
            if days > 0:
                # Calculate cutoff date
                cutoff_date = datetime.now() - timedelta(days=days)
                cutoff_str = cutoff_date.isoformat()

                query = """
                    SELECT
                        id,
                        table_name,
                        record_id,
                        action,
                        field_name,
                        old_value,
                        new_value,
                        ui_location,
                        created_at
                    FROM audit_log
                    WHERE created_at >= ?
                    ORDER BY created_at DESC, id DESC
                """
                parameters: tuple[str, ...] = (cutoff_str,)
            else:
                # Export all audit logs
                query = """
                    SELECT
                        id,
                        table_name,
                        record_id,
                        action,
                        field_name,
                        old_value,
                        new_value,
                        ui_location,
                        created_at
                    FROM audit_log
                    ORDER BY created_at DESC, id DESC
                """
                parameters = ()

            self.db.execute(query, parameters)
            rows = self.db.fetchall()

            # Write to CSV file
            with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
                fieldnames = [
                    "id",
                    "table_name",
                    "record_id",
                    "action",
                    "field_name",
                    "old_value",
                    "new_value",
                    "ui_location",
                    "created_at",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header row
                writer.writeheader()

                # Write each audit log row
                for row in rows:
                    writer.writerow(
                        {
                            "id": row["id"],
                            "table_name": row["table_name"] or "",
                            "record_id": row["record_id"] or "",
                            "action": row["action"] or "",
                            "field_name": row["field_name"] or "",
                            "old_value": row["old_value"] or "",
                            "new_value": row["new_value"] or "",
                            "ui_location": row["ui_location"] or "",
                            "created_at": row["created_at"] or "",
                        }
                    )

            record_count = len(rows)
            if days > 0:
                logger.info(
                    f"Exported {record_count} audit logs (last {days} days) "
                    f"to: {file_path}"
                )
            else:
                logger.info(
                    f"Exported {record_count} audit logs (all time) to: {file_path}"
                )

            return record_count

        except Exception as e:
            logger.error(f"Failed to export audit logs: {e}")
            raise
