# =============================================================================
# Cosmetics Records - Import Service
# =============================================================================
# This module provides the ImportService class, which handles importing data
# from CSV files. The primary use case is initial data migration from existing
# systems (Excel, old software, etc.).
#
# Key Features:
#   - Import 4 CSV file types: clients, treatments, product_sales, inventory
#   - Validate all data before any database writes
#   - Use transactions (all-or-nothing imports)
#   - Map temporary import_id values to actual database IDs
#   - Detailed error reporting with row numbers
#
# CSV File Structure:
#   - clients.csv: Required - client personal data with import_id for linking
#   - treatments.csv: Optional - treatment records linked to clients
#   - product_sales.csv: Optional - product sale records linked to clients
#   - inventory.csv: Optional - inventory items (standalone)
#
# Import Order:
#   1. Inventory (standalone, no dependencies)
#   2. Clients (creates mapping of import_id -> database ID)
#   3. Treatments (uses client mapping)
#   4. Product Sales (uses client mapping)
#
# Usage Example:
#   import_service = ImportService()
#   errors = import_service.validate_files(
#       clients_path="clients.csv",
#       treatments_path="treatments.csv"
#   )
#   if not errors:
#       result = import_service.import_data()
#       print(f"Imported {result.clients_count} clients")
#
# Design Decisions:
#   - Validate ALL files before ANY database writes (fail fast)
#   - Use import_id column to link records across files
#   - Transaction-based import ensures data integrity
#   - Return detailed validation errors for user feedback
# =============================================================================

import csv
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from cosmetics_records.database.connection import DatabaseConnection
from cosmetics_records.models.client import Client
from cosmetics_records.models.product import InventoryItem

# Configure module logger for debugging import operations
logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes for Import Results
# =============================================================================


@dataclass
class ValidationError:
    """
    Represents a single validation error during CSV parsing.

    Attributes:
        file_name: Name of the CSV file (e.g., "clients.csv")
        row_number: 1-indexed row number where error occurred (includes header)
        column: Name of the column with the error (if applicable)
        message: Human-readable error description
    """

    file_name: str
    row_number: Optional[int]
    column: Optional[str]
    message: str

    def __str__(self) -> str:
        """Format error for display to user."""
        parts = [self.file_name]
        if self.row_number is not None:
            parts.append(f"row {self.row_number}")
        if self.column:
            parts.append(f"column '{self.column}'")
        return f"{' '.join(parts)}: {self.message}"


@dataclass
class ImportPreview:
    """
    Preview of data to be imported (counts only).

    This is shown to the user before the actual import to confirm
    they want to proceed.

    Attributes:
        clients_count: Number of clients to import
        treatments_count: Number of treatment records to import
        products_count: Number of product records to import
        inventory_count: Number of inventory items to import
    """

    clients_count: int = 0
    treatments_count: int = 0
    products_count: int = 0
    inventory_count: int = 0


@dataclass
class ImportResult:
    """
    Result of the import operation.

    Attributes:
        success: Whether the import completed successfully
        clients_imported: Number of clients actually imported
        treatments_imported: Number of treatment records imported
        products_imported: Number of product records imported
        inventory_imported: Number of inventory items imported
        error_message: Error description if success is False
    """

    success: bool
    clients_imported: int = 0
    treatments_imported: int = 0
    products_imported: int = 0
    inventory_imported: int = 0
    error_message: Optional[str] = None


@dataclass
class ParsedData:
    """
    Container for all parsed and validated CSV data.

    This holds the data after parsing and validation, ready for import.
    Internal use only.

    Attributes:
        clients: List of tuples (import_id, client_dict)
        treatments: List of tuples (client_import_id, treatment_dict)
        products: List of tuples (client_import_id, product_dict)
        inventory: List of inventory_dict
    """

    clients: List[Tuple[str, dict]] = field(default_factory=list)
    treatments: List[Tuple[str, dict]] = field(default_factory=list)
    products: List[Tuple[str, dict]] = field(default_factory=list)
    inventory: List[dict] = field(default_factory=list)


# =============================================================================
# Import Service Class
# =============================================================================


class ImportService:
    """
    Service for importing data from CSV files.

    This class provides methods for validating and importing data from
    CSV files. The import process is designed to be safe and atomic:
    - All files are validated before any database writes
    - Import uses a transaction (all-or-nothing)
    - Detailed error messages help users fix CSV issues

    Typical workflow:
        1. Call validate_files() to check all CSV files
        2. Review validation errors (if any)
        3. Call get_preview() to see what will be imported
        4. Call import_data() to perform the actual import

    Attributes:
        _clients_path: Path to clients CSV file
        _treatments_path: Path to treatments CSV file (optional)
        _products_path: Path to products CSV file (optional)
        _inventory_path: Path to inventory CSV file (optional)
        _parsed_data: Parsed and validated data ready for import
        _errors: List of validation errors
    """

    # Required columns for each CSV file type
    # These columns MUST exist in the CSV header
    CLIENTS_REQUIRED_COLUMNS = {"import_id", "first_name", "last_name"}
    CLIENTS_OPTIONAL_COLUMNS = {
        "email",
        "phone",
        "address",
        "date_of_birth",
        "allergies",
        "tags",
        "planned_treatment",
        "notes",
    }

    TREATMENTS_REQUIRED_COLUMNS = {
        "client_import_id",
        "treatment_date",
        "treatment_notes",
    }

    PRODUCTS_REQUIRED_COLUMNS = {"client_import_id", "product_date", "product_text"}

    INVENTORY_REQUIRED_COLUMNS = {"name", "capacity", "unit"}
    INVENTORY_OPTIONAL_COLUMNS = {"description"}

    # Valid inventory units (must match InventoryItem model)
    VALID_UNITS = {"ml", "g", "Pc."}

    def __init__(self) -> None:
        """Initialize the import service with empty state."""
        self._clients_path: Optional[Path] = None
        self._treatments_path: Optional[Path] = None
        self._products_path: Optional[Path] = None
        self._inventory_path: Optional[Path] = None
        self._parsed_data: Optional[ParsedData] = None
        self._errors: List[ValidationError] = []

        logger.debug("ImportService initialized")

    def _get_parsed_data(self) -> ParsedData:
        """Get parsed data with assertion that it's not None."""
        assert self._parsed_data is not None, "ParsedData not initialized"
        return self._parsed_data

    def validate_files(
        self,
        clients_path: str,
        treatments_path: Optional[str] = None,
        products_path: Optional[str] = None,
        inventory_path: Optional[str] = None,
    ) -> List[ValidationError]:
        """
        Validate all provided CSV files.

        This method parses and validates all CSV files WITHOUT writing
        anything to the database. It checks:
        - File existence and readability
        - Required columns are present
        - Data types are correct (dates, numbers)
        - import_id values are unique (in clients.csv)
        - client_import_id values reference valid clients
        - Inventory units are valid (ml, g, Pc.)

        Args:
            clients_path: Path to clients CSV file (REQUIRED)
            treatments_path: Path to treatments CSV file (optional)
            products_path: Path to products CSV file (optional)
            inventory_path: Path to inventory CSV file (optional)

        Returns:
            List of ValidationError objects. Empty list means validation passed.

        Example:
            >>> service = ImportService()
            >>> errors = service.validate_files(
            ...     clients_path="/path/to/clients.csv",
            ...     treatments_path="/path/to/treatments.csv"
            ... )
            >>> if errors:
            ...     for error in errors:
            ...         print(error)
            ... else:
            ...     print("Validation passed!")
        """
        # Reset state for new validation
        self._errors = []
        self._parsed_data = ParsedData()

        # Store file paths
        self._clients_path = Path(clients_path)
        self._treatments_path = Path(treatments_path) if treatments_path else None
        self._products_path = Path(products_path) if products_path else None
        self._inventory_path = Path(inventory_path) if inventory_path else None

        logger.info(
            f"Starting validation: clients={clients_path}, "
            f"treatments={treatments_path}, products={products_path}, "
            f"inventory={inventory_path}"
        )

        # Step 1: Validate file existence
        self._validate_file_exists(self._clients_path, "clients.csv", required=True)
        if self._treatments_path:
            self._validate_file_exists(self._treatments_path, "treatments.csv")
        if self._products_path:
            self._validate_file_exists(self._products_path, "product_sales.csv")
        if self._inventory_path:
            self._validate_file_exists(self._inventory_path, "inventory.csv")

        # Stop early if files don't exist
        if self._errors:
            return self._errors

        # Step 2: Parse and validate each file
        # Parse clients first (needed to validate references in other files)
        client_import_ids = self._parse_clients_csv()

        # Parse optional files
        if self._treatments_path and self._treatments_path.exists():
            self._parse_treatments_csv(client_import_ids)

        if self._products_path and self._products_path.exists():
            self._parse_products_csv(client_import_ids)

        if self._inventory_path and self._inventory_path.exists():
            self._parse_inventory_csv()

        logger.info(f"Validation complete: {len(self._errors)} errors found")
        return self._errors

    def get_preview(self) -> Optional[ImportPreview]:
        """
        Get a preview of what will be imported.

        This method returns counts of records that will be imported.
        Must be called after validate_files() with no errors.

        Returns:
            ImportPreview with counts, or None if validation hasn't passed

        Example:
            >>> errors = service.validate_files(clients_path="clients.csv")
            >>> if not errors:
            ...     preview = service.get_preview()
            ...     print(f"Will import {preview.clients_count} clients")
        """
        if self._errors or self._parsed_data is None:
            return None

        return ImportPreview(
            clients_count=len(self._parsed_data.clients),
            treatments_count=len(self._parsed_data.treatments),
            products_count=len(self._parsed_data.products),
            inventory_count=len(self._parsed_data.inventory),
        )

    def import_data(self) -> ImportResult:
        """
        Import all validated data into the database.

        This method performs the actual import using a database transaction.
        If any error occurs, the entire import is rolled back.

        Must be called after validate_files() returns no errors.

        Import order:
        1. Inventory (no dependencies)
        2. Clients (creates import_id -> database ID mapping)
        3. Treatments (uses client mapping)
        4. Products (uses client mapping)

        Returns:
            ImportResult with success status and counts

        Raises:
            RuntimeError: If called before successful validation

        Example:
            >>> errors = service.validate_files(clients_path="clients.csv")
            >>> if not errors:
            ...     result = service.import_data()
            ...     if result.success:
            ...         print(f"Imported {result.clients_imported} clients")
            ...     else:
            ...         print(f"Import failed: {result.error_message}")
        """
        # Ensure validation passed
        if self._errors:
            raise RuntimeError(
                "Cannot import: validation errors exist. "
                "Call validate_files() and fix errors first."
            )

        if self._parsed_data is None:
            raise RuntimeError(
                "Cannot import: no data parsed. " "Call validate_files() first."
            )

        logger.info("Starting import...")

        try:
            # Use database connection with transaction
            with DatabaseConnection() as db:
                # Dictionary to map import_id -> actual database ID
                client_id_mapping: Dict[str, int] = {}

                # Step 1: Import inventory (no dependencies)
                inventory_count = self._import_inventory(db)

                # Step 2: Import clients (creates ID mapping)
                clients_count = self._import_clients(db, client_id_mapping)

                # Step 3: Import treatments (uses client mapping)
                treatments_count = self._import_treatments(db, client_id_mapping)

                # Step 4: Import products (uses client mapping)
                products_count = self._import_products(db, client_id_mapping)

                # Commit the transaction
                db.commit()

                logger.info(
                    f"Import complete: {clients_count} clients, "
                    f"{treatments_count} treatments, {products_count} products, "
                    f"{inventory_count} inventory items"
                )

                return ImportResult(
                    success=True,
                    clients_imported=clients_count,
                    treatments_imported=treatments_count,
                    products_imported=products_count,
                    inventory_imported=inventory_count,
                )

        except Exception as e:
            # Transaction is automatically rolled back on exception
            logger.error(f"Import failed: {e}")
            return ImportResult(
                success=False,
                error_message=str(e),
            )

    # =========================================================================
    # File Validation Helpers
    # =========================================================================

    def _validate_file_exists(
        self, path: Path, display_name: str, required: bool = False
    ) -> None:
        """
        Check if a file exists and is readable.

        Args:
            path: Path to the file
            display_name: Name to show in error messages
            required: If True, add error when file doesn't exist
        """
        if not path.exists():
            if required:
                self._add_error(display_name, None, None, f"File not found: {path}")
            return

        if not path.is_file():
            self._add_error(display_name, None, None, f"Not a file: {path}")
            return

        # Try to read the file to check permissions
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                f.read(1)
        except PermissionError:
            self._add_error(
                display_name, None, None, f"Permission denied reading file: {path}"
            )
        except Exception as e:
            self._add_error(display_name, None, None, f"Cannot read file: {e}")

    def _add_error(
        self,
        file_name: str,
        row_number: Optional[int],
        column: Optional[str],
        message: str,
    ) -> None:
        """Add a validation error to the error list."""
        error = ValidationError(
            file_name=file_name,
            row_number=row_number,
            column=column,
            message=message,
        )
        self._errors.append(error)
        logger.debug(f"Validation error: {error}")

    # =========================================================================
    # CSV Parsing Methods
    # =========================================================================

    def _parse_clients_csv(self) -> set:
        """
        Parse and validate the clients CSV file.

        Returns:
            Set of valid import_id values for reference validation

        Note:
            Populates self._parsed_data.clients and self._errors
        """
        if not self._clients_path or not self._clients_path.exists():
            return set()

        file_name = "clients.csv"
        valid_import_ids: set = set()

        try:
            with open(self._clients_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)

                # Validate header columns
                if reader.fieldnames is None:
                    self._add_error(file_name, None, None, "Empty file or invalid CSV")
                    return set()

                # Check required columns
                missing_cols = self.CLIENTS_REQUIRED_COLUMNS - set(reader.fieldnames)
                if missing_cols:
                    self._add_error(
                        file_name,
                        None,
                        None,
                        f"Missing required columns: {', '.join(sorted(missing_cols))}",
                    )
                    return set()

                # Track import_id values to detect duplicates
                seen_import_ids: Dict[str, int] = {}  # import_id -> row number

                # Parse each row (row_number is 2-indexed: 1 for header + row index)
                for row_idx, row in enumerate(reader, start=2):
                    import_id = row.get("import_id", "").strip()

                    # Validate import_id is not empty
                    if not import_id:
                        self._add_error(
                            file_name, row_idx, "import_id", "import_id cannot be empty"
                        )
                        continue

                    # Check for duplicate import_id
                    if import_id in seen_import_ids:
                        self._add_error(
                            file_name,
                            row_idx,
                            "import_id",
                            f"Duplicate import_id '{import_id}' "
                            f"(first seen on row {seen_import_ids[import_id]})",
                        )
                        continue

                    seen_import_ids[import_id] = row_idx

                    # Validate required fields
                    first_name = row.get("first_name", "").strip()
                    last_name = row.get("last_name", "").strip()

                    if not first_name:
                        self._add_error(
                            file_name,
                            row_idx,
                            "first_name",
                            "first_name cannot be empty",
                        )
                        continue

                    if not last_name:
                        self._add_error(
                            file_name, row_idx, "last_name", "last_name cannot be empty"
                        )
                        continue

                    # Validate optional date_of_birth format
                    dob_str = row.get("date_of_birth", "").strip()
                    dob = None
                    if dob_str:
                        dob = self._parse_date(
                            dob_str, file_name, row_idx, "date_of_birth"
                        )
                        if dob is None and dob_str:
                            # Error already added by _parse_date
                            continue

                    # Validate email format (basic check)
                    email = row.get("email", "").strip() or None
                    if email and "@" not in email:
                        self._add_error(
                            file_name,
                            row_idx,
                            "email",
                            f"Invalid email format: {email}",
                        )
                        continue

                    # Parse tags (comma-separated)
                    tags_str = row.get("tags", "").strip()
                    tags = [t.strip() for t in tags_str.split(",") if t.strip()]

                    # Build client data dictionary
                    client_data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": row.get("phone", "").strip() or None,
                        "address": row.get("address", "").strip() or None,
                        "date_of_birth": dob,
                        "allergies": row.get("allergies", "").strip() or None,
                        "tags": tags,
                        "planned_treatment": row.get("planned_treatment", "").strip()
                        or None,
                        "notes": row.get("notes", "").strip() or None,
                    }

                    # Add to parsed data
                    self._get_parsed_data().clients.append((import_id, client_data))
                    valid_import_ids.add(import_id)

        except Exception as e:
            self._add_error(file_name, None, None, f"Error reading file: {e}")

        logger.debug(f"Parsed {len(valid_import_ids)} clients from {file_name}")
        return valid_import_ids

    def _parse_treatments_csv(self, valid_client_ids: set) -> None:
        """
        Parse and validate the treatments CSV file.

        Args:
            valid_client_ids: Set of valid client import_id values

        Note:
            Populates self._parsed_data.treatments and self._errors
        """
        if not self._treatments_path or not self._treatments_path.exists():
            return

        file_name = "treatments.csv"

        try:
            with open(
                self._treatments_path, "r", encoding="utf-8-sig", newline=""
            ) as f:
                reader = csv.DictReader(f)

                # Validate header columns
                if reader.fieldnames is None:
                    self._add_error(file_name, None, None, "Empty file or invalid CSV")
                    return

                # Check required columns
                missing_cols = self.TREATMENTS_REQUIRED_COLUMNS - set(reader.fieldnames)
                if missing_cols:
                    self._add_error(
                        file_name,
                        None,
                        None,
                        f"Missing required columns: {', '.join(sorted(missing_cols))}",
                    )
                    return

                # Parse each row
                for row_idx, row in enumerate(reader, start=2):
                    client_import_id = row.get("client_import_id", "").strip()

                    # Validate client_import_id exists
                    if not client_import_id:
                        self._add_error(
                            file_name,
                            row_idx,
                            "client_import_id",
                            "client_import_id cannot be empty",
                        )
                        continue

                    # Validate client_import_id references valid client
                    if client_import_id not in valid_client_ids:
                        self._add_error(
                            file_name,
                            row_idx,
                            "client_import_id",
                            f"client_import_id '{client_import_id}' "
                            "not found in clients.csv",
                        )
                        continue

                    # Validate treatment_date
                    date_str = row.get("treatment_date", "").strip()
                    if not date_str:
                        self._add_error(
                            file_name,
                            row_idx,
                            "treatment_date",
                            "treatment_date cannot be empty",
                        )
                        continue

                    treatment_date = self._parse_date(
                        date_str, file_name, row_idx, "treatment_date"
                    )
                    if treatment_date is None:
                        continue

                    # Validate treatment_notes
                    treatment_notes = row.get("treatment_notes", "").strip()
                    if not treatment_notes:
                        self._add_error(
                            file_name,
                            row_idx,
                            "treatment_notes",
                            "treatment_notes cannot be empty",
                        )
                        continue

                    # Build treatment data dictionary
                    treatment_data = {
                        "treatment_date": treatment_date,
                        "treatment_notes": treatment_notes,
                    }

                    # Add to parsed data
                    self._get_parsed_data().treatments.append(
                        (client_import_id, treatment_data)
                    )

        except Exception as e:
            self._add_error(file_name, None, None, f"Error reading file: {e}")

        parsed_treatments = len(self._get_parsed_data().treatments)
        logger.debug(f"Parsed {parsed_treatments} treatments from {file_name}")

    def _parse_products_csv(self, valid_client_ids: set) -> None:
        """
        Parse and validate the product_sales CSV file.

        Args:
            valid_client_ids: Set of valid client import_id values

        Note:
            Populates self._parsed_data.products and self._errors
        """
        if not self._products_path or not self._products_path.exists():
            return

        file_name = "product_sales.csv"

        try:
            with open(self._products_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)

                # Validate header columns
                if reader.fieldnames is None:
                    self._add_error(file_name, None, None, "Empty file or invalid CSV")
                    return

                # Check required columns
                missing_cols = self.PRODUCTS_REQUIRED_COLUMNS - set(reader.fieldnames)
                if missing_cols:
                    self._add_error(
                        file_name,
                        None,
                        None,
                        f"Missing required columns: {', '.join(sorted(missing_cols))}",
                    )
                    return

                # Parse each row
                for row_idx, row in enumerate(reader, start=2):
                    client_import_id = row.get("client_import_id", "").strip()

                    # Validate client_import_id exists
                    if not client_import_id:
                        self._add_error(
                            file_name,
                            row_idx,
                            "client_import_id",
                            "client_import_id cannot be empty",
                        )
                        continue

                    # Validate client_import_id references valid client
                    if client_import_id not in valid_client_ids:
                        self._add_error(
                            file_name,
                            row_idx,
                            "client_import_id",
                            f"client_import_id '{client_import_id}' "
                            "not found in clients.csv",
                        )
                        continue

                    # Validate product_date
                    date_str = row.get("product_date", "").strip()
                    if not date_str:
                        self._add_error(
                            file_name,
                            row_idx,
                            "product_date",
                            "product_date cannot be empty",
                        )
                        continue

                    product_date = self._parse_date(
                        date_str, file_name, row_idx, "product_date"
                    )
                    if product_date is None:
                        continue

                    # Validate product_text
                    product_text = row.get("product_text", "").strip()
                    if not product_text:
                        self._add_error(
                            file_name,
                            row_idx,
                            "product_text",
                            "product_text cannot be empty",
                        )
                        continue

                    # Build product data dictionary
                    product_data = {
                        "product_date": product_date,
                        "product_text": product_text,
                    }

                    # Add to parsed data
                    self._get_parsed_data().products.append(
                        (client_import_id, product_data)
                    )

        except Exception as e:
            self._add_error(file_name, None, None, f"Error reading file: {e}")

        logger.debug(
            f"Parsed {len(self._get_parsed_data().products)} products from {file_name}"
        )

    def _parse_inventory_csv(self) -> None:
        """
        Parse and validate the inventory CSV file.

        Note:
            Populates self._parsed_data.inventory and self._errors
        """
        if not self._inventory_path or not self._inventory_path.exists():
            return

        file_name = "inventory.csv"

        try:
            with open(self._inventory_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)

                # Validate header columns
                if reader.fieldnames is None:
                    self._add_error(file_name, None, None, "Empty file or invalid CSV")
                    return

                # Check required columns
                missing_cols = self.INVENTORY_REQUIRED_COLUMNS - set(reader.fieldnames)
                if missing_cols:
                    self._add_error(
                        file_name,
                        None,
                        None,
                        f"Missing required columns: {', '.join(sorted(missing_cols))}",
                    )
                    return

                # Parse each row
                for row_idx, row in enumerate(reader, start=2):
                    # Validate name
                    name = row.get("name", "").strip()
                    if not name:
                        self._add_error(
                            file_name, row_idx, "name", "name cannot be empty"
                        )
                        continue

                    # Validate capacity
                    capacity_str = row.get("capacity", "").strip()
                    if not capacity_str:
                        self._add_error(
                            file_name, row_idx, "capacity", "capacity cannot be empty"
                        )
                        continue

                    try:
                        capacity = float(capacity_str)
                        if capacity <= 0:
                            self._add_error(
                                file_name,
                                row_idx,
                                "capacity",
                                f"capacity must be greater than 0, got {capacity}",
                            )
                            continue
                    except ValueError:
                        self._add_error(
                            file_name,
                            row_idx,
                            "capacity",
                            f"Invalid number format: '{capacity_str}'",
                        )
                        continue

                    # Validate unit
                    unit = row.get("unit", "").strip()
                    if not unit:
                        self._add_error(
                            file_name, row_idx, "unit", "unit cannot be empty"
                        )
                        continue

                    if unit not in self.VALID_UNITS:
                        self._add_error(
                            file_name,
                            row_idx,
                            "unit",
                            f"Invalid unit '{unit}' "
                            f"(must be one of: {', '.join(sorted(self.VALID_UNITS))})",
                        )
                        continue

                    # Build inventory data dictionary
                    inventory_data = {
                        "name": name,
                        "description": row.get("description", "").strip() or None,
                        "capacity": capacity,
                        "unit": unit,
                    }

                    # Add to parsed data
                    self._get_parsed_data().inventory.append(inventory_data)

        except Exception as e:
            self._add_error(file_name, None, None, f"Error reading file: {e}")

        logger.debug(
            f"Parsed {len(self._get_parsed_data().inventory)} "
            f"inventory items from {file_name}"
        )

    def _parse_date(
        self, date_str: str, file_name: str, row_number: int, column: str
    ) -> Optional[date]:
        """
        Parse a date string in YYYY-MM-DD format.

        Args:
            date_str: Date string to parse
            file_name: Name of the file (for error messages)
            row_number: Row number (for error messages)
            column: Column name (for error messages)

        Returns:
            Parsed date object, or None if invalid (error is added automatically)
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            self._add_error(
                file_name,
                row_number,
                column,
                f"Invalid date format '{date_str}' (expected YYYY-MM-DD)",
            )
            return None

    # =========================================================================
    # Import Methods
    # =========================================================================

    def _import_inventory(self, db: DatabaseConnection) -> int:
        """
        Import inventory items into the database.

        Args:
            db: Active database connection

        Returns:
            Number of items imported
        """
        if not self._parsed_data or not self._parsed_data.inventory:
            return 0

        count = 0
        for item_data in self._parsed_data.inventory:
            # Create inventory item model
            item = InventoryItem(
                name=item_data["name"],
                description=item_data["description"],
                capacity=item_data["capacity"],
                unit=item_data["unit"],
            )

            # Insert into database
            query = """
                INSERT INTO inventory (name, description, capacity, unit)
                VALUES (?, ?, ?, ?)
            """
            db.execute(
                query,
                (item.name, item.description, item.capacity, item.unit),
            )
            count += 1

        logger.debug(f"Imported {count} inventory items")
        return count

    def _import_clients(
        self, db: DatabaseConnection, id_mapping: Dict[str, int]
    ) -> int:
        """
        Import clients into the database.

        Args:
            db: Active database connection
            id_mapping: Dictionary to populate with import_id -> database ID mapping

        Returns:
            Number of clients imported
        """
        if not self._parsed_data or not self._parsed_data.clients:
            return 0

        count = 0
        for import_id, client_data in self._parsed_data.clients:
            # Create client model
            client = Client(
                first_name=client_data["first_name"],
                last_name=client_data["last_name"],
                email=client_data["email"],
                phone=client_data["phone"],
                address=client_data["address"],
                date_of_birth=client_data["date_of_birth"],
                allergies=client_data["allergies"],
                tags=client_data["tags"],
                planned_treatment=client_data["planned_treatment"],
                notes=client_data["notes"],
            )

            # Convert tags to comma-separated string
            tags_str = client.tags_string()

            # Insert into database
            query = """
                INSERT INTO clients (
                    first_name, last_name, email, phone, address,
                    date_of_birth, allergies, tags, planned_treatment, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            db.execute(
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

            # Get the new database ID and store in mapping
            new_id = db.get_last_insert_id()
            id_mapping[import_id] = new_id
            count += 1

        logger.debug(f"Imported {count} clients")
        return count

    def _import_treatments(
        self, db: DatabaseConnection, client_id_mapping: Dict[str, int]
    ) -> int:
        """
        Import treatment records into the database.

        Args:
            db: Active database connection
            client_id_mapping: Dictionary mapping import_id -> database ID

        Returns:
            Number of treatments imported
        """
        if not self._parsed_data or not self._parsed_data.treatments:
            return 0

        count = 0
        for client_import_id, treatment_data in self._parsed_data.treatments:
            # Look up the actual database client ID
            client_id = client_id_mapping.get(client_import_id)
            if client_id is None:
                # This shouldn't happen after validation, but be safe
                logger.warning(
                    f"Skipping treatment: client_import_id "
                    f"'{client_import_id}' not found"
                )
                continue

            # Insert into database
            query = """
                INSERT INTO treatment_records
                (client_id, treatment_date, treatment_notes)
                VALUES (?, ?, ?)
            """
            db.execute(
                query,
                (
                    client_id,
                    treatment_data["treatment_date"],
                    treatment_data["treatment_notes"],
                ),
            )
            count += 1

        logger.debug(f"Imported {count} treatments")
        return count

    def _import_products(
        self, db: DatabaseConnection, client_id_mapping: Dict[str, int]
    ) -> int:
        """
        Import product records into the database.

        Args:
            db: Active database connection
            client_id_mapping: Dictionary mapping import_id -> database ID

        Returns:
            Number of products imported
        """
        if not self._parsed_data or not self._parsed_data.products:
            return 0

        count = 0
        for client_import_id, product_data in self._parsed_data.products:
            # Look up the actual database client ID
            client_id = client_id_mapping.get(client_import_id)
            if client_id is None:
                # This shouldn't happen after validation, but be safe
                logger.warning(
                    f"Skipping product: client_import_id '{client_import_id}' not found"
                )
                continue

            # Insert into database
            query = """
                INSERT INTO product_records (client_id, product_date, product_text)
                VALUES (?, ?, ?)
            """
            db.execute(
                query,
                (
                    client_id,
                    product_data["product_date"],
                    product_data["product_text"],
                ),
            )
            count += 1

        logger.debug(f"Imported {count} products")
        return count
