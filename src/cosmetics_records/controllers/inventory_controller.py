# =============================================================================
# Cosmetics Records - Inventory Controller
# =============================================================================
# This controller handles all business logic for inventory management,
# tracking products available in the salon.
#
# Key Responsibilities:
#   - CRUD operations for inventory items
#   - Search and filtering (fuzzy search, alphabetical filtering)
#   - Pagination support for large inventories
#   - Autocomplete support (get all product names)
#   - Structured product data (name, capacity, unit)
#
# Design Patterns:
#   - Repository Pattern: Encapsulates database access
#   - Value Object: Capacity + Unit form a logical unit
#   - Display Name Generation: Helper for UI formatting
#
# WHY separate from ProductRecord:
#   - Inventory = what we HAVE in stock (current state)
#   - ProductRecord = what we USED for clients (historical data)
#   - Separation allows flexibility (can record products not in inventory)
#
# WHY this controller exists:
#   - Centralizes inventory business logic
#   - Provides clean API for inventory operations
#   - Handles database complexity for views
#   - Enables autocomplete and search features
# =============================================================================

import logging
from typing import List, Optional

from thefuzz import fuzz

from cosmetics_records.database.connection import DatabaseConnection
from cosmetics_records.models.product import InventoryItem
from cosmetics_records.services.audit_service import AuditService

# Configure module logger for debugging and error tracking
logger = logging.getLogger(__name__)


class InventoryController:
    """
    Controller for managing inventory items.

    This class provides high-level operations for inventory management,
    including creating, reading, updating, and deleting items, as well
    as searching and filtering the inventory.

    Attributes:
        db: DatabaseConnection instance for executing queries

    Example:
        >>> with DatabaseConnection() as db:
        ...     controller = InventoryController(db)
        ...     item = InventoryItem(
        ...         name="Retinol Serum",
        ...         capacity=30.0,
        ...         unit="ml"
        ...     )
        ...     item_id = controller.create_item(item)
    """

    def __init__(self, db: DatabaseConnection):
        """
        Initialize the controller with a database connection.

        Args:
            db: Active DatabaseConnection instance (must be within context manager)
        """
        self.db = db
        logger.debug("InventoryController initialized")

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create_item(self, item: InventoryItem) -> int:
        """
        Create a new inventory item in the database.

        This method inserts a new inventory item and returns the auto-generated
        ID. The created_at and updated_at timestamps are set automatically.

        Args:
            item: InventoryItem model with validated data (ID should be None)

        Returns:
            int: The newly created inventory item's ID

        Raises:
            sqlite3.Error: If the database insert fails
            ValueError: If item.id is not None (trying to create existing item)

        Example:
            >>> item = InventoryItem(
            ...     name="Hyaluronic Acid Serum",
            ...     description="Deep hydration formula",
            ...     capacity=30.0,
            ...     unit="ml"
            ... )
            >>> item_id = controller.create_item(item)
        """
        # Validate that we're creating a NEW item (ID should be None)
        if item.id is not None:
            raise ValueError(
                f"Cannot create inventory item with existing ID {item.id}. "
                "Use update_item() instead."
            )

        # Execute INSERT query with parameter binding
        # WHY separate capacity and unit: Allows numeric queries and
        # standardized unit validation
        query = """
            INSERT INTO inventory (
                name, description, capacity, unit
            ) VALUES (?, ?, ?, ?)
        """

        self.db.execute(
            query,
            (
                item.name,
                item.description,
                item.capacity,
                item.unit,
            ),
        )

        # Commit the transaction to persist the change
        self.db.commit()

        # Get the auto-generated ID from the database
        item_id = self.db.get_last_insert_id()

        # Log creation to audit log
        audit = AuditService(self.db)
        audit.log_create(
            "inventory_items", item_id, item.display_name(), "InventoryController"
        )

        logger.info(f"Created inventory item: {item.display_name()} (ID: {item_id})")
        return item_id

    def get_item(self, item_id: int) -> Optional[InventoryItem]:
        """
        Retrieve a single inventory item by ID.

        This method fetches an inventory item and converts it to an
        InventoryItem model. Returns None if the item doesn't exist.

        Args:
            item_id: The unique identifier of the inventory item

        Returns:
            InventoryItem model if found, None otherwise

        Example:
            >>> item = controller.get_item(42)
            >>> if item:
            ...     print(f"Found: {item.display_name()}")
            ... else:
            ...     print("Item not found")
        """
        # Query for specific inventory item by ID
        query = """
            SELECT id, name, description, capacity, unit,
                   created_at, updated_at
            FROM inventory
            WHERE id = ?
        """

        self.db.execute(query, (item_id,))
        row = self.db.fetchone()

        # Return None if item doesn't exist
        if row is None:
            logger.debug(f"Inventory item not found: ID {item_id}")
            return None

        # Convert database row to InventoryItem model
        item = self._row_to_inventory_item(row)
        logger.debug(f"Retrieved inventory item: {item.display_name()} (ID: {item_id})")
        return item

    def update_item(self, item: InventoryItem) -> bool:
        """
        Update an existing inventory item.

        This method updates all fields of an inventory item. The updated_at
        timestamp is automatically updated by the database.

        Args:
            item: InventoryItem model with updated data (must have valid ID)

        Returns:
            True if item was updated, False if item not found

        Raises:
            ValueError: If item.id is None (can't update without ID)
            sqlite3.Error: If the database update fails

        Example:
            >>> item = controller.get_item(42)
            >>> item.capacity = 50.0  # Changed from 30ml to 50ml
            >>> if controller.update_item(item):
            ...     print("Item updated successfully")
        """
        # Validate that we have an item ID to update
        if item.id is None:
            raise ValueError(
                "Cannot update inventory item without ID. Use create_item() instead."
            )

        # Fetch old item for audit logging
        old_item = self.get_item(item.id)
        if old_item is None:
            logger.warning(f"Update failed: Inventory item ID {item.id} not found")
            return False

        # Execute UPDATE query
        # WHY we update all fields: Simplifies logic, ensures consistency
        query = """
            UPDATE inventory
            SET name = ?, description = ?, capacity = ?, unit = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        self.db.execute(
            query,
            (
                item.name,
                item.description,
                item.capacity,
                item.unit,
                item.id,
            ),
        )

        # Commit the transaction
        self.db.commit()

        # Log changes to audit log
        audit = AuditService(self.db)
        if old_item.name != item.name:
            audit.log_update(
                "inventory_items",
                item.id,
                "name",
                old_item.name,
                item.name,
                "InventoryController",
            )
        if old_item.description != item.description:
            audit.log_update(
                "inventory_items",
                item.id,
                "description",
                old_item.description or "",
                item.description or "",
                "InventoryController",
            )
        if old_item.capacity != item.capacity:
            audit.log_update(
                "inventory_items",
                item.id,
                "capacity",
                str(old_item.capacity),
                str(item.capacity),
                "InventoryController",
            )
        if old_item.unit != item.unit:
            audit.log_update(
                "inventory_items",
                item.id,
                "unit",
                old_item.unit,
                item.unit,
                "InventoryController",
            )

        logger.info(f"Updated inventory item: {item.display_name()} (ID: {item.id})")
        return True

    def delete_item(self, item_id: int) -> bool:
        """
        Delete an inventory item.

        This method permanently removes an inventory item from the database.
        This operation is irreversible.

        Args:
            item_id: The unique identifier of the inventory item to delete

        Returns:
            True if item was deleted, False if item not found

        Raises:
            sqlite3.Error: If the database delete fails

        Warning:
            This operation is IRREVERSIBLE. The inventory item will be
            permanently deleted. Note that ProductRecords (client history)
            use free-text and are NOT linked to inventory, so deleting an
            inventory item won't affect historical records.

        Example:
            >>> if controller.delete_item(42):
            ...     print("Inventory item deleted")
            ... else:
            ...     print("Item not found")
        """
        # Fetch item info for audit logging before deletion
        item = self.get_item(item_id)
        if item is None:
            logger.warning(f"Delete failed: Inventory item ID {item_id} not found")
            return False

        item_name = item.display_name()

        # Execute DELETE query
        # NOTE: This won't affect ProductRecords because they use free-text,
        # not foreign keys to inventory
        query = "DELETE FROM inventory WHERE id = ?"

        self.db.execute(query, (item_id,))
        self.db.commit()

        # Log deletion to audit log
        audit = AuditService(self.db)
        audit.log_delete("inventory_items", item_id, item_name, "InventoryController")

        logger.info(f"Deleted inventory item ID {item_id}")
        return True

    # =========================================================================
    # Search & Filter Operations
    # =========================================================================

    def get_all_items(self, limit: int = 20, offset: int = 0) -> List[InventoryItem]:
        """
        Get a paginated list of all inventory items, ordered alphabetically.

        This method retrieves inventory items sorted by name. Supports
        pagination for handling large inventories efficiently.

        Args:
            limit: Maximum number of items to return (default: 20)
            offset: Number of items to skip (for pagination, default: 0)

        Returns:
            List of InventoryItem models, empty list if no items exist

        Example:
            >>> # Get first page (items 1-20)
            >>> page1 = controller.get_all_items(limit=20, offset=0)
            >>>
            >>> # Get second page (items 21-40)
            >>> page2 = controller.get_all_items(limit=20, offset=20)
        """
        # Query with ORDER BY for alphabetical sorting
        # WHY order by name: Standard for product lists and catalogs
        # This matches the index we created: idx_inventory_name
        query = """
            SELECT id, name, description, capacity, unit,
                   created_at, updated_at
            FROM inventory
            ORDER BY name
            LIMIT ? OFFSET ?
        """

        self.db.execute(query, (limit, offset))
        rows = self.db.fetchall()

        # Convert all rows to InventoryItem models
        items = [self._row_to_inventory_item(row) for row in rows]

        logger.debug(
            f"Retrieved {len(items)} inventory items (limit={limit}, offset={offset})"
        )
        return items

    def search_items(self, query: str, limit: int = 20) -> List[InventoryItem]:
        """
        Fuzzy search for inventory items by name.

        This method performs a fuzzy search using the Levenshtein distance
        algorithm (via thefuzz library). It searches the name field,
        returning results that meet the 60% similarity threshold.

        Args:
            query: Search string (product name or partial name)
            limit: Maximum number of results to return (default: 20)

        Returns:
            List of InventoryItem models ordered by relevance (highest match first),
            empty list if no matches found

        Raises:
            ValueError: If query is empty or only whitespace

        Example:
            >>> # Find products with similar names
            >>> results = controller.search_items("serum")
            >>> # Might return: "Retinol Serum", "Vitamin C Serum", "Serum Collection"
            >>>
            >>> # Handles typos
            >>> results = controller.search_items("vitmin c")
            >>> # Still finds "Vitamin C Serum"

        Note:
            Fuzzy matching uses 60% threshold, which allows for typos and
            partial matches while filtering out completely unrelated results.
        """
        # Validate search query
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        # Normalize query for consistent matching
        query = query.strip().lower()

        # Fetch all items for fuzzy matching
        # WHY fetch all: SQLite doesn't have built-in fuzzy matching,
        # so we must do it in Python. For large inventories, consider
        # implementing a search index or using full-text search (FTS).
        all_items_query = """
            SELECT id, name, description, capacity, unit,
                   created_at, updated_at
            FROM inventory
        """

        self.db.execute(all_items_query)
        rows = self.db.fetchall()

        # Perform fuzzy matching on each item
        # Store tuples of (item, score) for sorting
        matches = []

        for row in rows:
            item = self._row_to_inventory_item(row)

            # Search on item name (lowercase for case-insensitive matching)
            searchable_text = item.name.lower()

            # Calculate fuzzy match score (0-100)
            # WHY partial_ratio: Allows matching substrings
            # Example: "serum" matches "Retinol Serum" with high score
            score = fuzz.partial_ratio(query, searchable_text)

            # Only include matches above 60% threshold
            # WHY 60%: Good balance between flexibility and precision
            if score >= 60:
                matches.append((item, score))

        # Sort by score (highest first) and limit results
        # WHY sort by score: Most relevant results should appear first
        matches.sort(key=lambda x: x[1], reverse=True)
        result_items = [item for item, score in matches[:limit]]

        logger.debug(
            f"Fuzzy search for '{query}' found {len(result_items)} matches "
            f"(from {len(rows)} total items)"
        )
        return result_items

    def filter_by_letter(
        self, letter: str, limit: int = 20, offset: int = 0
    ) -> List[InventoryItem]:
        """
        Filter inventory items by the first letter of their name.

        This is useful for alphabetical navigation (e.g., "Show all products
        starting with 'S'"). Common pattern in product catalogs and lists.

        Args:
            letter: Single letter to filter by (case-insensitive)
            limit: Maximum number of items to return (default: 20)
            offset: Number of items to skip (for pagination, default: 0)

        Returns:
            List of InventoryItem models, ordered by name,
            empty list if no matches

        Raises:
            ValueError: If letter is not a single alphabetic character

        Example:
            >>> # Get all products with names starting with 'S'
            >>> s_items = controller.filter_by_letter('S')
            >>> # Might return: "Serum", "Sunscreen", "Salicylic Acid"
        """
        # Validate input
        if not letter or len(letter.strip()) != 1 or not letter.strip().isalpha():
            raise ValueError(
                f"Letter must be a single alphabetic character, got: '{letter}'"
            )

        # Normalize to uppercase for consistent matching
        letter = letter.strip().upper()

        # Query using LIKE for prefix matching
        # WHY LIKE 'S%': Matches any name starting with 'S'
        # The % is a wildcard that matches any characters after
        query = """
            SELECT id, name, description, capacity, unit,
                   created_at, updated_at
            FROM inventory
            WHERE name LIKE ?
            ORDER BY name
            LIMIT ? OFFSET ?
        """

        # Construct the LIKE pattern
        # Example: letter='S' becomes pattern='S%'
        pattern = f"{letter}%"

        self.db.execute(query, (pattern, limit, offset))
        rows = self.db.fetchall()

        # Convert rows to InventoryItem models
        items = [self._row_to_inventory_item(row) for row in rows]

        logger.debug(
            f"Filtered by letter '{letter}': found {len(items)} items "
            f"(limit={limit}, offset={offset})"
        )
        return items

    def get_item_count(self) -> int:
        """
        Get the total number of inventory items in the database.

        This is useful for pagination calculations and displaying
        statistics (e.g., "Showing 1-20 of 85 products").

        Returns:
            Total count of inventory items

        Example:
            >>> total = controller.get_item_count()
            >>> print(f"Total inventory items: {total}")
        """
        # Simple COUNT query
        # WHY COUNT(*): Efficient way to get total rows
        query = "SELECT COUNT(*) FROM inventory"

        self.db.execute(query)
        row = self.db.fetchone()

        # fetchone() returns a Row object, access first column
        count = row[0]

        logger.debug(f"Total inventory item count: {count}")
        return count

    def get_all_names(self) -> List[str]:
        """
        Get all inventory item display names for autocomplete.

        This method retrieves all product names formatted as display names
        (e.g., "Retinol Serum (30 ml)") for use in autocomplete dropdowns
        and selection lists.

        Returns:
            List of display names, ordered alphabetically, empty list if no items

        Example:
            >>> names = controller.get_all_names()
            >>> # Returns: ["Face Cream (50 g)", "Retinol Serum (30 ml)", ...]
            >>>
            >>> # Use in autocomplete dropdown
            >>> for name in names:
            ...     dropdown.add_option(name)

        Note:
            This loads all product names into memory. For very large inventories
            (thousands of items), consider implementing server-side autocomplete
            with search queries instead.
        """
        # Query for all items to generate display names
        # WHY ORDER BY name: Alphabetical order is standard for autocomplete
        query = """
            SELECT id, name, description, capacity, unit,
                   created_at, updated_at
            FROM inventory
            ORDER BY name
        """

        self.db.execute(query)
        rows = self.db.fetchall()

        # Convert rows to InventoryItem models and get display names
        # WHY use display_name(): Provides consistent formatting with
        # capacity and unit (e.g., "Serum (30 ml)")
        display_names = [
            self._row_to_inventory_item(row).display_name() for row in rows
        ]

        logger.debug(f"Retrieved {len(display_names)} inventory item display names")
        return display_names

    # =========================================================================
    # Helper Methods (Private)
    # =========================================================================

    def _row_to_inventory_item(self, row) -> InventoryItem:
        """
        Convert a database row to an InventoryItem model.

        This helper method centralizes the conversion logic from database
        rows (sqlite3.Row objects) to Pydantic InventoryItem models.

        Args:
            row: sqlite3.Row object from a SELECT query

        Returns:
            InventoryItem model with data from the row

        Note:
            This is a private method (name starts with _) meant for internal
            use only. It assumes the row has the standard inventory table
            structure.
        """
        # Create InventoryItem model from row data
        # Pydantic handles type conversion and validation
        # (e.g., ensures unit is one of: "ml", "g", "Pc.")
        return InventoryItem(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            capacity=row["capacity"],
            unit=row["unit"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
