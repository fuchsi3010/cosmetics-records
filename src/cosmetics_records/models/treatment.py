# =============================================================================
# Cosmetics Records - Treatment Record Data Model
# =============================================================================
# This module defines the TreatmentRecord model, which represents individual
# treatment sessions performed for clients. Each record captures what treatment
# was performed, when, and for which client.
#
# Key Features:
#   - Links to a specific client via client_id
#   - Records treatment date (defaults to today)
#   - Stores detailed treatment notes
#   - Tracks creation and modification times
#   - Can detect if a record was edited after creation
# =============================================================================

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TreatmentRecord(BaseModel):
    """
    Represents a single treatment session for a client.

    This model stores information about treatments performed on clients,
    including the date, detailed notes about what was done, and links
    to the client record. It's used to maintain a complete history of
    all treatments performed.

    Attributes:
        id: Database primary key (None for new records)
        client_id: Foreign key to the client who received treatment (required)
        treatment_date: Date when the treatment was performed (defaults to today)
        treatment_notes: Detailed description of the treatment (required)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last modified
    """

    # Primary key - None for new records, populated by database
    id: Optional[int] = None

    # Foreign key to the client table
    # This is REQUIRED - every treatment must be associated with a client
    # The database enforces referential integrity on this field
    client_id: int = Field(..., gt=0)

    # Date when the treatment was performed
    # Defaults to today's date when creating a new record
    # This allows quick entry without always specifying the date
    treatment_date: date = Field(default_factory=date.today)

    # Detailed notes about the treatment performed
    # This is REQUIRED - we need to document what was done
    # Should include: procedures performed, products used, observations, etc.
    treatment_notes: str = Field(..., min_length=1)

    # Timestamps - managed by database triggers
    # These track when the record was created and last modified
    # Useful for audit trails and detecting edited records
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # =========================================================================
    # Validation Methods
    # =========================================================================
    # These validators ensure data integrity by checking and cleaning data
    # before it's stored in the model.

    @field_validator("treatment_notes")
    @classmethod
    def validate_notes_not_empty(cls, v: str) -> str:
        """
        Validate that treatment notes are not empty or whitespace-only.

        Treatment notes are critical documentation - we need to ensure they
        contain actual content and aren't just whitespace. This prevents
        records like "   " which would pass min_length but aren't valid.

        Args:
            v: The treatment notes to validate

        Returns:
            The stripped treatment notes

        Raises:
            ValueError: If notes are empty after stripping whitespace
        """
        # Strip whitespace from both ends
        stripped = v.strip()

        # Ensure the notes have actual content after stripping
        if not stripped:
            raise ValueError("Treatment notes cannot be empty or only whitespace")

        return stripped

    @field_validator("client_id")
    @classmethod
    def validate_client_id_positive(cls, v: int) -> int:
        """
        Validate that client_id is a positive integer.

        Client IDs should always be positive (database auto-increment starts at 1).
        This catches programming errors where invalid IDs might be passed.

        Args:
            v: The client_id to validate

        Returns:
            The validated client_id

        Raises:
            ValueError: If client_id is not positive
        """
        if v <= 0:
            raise ValueError("client_id must be a positive integer")

        return v

    @field_validator("treatment_date")
    @classmethod
    def validate_treatment_date(cls, v: date) -> date:
        """
        Validate that treatment_date is not in the future.

        We generally don't want to record treatments that haven't happened yet.
        This prevents accidental data entry errors (e.g., typing 2025 instead
        of 2024). If future treatments need to be scheduled, use a separate
        appointment system.

        Args:
            v: The treatment date to validate

        Returns:
            The validated treatment date

        Raises:
            ValueError: If treatment_date is in the future

        Note:
            We allow today's date (treatment performed today is valid)
        """
        # Get today's date for comparison
        today = date.today()

        # Check if the treatment date is in the future
        if v > today:
            raise ValueError(
                f"Treatment date cannot be in the future. "
                f"Got {v}, but today is {today}"
            )

        return v

    # =========================================================================
    # Helper Methods
    # =========================================================================
    # These methods provide convenient ways to work with treatment data

    def was_edited(self) -> bool:
        """
        Check if this treatment record was edited after creation.

        This helps identify records that were modified, which can be important
        for audit purposes or data quality checks. We consider a record "edited"
        if the updated_at timestamp is more than 1 second after created_at.

        The 1-second buffer accounts for database operations that might set
        both timestamps within the same second during initial creation.

        Returns:
            True if the record was edited, False otherwise
            Returns False if either timestamp is None (new unsaved record)

        Example:
            >>> treatment = TreatmentRecord(
            ...     client_id=1,
            ...     treatment_notes="Initial notes",
            ...     created_at=datetime(2024, 1, 1, 10, 0, 0),
            ...     updated_at=datetime(2024, 1, 1, 10, 0, 0)
            ... )
            >>> treatment.was_edited()
            False  # Timestamps are the same
            >>>
            >>> treatment.updated_at = datetime(2024, 1, 1, 10, 5, 0)
            >>> treatment.was_edited()
            True  # Updated 5 minutes later
        """
        # If either timestamp is missing, can't determine edit status
        # This happens for new records that haven't been saved yet
        if self.created_at is None or self.updated_at is None:
            return False

        # Calculate the time difference in seconds
        # Convert to total_seconds() for precise comparison
        time_diff = (self.updated_at - self.created_at).total_seconds()

        # Consider it edited if updated_at is more than 1 second after created_at
        # The 1-second buffer handles database timing precision
        return time_diff > 1.0

    # =========================================================================
    # Pydantic Configuration
    # =========================================================================

    class Config:
        """Pydantic model configuration."""

        # Allow population by field name (for ORM compatibility)
        # This enables creating models from database rows directly
        from_attributes = True

        # Enable JSON schema generation for API documentation
        json_schema_extra = {
            "example": {
                "client_id": 1,
                "treatment_date": "2024-01-15",
                "treatment_notes": (
                    "Performed deep cleansing facial. "
                    "Used hyaluronic acid serum and moisturizer. "
                    "Client tolerated treatment well. "
                    "Recommended weekly treatments for 4 weeks."
                ),
                "created_at": "2024-01-15T14:30:00",
                "updated_at": "2024-01-15T14:30:00",
            }
        }
