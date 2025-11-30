# =============================================================================
# Cosmetics Records - Client Controller
# =============================================================================
# This controller handles all business logic for client management, acting as
# the bridge between the database layer and the user interface.
#
# Key Responsibilities:
#   - CRUD operations (Create, Read, Update, Delete) for clients
#   - Search and filtering (fuzzy search, alphabetical filtering)
#   - Pagination support for large datasets
#   - CSV export for mail merge functionality
#   - Data validation via Pydantic models
#
# Design Patterns:
#   - Repository Pattern: Encapsulates database access logic
#   - Dependency Injection: DatabaseConnection passed in constructor
#   - Return Type Conventions:
#     * Create operations return new ID (int)
#     * Read operations return model or None if not found
#     * Update/Delete operations return bool (success/failure)
#     * List operations return List[Model] (empty list if none found)
#
# WHY this controller exists:
#   - Centralizes client business logic in one place
#   - Prevents SQL duplication across views
#   - Makes testing easier (mock the database)
#   - Provides consistent API for all client operations
# =============================================================================

import csv
import logging
from typing import List, Optional

from thefuzz import fuzz

from cosmetics_records.database.connection import DatabaseConnection
from cosmetics_records.models.client import Client
from cosmetics_records.services.audit_service import AuditService

# Configure module logger for debugging and error tracking
logger = logging.getLogger(__name__)


class ClientController:
    """
    Controller for managing client records and operations.

    This class provides a high-level API for working with clients,
    handling all database interactions and business logic. It uses
    Pydantic models for type safety and validation.

    Attributes:
        db: DatabaseConnection instance for executing queries

    Example:
        >>> with DatabaseConnection() as db:
        ...     controller = ClientController(db)
        ...     client = Client(first_name="Jane", last_name="Doe")
        ...     client_id = controller.create_client(client)
        ...     print(f"Created client with ID: {client_id}")
    """

    def __init__(self, db: DatabaseConnection):
        """
        Initialize the controller with a database connection.

        Args:
            db: Active DatabaseConnection instance (must be within context manager)

        Note:
            The database connection should be managed by the caller using
            a 'with' statement to ensure proper cleanup.
        """
        self.db = db
        logger.debug("ClientController initialized")

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create_client(self, client: Client) -> int:
        """
        Create a new client record in the database.

        This method inserts a new client and returns the auto-generated ID.
        The created_at and updated_at timestamps are set automatically by
        the database.

        Args:
            client: Client model with validated data (ID should be None)

        Returns:
            int: The newly created client's ID

        Raises:
            sqlite3.Error: If the database insert fails
            ValueError: If client.id is not None (trying to create existing client)

        Example:
            >>> client = Client(first_name="Jane", last_name="Doe",
            ...                 email="jane@example.com")
            >>> client_id = controller.create_client(client)
            >>> print(f"New client ID: {client_id}")
        """
        # Validate that we're creating a NEW client (ID should be None)
        # This prevents accidentally overwriting existing clients
        if client.id is not None:
            raise ValueError(
                f"Cannot create client with existing ID {client.id}. "
                "Use update_client() instead."
            )

        # Convert tags list to comma-separated string for database storage
        # The database stores tags as TEXT, not as an array
        tags_str = client.tags_string()

        # Execute INSERT query with parameter binding (prevents SQL injection)
        # WHY we use ? placeholders: Security and automatic type conversion
        query = """
            INSERT INTO clients (
                first_name, last_name, email, phone, address,
                date_of_birth, allergies, tags, planned_treatment, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.db.execute(
            query,
            (
                client.first_name,
                client.last_name,
                client.email,
                client.phone,
                client.address,
                client.date_of_birth,
                client.allergies,
                tags_str,
                client.planned_treatment,
                client.notes,
            ),
        )

        # Commit the transaction to persist the change
        # WHY explicit commit: Allows grouping multiple operations into one transaction
        self.db.commit()

        # Get the auto-generated ID from the database
        client_id = self.db.get_last_insert_id()

        # Log creation to audit log
        audit = AuditService(self.db)
        audit.log_create("clients", client_id, client.full_name(), "ClientController")

        logger.info(f"Created client: {client.full_name()} (ID: {client_id})")
        return client_id

    def get_client(self, client_id: int) -> Optional[Client]:
        """
        Retrieve a single client by ID.

        This method fetches a client record and converts it to a Client model.
        Returns None if the client doesn't exist.

        Args:
            client_id: The unique identifier of the client

        Returns:
            Client model if found, None otherwise

        Example:
            >>> client = controller.get_client(42)
            >>> if client:
            ...     print(f"Found: {client.full_name()}")
            ... else:
            ...     print("Client not found")
        """
        # Query for specific client by ID
        query = """
            SELECT id, first_name, last_name, email, phone, address,
                   date_of_birth, allergies, tags, planned_treatment, notes,
                   created_at, updated_at
            FROM clients
            WHERE id = ?
        """

        self.db.execute(query, (client_id,))
        row = self.db.fetchone()

        # Return None if client doesn't exist
        if row is None:
            logger.debug(f"Client not found: ID {client_id}")
            return None

        # Convert database row to Client model
        # WHY helper method: Keeps conversion logic DRY (Don't Repeat Yourself)
        client = self._row_to_client(row)
        logger.debug(f"Retrieved client: {client.full_name()} (ID: {client_id})")
        return client

    def update_client(self, client: Client) -> bool:
        """
        Update an existing client record.

        This method updates all fields of a client. The updated_at timestamp
        is automatically updated by the database.

        Args:
            client: Client model with updated data (must have valid ID)

        Returns:
            True if client was updated, False if client not found

        Raises:
            ValueError: If client.id is None (can't update without ID)
            sqlite3.Error: If the database update fails

        Example:
            >>> client = controller.get_client(42)
            >>> client.email = "newemail@example.com"
            >>> if controller.update_client(client):
            ...     print("Client updated successfully")
        """
        # Validate that we have a client ID to update
        if client.id is None:
            raise ValueError(
                "Cannot update client without ID. Use create_client() instead."
            )

        # Fetch old client for audit logging
        old_client = self.get_client(client.id)
        if old_client is None:
            logger.warning(f"Update failed: Client ID {client.id} not found")
            return False

        # Convert tags list to comma-separated string
        tags_str = client.tags_string()

        # Execute UPDATE query
        # WHY we update all fields: Simplifies logic, ensures consistency
        # Alternative would be to track which fields changed (more complex)
        query = """
            UPDATE clients
            SET first_name = ?, last_name = ?, email = ?, phone = ?, address = ?,
                date_of_birth = ?, allergies = ?, tags = ?, planned_treatment = ?,
                notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        self.db.execute(
            query,
            (
                client.first_name,
                client.last_name,
                client.email,
                client.phone,
                client.address,
                client.date_of_birth,
                client.allergies,
                tags_str,
                client.planned_treatment,
                client.notes,
                client.id,
            ),
        )

        # Commit the transaction
        self.db.commit()

        # Log changes to audit log
        audit = AuditService(self.db)

        if old_client.first_name != client.first_name:
            audit.log_update(
                "clients",
                client.id,
                "first_name",
                old_client.first_name,
                client.first_name,
                "ClientController",
            )
        if old_client.last_name != client.last_name:
            audit.log_update(
                "clients",
                client.id,
                "last_name",
                old_client.last_name,
                client.last_name,
                "ClientController",
            )
        if old_client.email != client.email:
            audit.log_update(
                "clients",
                client.id,
                "email",
                old_client.email or "",
                client.email or "",
                "ClientController",
            )
        if old_client.phone != client.phone:
            audit.log_update(
                "clients",
                client.id,
                "phone",
                old_client.phone or "",
                client.phone or "",
                "ClientController",
            )
        if old_client.address != client.address:
            audit.log_update(
                "clients",
                client.id,
                "address",
                old_client.address or "",
                client.address or "",
                "ClientController",
            )
        if str(old_client.date_of_birth) != str(client.date_of_birth):
            audit.log_update(
                "clients",
                client.id,
                "date_of_birth",
                str(old_client.date_of_birth) if old_client.date_of_birth else "",
                str(client.date_of_birth) if client.date_of_birth else "",
                "ClientController",
            )
        if old_client.allergies != client.allergies:
            audit.log_update(
                "clients",
                client.id,
                "allergies",
                old_client.allergies or "",
                client.allergies or "",
                "ClientController",
            )
        if old_client.tags_string() != client.tags_string():
            audit.log_update(
                "clients",
                client.id,
                "tags",
                old_client.tags_string(),
                client.tags_string(),
                "ClientController",
            )
        if old_client.planned_treatment != client.planned_treatment:
            audit.log_update(
                "clients",
                client.id,
                "planned_treatment",
                old_client.planned_treatment or "",
                client.planned_treatment or "",
                "ClientController",
            )
        if old_client.notes != client.notes:
            audit.log_update(
                "clients",
                client.id,
                "notes",
                old_client.notes or "",
                client.notes or "",
                "ClientController",
            )

        logger.info(f"Updated client: {client.full_name()} (ID: {client.id})")
        return True

    def delete_client(self, client_id: int) -> bool:
        """
        Delete a client and all associated records.

        This method deletes a client from the database. Due to ON DELETE CASCADE
        foreign key constraints, all related treatment and product records are
        automatically deleted as well.

        Args:
            client_id: The unique identifier of the client to delete

        Returns:
            True if client was deleted, False if client not found

        Raises:
            sqlite3.Error: If the database delete fails

        Warning:
            This operation is IRREVERSIBLE. All client data and history will
            be permanently deleted. Consider implementing soft deletes (marking
            as inactive) for production use.

        Example:
            >>> if controller.delete_client(42):
            ...     print("Client and all records deleted")
            ... else:
            ...     print("Client not found")
        """
        # Fetch client info for audit logging before deletion
        client = self.get_client(client_id)
        if client is None:
            logger.warning(f"Delete failed: Client ID {client_id} not found")
            return False

        client_name = client.full_name()

        # Execute DELETE query
        # WHY ON DELETE CASCADE is important: When we delete a client,
        # their treatment_records and product_records are automatically deleted.
        # This prevents orphaned records that reference non-existent clients.
        query = "DELETE FROM clients WHERE id = ?"

        self.db.execute(query, (client_id,))
        self.db.commit()

        # Log deletion to audit log
        audit = AuditService(self.db)
        audit.log_delete("clients", client_id, client_name, "ClientController")

        logger.info(
            f"Deleted client ID {client_id} ({client_name}) and all associated records"
        )
        return True

    # =========================================================================
    # Search & Filter Operations
    # =========================================================================

    def get_all_clients(self, limit: int = 20, offset: int = 0) -> List[Client]:
        """
        Get a paginated list of all clients, ordered alphabetically.

        This method retrieves clients sorted by last name, then first name.
        Supports pagination for handling large datasets efficiently.

        Args:
            limit: Maximum number of clients to return (default: 20)
            offset: Number of clients to skip (for pagination, default: 0)

        Returns:
            List of Client models, empty list if no clients exist

        Example:
            >>> # Get first page (clients 1-20)
            >>> page1 = controller.get_all_clients(limit=20, offset=0)
            >>>
            >>> # Get second page (clients 21-40)
            >>> page2 = controller.get_all_clients(limit=20, offset=20)
        """
        # Query with ORDER BY for alphabetical sorting
        # WHY order by last_name, first_name: Standard sorting convention
        # for contact lists (phone book style)
        query = """
            SELECT id, first_name, last_name, email, phone, address,
                   date_of_birth, allergies, tags, planned_treatment, notes,
                   created_at, updated_at
            FROM clients
            ORDER BY last_name, first_name
            LIMIT ? OFFSET ?
        """

        self.db.execute(query, (limit, offset))
        rows = self.db.fetchall()

        # Convert all rows to Client models
        clients = [self._row_to_client(row) for row in rows]

        logger.debug(
            f"Retrieved {len(clients)} clients (limit={limit}, offset={offset})"
        )
        return clients

    def search_clients(self, query: str, limit: int = 20) -> List[Client]:
        """
        Fuzzy search for clients by name and tags.

        This method performs a fuzzy search using the Levenshtein distance
        algorithm (via thefuzz library). It searches across first name,
        last name, and tags fields, returning results that meet the
        60% similarity threshold.

        Args:
            query: Search string (can be partial name, full name, or tag)
            limit: Maximum number of results to return (default: 20)

        Returns:
            List of Client models ordered by relevance (highest match first),
            empty list if no matches found

        Raises:
            ValueError: If query is empty or only whitespace

        Example:
            >>> # Find clients with similar names
            >>> results = controller.search_clients("john sm")
            >>> # Might return: "John Smith", "John Smythe", "Joan Smith"
            >>>
            >>> # Search by tag
            >>> vip_clients = controller.search_clients("VIP")

        Note:
            Fuzzy matching uses 60% threshold, which allows for typos and
            partial matches while filtering out completely unrelated results.
        """
        # Validate search query
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        # Normalize query for consistent matching
        query = query.strip().lower()

        # Fetch all clients for fuzzy matching
        # WHY fetch all: SQLite doesn't have built-in fuzzy matching,
        # so we must do it in Python. For large datasets, consider
        # implementing a search index or using full-text search (FTS).
        all_clients_query = """
            SELECT id, first_name, last_name, email, phone, address,
                   date_of_birth, allergies, tags, planned_treatment, notes,
                   created_at, updated_at
            FROM clients
        """

        self.db.execute(all_clients_query)
        rows = self.db.fetchall()

        # Perform fuzzy matching on each client
        # Store tuples of (client, score) for sorting
        matches = []

        for row in rows:
            client = self._row_to_client(row)

            # Build searchable text from multiple fields
            # WHY include tags: Users often search by category (e.g., "VIP")
            searchable_text = " ".join(
                [
                    client.first_name.lower(),
                    client.last_name.lower(),
                    " ".join(client.tags).lower(),
                ]
            )

            # Calculate fuzzy match score (0-100)
            # WHY partial_ratio: Allows matching substrings
            # Example: "john" matches "John Smith" with high score
            score = fuzz.partial_ratio(query, searchable_text)

            # Only include matches above 60% threshold
            # WHY 60%: Good balance between flexibility and precision
            # Lower values would return too many false positives
            if score >= 60:
                matches.append((client, score))

        # Sort by score (highest first) and limit results
        # WHY sort by score: Most relevant results should appear first
        matches.sort(key=lambda x: x[1], reverse=True)
        result_clients = [client for client, score in matches[:limit]]

        logger.debug(
            f"Fuzzy search for '{query}' found {len(result_clients)} matches "
            f"(from {len(rows)} total clients)"
        )
        return result_clients

    def filter_by_letter(
        self, letter: str, limit: int = 20, offset: int = 0
    ) -> List[Client]:
        """
        Filter clients by the first letter of their last name.

        This is useful for alphabetical navigation (e.g., "Show all clients
        whose last name starts with 'S'"). Common pattern in contact lists
        and address books.

        Args:
            letter: Single letter to filter by (case-insensitive)
            limit: Maximum number of clients to return (default: 20)
            offset: Number of clients to skip (for pagination, default: 0)

        Returns:
            List of Client models, ordered by last_name then first_name,
            empty list if no matches

        Raises:
            ValueError: If letter is not a single alphabetic character

        Example:
            >>> # Get all clients with last names starting with 'S'
            >>> s_clients = controller.filter_by_letter('S')
            >>> # Might return: "Smith", "Sanchez", "Sullivan"
        """
        # Validate input
        if not letter or len(letter.strip()) != 1 or not letter.strip().isalpha():
            raise ValueError(
                f"Letter must be a single alphabetic character, got: '{letter}'"
            )

        # Normalize to uppercase for consistent matching
        letter = letter.strip().upper()

        # Query using LIKE for prefix matching
        # WHY LIKE 'S%': Matches any last_name starting with 'S'
        # The % is a wildcard that matches any characters after
        query = """
            SELECT id, first_name, last_name, email, phone, address,
                   date_of_birth, allergies, tags, planned_treatment, notes,
                   created_at, updated_at
            FROM clients
            WHERE last_name LIKE ?
            ORDER BY last_name, first_name
            LIMIT ? OFFSET ?
        """

        # Construct the LIKE pattern
        # Example: letter='S' becomes pattern='S%'
        pattern = f"{letter}%"

        self.db.execute(query, (pattern, limit, offset))
        rows = self.db.fetchall()

        # Convert rows to Client models
        clients = [self._row_to_client(row) for row in rows]

        logger.debug(
            f"Filtered by letter '{letter}': found {len(clients)} clients "
            f"(limit={limit}, offset={offset})"
        )
        return clients

    def get_client_count(self) -> int:
        """
        Get the total number of clients in the database.

        This is useful for pagination calculations and displaying
        statistics (e.g., "Showing 1-20 of 145 clients").

        Returns:
            Total count of client records

        Example:
            >>> total = controller.get_client_count()
            >>> print(f"Total clients: {total}")
        """
        # Simple COUNT query
        # WHY COUNT(*): Efficient way to get total rows
        query = "SELECT COUNT(*) FROM clients"

        self.db.execute(query)
        row = self.db.fetchone()

        # fetchone() returns a Row object, access first column
        count = row[0]

        logger.debug(f"Total client count: {count}")
        return count

    # =========================================================================
    # Export Operations
    # =========================================================================

    def export_for_mail_merge(self, file_path: str) -> int:
        """
        Export clients to CSV file for mail merge operations.

        This method creates a CSV file with columns suitable for mail merge
        in word processors (Microsoft Word, LibreOffice Writer, etc.). Only
        includes fields commonly needed for correspondence.

        Args:
            file_path: Absolute path where CSV file should be saved

        Returns:
            Number of client records exported

        Raises:
            IOError: If file cannot be written
            PermissionError: If lacking write permissions
            sqlite3.Error: If database query fails

        Example:
            >>> count = controller.export_for_mail_merge("/tmp/clients.csv")
            >>> print(f"Exported {count} clients to CSV")

        CSV Format:
            first_name,last_name,address,email
            Jane,Doe,123 Main St,jane@example.com
            John,Smith,456 Oak Ave,john@example.com

        Note:
            The CSV uses standard format: comma-separated, quoted strings,
            headers in first row. Compatible with Excel, LibreOffice Calc,
            and mail merge features in word processors.
        """
        # Query for mail merge fields
        # WHY only these fields: Common requirements for mail merge
        # (name for salutation, address for envelope, email for contact)
        query = """
            SELECT first_name, last_name, address, email
            FROM clients
            ORDER BY last_name, first_name
        """

        self.db.execute(query)
        rows = self.db.fetchall()

        # Open CSV file for writing
        # WHY 'w' mode: Overwrites existing file (fresh export each time)
        # WHY newline='': Prevents extra blank lines on Windows
        # WHY utf-8 encoding: Supports international characters
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            # Create CSV writer with standard settings
            # quoting=csv.QUOTE_MINIMAL: Only quote fields with special chars
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

            # Write header row
            # WHY header row: Identifies columns for mail merge software
            writer.writerow(["first_name", "last_name", "address", "email"])

            # Write data rows
            # WHY dict access by name: More robust than index-based access
            for row in rows:
                writer.writerow(
                    [
                        row["first_name"],
                        row["last_name"],
                        row["address"] or "",  # Empty string if NULL
                        row["email"] or "",  # Empty string if NULL
                    ]
                )

        # Return count of exported records
        count = len(rows)
        logger.info(f"Exported {count} clients to CSV: {file_path}")
        return count

    # =========================================================================
    # Helper Methods (Private)
    # =========================================================================

    def _row_to_client(self, row) -> Client:
        """
        Convert a database row to a Client model.

        This helper method centralizes the conversion logic from database
        rows (sqlite3.Row objects) to Pydantic Client models. It handles
        all type conversions and data transformations.

        Args:
            row: sqlite3.Row object from a SELECT query

        Returns:
            Client model with data from the row

        Note:
            This is a private method (name starts with _) meant for internal
            use only. It assumes the row has the standard client table structure.
        """
        # Convert tags from comma-separated string to list
        # WHY helper method: Client.from_tags_string() handles empty strings correctly
        tags_list = Client.from_tags_string(row["tags"] or "")

        # Create Client model from row data
        # WHY **dict: Unpacks the dictionary as keyword arguments
        # Pydantic handles type conversion (str to datetime, etc.)
        return Client(
            id=row["id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            phone=row["phone"],
            address=row["address"],
            date_of_birth=row["date_of_birth"],
            allergies=row["allergies"],
            tags=tags_list,
            planned_treatment=row["planned_treatment"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
