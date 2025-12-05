# =============================================================================
# Cosmetics Records - Client Data Model
# =============================================================================
# This module defines the Client model, which represents customer information
# in the cosmetics records application. The model handles validation, type
# safety, and provides helper methods for working with client data.
#
# Key Features:
#   - Validates required fields (first_name, last_name)
#   - Optional email validation using Pydantic's EmailStr
#   - Tag management (converts between list and comma-separated string)
#   - Age calculation from date of birth
#   - Full name formatting
# =============================================================================

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from cosmetics_records.utils.validators import is_valid_email


class Client(BaseModel):
    """
    Represents a client/customer in the cosmetics records system.

    This model stores all client information including personal details,
    contact information, medical information (allergies), and treatment plans.
    It includes automatic validation to ensure data integrity.

    Attributes:
        id: Database primary key (None for new clients)
        first_name: Client's first name (required, cannot be empty)
        last_name: Client's last name (required, cannot be empty)
        email: Optional email address (validated if provided)
        phone: Optional phone number
        address: Optional physical address
        date_of_birth: Optional date of birth (used for age calculation)
        allergies: Optional allergy information (important for treatment safety)
        tags: List of tags for categorization (stored as CSV in database)
        planned_treatment: Optional description of upcoming treatment plans
        notes: Optional general notes about the client
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last modified
    """

    # Primary key - None for new records, populated by database
    id: Optional[int] = None

    # Required fields - client name (validated to ensure non-empty)
    # These are the minimum information needed to create a client record
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)

    # Optional contact information
    # Email validated with custom validator to ensure proper format
    email: Optional[str] = None

    # Phone stored as string to allow various formats (international, etc.)
    phone: Optional[str] = None

    # Physical address for communication/records
    address: Optional[str] = None

    # Medical/personal information
    # Date of birth - used to calculate age for treatment planning
    date_of_birth: Optional[date] = None

    # Allergy information - CRITICAL for treatment safety
    # Store any substances the client is allergic to or sensitive to
    allergies: Optional[str] = None

    # Tags for categorization and filtering
    # Stored as List in Python, converted to comma-separated string for DB
    # Examples: ["VIP", "Monthly Client", "Sensitive Skin"]
    tags: List[str] = Field(default_factory=list)

    # Treatment planning
    # Free-text field for planned treatments or procedures
    planned_treatment: Optional[str] = None

    # General notes field for any additional information
    notes: Optional[str] = None

    # Timestamps - managed by database triggers
    # These track when the record was created and last modified
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # =========================================================================
    # Validation Methods
    # =========================================================================
    # These validators ensure data integrity by checking and cleaning data
    # before it's stored in the model.

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """
        Validate that name fields are not empty or whitespace-only.

        This prevents users from creating records with names like "   " which
        would pass the min_length check but aren't actually valid names.

        Args:
            v: The name value to validate

        Returns:
            The stripped name value

        Raises:
            ValueError: If the name is empty after stripping whitespace
        """
        # Strip whitespace from both ends
        stripped = v.strip()

        # Ensure the name has actual content after stripping
        if not stripped:
            raise ValueError("Name cannot be empty or only whitespace")

        return stripped

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate email format if provided.

        This checks that the email follows a basic valid email pattern.
        We use a simple regex that covers most common email formats.

        Args:
            v: The email to validate (can be None)

        Returns:
            The validated email, or None if not provided

        Raises:
            ValueError: If email format is invalid
        """
        # If no email provided, that's fine
        if v is None:
            return None

        # Strip whitespace
        stripped = v.strip()

        # If empty after stripping, return None
        if not stripped:
            return None

        # Validate email format using shared validator
        # WHY shared: Ensures consistent validation across model and UI
        if not is_valid_email(stripped):
            raise ValueError(f"Invalid email format: {stripped}")

        return stripped

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """
        Validate and clean the tags list.

        This ensures tags don't contain empty strings and strips whitespace
        from each tag. This prevents issues when converting to CSV format.

        Args:
            v: The list of tags to validate

        Returns:
            Cleaned list of non-empty tags

        Example:
            ["VIP ", " ", "Regular"] -> ["VIP", "Regular"]
        """
        # Strip whitespace from each tag and filter out empty strings
        # This prevents issues with comma-separated storage and display
        cleaned_tags = [tag.strip() for tag in v if tag.strip()]

        return cleaned_tags

    # =========================================================================
    # Helper Methods
    # =========================================================================
    # These methods provide convenient ways to work with client data

    def full_name(self) -> str:
        """
        Get the client's full name in "First Last" format.

        This is a convenience method used throughout the UI for displaying
        client names in a consistent format.

        Returns:
            Full name as a single string

        Example:
            >>> client = Client(first_name="Jane", last_name="Doe")
            >>> client.full_name()
            "Jane Doe"
        """
        return f"{self.first_name} {self.last_name}"

    def age(self) -> Optional[int]:
        """
        Calculate the client's current age from their date of birth.

        This is useful for treatment planning and age-restricted services.
        Returns None if date of birth is not set.

        Returns:
            Age in years, or None if date_of_birth is not set

        Example:
            >>> from datetime import date
            >>> client = Client(
            ...     first_name="Jane",
            ...     last_name="Doe",
            ...     date_of_birth=date(1990, 1, 1)
            ... )
            >>> client.age()  # Returns current age
            33  # (or whatever the current age would be)
        """
        # Return None if date of birth is not set
        if self.date_of_birth is None:
            return None

        # Calculate age using today's date
        today = date.today()

        # Calculate the age in years
        # This handles leap years correctly by comparing month/day
        age = (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

        return age

    def tags_string(self) -> str:
        """
        Convert the tags list to a comma-separated string for database storage.

        The database stores tags as a TEXT field with comma-separated values.
        This method handles the conversion from Python list to CSV format.

        Returns:
            Comma-separated string of tags, or empty string if no tags

        Example:
            >>> client = Client(
            ...     first_name="Jane",
            ...     last_name="Doe",
            ...     tags=["VIP", "Regular", "Sensitive Skin"]
            ... )
            >>> client.tags_string()
            "VIP, Regular, Sensitive Skin"
        """
        # Join tags with comma and space for readability
        # Empty list returns empty string
        return ", ".join(self.tags)

    @classmethod
    def from_tags_string(cls, tags: str) -> List[str]:
        """
        Parse a comma-separated string into a list of tags.

        This is the inverse of tags_string() - it converts from database
        format (CSV) back to Python list format. Used when loading client
        records from the database.

        Args:
            tags: Comma-separated string of tags

        Returns:
            List of individual tags (stripped of whitespace)

        Example:
            >>> Client.from_tags_string("VIP, Regular, Sensitive Skin")
            ["VIP", "Regular", "Sensitive Skin"]
            >>> Client.from_tags_string("")
            []
        """
        # Handle empty string case - return empty list
        if not tags or not tags.strip():
            return []

        # Split by comma, strip whitespace from each tag, filter empty strings
        # This handles cases like "VIP, , Regular" (double commas)
        return [tag.strip() for tag in tags.split(",") if tag.strip()]

    # =========================================================================
    # Pydantic Configuration
    # =========================================================================

    class Config:
        """Pydantic model configuration."""

        # Allow population by field name (for ORM compatibility)
        from_attributes = True

        # Enable JSON schema generation for API documentation
        json_schema_extra = {
            "example": {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.doe@example.com",
                "phone": "+1-555-0123",
                "date_of_birth": "1990-01-01",
                "allergies": "Sensitive to retinol",
                "tags": ["VIP", "Regular Client"],
                "planned_treatment": "Monthly facial treatment",
                "notes": "Prefers morning appointments",
            }
        }
