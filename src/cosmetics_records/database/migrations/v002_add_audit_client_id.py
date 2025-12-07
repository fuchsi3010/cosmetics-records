# =============================================================================
# Cosmetics Records - Migration v002: Add client_id to audit_log
# =============================================================================
# This migration adds a client_id column to the audit_log table to track
# which client was affected by each change.
#
# Changes:
#   - Add client_id column to audit_log table (nullable for existing entries)
#   - Create index for faster queries by client_id
#
# This allows the audit log to show which client was affected by each action,
# even for treatment and product records, and after records are deleted.
# =============================================================================

import logging
from cosmetics_records.database.connection import DatabaseConnection

# Configure module logger
logger = logging.getLogger(__name__)


def apply(db: DatabaseConnection) -> None:
    """
    Apply the v002 migration: Add client_id to audit_log table.

    Args:
        db: DatabaseConnection instance to execute the migration

    Note:
        This migration adds a nullable client_id column. Existing audit entries
        will have NULL client_id values. New entries should populate this field.
    """
    logger.info("Applying migration v002: Add client_id to audit_log")

    # Add client_id column to audit_log table
    # WHY nullable: Existing entries don't have client_id, and some entries
    # (like inventory changes) may not be related to a specific client
    # NOTE: No foreign key constraint - audit logs should persist even after
    # client deletion to maintain the audit trail
    db.execute(
        """
        ALTER TABLE audit_log
        ADD COLUMN client_id INTEGER
    """
    )

    # Create index for faster lookups by client_id
    # WHY index: Allows efficient filtering of audit logs by client
    db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_log_client_id
        ON audit_log(client_id)
    """
    )

    db.commit()

    logger.info("Migration v002 completed: client_id column added to audit_log")
