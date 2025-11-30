# =============================================================================
# Cosmetics Records - Database Connection Module
# =============================================================================
# This module provides the DatabaseConnection class, which acts as the primary
# interface for all database operations in the application.
#
# Key Features:
#   - Context manager support for safe connection handling
#   - Automatic connection cleanup (prevents file locks)
#   - Parameter binding for SQL injection prevention
#   - Transaction support (commit/rollback)
#   - Foreign key constraint enforcement
#   - Configurable database path with sensible defaults
#
# Usage Example:
#   with DatabaseConnection() as db:
#       db.execute("INSERT INTO clients (name) VALUES (?)", ("John",))
#       db.commit()
# =============================================================================

import sqlite3
from pathlib import Path
from typing import Any, Optional, Tuple, List
import logging

# Configure module logger for debugging database operations
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    A context manager for safe SQLite3 database connections.

    This class encapsulates all database connection logic, ensuring:
    - Connections are properly closed after use
    - Foreign keys are enforced (SQLite doesn't do this by default)
    - Transactions can be committed or rolled back safely
    - SQL queries use parameter binding to prevent injection attacks

    Attributes:
        db_path (Path): The filesystem path to the SQLite database file
        connection (Optional[sqlite3.Connection]): The active database connection
        cursor (Optional[sqlite3.Cursor]): The cursor for executing queries
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize a database connection manager.

        Args:
            db_path: Path to the SQLite database file. If None, uses the
                    default user data directory (~/.local/share/cosmetics_records/)

        Note:
            The database file is NOT created here - only the path is stored.
            Actual connection happens in __enter__() when used as context manager.
        """
        # If no path provided, use platform-appropriate user data directory
        if db_path is None:
            # ~/.local/share on Linux, ~/Library/Application Support on macOS
            user_data_dir = Path.home() / ".local" / "share" / "cosmetics_records"
            # Ensure the directory exists before we try to create the database
            user_data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = user_data_dir / "cosmetics_records.db"
        else:
            self.db_path = Path(db_path)

        # These will be initialized when entering the context manager
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

        logger.info(f"DatabaseConnection initialized with path: {self.db_path}")

    def __enter__(self) -> "DatabaseConnection":
        """
        Enter the context manager - establishes the database connection.

        This method is called automatically when using 'with' statement.
        It creates the actual connection and enables foreign key support.

        Returns:
            self: The DatabaseConnection instance for chaining

        Note:
            Foreign key support is OFF by default in SQLite and must be
            enabled for each connection. This is crucial for referential
            integrity (e.g., preventing orphaned treatment records when
            a client is deleted).
        """
        try:
            # Create connection to the SQLite database file
            # If the file doesn't exist, SQLite creates it automatically
            self.connection = sqlite3.connect(str(self.db_path))

            # Enable foreign key constraint enforcement
            # WHY: SQLite disables this by default for backwards compatibility,
            # but we need it to maintain referential integrity
            self.connection.execute("PRAGMA foreign_keys = ON")

            # Set row factory to access columns by name (not just index)
            # This allows: row['name'] instead of row[0]
            self.connection.row_factory = sqlite3.Row

            # Create a cursor for executing queries
            self.cursor = self.connection.cursor()

            logger.debug("Database connection established successfully")
            return self

        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            # Re-raise the exception so caller knows connection failed
            raise

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the context manager - closes the database connection.

        This method is called automatically when exiting 'with' block,
        even if an exception occurred. It ensures proper cleanup.

        Args:
            exc_type: The type of exception that occurred (if any)
            exc_val: The exception instance (if any)
            exc_tb: The traceback object (if any)

        Note:
            If an exception occurred during the with block, we rollback
            any uncommitted changes. This prevents partial updates that
            could leave the database in an inconsistent state.
        """
        if self.connection:
            try:
                # If an exception occurred, rollback any uncommitted changes
                if exc_type is not None:
                    logger.warning(
                        f"Exception occurred, rolling back transaction: {exc_val}"
                    )
                    self.connection.rollback()

                # Close the connection to release the database file lock
                self.connection.close()
                logger.debug("Database connection closed")

            except sqlite3.Error as e:
                logger.error(f"Error closing database connection: {e}")
                # We don't re-raise here because we're already cleaning up

        # Reset connection and cursor to None
        self.connection = None
        self.cursor = None

    def execute(self, query: str, parameters: Tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """
        Execute a SQL query with parameter binding.

        This is the primary method for running SQL commands. It uses
        parameter binding to prevent SQL injection attacks.

        Args:
            query: The SQL query to execute. Use ? placeholders for parameters.
                  Example: "SELECT * FROM clients WHERE id = ?"
            parameters: Tuple of values to bind to the ? placeholders.
                       Example: (42,)

        Returns:
            sqlite3.Cursor: The cursor with query results

        Raises:
            RuntimeError: If called outside of context manager (no connection)
            sqlite3.Error: If the SQL query fails

        Example:
            with DatabaseConnection() as db:
                cursor = db.execute(
                    "INSERT INTO clients (name, email) VALUES (?, ?)",
                    ("John Doe", "john@example.com")
                )
                db.commit()

        Note:
            This method does NOT automatically commit. You must call commit()
            explicitly for INSERT, UPDATE, DELETE operations. This allows
            multiple operations to be grouped into a single transaction.
        """
        # Ensure we're inside a context manager (connection exists)
        if not self.cursor or not self.connection:
            raise RuntimeError(
                "Database connection not established. "
                "Use 'with DatabaseConnection() as db:' syntax."
            )

        try:
            # Execute the query with parameter binding
            # WHY parameter binding: It prevents SQL injection by ensuring
            # user input is treated as data, not executable SQL code
            logger.debug(f"Executing query: {query[:100]}...")  # Log first 100 chars
            self.cursor.execute(query, parameters)
            return self.cursor

        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {e}\nQuery: {query}")
            # Re-raise so caller can handle the error appropriately
            raise

    def executemany(
        self, query: str, parameters_list: List[Tuple[Any, ...]]
    ) -> sqlite3.Cursor:
        """
        Execute a SQL query multiple times with different parameters.

        This is more efficient than calling execute() in a loop because
        SQLite can optimize the execution plan.

        Args:
            query: The SQL query with ? placeholders
            parameters_list: List of parameter tuples, one for each execution

        Returns:
            sqlite3.Cursor: The cursor after all executions

        Raises:
            RuntimeError: If called outside of context manager
            sqlite3.Error: If the SQL query fails

        Example:
            with DatabaseConnection() as db:
                db.executemany(
                    "INSERT INTO clients (name) VALUES (?)",
                    [("Alice",), ("Bob",), ("Charlie",)]
                )
                db.commit()
        """
        if not self.cursor or not self.connection:
            raise RuntimeError(
                "Database connection not established. "
                "Use 'with DatabaseConnection() as db:' syntax."
            )

        try:
            logger.debug(
                f"Executing batch query with {len(parameters_list)} parameter sets"
            )
            self.cursor.executemany(query, parameters_list)
            return self.cursor

        except sqlite3.Error as e:
            logger.error(f"Batch query execution failed: {e}\nQuery: {query}")
            raise

    def commit(self) -> None:
        """
        Commit the current transaction to the database.

        This persists all changes made since the last commit or rollback.
        Until commit() is called, changes are only visible within the
        current connection.

        Raises:
            RuntimeError: If called outside of context manager
            sqlite3.Error: If the commit fails

        Note:
            Always call commit() after INSERT, UPDATE, or DELETE operations.
            Without commit(), changes are lost when the connection closes.
        """
        if not self.connection:
            raise RuntimeError(
                "Database connection not established. "
                "Use 'with DatabaseConnection() as db:' syntax."
            )

        try:
            self.connection.commit()
            logger.debug("Transaction committed successfully")

        except sqlite3.Error as e:
            logger.error(f"Failed to commit transaction: {e}")
            raise

    def rollback(self) -> None:
        """
        Roll back the current transaction.

        This discards all changes made since the last commit. Useful for
        recovering from errors or cancelling a multi-step operation.

        Raises:
            RuntimeError: If called outside of context manager
            sqlite3.Error: If the rollback fails

        Example:
            with DatabaseConnection() as db:
                try:
                    db.execute("INSERT INTO clients (...) VALUES (...)", ...)
                    db.execute("INSERT INTO treatments (...) VALUES (...)", ...)
                    db.commit()
                except sqlite3.Error:
                    db.rollback()  # Undo both inserts
                    raise
        """
        if not self.connection:
            raise RuntimeError(
                "Database connection not established. "
                "Use 'with DatabaseConnection() as db:' syntax."
            )

        try:
            self.connection.rollback()
            logger.debug("Transaction rolled back")

        except sqlite3.Error as e:
            logger.error(f"Failed to roll back transaction: {e}")
            raise

    def fetchone(self) -> Optional[sqlite3.Row]:
        """
        Fetch the next row from the last executed query.

        Returns:
            Optional[sqlite3.Row]: The next row as a Row object, or None if
                                  no more rows are available.

        Raises:
            RuntimeError: If called outside of context manager

        Example:
            with DatabaseConnection() as db:
                db.execute("SELECT * FROM clients WHERE id = ?", (42,))
                row = db.fetchone()
                if row:
                    print(row['first_name'], row['last_name'])
        """
        if not self.cursor:
            raise RuntimeError(
                "Database connection not established. "
                "Use 'with DatabaseConnection() as db:' syntax."
            )

        return self.cursor.fetchone()

    def fetchall(self) -> List[sqlite3.Row]:
        """
        Fetch all remaining rows from the last executed query.

        Returns:
            List[sqlite3.Row]: All remaining rows as a list of Row objects.
                              Empty list if no rows are available.

        Raises:
            RuntimeError: If called outside of context manager

        Warning:
            This loads all results into memory at once. For very large
            result sets, consider using fetchone() in a loop instead.

        Example:
            with DatabaseConnection() as db:
                db.execute("SELECT * FROM clients ORDER BY last_name")
                rows = db.fetchall()
                for row in rows:
                    print(row['first_name'], row['last_name'])
        """
        if not self.cursor:
            raise RuntimeError(
                "Database connection not established. "
                "Use 'with DatabaseConnection() as db:' syntax."
            )

        return self.cursor.fetchall()

    def get_last_insert_id(self) -> int:
        """
        Get the ID of the last inserted row.

        This is useful when you insert a record and need its auto-generated
        ID for creating related records.

        Returns:
            int: The ID (ROWID) of the last inserted row

        Raises:
            RuntimeError: If called outside of context manager

        Example:
            with DatabaseConnection() as db:
                db.execute(
                    "INSERT INTO clients (name) VALUES (?)",
                    ("John Doe",)
                )
                db.commit()
                client_id = db.get_last_insert_id()
                # Now use client_id for related records
        """
        if not self.cursor:
            raise RuntimeError(
                "Database connection not established. "
                "Use 'with DatabaseConnection() as db:' syntax."
            )

        return self.cursor.lastrowid
