# =============================================================================
# Cosmetics Records - Initial Database Schema Migration (v001)
# =============================================================================
# This migration creates the foundational database schema for the application.
#
# Tables Created:
#   1. clients - Core client information and contact details
#   2. treatment_records - Historical treatment notes per client
#   3. product_records - Product usage tracking per client
#   4. inventory - Product inventory management
#   5. audit_log - Change tracking for compliance and debugging
#   6. schema_migrations - Migration version tracking (created by manager)
#
# Design Decisions:
#   - All timestamps use SQLite's CURRENT_TIMESTAMP (UTC)
#   - Foreign keys use ON DELETE CASCADE for automatic cleanup
#   - Indexes are created for common query patterns
#   - TEXT fields are preferred over VARCHAR (SQLite recommendation)
#   - REAL is used for decimal numbers (ml, grams)
#
# WHY these tables:
#   - clients: Core entity - everyone we provide services to
#   - treatment_records: History of treatments for medical/legal compliance
#   - product_records: Track which products were used (allergy tracking)
#   - inventory: Manage stock levels and product information
#   - audit_log: Change history for accountability and debugging
# =============================================================================

from cosmetics_records.database.connection import DatabaseConnection
import logging

logger = logging.getLogger(__name__)


def apply(db: DatabaseConnection) -> None:
    """
    Apply the initial schema migration.

    This function is called by the MigrationManager to create all
    initial database tables and indexes.

    Args:
        db: An active DatabaseConnection instance

    Raises:
        sqlite3.Error: If any SQL statement fails

    Note:
        This function assumes it's running within a transaction context
        managed by MigrationManager. If it fails, the transaction will
        be rolled back automatically.
    """
    logger.info("Applying v001_initial_schema migration")

    # =========================================================================
    # TABLE: clients
    # =========================================================================
    # Stores core client information including contact details, medical info,
    # and administrative notes.
    #
    # Key Fields:
    #   - date_of_birth: Used for age-appropriate treatment recommendations
    #   - allergies: Critical for safety - checked before product application
    #   - tags: Comma-separated for filtering (e.g., "VIP,sensitive-skin")
    #   - planned_treatment: Next scheduled treatment or long-term plan
    #
    # WHY separate first_name and last_name:
    #   - Allows proper sorting by last name (cultural norm in many countries)
    #   - Enables formal salutations ("Dear Mr. Smith")
    #
    # WHY TEXT instead of VARCHAR:
    #   - SQLite treats VARCHAR(N) identically to TEXT anyway
    #   - TEXT is more flexible and recommended by SQLite docs
    # =========================================================================
    create_clients_table = """
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        address TEXT,
        date_of_birth DATE,
        allergies TEXT,
        tags TEXT,
        planned_treatment TEXT,
        notes TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """
    db.execute(create_clients_table)
    logger.debug("Created clients table")

    # Index for client search and sorting
    # WHY this index: Most common query is "find client by last name"
    # Combined index on (last_name, first_name) supports:
    #   - WHERE last_name = 'Smith'
    #   - WHERE last_name = 'Smith' AND first_name = 'John'
    #   - ORDER BY last_name, first_name
    create_clients_name_index = """
    CREATE INDEX IF NOT EXISTS idx_clients_name
    ON clients(last_name, first_name)
    """
    db.execute(create_clients_name_index)
    logger.debug("Created index on clients(last_name, first_name)")

    # =========================================================================
    # TABLE: treatment_records
    # =========================================================================
    # Stores historical records of treatments performed on clients.
    #
    # Key Fields:
    #   - client_id: Links to clients table (ON DELETE CASCADE)
    #   - treatment_date: When the treatment was performed
    #   - treatment_notes: Detailed notes about the procedure, results, etc.
    #
    # WHY ON DELETE CASCADE:
    #   - When a client is deleted, their treatment history should go too
    #   - Prevents orphaned records that reference non-existent clients
    #   - Simplifies cleanup code (don't need to manually delete treatments)
    #
    # WHY treatment_notes is NOT NULL:
    #   - A treatment without notes has no value
    #   - Forces practitioners to document their work (legal protection)
    #
    # WHY separate table instead of array in clients:
    #   - Unlimited treatments per client
    #   - Can query treatments independently (e.g., "all treatments this month")
    #   - Easier to add treatment-specific fields later (duration, cost, etc.)
    # =========================================================================
    create_treatment_records_table = """
    CREATE TABLE IF NOT EXISTS treatment_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        treatment_date DATE NOT NULL,
        treatment_notes TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    )
    """
    db.execute(create_treatment_records_table)
    logger.debug("Created treatment_records table")

    # Index for querying treatments by client, most recent first
    # WHY DESC on treatment_date: Most common query is "show recent treatments"
    # This index supports:
    #   - WHERE client_id = 42
    #   - WHERE client_id = 42 ORDER BY treatment_date DESC
    create_treatment_records_index = """
    CREATE INDEX IF NOT EXISTS idx_treatment_records_client_date
    ON treatment_records(client_id, treatment_date DESC)
    """
    db.execute(create_treatment_records_index)
    logger.debug("Created index on treatment_records(client_id, treatment_date DESC)")

    # =========================================================================
    # TABLE: product_records
    # =========================================================================
    # Tracks which products were used/recommended for each client.
    #
    # Key Fields:
    #   - client_id: Links to clients table (ON DELETE CASCADE)
    #   - product_date: When the product was used/recommended
    #   - product_text: Description of the product and usage notes
    #
    # WHY this table:
    #   - Allergy tracking: If client has reaction, can check product history
    #   - Repurchase recommendations: "You used this product 6 months ago"
    #   - Inventory planning: Track which products are used most
    #
    # WHY product_text instead of FK to inventory:
    #   - Products might be discontinued or renamed over time
    #   - Free-form text allows recording external/client's own products
    #   - Historical records remain accurate even if inventory changes
    # =========================================================================
    create_product_records_table = """
    CREATE TABLE IF NOT EXISTS product_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        product_date DATE NOT NULL,
        product_text TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    )
    """
    db.execute(create_product_records_table)
    logger.debug("Created product_records table")

    # Index for querying products by client, most recent first
    # Same rationale as treatment_records index
    create_product_records_index = """
    CREATE INDEX IF NOT EXISTS idx_product_records_client_date
    ON product_records(client_id, product_date DESC)
    """
    db.execute(create_product_records_index)
    logger.debug("Created index on product_records(client_id, product_date DESC)")

    # =========================================================================
    # TABLE: inventory
    # =========================================================================
    # Manages the product inventory - what products are available and in
    # what quantities.
    #
    # Key Fields:
    #   - name: Product name (e.g., "Hyaluronic Acid Serum")
    #   - description: Detailed product information, ingredients, etc.
    #   - capacity: Numeric size/quantity (e.g., 30, 50, 100)
    #   - unit: Unit of measurement (ml, g, or Pc. for pieces)
    #
    # WHY separate capacity and unit:
    #   - Allows numeric queries (e.g., "products > 50ml")
    #   - Supports mixed units (some in ml, some in grams)
    #   - Easier to display (concatenate capacity + unit in UI)
    #
    # WHY CHECK constraint on unit:
    #   - Enforces data consistency (prevents typos like "milliliters")
    #   - Makes queries predictable (know exactly which values exist)
    #   - "Pc." is standard abbreviation for "pieces" (countable items)
    #
    # WHY REAL for capacity:
    #   - Supports decimal values (e.g., 0.5ml, 2.5g)
    #   - More accurate than INTEGER for small quantities
    # =========================================================================
    create_inventory_table = """
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        capacity REAL NOT NULL,
        unit TEXT NOT NULL CHECK(unit IN ('ml', 'g', 'Pc.')),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """
    db.execute(create_inventory_table)
    logger.debug("Created inventory table")

    # Index for searching products by name
    # WHY this index: Common query is "find product by name" for autocomplete
    # Supports:
    #   - WHERE name LIKE 'Serum%'
    #   - ORDER BY name
    create_inventory_name_index = """
    CREATE INDEX IF NOT EXISTS idx_inventory_name
    ON inventory(name)
    """
    db.execute(create_inventory_name_index)
    logger.debug("Created index on inventory(name)")

    # =========================================================================
    # TABLE: audit_log
    # =========================================================================
    # Tracks all changes made to records for compliance, debugging, and
    # accountability.
    #
    # Key Fields:
    #   - table_name: Which table was modified (e.g., "clients")
    #   - record_id: Which record was modified (the primary key)
    #   - action: What happened (CREATE, UPDATE, DELETE)
    #   - field_name: Which field changed (NULL for CREATE/DELETE)
    #   - old_value: Previous value (NULL for CREATE)
    #   - new_value: New value (NULL for DELETE)
    #   - ui_location: Which screen/form the change came from (for debugging)
    #
    # WHY audit logging:
    #   - Compliance: Many jurisdictions require medical record change tracking
    #   - Debugging: "Who changed this client's email and when?"
    #   - Undo functionality: Could rebuild previous state from audit log
    #   - Accountability: Track which user made which changes
    #
    # WHY separate old_value and new_value as TEXT:
    #   - Can store any data type by converting to string
    #   - Simple to implement (no complex JSON parsing)
    #   - Human-readable in database viewer
    #
    # NOTE: This table will grow large over time. Consider archiving old
    # entries periodically (e.g., records older than 7 years).
    # =========================================================================
    create_audit_log_table = """
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT NOT NULL,
        record_id INTEGER NOT NULL,
        action TEXT NOT NULL CHECK(action IN ('CREATE', 'UPDATE', 'DELETE')),
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        ui_location TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """
    db.execute(create_audit_log_table)
    logger.debug("Created audit_log table")

    # Index for querying audit log by table and record
    # WHY this index: Common query is "show all changes to client #42"
    # Supports:
    #   - WHERE table_name = 'clients' AND record_id = 42
    #   - WHERE table_name = 'clients' AND record_id = 42 ORDER BY created_at
    create_audit_log_table_record_index = """
    CREATE INDEX IF NOT EXISTS idx_audit_log_table_record
    ON audit_log(table_name, record_id)
    """
    db.execute(create_audit_log_table_record_index)
    logger.debug("Created index on audit_log(table_name, record_id)")

    # Index for querying audit log by date
    # WHY this index: Common query is "show all changes today/this week"
    # WHY DESC: Most recent changes are usually most relevant
    # Supports:
    #   - WHERE created_at > '2024-01-01'
    #   - ORDER BY created_at DESC
    create_audit_log_date_index = """
    CREATE INDEX IF NOT EXISTS idx_audit_log_created_at
    ON audit_log(created_at DESC)
    """
    db.execute(create_audit_log_date_index)
    logger.debug("Created index on audit_log(created_at DESC)")

    # =========================================================================
    # Migration Complete
    # =========================================================================
    logger.info("v001_initial_schema migration completed successfully")
