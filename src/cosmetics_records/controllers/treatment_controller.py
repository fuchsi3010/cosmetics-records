# =============================================================================
# Cosmetics Records - Treatment Controller
# =============================================================================
# This controller handles all business logic for treatment record management,
# managing the history of treatments performed on clients.
#
# Key Responsibilities:
#   - CRUD operations for treatment records
#   - Retrieve treatments for specific clients
#   - Pagination support for treatment history
#   - Duplicate detection (prevent multiple treatments on same date)
#   - Automatic timestamp management
#
# Design Patterns:
#   - Repository Pattern: Encapsulates database access
#   - Foreign Key Management: Ensures referential integrity with clients
#   - Date-based duplicate detection: Prevents accidental duplicate entries
#
# WHY this controller exists:
#   - Centralizes treatment business logic
#   - Enforces business rules (e.g., one treatment per client per day)
#   - Provides clean API for treatment operations
#   - Handles database complexity for views
# =============================================================================

import logging
from datetime import date
from typing import List, Optional

from cosmetics_records.database.connection import DatabaseConnection
from cosmetics_records.models.treatment import TreatmentRecord
from cosmetics_records.services.audit_service import AuditService

# Configure module logger for debugging and error tracking
logger = logging.getLogger(__name__)


class TreatmentController:
    """
    Controller for managing treatment records.

    This class provides high-level operations for treatment records,
    including creating, reading, updating, and deleting treatments,
    as well as retrieving treatment history for specific clients.

    Attributes:
        db: DatabaseConnection instance for executing queries

    Example:
        >>> with DatabaseConnection() as db:
        ...     controller = TreatmentController(db)
        ...     treatment = TreatmentRecord(
        ...         client_id=1,
        ...         treatment_notes="Deep cleansing facial"
        ...     )
        ...     treatment_id = controller.create_treatment(treatment)
    """

    def __init__(self, db: DatabaseConnection):
        """
        Initialize the controller with a database connection.

        Args:
            db: Active DatabaseConnection instance (must be within context manager)
        """
        self.db = db
        logger.debug("TreatmentController initialized")

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create_treatment(self, treatment: TreatmentRecord) -> int:
        """
        Create a new treatment record in the database.

        This method inserts a new treatment record and returns the auto-generated
        ID. The created_at and updated_at timestamps are set automatically.

        Args:
            treatment: TreatmentRecord model with validated data (ID should be None)

        Returns:
            int: The newly created treatment's ID

        Raises:
            sqlite3.Error: If the database insert fails
            ValueError: If treatment.id is not None (trying to create existing record)
            sqlite3.IntegrityError: If client_id doesn't exist (foreign key violation)

        Example:
            >>> treatment = TreatmentRecord(
            ...     client_id=1,
            ...     treatment_date=date.today(),
            ...     treatment_notes="Applied retinol serum, advised on sun protection"
            ... )
            >>> treatment_id = controller.create_treatment(treatment)
        """
        # Validate that we're creating a NEW treatment (ID should be None)
        if treatment.id is not None:
            raise ValueError(
                f"Cannot create treatment with existing ID {treatment.id}. "
                "Use update_treatment() instead."
            )

        # Execute INSERT query with parameter binding
        # WHY all fields are NOT NULL except id: Treatment records must be complete
        # to be meaningful (who, when, what was done)
        query = """
            INSERT INTO treatment_records (
                client_id, treatment_date, treatment_notes
            ) VALUES (?, ?, ?)
        """

        self.db.execute(
            query,
            (
                treatment.client_id,
                treatment.treatment_date,
                treatment.treatment_notes,
            ),
        )

        # Commit the transaction to persist the change
        self.db.commit()

        # Get the auto-generated ID from the database
        treatment_id = self.db.get_last_insert_id()

        # Log creation to audit log
        audit = AuditService(self.db)
        description = f"Treatment on {treatment.treatment_date}"
        audit.log_create(
            "treatment_records", treatment_id, description, "TreatmentController"
        )

        logger.info(
            f"Created treatment for client {treatment.client_id} "
            f"on {treatment.treatment_date} (ID: {treatment_id})"
        )
        return treatment_id

    def get_treatment(self, treatment_id: int) -> Optional[TreatmentRecord]:
        """
        Retrieve a single treatment record by ID.

        This method fetches a treatment record and converts it to a
        TreatmentRecord model. Returns None if the treatment doesn't exist.

        Args:
            treatment_id: The unique identifier of the treatment record

        Returns:
            TreatmentRecord model if found, None otherwise

        Example:
            >>> treatment = controller.get_treatment(42)
            >>> if treatment:
            ...     print(f"Treatment date: {treatment.treatment_date}")
            ... else:
            ...     print("Treatment not found")
        """
        # Query for specific treatment by ID
        query = """
            SELECT id, client_id, treatment_date, treatment_notes,
                   created_at, updated_at
            FROM treatment_records
            WHERE id = ?
        """

        self.db.execute(query, (treatment_id,))
        row = self.db.fetchone()

        # Return None if treatment doesn't exist
        if row is None:
            logger.debug(f"Treatment not found: ID {treatment_id}")
            return None

        # Convert database row to TreatmentRecord model
        treatment = self._row_to_treatment(row)
        logger.debug(f"Retrieved treatment ID {treatment_id}")
        return treatment

    def update_treatment(self, treatment: TreatmentRecord) -> bool:
        """
        Update an existing treatment record.

        This method updates all fields of a treatment. The updated_at timestamp
        is automatically updated by the database.

        Args:
            treatment: TreatmentRecord model with updated data (must have valid ID)

        Returns:
            True if treatment was updated, False if treatment not found

        Raises:
            ValueError: If treatment.id is None (can't update without ID)
            sqlite3.Error: If the database update fails
            sqlite3.IntegrityError: If client_id is changed to non-existent client

        Example:
            >>> treatment = controller.get_treatment(42)
            >>> treatment.treatment_notes += " - Follow-up scheduled"
            >>> if controller.update_treatment(treatment):
            ...     print("Treatment updated successfully")
        """
        # Validate that we have a treatment ID to update
        if treatment.id is None:
            raise ValueError(
                "Cannot update treatment without ID. Use create_treatment() instead."
            )

        # Fetch old treatment for audit logging
        old_treatment = self.get_treatment(treatment.id)
        if old_treatment is None:
            logger.warning(f"Update failed: Treatment ID {treatment.id} not found")
            return False

        # Execute UPDATE query
        # WHY we update all fields: Simplifies logic, ensures consistency
        query = """
            UPDATE treatment_records
            SET client_id = ?, treatment_date = ?, treatment_notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        self.db.execute(
            query,
            (
                treatment.client_id,
                treatment.treatment_date,
                treatment.treatment_notes,
                treatment.id,
            ),
        )

        # Commit the transaction
        self.db.commit()

        # Log changes to audit log
        audit = AuditService(self.db)
        if str(old_treatment.treatment_date) != str(treatment.treatment_date):
            audit.log_update(
                "treatment_records",
                treatment.id,
                "treatment_date",
                str(old_treatment.treatment_date),
                str(treatment.treatment_date),
                "TreatmentController",
            )
        if old_treatment.treatment_notes != treatment.treatment_notes:
            audit.log_update(
                "treatment_records",
                treatment.id,
                "treatment_notes",
                old_treatment.treatment_notes or "",
                treatment.treatment_notes or "",
                "TreatmentController",
            )

        logger.info(f"Updated treatment ID {treatment.id}")
        return True

    def delete_treatment(self, treatment_id: int) -> bool:
        """
        Delete a treatment record.

        This method permanently removes a treatment record from the database.
        This operation is irreversible.

        Args:
            treatment_id: The unique identifier of the treatment to delete

        Returns:
            True if treatment was deleted, False if treatment not found

        Raises:
            sqlite3.Error: If the database delete fails

        Warning:
            This operation is IRREVERSIBLE. The treatment record will be
            permanently deleted. Consider implementing soft deletes (marking
            as inactive) for production use.

        Example:
            >>> if controller.delete_treatment(42):
            ...     print("Treatment deleted")
            ... else:
            ...     print("Treatment not found")
        """
        # Fetch treatment info for audit logging before deletion
        treatment = self.get_treatment(treatment_id)
        if treatment is None:
            logger.warning(f"Delete failed: Treatment ID {treatment_id} not found")
            return False

        description = f"Treatment on {treatment.treatment_date}"

        # Execute DELETE query
        query = "DELETE FROM treatment_records WHERE id = ?"

        self.db.execute(query, (treatment_id,))
        self.db.commit()

        # Log deletion to audit log
        audit = AuditService(self.db)
        audit.log_delete(
            "treatment_records", treatment_id, description, "TreatmentController"
        )

        logger.info(f"Deleted treatment ID {treatment_id}")
        return True

    # =========================================================================
    # Query Operations
    # =========================================================================

    def get_treatments_for_client(
        self, client_id: int, limit: int = 20, offset: int = 0
    ) -> List[TreatmentRecord]:
        """
        Get paginated treatment history for a specific client.

        This method retrieves treatments for a client, ordered by date
        (most recent first). Supports pagination for clients with many
        treatment records.

        Args:
            client_id: The unique identifier of the client
            limit: Maximum number of treatments to return (default: 20)
            offset: Number of treatments to skip (for pagination, default: 0)

        Returns:
            List of TreatmentRecord models, empty list if no treatments exist

        Example:
            >>> # Get most recent 10 treatments for client 42
            >>> recent = controller.get_treatments_for_client(42, limit=10)
            >>>
            >>> # Get next page (treatments 11-20)
            >>> next_page = controller.get_treatments_for_client(42, limit=10, offset=10)
        """
        # Query with ORDER BY for chronological sorting (newest first)
        # WHY DESC: Most recent treatments are usually most relevant
        # This matches the index we created: idx_treatment_records_client_date
        query = """
            SELECT id, client_id, treatment_date, treatment_notes,
                   created_at, updated_at
            FROM treatment_records
            WHERE client_id = ?
            ORDER BY treatment_date DESC
            LIMIT ? OFFSET ?
        """

        self.db.execute(query, (client_id, limit, offset))
        rows = self.db.fetchall()

        # Convert all rows to TreatmentRecord models
        treatments = [self._row_to_treatment(row) for row in rows]

        logger.debug(
            f"Retrieved {len(treatments)} treatments for client {client_id} "
            f"(limit={limit}, offset={offset})"
        )
        return treatments

    def get_treatment_count_for_client(self, client_id: int) -> int:
        """
        Count the total number of treatments for a specific client.

        This is useful for pagination calculations and displaying statistics
        (e.g., "Client has received 24 treatments").

        Args:
            client_id: The unique identifier of the client

        Returns:
            Total count of treatment records for the client

        Example:
            >>> total = controller.get_treatment_count_for_client(42)
            >>> print(f"Client has {total} treatment records")
        """
        # Simple COUNT query filtered by client
        query = "SELECT COUNT(*) FROM treatment_records WHERE client_id = ?"

        self.db.execute(query, (client_id,))
        row = self.db.fetchone()

        # fetchone() returns a Row object, access first column
        count = row[0]

        logger.debug(f"Client {client_id} has {count} treatment records")
        return count

    def treatment_exists_for_date(
        self, client_id: int, treatment_date: date
    ) -> Optional[int]:
        """
        Check if a treatment already exists for a specific client and date.

        This method helps prevent duplicate entries by checking if a treatment
        record already exists for the given client on the given date. Returns
        the existing treatment's ID if found.

        Args:
            client_id: The unique identifier of the client
            treatment_date: The date to check

        Returns:
            int: The ID of the existing treatment, or None if no treatment exists

        Example:
            >>> from datetime import date
            >>> today = date.today()
            >>> existing_id = controller.treatment_exists_for_date(42, today)
            >>> if existing_id:
            ...     print(f"Treatment already exists with ID: {existing_id}")
            ... else:
            ...     print("No treatment for this date, safe to create")

        Note:
            This is useful for preventing duplicate entries when users might
            accidentally submit the same treatment form multiple times, or
            when implementing "one treatment per day" business rules.
        """
        # Query for treatment on specific date for specific client
        # WHY check both client_id AND date: A date might have treatments
        # for multiple clients, we only care about this specific client
        query = """
            SELECT id
            FROM treatment_records
            WHERE client_id = ? AND treatment_date = ?
            LIMIT 1
        """

        self.db.execute(query, (client_id, treatment_date))
        row = self.db.fetchone()

        if row is None:
            logger.debug(
                f"No treatment found for client {client_id} on {treatment_date}"
            )
            return None

        # Return the ID of the existing treatment
        existing_id = row["id"]
        logger.debug(
            f"Treatment already exists: client {client_id}, "
            f"date {treatment_date}, ID {existing_id}"
        )
        return existing_id

    def get_treatment_for_date(
        self, client_id: int, treatment_date: date
    ) -> Optional[TreatmentRecord]:
        """
        Get a treatment record for a specific client and date.

        This method retrieves the full treatment record for a client on a
        specific date, useful when you need to edit an existing entry.

        Args:
            client_id: The unique identifier of the client
            treatment_date: The date to look up

        Returns:
            TreatmentRecord if found, None otherwise

        Example:
            >>> from datetime import date
            >>> today = date.today()
            >>> treatment = controller.get_treatment_for_date(42, today)
            >>> if treatment:
            ...     print(f"Found treatment: {treatment.treatment_notes}")
        """
        query = """
            SELECT id, client_id, treatment_date, treatment_notes,
                   created_at, updated_at
            FROM treatment_records
            WHERE client_id = ? AND treatment_date = ?
            LIMIT 1
        """

        self.db.execute(query, (client_id, treatment_date))
        row = self.db.fetchone()

        if row is None:
            logger.debug(
                f"No treatment found for client {client_id} on {treatment_date}"
            )
            return None

        treatment = self._row_to_treatment(row)
        logger.debug(f"Retrieved treatment for client {client_id} on {treatment_date}")
        return treatment

    # =========================================================================
    # Helper Methods (Private)
    # =========================================================================

    def _row_to_treatment(self, row) -> TreatmentRecord:
        """
        Convert a database row to a TreatmentRecord model.

        This helper method centralizes the conversion logic from database
        rows (sqlite3.Row objects) to Pydantic TreatmentRecord models.

        Args:
            row: sqlite3.Row object from a SELECT query

        Returns:
            TreatmentRecord model with data from the row

        Note:
            This is a private method (name starts with _) meant for internal
            use only. It assumes the row has the standard treatment_records
            table structure.
        """
        # Create TreatmentRecord model from row data
        # Pydantic handles type conversion (str to date, str to datetime, etc.)
        return TreatmentRecord(
            id=row["id"],
            client_id=row["client_id"],
            treatment_date=row["treatment_date"],
            treatment_notes=row["treatment_notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
