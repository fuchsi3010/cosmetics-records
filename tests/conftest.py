# =============================================================================
# Cosmetics Records - Pytest Configuration and Fixtures
# =============================================================================
# This file contains shared pytest fixtures that are used across all test files.
# Fixtures provide reusable test components like temporary databases, sample
# data, and pre-configured controllers.
#
# Key Fixtures:
#   - temp_db: Provides a temporary database file that's cleaned up after test
#   - db_connection: Database connection with migrations applied
#   - sample_client: Pre-created sample client for testing
#   - sample_treatment: Pre-created sample treatment for testing
#   - sample_inventory_item: Pre-created sample inventory item
#
# These fixtures follow pytest best practices:
#   - Automatic cleanup (via yield and context managers)
#   - Isolation (each test gets its own fresh database)
#   - Reusability (can be used in any test file)
# =============================================================================

import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest

from cosmetics_records.database.connection import DatabaseConnection
from cosmetics_records.database.migrations.migration_manager import MigrationManager
from cosmetics_records.models.audit import AuditAction, AuditLog
from cosmetics_records.models.client import Client
from cosmetics_records.models.product import InventoryItem, ProductRecord
from cosmetics_records.models.treatment import TreatmentRecord


@pytest.fixture
def temp_db():
    """
    Create a temporary database file for testing.

    This fixture creates a temporary SQLite database file that's automatically
    deleted after the test completes. This ensures test isolation - each test
    gets its own fresh database.

    Yields:
        str: Path to the temporary database file

    Note:
        The database file is NOT initialized with schema - it's just an empty
        file. Use the db_connection fixture if you need a ready-to-use database.

    Example:
        >>> def test_something(temp_db):
        ...     # temp_db is the path to an empty database file
        ...     db = DatabaseConnection(temp_db)
        ...     # ... do something with db
    """
    # Create a temporary file with .db extension
    # delete=False means the file persists until we explicitly delete it
    # suffix='.db' gives it a proper database file extension
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Yield the path to the test
    # Everything after yield runs AFTER the test completes (cleanup)
    yield db_path

    # Cleanup: Remove the temporary database file
    # missing_ok=True prevents errors if file was already deleted
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def db_connection(temp_db):
    """
    Create a database connection with migrations applied.

    This fixture provides a fully initialized database with:
    - Schema created (all tables)
    - Migrations applied
    - Foreign keys enabled
    - Ready for use in tests

    The database is automatically cleaned up after the test.

    Args:
        temp_db: The temp_db fixture (automatically injected by pytest)

    Yields:
        DatabaseConnection: An active database connection within a context manager

    Example:
        >>> def test_create_client(db_connection):
        ...     # Database is ready to use, tables exist
        ...     db_connection.execute("INSERT INTO clients ...")
        ...     db_connection.commit()
    """
    # Use the context manager properly - this keeps the connection open
    with DatabaseConnection(temp_db) as db:
        # Apply all migrations to set up the schema
        # This creates all tables, indexes, triggers, etc.
        manager = MigrationManager(db)
        manager.apply_migrations()

        # Yield the connection to the test
        # The connection stays open during the test
        yield db


@pytest.fixture
def sample_client():
    """
    Create a sample client for testing.

    This fixture provides a pre-configured Client model with realistic test
    data. It's NOT saved to the database - it's just a model instance that
    can be used for testing validation, creation, etc.

    Returns:
        Client: A Client model instance with sample data

    Example:
        >>> def test_client_full_name(sample_client):
        ...     assert sample_client.full_name() == "Jane Doe"
    """
    return Client(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        phone="+1-555-0123",
        address="123 Main St, Springfield, IL 62701",
        date_of_birth=date(1990, 1, 15),
        allergies="Sensitive to retinol",
        tags=["VIP", "Regular"],
        planned_treatment="Monthly facial treatment",
        notes="Prefers morning appointments",
    )


@pytest.fixture
def sample_treatment():
    """
    Create a sample treatment record for testing.

    This fixture provides a pre-configured TreatmentRecord model. Note that
    it has client_id=1, so it expects a client with ID 1 to exist in the
    database when you insert it.

    Returns:
        TreatmentRecord: A TreatmentRecord model instance with sample data

    Example:
        >>> def test_create_treatment(db_connection, sample_treatment):
        ...     # First create a client, then use sample_treatment
        ...     treatment_id = controller.create_treatment(sample_treatment)
    """
    return TreatmentRecord(
        client_id=1,
        treatment_date=date.today(),
        treatment_notes=(
            "Performed deep cleansing facial. "
            "Applied hyaluronic acid serum and moisturizer. "
            "Client tolerated treatment well. "
            "Recommended follow-up in 2 weeks."
        ),
    )


@pytest.fixture
def sample_product_record():
    """
    Create a sample product record for testing.

    This fixture provides a pre-configured ProductRecord model. Like
    sample_treatment, it expects client_id=1 to exist in the database.

    Returns:
        ProductRecord: A ProductRecord model instance with sample data

    Example:
        >>> def test_create_product(db_connection, sample_product_record):
        ...     # First create a client, then use sample_product_record
        ...     product_id = controller.create_product(sample_product_record)
    """
    return ProductRecord(
        client_id=1,
        product_date=date.today(),
        product_text="Retinol Serum 30ml - Advanced anti-aging formula",
    )


@pytest.fixture
def sample_inventory_item():
    """
    Create a sample inventory item for testing.

    This fixture provides a pre-configured InventoryItem model with valid
    data that passes all validation rules (unit is one of the allowed values,
    capacity is positive, etc.).

    Returns:
        InventoryItem: An InventoryItem model instance with sample data

    Example:
        >>> def test_create_inventory(db_connection, sample_inventory_item):
        ...     item_id = controller.create_item(sample_inventory_item)
    """
    return InventoryItem(
        name="Hyaluronic Acid Serum",
        description="Deep hydration formula with 2% hyaluronic acid",
        capacity=30.0,
        unit="ml",
    )


@pytest.fixture
def sample_audit_log():
    """
    Create a sample audit log entry for testing.

    This fixture provides a pre-configured AuditLog model for testing
    audit logging functionality.

    Returns:
        AuditLog: An AuditLog model instance with sample data

    Example:
        >>> def test_audit_log_description(sample_audit_log):
        ...     desc = sample_audit_log.get_description("Jane Doe")
        ...     assert "updated" in desc.lower()
    """
    return AuditLog(
        table_name="clients",
        record_id=1,
        action=AuditAction.UPDATE,
        field_name="email",
        old_value="old@example.com",
        new_value="new@example.com",
        ui_location="ClientEditView",
        created_at=datetime.now(),
    )


# =============================================================================
# Pytest Configuration Hooks
# =============================================================================
# These hooks customize pytest's behavior for our test suite


def pytest_configure(config):
    """
    Configure pytest before tests run.

    This hook is called before any tests are collected or run. We use it to
    set up any global test configuration.

    Args:
        config: pytest configuration object
    """
    # Add custom markers for categorizing tests
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# =============================================================================
# Helper Functions for Tests
# =============================================================================
# These are utility functions that tests can import and use


def create_client_in_db(db, client: Client) -> int:
    """
    Helper function to insert a client directly into the database.

    This is useful in tests where you need a client to exist but don't want
    to test the client creation logic itself (you're testing something else).

    Args:
        db: DatabaseConnection instance
        client: Client model to insert

    Returns:
        int: The ID of the newly created client

    Example:
        >>> def test_something(db_connection, sample_client):
        ...     client_id = create_client_in_db(db_connection, sample_client)
        ...     # Now client with client_id exists in the database
    """
    from cosmetics_records.controllers.client_controller import ClientController

    controller = ClientController(db)
    return controller.create_client(client)


def create_treatment_in_db(db, treatment: TreatmentRecord) -> int:
    """
    Helper function to insert a treatment directly into the database.

    Args:
        db: DatabaseConnection instance
        treatment: TreatmentRecord model to insert

    Returns:
        int: The ID of the newly created treatment

    Example:
        >>> def test_something(db_connection, sample_client, sample_treatment):
        ...     client_id = create_client_in_db(db_connection, sample_client)
        ...     treatment_id = create_treatment_in_db(db_connection, sample_treatment)
    """
    from cosmetics_records.controllers.treatment_controller import TreatmentController

    controller = TreatmentController(db)
    return controller.create_treatment(treatment)


def create_inventory_item_in_db(db, item: InventoryItem) -> int:
    """
    Helper function to insert an inventory item directly into the database.

    Args:
        db: DatabaseConnection instance
        item: InventoryItem model to insert

    Returns:
        int: The ID of the newly created inventory item

    Example:
        >>> def test_something(db_connection, sample_inventory_item):
        ...     item_id = create_inventory_item_in_db(db_connection, sample_inventory_item)
    """
    from cosmetics_records.controllers.inventory_controller import InventoryController

    controller = InventoryController(db)
    return controller.create_item(item)
