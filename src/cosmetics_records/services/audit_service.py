# =============================================================================
# Cosmetics Records - Audit Service
# =============================================================================
# This module provides the AuditService class, which handles all audit logging
# operations in the application. It provides a clean interface for logging
# CREATE, UPDATE, and DELETE operations to the audit_log table.
#
# Key Features:
#   - Log all data changes (CREATE/UPDATE/DELETE) with context
#   - Query audit logs with pagination and filtering
#   - Track which UI view made each change
#   - Automatic cleanup of old audit logs
#   - Human-readable change descriptions
#
# Usage Example:
#   audit_service = AuditService(db)
#   audit_service.log_create("clients", client_id, "Jane Doe", "ClientEditView")
#   audit_service.log_update("clients", 5, "email", "old@example.com",
#                           "new@example.com", "ClientEditView")
#
# Design Decisions:
#   - All values stored as strings for simplicity (converts from actual types)
#   - UI location tracking helps trace where changes originated
#   - Pagination prevents memory issues with large audit logs
#   - Retention policy prevents unlimited growth of audit log table
# =============================================================================

import logging
from datetime import datetime
from typing import List, Optional, Union

from cosmetics_records.database.connection import DatabaseConnection
from cosmetics_records.models.audit import AuditAction, AuditLog

# Configure module logger for debugging audit operations
logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for logging all data changes to the audit_log table.

    This class provides a high-level interface for creating audit log entries
    and querying the audit history. Every data modification in the application
    should be logged through this service to maintain a complete audit trail.

    The service handles:
    - Converting values to strings for storage
    - Recording timestamp, table, record ID, and UI location
    - Providing filtered and paginated access to audit logs
    - Cleaning up old logs based on retention policies

    Attributes:
        db: DatabaseConnection instance for executing queries
    """

    def __init__(self, db: DatabaseConnection):
        """
        Initialize the audit service with a database connection.

        Args:
            db: DatabaseConnection instance (must be used within a context
                manager - the service does NOT manage connection lifecycle)

        Note:
            The caller is responsible for managing the database connection
            lifecycle (opening/closing via context manager). This service
            just uses the connection that's passed in.
        """
        self.db = db
        logger.debug("AuditService initialized")

    def log_create(
        self,
        table_name: str,
        record_id: int,
        new_value: str,
        ui_location: str,
        client_id: Optional[int] = None,
    ) -> None:
        """
        Log a CREATE action to the audit log.

        This records when a new record is created in the database. The new_value
        should be a human-readable representation of the record (e.g., client
        name, product name) for display in the audit history.

        Args:
            table_name: Name of the table where record was created
                       (e.g., "clients", "treatment_records")
            record_id: The ID of the newly created record
            new_value: Human-readable representation of the new record
                      (e.g., "Jane Doe", "Retinol Serum 30ml")
            ui_location: Name of the UI view that created the record
                        (e.g., "ClientEditView", "TreatmentHistoryView")
            client_id: Optional ID of the client this change is related to

        Raises:
            sqlite3.Error: If the database insert fails

        Example:
            >>> audit_service.log_create(
            ...     "clients",
            ...     42,
            ...     "Jane Doe",
            ...     "ClientEditView",
            ...     client_id=42
            ... )
        """
        try:
            # Create an AuditLog model instance for validation
            # This ensures all data meets the model's validation rules
            audit_log = AuditLog(
                table_name=table_name,
                record_id=record_id,
                action=AuditAction.CREATE,
                field_name=None,  # CREATE applies to whole record, not a field
                old_value=None,  # No old value for newly created records
                new_value=new_value,
                ui_location=ui_location,
                client_id=client_id,
            )

            # Insert the audit log into the database
            # The created_at timestamp is automatically set by a database trigger
            self.db.execute(
                """
                INSERT INTO audit_log (
                    table_name,
                    record_id,
                    action,
                    field_name,
                    old_value,
                    new_value,
                    ui_location,
                    client_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_log.table_name,
                    audit_log.record_id,
                    audit_log.action.value,  # Convert Enum to string
                    audit_log.field_name,
                    audit_log.old_value,
                    audit_log.new_value,
                    audit_log.ui_location,
                    audit_log.client_id,
                ),
            )

            # Commit the transaction to persist the audit log
            self.db.commit()

            logger.info(
                f"CREATE logged: {table_name}[{record_id}] = '{new_value}' "
                f"from {ui_location} (client_id={client_id})"
            )

        except Exception as e:
            logger.error(f"Failed to log CREATE action: {e}")
            # Re-raise so caller knows the audit failed
            # This is important - we don't want to silently lose audit records
            raise

    def log_update(
        self,
        table_name: str,
        record_id: int,
        field_name: str,
        old_value: str,
        new_value: str,
        ui_location: str,
        client_id: Optional[int] = None,
    ) -> None:
        """
        Log an UPDATE action to the audit log.

        This records when an existing record is modified. It captures both the
        old and new values so you can see exactly what changed. Field-level
        tracking allows precise audit trails.

        Args:
            table_name: Name of the table where record was updated
            record_id: The ID of the updated record
            field_name: Name of the field that was changed
                       (e.g., "email", "allergies", "treatment_notes")
            old_value: Previous value before the change (as string)
            new_value: New value after the change (as string)
            ui_location: Name of the UI view that made the update
            client_id: Optional ID of the client this change is related to

        Raises:
            sqlite3.Error: If the database insert fails

        Example:
            >>> audit_service.log_update(
            ...     "clients",
            ...     42,
            ...     "email",
            ...     "old@example.com",
            ...     "new@example.com",
            ...     "ClientEditView",
            ...     client_id=42
            ... )
        """
        # Skip logging if values are identical (no actual change occurred)
        if old_value == new_value:
            logger.debug(
                f"Skipping UPDATE log for {table_name}[{record_id}].{field_name}: "
                f"values unchanged"
            )
            return

        try:
            # Create an AuditLog model instance for validation
            audit_log = AuditLog(
                table_name=table_name,
                record_id=record_id,
                action=AuditAction.UPDATE,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                ui_location=ui_location,
                client_id=client_id,
            )

            # Insert the audit log into the database
            self.db.execute(
                """
                INSERT INTO audit_log (
                    table_name,
                    record_id,
                    action,
                    field_name,
                    old_value,
                    new_value,
                    ui_location,
                    client_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_log.table_name,
                    audit_log.record_id,
                    audit_log.action.value,
                    audit_log.field_name,
                    audit_log.old_value,
                    audit_log.new_value,
                    audit_log.ui_location,
                    audit_log.client_id,
                ),
            )

            # Commit the transaction
            self.db.commit()

            logger.info(
                f"UPDATE logged: {table_name}[{record_id}].{field_name} "
                f"changed from '{old_value}' to '{new_value}' from {ui_location}"
            )

        except Exception as e:
            logger.error(f"Failed to log UPDATE action: {e}")
            raise

    def log_delete(
        self,
        table_name: str,
        record_id: int,
        old_value: str,
        ui_location: str,
        client_id: Optional[int] = None,
    ) -> None:
        """
        Log a DELETE action to the audit log.

        This records when a record is deleted from the database. The old_value
        should be a human-readable representation of what was deleted so the
        audit trail shows what was removed.

        Args:
            table_name: Name of the table where record was deleted
            record_id: The ID of the deleted record
            old_value: Human-readable representation of the deleted record
                      (e.g., "Jane Doe", "Treatment on 2024-01-15")
            ui_location: Name of the UI view that performed the deletion
            client_id: Optional ID of the client this change is related to

        Raises:
            sqlite3.Error: If the database insert fails

        Example:
            >>> audit_service.log_delete(
            ...     "treatment_records",
            ...     123,
            ...     "Treatment on 2024-01-15 for Jane Doe",
            ...     "TreatmentHistoryView",
            ...     client_id=5
            ... )
        """
        try:
            # Create an AuditLog model instance for validation
            audit_log = AuditLog(
                table_name=table_name,
                record_id=record_id,
                action=AuditAction.DELETE,
                field_name=None,  # DELETE applies to whole record
                old_value=old_value,
                new_value=None,  # No new value for deleted records
                ui_location=ui_location,
                client_id=client_id,
            )

            # Insert the audit log into the database
            self.db.execute(
                """
                INSERT INTO audit_log (
                    table_name,
                    record_id,
                    action,
                    field_name,
                    old_value,
                    new_value,
                    ui_location,
                    client_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_log.table_name,
                    audit_log.record_id,
                    audit_log.action.value,
                    audit_log.field_name,
                    audit_log.old_value,
                    audit_log.new_value,
                    audit_log.ui_location,
                    audit_log.client_id,
                ),
            )

            # Commit the transaction
            self.db.commit()

            logger.info(
                f"DELETE logged: {table_name}[{record_id}] = '{old_value}' "
                f"from {ui_location} (client_id={client_id})"
            )

        except Exception as e:
            logger.error(f"Failed to log DELETE action: {e}")
            raise

    def get_audit_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        table_filter: Optional[str] = None,
        action_filter: Optional[str] = None,
    ) -> List[AuditLog]:
        """
        Get paginated audit logs with optional filters.

        This provides a flexible way to query the audit log with pagination
        to prevent memory issues when loading large audit histories. Filters
        allow narrowing down to specific tables or action types.

        Args:
            limit: Maximum number of records to return (default: 50)
            offset: Number of records to skip (for pagination, default: 0)
            table_filter: Optional table name to filter by
                         (e.g., "clients" to see only client changes)
            action_filter: Optional action to filter by
                          (e.g., "DELETE" to see only deletions)

        Returns:
            List of AuditLog instances, ordered by most recent first

        Example:
            >>> # Get the 50 most recent audit logs
            >>> logs = audit_service.get_audit_logs()
            >>>
            >>> # Get the next 50 logs (pagination)
            >>> more_logs = audit_service.get_audit_logs(limit=50, offset=50)
            >>>
            >>> # Get all client changes
            >>> client_logs = audit_service.get_audit_logs(table_filter="clients")
            >>>
            >>> # Get all deletions
            >>> deletions = audit_service.get_audit_logs(action_filter="DELETE")
        """
        try:
            # Build the SQL query dynamically based on filters
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
                    created_at,
                    client_id
                FROM audit_log
            """

            # Build WHERE clause if filters are provided
            where_clauses: List[str] = []
            parameters: List[Union[str, int]] = []

            if table_filter:
                where_clauses.append("table_name = ?")
                parameters.append(table_filter)

            if action_filter:
                where_clauses.append("action = ?")
                parameters.append(action_filter)

            # Add WHERE clause if we have any filters
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            # Order by most recent first (newest at the top)
            # This is the most common use case for audit logs
            query += " ORDER BY created_at DESC, id DESC"

            # Add pagination
            query += " LIMIT ? OFFSET ?"
            parameters.extend([limit, offset])

            # Execute the query
            self.db.execute(query, tuple(parameters))
            rows = self.db.fetchall()

            # Convert database rows to AuditLog model instances
            audit_logs = []
            for row in rows:
                audit_log = AuditLog(
                    id=row["id"],
                    table_name=row["table_name"],
                    record_id=row["record_id"],
                    action=AuditAction(row["action"]),  # Convert string to Enum
                    field_name=row["field_name"],
                    old_value=row["old_value"],
                    new_value=row["new_value"],
                    ui_location=row["ui_location"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    client_id=row["client_id"],
                )
                audit_logs.append(audit_log)

            logger.debug(
                f"Retrieved {len(audit_logs)} audit logs "
                f"(limit={limit}, offset={offset})"
            )

            return audit_logs

        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            raise

    def get_audit_log_count(
        self,
        table_filter: Optional[str] = None,
        action_filter: Optional[str] = None,
    ) -> int:
        """
        Count audit logs with optional filters.

        This is useful for pagination - you need to know the total count
        to calculate how many pages there are. Uses the same filters as
        get_audit_logs() for consistency.

        Args:
            table_filter: Optional table name to filter by
            action_filter: Optional action to filter by

        Returns:
            Total count of audit logs matching the filters

        Example:
            >>> # Get total count of all audit logs
            >>> total = audit_service.get_audit_log_count()
            >>> pages = (total + 49) // 50  # Calculate page count for 50 per page
            >>>
            >>> # Count client changes
            >>> client_changes = audit_service.get_audit_log_count(
            ...     table_filter="clients"
            ... )
        """
        try:
            # Build the SQL query with COUNT
            query = "SELECT COUNT(*) as count FROM audit_log"

            # Build WHERE clause if filters are provided
            where_clauses = []
            parameters = []

            if table_filter:
                where_clauses.append("table_name = ?")
                parameters.append(table_filter)

            if action_filter:
                where_clauses.append("action = ?")
                parameters.append(action_filter)

            # Add WHERE clause if we have any filters
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            # Execute the query
            self.db.execute(query, tuple(parameters))
            row = self.db.fetchone()

            count = row["count"] if row else 0

            logger.debug(f"Audit log count: {count}")

            return count

        except Exception as e:
            logger.error(f"Failed to count audit logs: {e}")
            raise

    def cleanup_old_logs(self, retention_count: int) -> int:
        """
        Delete old audit logs beyond retention limit.

        This implements a retention policy to prevent the audit log table
        from growing unbounded. It keeps the N most recent logs and deletes
        older ones. This is important for database performance and storage.

        Args:
            retention_count: Number of most recent logs to keep
                           (e.g., 10000 to keep the last 10,000 audit entries)

        Returns:
            Number of audit logs deleted

        Raises:
            sqlite3.Error: If the delete operation fails

        Example:
            >>> # Keep only the 10,000 most recent audit logs
            >>> deleted = audit_service.cleanup_old_logs(10000)
            >>> print(f"Deleted {deleted} old audit logs")
        """
        try:
            # First, check current count to determine if cleanup is needed
            self.db.execute("SELECT COUNT(*) as count FROM audit_log")
            row = self.db.fetchone()
            current_count = row["count"] if row else 0

            # If we're under the retention limit, no cleanup needed
            if current_count <= retention_count:
                logger.debug(f"No cleanup needed: {current_count} <= {retention_count}")
                return 0

            # Calculate how many to delete
            to_delete = current_count - retention_count

            # Delete the oldest logs
            # We use a subquery to find the ID threshold for deletion
            # This is more efficient than deleting row by row
            self.db.execute(
                """
                DELETE FROM audit_log
                WHERE id NOT IN (
                    SELECT id FROM audit_log
                    ORDER BY created_at DESC, id DESC
                    LIMIT ?
                )
                """,
                (retention_count,),
            )

            # Commit the deletion
            self.db.commit()

            logger.info(
                f"Cleaned up {to_delete} old audit logs "
                f"(kept {retention_count} most recent)"
            )

            return to_delete

        except Exception as e:
            logger.error(f"Failed to cleanup old audit logs: {e}")
            raise

    def get_logs_for_record(self, table_name: str, record_id: int) -> List[AuditLog]:
        """
        Get all audit logs for a specific record.

        This provides a complete history of changes for a single record,
        which is useful for displaying record-specific audit trails in the UI.

        Args:
            table_name: Name of the table containing the record
            record_id: ID of the record to get audit logs for

        Returns:
            List of AuditLog instances for the record, ordered by most recent first

        Example:
            >>> # Get all changes for client with ID 42
            >>> client_history = audit_service.get_logs_for_record("clients", 42)
            >>> for log in client_history:
            ...     print(log.get_description())
        """
        try:
            # Query for all logs matching this table and record ID
            self.db.execute(
                """
                SELECT
                    id,
                    table_name,
                    record_id,
                    action,
                    field_name,
                    old_value,
                    new_value,
                    ui_location,
                    created_at,
                    client_id
                FROM audit_log
                WHERE table_name = ? AND record_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (table_name, record_id),
            )

            rows = self.db.fetchall()

            # Convert database rows to AuditLog model instances
            audit_logs = []
            for row in rows:
                audit_log = AuditLog(
                    id=row["id"],
                    table_name=row["table_name"],
                    record_id=row["record_id"],
                    action=AuditAction(row["action"]),
                    field_name=row["field_name"],
                    old_value=row["old_value"],
                    new_value=row["new_value"],
                    ui_location=row["ui_location"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    client_id=row["client_id"],
                )
                audit_logs.append(audit_log)

            logger.debug(
                f"Retrieved {len(audit_logs)} audit logs for "
                f"{table_name}[{record_id}]"
            )

            return audit_logs

        except Exception as e:
            logger.error(f"Failed to get audit logs for {table_name}[{record_id}]: {e}")
            raise
