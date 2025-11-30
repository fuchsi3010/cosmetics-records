# =============================================================================
# Cosmetics Records - Product Controller
# =============================================================================
# This controller handles all business logic for product record management,
# tracking which products were used or recommended for clients.
#
# Key Responsibilities:
#   - CRUD operations for product records (client history)
#   - Retrieve product history for specific clients
#   - Pagination support for product records
#   - Duplicate detection (prevent multiple records on same date)
#   - Free-text product tracking (not linked to inventory)
#
# Design Patterns:
#   - Repository Pattern: Encapsulates database access
#   - Foreign Key Management: Ensures referential integrity with clients
#   - Date-based duplicate detection: Prevents accidental duplicate entries
#
# WHY free-text instead of inventory links:
#   - Flexibility: Can record any product, even if not in inventory
#   - Historical accuracy: Records remain valid even if inventory changes
#   - Simplicity: No need to maintain complex inventory relationships
#
# WHY this controller exists:
#   - Centralizes product record business logic
#   - Provides clean API for tracking product usage
#   - Handles database complexity for views
#   - Enforces business rules consistently
# =============================================================================

import logging
from datetime import date
from typing import List, Optional

from cosmetics_records.database.connection import DatabaseConnection
from cosmetics_records.models.product import ProductRecord

# Configure module logger for debugging and error tracking
logger = logging.getLogger(__name__)


class ProductController:
    """
    Controller for managing product records.

    This class provides high-level operations for product records (client
    history), including creating, reading, updating, and deleting records,
    as well as retrieving product history for specific clients.

    Note: ProductRecord uses free-text for products, NOT linked to inventory.

    Attributes:
        db: DatabaseConnection instance for executing queries

    Example:
        >>> with DatabaseConnection() as db:
        ...     controller = ProductController(db)
        ...     record = ProductRecord(
        ...         client_id=1,
        ...         product_text="Retinol Serum 30ml - Apply nightly"
        ...     )
        ...     record_id = controller.create_product_record(record)
    """

    def __init__(self, db: DatabaseConnection):
        """
        Initialize the controller with a database connection.

        Args:
            db: Active DatabaseConnection instance (must be within context manager)
        """
        self.db = db
        logger.debug("ProductController initialized")

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create_product_record(self, record: ProductRecord) -> int:
        """
        Create a new product record in the database.

        This method inserts a new product record and returns the auto-generated
        ID. The created_at and updated_at timestamps are set automatically.

        Args:
            record: ProductRecord model with validated data (ID should be None)

        Returns:
            int: The newly created product record's ID

        Raises:
            sqlite3.Error: If the database insert fails
            ValueError: If record.id is not None (trying to create existing record)
            sqlite3.IntegrityError: If client_id doesn't exist (foreign key violation)

        Example:
            >>> record = ProductRecord(
            ...     client_id=1,
            ...     product_date=date.today(),
            ...     product_text="Vitamin C Serum 15ml - Morning application"
            ... )
            >>> record_id = controller.create_product_record(record)
        """
        # Validate that we're creating a NEW record (ID should be None)
        if record.id is not None:
            raise ValueError(
                f"Cannot create product record with existing ID {record.id}. "
                "Use update_product_record() instead."
            )

        # Execute INSERT query with parameter binding
        # WHY free-text product_text: Allows recording any product without
        # being restricted to inventory items
        query = """
            INSERT INTO product_records (
                client_id, product_date, product_text
            ) VALUES (?, ?, ?)
        """

        self.db.execute(
            query,
            (
                record.client_id,
                record.product_date,
                record.product_text,
            ),
        )

        # Commit the transaction to persist the change
        self.db.commit()

        # Get the auto-generated ID from the database
        record_id = self.db.get_last_insert_id()

        logger.info(
            f"Created product record for client {record.client_id} "
            f"on {record.product_date} (ID: {record_id})"
        )
        return record_id

    def get_product_record(self, record_id: int) -> Optional[ProductRecord]:
        """
        Retrieve a single product record by ID.

        This method fetches a product record and converts it to a
        ProductRecord model. Returns None if the record doesn't exist.

        Args:
            record_id: The unique identifier of the product record

        Returns:
            ProductRecord model if found, None otherwise

        Example:
            >>> record = controller.get_product_record(42)
            >>> if record:
            ...     print(f"Product: {record.product_text}")
            ... else:
            ...     print("Product record not found")
        """
        # Query for specific product record by ID
        query = """
            SELECT id, client_id, product_date, product_text,
                   created_at, updated_at
            FROM product_records
            WHERE id = ?
        """

        self.db.execute(query, (record_id,))
        row = self.db.fetchone()

        # Return None if record doesn't exist
        if row is None:
            logger.debug(f"Product record not found: ID {record_id}")
            return None

        # Convert database row to ProductRecord model
        record = self._row_to_product_record(row)
        logger.debug(f"Retrieved product record ID {record_id}")
        return record

    def update_product_record(self, record: ProductRecord) -> bool:
        """
        Update an existing product record.

        This method updates all fields of a product record. The updated_at
        timestamp is automatically updated by the database.

        Args:
            record: ProductRecord model with updated data (must have valid ID)

        Returns:
            True if record was updated, False if record not found

        Raises:
            ValueError: If record.id is None (can't update without ID)
            sqlite3.Error: If the database update fails
            sqlite3.IntegrityError: If client_id is changed to non-existent client

        Example:
            >>> record = controller.get_product_record(42)
            >>> record.product_text += " - Client reported excellent results"
            >>> if controller.update_product_record(record):
            ...     print("Product record updated successfully")
        """
        # Validate that we have a record ID to update
        if record.id is None:
            raise ValueError(
                "Cannot update product record without ID. "
                "Use create_product_record() instead."
            )

        # Execute UPDATE query
        # WHY we update all fields: Simplifies logic, ensures consistency
        query = """
            UPDATE product_records
            SET client_id = ?, product_date = ?, product_text = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        self.db.execute(
            query,
            (
                record.client_id,
                record.product_date,
                record.product_text,
                record.id,
            ),
        )

        # Commit the transaction
        self.db.commit()

        # Check if any row was actually updated
        rows_affected = self.db.cursor.rowcount

        if rows_affected == 0:
            logger.warning(f"Update failed: Product record ID {record.id} not found")
            return False

        logger.info(f"Updated product record ID {record.id}")
        return True

    def delete_product_record(self, record_id: int) -> bool:
        """
        Delete a product record.

        This method permanently removes a product record from the database.
        This operation is irreversible.

        Args:
            record_id: The unique identifier of the product record to delete

        Returns:
            True if record was deleted, False if record not found

        Raises:
            sqlite3.Error: If the database delete fails

        Warning:
            This operation is IRREVERSIBLE. The product record will be
            permanently deleted. Consider implementing soft deletes (marking
            as inactive) for production use.

        Example:
            >>> if controller.delete_product_record(42):
            ...     print("Product record deleted")
            ... else:
            ...     print("Product record not found")
        """
        # Execute DELETE query
        query = "DELETE FROM product_records WHERE id = ?"

        self.db.execute(query, (record_id,))
        self.db.commit()

        # Check if any row was actually deleted
        rows_affected = self.db.cursor.rowcount

        if rows_affected == 0:
            logger.warning(f"Delete failed: Product record ID {record_id} not found")
            return False

        logger.info(f"Deleted product record ID {record_id}")
        return True

    # =========================================================================
    # Query Operations
    # =========================================================================

    def get_product_records_for_client(
        self, client_id: int, limit: int = 20, offset: int = 0
    ) -> List[ProductRecord]:
        """
        Get paginated product history for a specific client.

        This method retrieves product records for a client, ordered by date
        (most recent first). Supports pagination for clients with many
        product records.

        Args:
            client_id: The unique identifier of the client
            limit: Maximum number of records to return (default: 20)
            offset: Number of records to skip (for pagination, default: 0)

        Returns:
            List of ProductRecord models, empty list if no records exist

        Example:
            >>> # Get most recent 10 product records for client 42
            >>> recent = controller.get_product_records_for_client(42, limit=10)
            >>>
            >>> # Get next page (records 11-20)
            >>> next_page = controller.get_product_records_for_client(
            ...     42, limit=10, offset=10
            ... )
        """
        # Query with ORDER BY for chronological sorting (newest first)
        # WHY DESC: Most recent product usage is usually most relevant
        # This matches the index: idx_product_records_client_date
        query = """
            SELECT id, client_id, product_date, product_text,
                   created_at, updated_at
            FROM product_records
            WHERE client_id = ?
            ORDER BY product_date DESC
            LIMIT ? OFFSET ?
        """

        self.db.execute(query, (client_id, limit, offset))
        rows = self.db.fetchall()

        # Convert all rows to ProductRecord models
        records = [self._row_to_product_record(row) for row in rows]

        logger.debug(
            f"Retrieved {len(records)} product records for client {client_id} "
            f"(limit={limit}, offset={offset})"
        )
        return records

    def get_product_record_count_for_client(self, client_id: int) -> int:
        """
        Count the total number of product records for a specific client.

        This is useful for pagination calculations and displaying statistics
        (e.g., "Client has used 15 different products").

        Args:
            client_id: The unique identifier of the client

        Returns:
            Total count of product records for the client

        Example:
            >>> total = controller.get_product_record_count_for_client(42)
            >>> print(f"Client has {total} product records")
        """
        # Simple COUNT query filtered by client
        query = "SELECT COUNT(*) FROM product_records WHERE client_id = ?"

        self.db.execute(query, (client_id,))
        row = self.db.fetchone()

        # fetchone() returns a Row object, access first column
        count = row[0]

        logger.debug(f"Client {client_id} has {count} product records")
        return count

    def product_record_exists_for_date(
        self, client_id: int, product_date: date
    ) -> Optional[int]:
        """
        Check if a product record already exists for a specific client and date.

        This method helps prevent duplicate entries by checking if a product
        record already exists for the given client on the given date. Returns
        the existing record's ID if found.

        Args:
            client_id: The unique identifier of the client
            product_date: The date to check

        Returns:
            int: The ID of the existing product record, or None if no record exists

        Example:
            >>> from datetime import date
            >>> today = date.today()
            >>> existing_id = controller.product_record_exists_for_date(42, today)
            >>> if existing_id:
            ...     print(f"Product record already exists with ID: {existing_id}")
            ... else:
            ...     print("No record for this date, safe to create")

        Note:
            This is useful for preventing duplicate entries when users might
            accidentally submit the same product form multiple times. However,
            unlike treatments, multiple product records per day might be valid
            (client might purchase multiple products on the same day).
        """
        # Query for product record on specific date for specific client
        # WHY check both client_id AND date: A date might have records
        # for multiple clients, we only care about this specific client
        query = """
            SELECT id
            FROM product_records
            WHERE client_id = ? AND product_date = ?
            LIMIT 1
        """

        self.db.execute(query, (client_id, product_date))
        row = self.db.fetchone()

        if row is None:
            logger.debug(
                f"No product record found for client {client_id} on {product_date}"
            )
            return None

        # Return the ID of the existing record
        existing_id = row["id"]
        logger.debug(
            f"Product record already exists: client {client_id}, "
            f"date {product_date}, ID {existing_id}"
        )
        return existing_id

    def get_product_for_date(
        self, client_id: int, product_date: date
    ) -> Optional[ProductRecord]:
        """
        Get a product record for a specific client and date.

        This method retrieves the full product record for a client on a
        specific date, useful when you need to edit an existing entry.

        Args:
            client_id: The unique identifier of the client
            product_date: The date to look up

        Returns:
            ProductRecord if found, None otherwise

        Example:
            >>> from datetime import date
            >>> today = date.today()
            >>> product = controller.get_product_for_date(42, today)
            >>> if product:
            ...     print(f"Found product: {product.product_text}")
        """
        query = """
            SELECT id, client_id, product_date, product_text,
                   created_at, updated_at
            FROM product_records
            WHERE client_id = ? AND product_date = ?
            LIMIT 1
        """

        self.db.execute(query, (client_id, product_date))
        row = self.db.fetchone()

        if row is None:
            logger.debug(
                f"No product record found for client {client_id} on {product_date}"
            )
            return None

        product = self._row_to_product_record(row)
        logger.debug(
            f"Retrieved product record for client {client_id} on {product_date}"
        )
        return product

    # =========================================================================
    # Helper Methods (Private)
    # =========================================================================

    def _row_to_product_record(self, row) -> ProductRecord:
        """
        Convert a database row to a ProductRecord model.

        This helper method centralizes the conversion logic from database
        rows (sqlite3.Row objects) to Pydantic ProductRecord models.

        Args:
            row: sqlite3.Row object from a SELECT query

        Returns:
            ProductRecord model with data from the row

        Note:
            This is a private method (name starts with _) meant for internal
            use only. It assumes the row has the standard product_records
            table structure.
        """
        # Create ProductRecord model from row data
        # Pydantic handles type conversion (str to date, str to datetime, etc.)
        return ProductRecord(
            id=row["id"],
            client_id=row["client_id"],
            product_date=row["product_date"],
            product_text=row["product_text"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
