# =============================================================================
# Cosmetics Records - Database Migration Manager
# =============================================================================
# This module manages database schema migrations in a controlled, versioned way.
#
# Key Features:
#   - Tracks which migrations have been applied (schema_migrations table)
#   - Applies pending migrations in sequential order (v001, v002, etc.)
#   - Creates automatic backups before running migrations
#   - User-friendly error messages for troubleshooting
#   - Idempotent operations (safe to run multiple times)
#
# Migration File Naming Convention:
#   vXXX_descriptive_name.py  (e.g., v001_initial_schema.py)
#
# Each migration file must have an apply(db: DatabaseConnection) function
# that contains the SQL statements to execute.
#
# Usage Example:
#   manager = MigrationManager()
#   manager.apply_migrations()  # Applies all pending migrations
# =============================================================================

import sqlite3
import sys
from pathlib import Path
from types import ModuleType
from typing import List, Optional, Tuple
import logging
import shutil
from datetime import datetime
import importlib.util

# Import the DatabaseConnection class from the parent package
from cosmetics_records.database.connection import DatabaseConnection

# Direct imports for PyInstaller compatibility
# WHY: In PyInstaller bundles, importlib.util.spec_from_file_location() cannot
# load bundled .py files. We import them directly here and reference them by name.
from cosmetics_records.database.migrations import v001_initial_schema

# Configure module logger
logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database schema migrations for version control and upgrades.

    This class ensures that database schema changes are applied in a
    controlled, repeatable manner. It tracks which migrations have been
    applied and only runs new ones.

    Attributes:
        db_connection: The DatabaseConnection instance to use
        migrations_dir: Path to the directory containing migration files
    """

    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """
        Initialize the migration manager.

        Args:
            db_connection: Optional DatabaseConnection instance. If None,
                          creates a new one with default settings.

        Note:
            We allow injecting a db_connection for testing purposes,
            but in production, we'll typically use the default.
        """
        # Use provided connection or create a default one
        self.db_connection = db_connection or DatabaseConnection()

        # Get the directory where migration files are stored
        # This is the same directory as this file (migration_manager.py)
        self.migrations_dir = Path(__file__).parent

        logger.info(f"MigrationManager initialized with dir: {self.migrations_dir}")

    def _ensure_schema_migrations_table(self) -> None:
        """
        Create the schema_migrations table if it doesn't exist.

        This table tracks which migrations have been applied, preventing
        duplicate application and allowing us to know the current schema version.

        Table structure:
            - id: Auto-incrementing primary key
            - version: Unique migration version (e.g., "v001", "v002")
            - applied_at: Timestamp when the migration was applied

        Note:
            This method is idempotent - safe to call multiple times.
            The IF NOT EXISTS clause ensures it only creates the table
            if it's missing.
        """
        # SQL to create the tracking table
        # WHY UNIQUE on version: Prevents the same migration from being
        # recorded twice, which would indicate a serious bug
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """

        try:
            with self.db_connection as db:
                db.execute(create_table_sql)
                db.commit()
                logger.debug("schema_migrations table ensured")

        except sqlite3.Error as e:
            logger.error(f"Failed to create schema_migrations table: {e}")
            raise RuntimeError(
                "Could not initialize migration tracking table. "
                f"Database may be corrupted. Error: {e}"
            )

    def _get_applied_migrations(self) -> List[str]:
        """
        Get a list of migration versions that have already been applied.

        Returns:
            List[str]: List of version strings (e.g., ["v001", "v002"])

        Note:
            This queries the schema_migrations table. If the table doesn't
            exist yet, _ensure_schema_migrations_table() should be called first.
        """
        try:
            with self.db_connection as db:
                # Query all applied migration versions
                db.execute("SELECT version FROM schema_migrations ORDER BY version")
                rows = db.fetchall()

                # Extract version strings from Row objects
                applied = [row["version"] for row in rows]
                logger.debug(f"Found {len(applied)} applied migrations: {applied}")
                return applied

        except sqlite3.Error as e:
            logger.error(f"Failed to query applied migrations: {e}")
            # Return empty list - assume no migrations applied yet
            # This handles the case where schema_migrations table doesn't exist
            return []

    # Registry of known migrations for PyInstaller compatibility
    # When running from a frozen bundle, glob() can't find bundled files,
    # so we explicitly list all migrations here.
    # The modules are imported at the top of this file for PyInstaller compatibility.
    KNOWN_MIGRATIONS = [
        "v001_initial_schema",
    ]

    # Map of migration names to their imported modules (for PyInstaller)
    # WHY: In PyInstaller, we can't dynamically load .py files, so we import
    # them directly and reference them from this dictionary.
    MIGRATION_MODULES = {
        "v001_initial_schema": v001_initial_schema,
    }

    def _discover_migration_files(self) -> List[Tuple[str, Path]]:
        """
        Discover all migration files in the migrations directory.

        Returns:
            List[Tuple[str, Path]]: List of (version, file_path) tuples,
                                   sorted by version number.
                                   Example: [("v001", Path("v001_initial.py"))]

        Note:
            Only files matching the pattern "v[0-9][0-9][0-9]_*.py" are
            considered migration files. This prevents accidentally treating
            other Python files (like __init__.py or this file) as migrations.

            When running from PyInstaller bundle, we use KNOWN_MIGRATIONS
            registry since glob() doesn't work for bundled files.
        """
        migrations = []

        # Try glob first (works in development)
        for file_path in self.migrations_dir.glob("v[0-9][0-9][0-9]_*.py"):
            # Extract the version from the filename
            # Example: "v001_initial_schema.py" -> "v001"
            version = file_path.stem.split("_")[0]  # stem removes .py extension
            migrations.append((version, file_path))

        # If glob found nothing (PyInstaller bundle), use registry
        if not migrations:
            logger.info("No migration files found via glob, using registry")
            for migration_name in self.KNOWN_MIGRATIONS:
                version = migration_name.split("_")[0]
                file_path = self.migrations_dir / f"{migration_name}.py"
                migrations.append((version, file_path))

        # Sort by version to ensure migrations are applied in order
        # This is critical - applying v002 before v001 could fail or corrupt data
        migrations.sort(key=lambda x: x[0])

        logger.info(f"Discovered {len(migrations)} migration files")
        return migrations

    def _get_pending_migrations(self) -> List[Tuple[str, Path]]:
        """
        Get the list of migrations that haven't been applied yet.

        Returns:
            List[Tuple[str, Path]]: List of (version, file_path) tuples for
                                   pending migrations, sorted by version.

        Note:
            This compares discovered migration files against the
            schema_migrations table to find which ones are new.
        """
        # Get migrations that have already been applied
        applied = set(self._get_applied_migrations())

        # Get all available migration files
        all_migrations = self._discover_migration_files()

        # Filter to only migrations not yet applied
        pending = [
            (version, path)
            for version, path in all_migrations
            if version not in applied
        ]

        logger.info(
            f"Found {len(pending)} pending migrations "
            f"out of {len(all_migrations)} total"
        )
        return pending

    def _backup_database(self) -> Optional[Path]:
        """
        Create a backup copy of the database before applying migrations.

        This is a safety measure - if a migration fails or corrupts data,
        we can restore from the backup.

        Returns:
            Path: The path to the backup file

        Raises:
            RuntimeError: If the backup fails

        Note:
            Backups are named with timestamps to avoid overwriting previous
            backups. Format: cosmetics_records_backup_YYYYMMDD_HHMMSS.db
        """
        # Get the database file path
        db_path = self.db_connection.db_path

        # Check if database file exists (it might not on first run)
        if not db_path.exists():
            logger.info("Database file doesn't exist yet - skipping backup")
            return None

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}.db"

        try:
            # Copy the database file
            # WHY shutil.copy2: Preserves metadata (timestamps, permissions)
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            raise RuntimeError(
                f"Could not create database backup before migration. "
                f"Aborting for safety. Error: {e}"
            )

    def _load_migration_module(self, version: str, file_path: Path) -> ModuleType:
        """
        Dynamically load a migration file as a Python module.

        Args:
            version: The migration version (e.g., "v001")
            file_path: Path to the migration .py file

        Returns:
            The loaded module object

        Raises:
            RuntimeError: If the file can't be loaded or doesn't have apply()

        Note:
            In development, we use dynamic imports via importlib.util.
            In PyInstaller bundles, we use pre-imported modules from
            MIGRATION_MODULES since dynamic file loading doesn't work.
        """
        # Get the migration name from the file path (e.g., "v001_initial_schema")
        migration_name = file_path.stem

        try:
            # Check if running from PyInstaller bundle
            # WHY: PyInstaller bundles .py files into the executable, so
            # importlib.util.spec_from_file_location() cannot load them.
            # We use pre-imported modules instead.
            if getattr(sys, "frozen", False):
                # Running from PyInstaller bundle - use pre-imported module
                if migration_name in self.MIGRATION_MODULES:
                    module = self.MIGRATION_MODULES[migration_name]
                    logger.debug(f"Loaded migration {version} from pre-imported module")
                else:
                    raise RuntimeError(
                        f"Migration {migration_name} is not in MIGRATION_MODULES. "
                        f"Add it to the registry in migration_manager.py."
                    )
            else:
                # Development mode - use dynamic loading
                spec = importlib.util.spec_from_file_location(version, file_path)

                if spec is None or spec.loader is None:
                    raise RuntimeError(f"Could not load module spec for {file_path}")

                # Create a module from the specification
                module = importlib.util.module_from_spec(spec)

                # Execute the module (runs its code)
                spec.loader.exec_module(module)

            # Verify the module has an apply() function
            if not hasattr(module, "apply"):
                raise RuntimeError(
                    f"Migration {version} is missing the required apply() function"
                )

            return module

        except Exception as e:
            logger.error(f"Failed to load migration {version}: {e}")
            raise RuntimeError(
                f"Could not load migration file {file_path}. "
                f"The file may be corrupt or have syntax errors. Error: {e}"
            )

    def _apply_migration(self, version: str, file_path: Path) -> None:
        """
        Apply a single migration and record it in schema_migrations.

        Args:
            version: The migration version (e.g., "v001")
            file_path: Path to the migration .py file

        Raises:
            RuntimeError: If the migration fails

        Note:
            This method wraps the migration in a transaction. If the migration
            fails, all changes are rolled back and the migration is not marked
            as applied.
        """
        logger.info(f"Applying migration {version} from {file_path.name}")

        try:
            # Load the migration module
            module = self._load_migration_module(version, file_path)

            # Apply the migration within a transaction
            with self.db_connection as db:
                # Call the migration's apply() function
                # The migration is responsible for executing SQL statements
                module.apply(db)

                # Record that this migration was applied
                db.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
                )

                # Commit the transaction
                # WHY commit here: We want the migration and its tracking record
                # to be atomic - either both succeed or both fail
                db.commit()

            logger.info(f"Successfully applied migration {version}")

        except Exception as e:
            logger.error(f"Migration {version} failed: {e}")
            raise RuntimeError(
                f"Failed to apply migration {version}. "
                f"Database has been rolled back to previous state. "
                f"Error: {e}"
            )

    def apply_migrations(self) -> int:
        """
        Apply all pending migrations to the database.

        This is the main entry point for running migrations. It:
        1. Creates a backup of the database
        2. Ensures the schema_migrations table exists
        3. Discovers pending migrations
        4. Applies them in order
        5. Tracks each successful application

        Returns:
            int: The number of migrations applied

        Raises:
            RuntimeError: If any migration fails

        Example:
            manager = MigrationManager()
            count = manager.apply_migrations()
            print(f"Applied {count} migrations")
        """
        logger.info("Starting migration process")

        try:
            # Step 1: Ensure the migration tracking table exists
            self._ensure_schema_migrations_table()

            # Step 2: Find migrations that need to be applied
            pending = self._get_pending_migrations()

            # If no pending migrations, we're done
            if not pending:
                logger.info("No pending migrations to apply")
                return 0

            # Step 3: Create a backup before making any changes
            backup_path = self._backup_database()
            if backup_path:
                logger.info(f"Created backup at {backup_path}")

            # Step 4: Apply each pending migration in order
            applied_count = 0
            for version, file_path in pending:
                self._apply_migration(version, file_path)
                applied_count += 1

            logger.info(f"Successfully applied {applied_count} migrations")
            return applied_count

        except Exception as e:
            logger.error(f"Migration process failed: {e}")
            raise RuntimeError(
                f"Migration process failed. Check logs for details. "
                f"If database is corrupted, restore from backup. Error: {e}"
            )

    def get_current_version(self) -> str:
        """
        Get the current database schema version.

        Returns:
            str: The latest applied migration version (e.g., "v003"),
                or "v000" if no migrations have been applied yet.

        Example:
            manager = MigrationManager()
            version = manager.get_current_version()
            print(f"Database is at version: {version}")
        """
        try:
            self._ensure_schema_migrations_table()
            applied = self._get_applied_migrations()

            # Return the highest version, or v000 if none applied
            if applied:
                return max(applied)
            else:
                return "v000"

        except Exception as e:
            logger.error(f"Failed to get current version: {e}")
            return "unknown"
