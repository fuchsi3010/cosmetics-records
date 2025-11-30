# =============================================================================
# Cosmetics Records - Audit Log Data Model
# =============================================================================
# This module defines the AuditLog model for tracking all data modifications
# in the application. Every CREATE, UPDATE, and DELETE operation is logged
# with details about what changed, when, and from which UI location.
#
# Key Features:
#   - Tracks all database modifications (CREATE/UPDATE/DELETE)
#   - Records old and new values for updates
#   - Identifies which UI view made the change
#   - Generates human-readable descriptions of changes
#   - Critical for compliance, debugging, and user transparency
# =============================================================================

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AuditAction(str, Enum):
    """
    Enumeration of possible audit actions.

    This strictly defines the types of database operations we track.
    Using an Enum ensures type safety and prevents invalid action types.

    Values:
        CREATE: A new record was created
        UPDATE: An existing record was modified
        DELETE: A record was deleted
    """

    CREATE = "CREATE"  # New record added to database
    UPDATE = "UPDATE"  # Existing record modified
    DELETE = "DELETE"  # Record removed from database


class AuditLog(BaseModel):
    """
    Represents a single audit log entry tracking a database change.

    This model captures comprehensive information about data modifications:
    - WHAT was changed (table_name, record_id, field_name)
    - HOW it changed (action, old_value, new_value)
    - WHEN it changed (created_at timestamp)
    - WHERE it was changed (ui_location - which view/screen)

    This provides a complete audit trail for compliance and debugging.

    Attributes:
        id: Database primary key (None for new records)
        table_name: Name of the database table that was modified
        record_id: Primary key of the modified record in that table
        action: Type of operation (CREATE/UPDATE/DELETE)
        field_name: Name of the field that changed (UPDATE only)
        old_value: Previous value before change (UPDATE/DELETE)
        new_value: New value after change (CREATE/UPDATE)
        ui_location: Name of the UI view/screen where change was made
        created_at: Timestamp when the change occurred
    """

    # Primary key - None for new records, populated by database
    id: Optional[int] = None

    # Table that was modified
    # Examples: "clients", "treatment_records", "product_records"
    # REQUIRED - we need to know which table was affected
    table_name: str = Field(..., min_length=1)

    # Primary key of the modified record in that table
    # REQUIRED - identifies the specific record that changed
    # Must be positive (database PKs start at 1)
    record_id: int = Field(..., gt=0)

    # Type of operation performed
    # REQUIRED - must be one of CREATE, UPDATE, or DELETE
    action: AuditAction

    # Field name that was modified (for UPDATE operations)
    # Examples: "first_name", "allergies", "treatment_notes"
    # Optional - only populated for UPDATE actions
    # For CREATE/DELETE, this is None (whole record created/deleted)
    field_name: Optional[str] = None

    # Previous value before the change
    # Optional - populated for UPDATE (old value) and DELETE (final value)
    # Stored as string for simplicity (convert from actual type)
    # None for CREATE (no previous value)
    old_value: Optional[str] = None

    # New value after the change
    # Optional - populated for CREATE (initial value) and UPDATE (new value)
    # Stored as string for simplicity
    # None for DELETE (no new value)
    new_value: Optional[str] = None

    # Name of the UI view/screen where the change was made
    # Examples: "ClientEditView", "TreatmentHistoryView", "InventoryView"
    # REQUIRED - helps trace where changes originated
    # Useful for debugging UI issues and understanding user workflows
    ui_location: str = Field(..., min_length=1)

    # Timestamp when the change occurred
    # Automatically populated by database trigger
    created_at: Optional[datetime] = None

    # =========================================================================
    # Validation Methods
    # =========================================================================

    @field_validator("table_name", "ui_location")
    @classmethod
    def validate_string_not_empty(cls, v: str) -> str:
        """
        Validate that string fields are not empty or whitespace-only.

        Table name and UI location are critical for audit trail - they must
        contain actual content.

        Args:
            v: The string to validate

        Returns:
            The stripped string

        Raises:
            ValueError: If string is empty after stripping whitespace
        """
        # Strip whitespace from both ends
        stripped = v.strip()

        # Ensure the string has actual content
        if not stripped:
            raise ValueError("Field cannot be empty or only whitespace")

        return stripped

    @field_validator("record_id")
    @classmethod
    def validate_record_id_positive(cls, v: int) -> int:
        """
        Validate that record_id is a positive integer.

        Record IDs should always be positive (database auto-increment starts at 1).

        Args:
            v: The record_id to validate

        Returns:
            The validated record_id

        Raises:
            ValueError: If record_id is not positive
        """
        if v <= 0:
            raise ValueError("record_id must be a positive integer")

        return v

    @field_validator("field_name")
    @classmethod
    def validate_field_name(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and clean the field_name.

        If provided, ensure it's not just whitespace. Convert empty strings
        to None for consistency.

        Args:
            v: The field_name to validate

        Returns:
            The stripped field_name, or None if empty
        """
        # If no field_name provided, return None
        if v is None:
            return None

        # Strip whitespace
        stripped = v.strip()

        # Return None for empty strings
        if not stripped:
            return None

        return stripped

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def get_description(self, client_name: Optional[str] = None) -> str:
        """
        Generate a human-readable description of the audit log entry.

        This creates user-friendly text that can be displayed in the audit
        history view. The description varies based on the action type and
        includes the client name when available.

        Args:
            client_name: Optional client name to include in the description
                        (e.g., "Jane Doe"). Makes the description more readable
                        than just showing a record ID.

        Returns:
            A formatted string describing the change

        Examples:
            >>> # CREATE action
            >>> log = AuditLog(
            ...     table_name="treatment_records",
            ...     record_id=123,
            ...     action=AuditAction.CREATE,
            ...     ui_location="TreatmentHistoryView"
            ... )
            >>> log.get_description("Jane Doe")
            "New treatment added for Jane Doe"
            >>>
            >>> # UPDATE action with field change
            >>> log = AuditLog(
            ...     table_name="clients",
            ...     record_id=5,
            ...     action=AuditAction.UPDATE,
            ...     field_name="allergies",
            ...     old_value="",
            ...     new_value="Sensitive to retinol",
            ...     ui_location="ClientEditView"
            ... )
            >>> log.get_description("Jane Doe")
            "Client updated: allergies changed from (empty) to 'Sensitive to retinol'"
            >>>
            >>> # DELETE action
            >>> log = AuditLog(
            ...     table_name="product_records",
            ...     record_id=456,
            ...     action=AuditAction.DELETE,
            ...     old_value="Retinol Serum 30ml",
            ...     ui_location="ProductHistoryView"
            ... )
            >>> log.get_description("Jane Doe")
            "Product record deleted: 'Retinol Serum 30ml'"
        """
        # Handle CREATE action
        if self.action == AuditAction.CREATE:
            # Determine record type from table name
            # Map table names to human-readable record types
            record_type_map = {
                "clients": "client",
                "treatment_records": "treatment",
                "product_records": "product record",
                "inventory_items": "inventory item",
            }

            # Get record type or default to table name
            record_type = record_type_map.get(self.table_name, self.table_name)

            # Include client name if provided and it's not a client creation
            if client_name and self.table_name != "clients":
                return f"New {record_type} added for {client_name}"
            else:
                return f"New {record_type} created"

        # Handle UPDATE action
        elif self.action == AuditAction.UPDATE:
            # Determine subject from table name
            subject_map = {
                "clients": "Client",
                "treatment_records": "Treatment",
                "product_records": "Product record",
                "inventory_items": "Inventory item",
            }

            subject = subject_map.get(self.table_name, "Record")

            # Format old and new values
            # Show "(empty)" for None or empty string
            old = self.old_value if self.old_value else "(empty)"
            new = self.new_value if self.new_value else "(empty)"

            # If we have a field name, show field-level detail
            if self.field_name:
                return (
                    f"{subject} updated: {self.field_name} "
                    f"changed from {old} to '{new}'"
                )
            else:
                # Generic update message if no field name
                return f"{subject} updated"

        # Handle DELETE action
        elif self.action == AuditAction.DELETE:
            # Determine record type from table name
            record_type_map = {
                "clients": "Client",
                "treatment_records": "Treatment record",
                "product_records": "Product record",
                "inventory_items": "Inventory item",
            }

            record_type = record_type_map.get(self.table_name, "Record")

            # Include old_value if available (shows what was deleted)
            if self.old_value:
                return f"{record_type} deleted: '{self.old_value}'"
            else:
                # Generic delete message if no old value
                return f"{record_type} deleted"

        # Fallback for unknown action (shouldn't happen due to Enum)
        else:
            return f"Unknown action: {self.action}"

    # =========================================================================
    # Pydantic Configuration
    # =========================================================================

    class Config:
        """Pydantic model configuration."""

        # Allow population by field name (for ORM compatibility)
        from_attributes = True

        # Enable JSON schema generation
        json_schema_extra = {
            "example": {
                "table_name": "clients",
                "record_id": 5,
                "action": "UPDATE",
                "field_name": "allergies",
                "old_value": "",
                "new_value": "Sensitive to retinol",
                "ui_location": "ClientEditView",
                "created_at": "2024-01-15T14:30:00",
            }
        }
