# =============================================================================
# Cosmetics Records - Product and Inventory Data Models
# =============================================================================
# This module defines two related models:
#   1. ProductRecord - Records products sold/used for specific clients
#   2. InventoryItem - Salon's inventory management (products in stock)
#
# IMPORTANT: ProductRecord uses free-text (not linked to inventory)
# This allows flexibility to record products without strict inventory tracking.
#
# Key Features:
#   - ProductRecord: Links products to clients with free-text description
#   - InventoryItem: Structured inventory with capacity, units, and validation
#   - Unit validation: Only ml, g, or Pc. (pieces) allowed
#   - Capacity validation: Must be greater than 0
# =============================================================================

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ProductRecord(BaseModel):
    """
    Represents a record of products sold to or used on a client.

    This model uses FREE-TEXT for product information, meaning it's NOT
    directly linked to the inventory system. This provides flexibility to
    record any product, even if it's not in the inventory (e.g., samples,
    discontinued items, or products from other sources).

    Attributes:
        id: Database primary key (None for new records)
        client_id: Foreign key to the client (required)
        product_date: Date when product was sold/used (defaults to today)
        product_text: Free-text description of the product (required)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last modified
    """

    # Primary key - None for new records, populated by database
    id: Optional[int] = None

    # Foreign key to the client table
    # This is REQUIRED - every product record must be associated with a client
    client_id: int = Field(..., gt=0)

    # Date when the product was sold or used
    # Defaults to today's date for convenience
    product_date: date = Field(default_factory=date.today)

    # Free-text description of the product
    # This is NOT linked to inventory - allows any text
    # Examples: "Retinol Serum 30ml", "Sample - Vitamin C", "Custom blend"
    # REQUIRED - must have actual content
    product_text: str = Field(..., min_length=1)

    # Timestamps - managed by database triggers
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # =========================================================================
    # Validation Methods
    # =========================================================================

    @field_validator("product_text")
    @classmethod
    def validate_product_text_not_empty(cls, v: str) -> str:
        """
        Validate that product text is not empty or whitespace-only.

        We need actual product information, not just whitespace. This ensures
        the record has meaningful content.

        Args:
            v: The product text to validate

        Returns:
            The stripped product text

        Raises:
            ValueError: If text is empty after stripping whitespace
        """
        # Strip whitespace from both ends
        stripped = v.strip()

        # Ensure the text has actual content after stripping
        if not stripped:
            raise ValueError("Product text cannot be empty or only whitespace")

        return stripped

    @field_validator("client_id")
    @classmethod
    def validate_client_id_positive(cls, v: int) -> int:
        """
        Validate that client_id is a positive integer.

        Client IDs should always be positive (database auto-increment starts at 1).

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

    @field_validator("product_date")
    @classmethod
    def validate_product_date(cls, v: date) -> date:
        """
        Validate that product_date is not in the future.

        We don't want to record product sales/usage that hasn't happened yet.
        This prevents data entry errors.

        Args:
            v: The product date to validate

        Returns:
            The validated product date

        Raises:
            ValueError: If product_date is in the future
        """
        # Get today's date for comparison
        today = date.today()

        # Check if the product date is in the future
        if v > today:
            raise ValueError(
                f"Product date cannot be in the future. "
                f"Got {v}, but today is {today}"
            )

        return v

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def was_edited(self) -> bool:
        """
        Check if this product record was edited after creation.

        This helps identify records that were modified, which can be important
        for audit purposes. We consider a record "edited" if the updated_at
        timestamp is more than 1 second after created_at.

        Returns:
            True if the record was edited, False otherwise
            Returns False if either timestamp is None (new unsaved record)
        """
        # If either timestamp is missing, can't determine edit status
        if self.created_at is None or self.updated_at is None:
            return False

        # Calculate the time difference in seconds
        time_diff = (self.updated_at - self.created_at).total_seconds()

        # Consider it edited if updated more than 1 second after creation
        return time_diff > 1.0

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
                "client_id": 1,
                "product_date": "2024-01-15",
                "product_text": "Retinol Serum 30ml - Night treatment",
                "created_at": "2024-01-15T14:30:00",
                "updated_at": "2024-01-15T14:30:00",
            }
        }


class InventoryItem(BaseModel):
    """
    Represents a product in the salon's inventory.

    This model provides structured inventory management with specific fields
    for product name, capacity, and units. Unlike ProductRecord (which uses
    free-text), InventoryItem enforces strict validation rules.

    Attributes:
        id: Database primary key (None for new records)
        name: Product name (required, non-empty)
        description: Optional detailed description of the product
        capacity: Product capacity/size (must be > 0)
        unit: Unit of measurement - ONLY "ml", "g", or "Pc." allowed
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last modified
    """

    # Primary key - None for new records, populated by database
    id: Optional[int] = None

    # Product name - REQUIRED
    # Should be concise identifier like "Retinol Serum", "Vitamin C Cream"
    name: str = Field(..., min_length=1)

    # Optional detailed description
    # Use for ingredients, usage instructions, benefits, etc.
    description: Optional[str] = None

    # Product capacity/size - MUST be greater than 0
    # Examples: 30.0 (for 30ml), 50.0 (for 50g), 1.0 (for 1 piece)
    # Using float to support decimal values like 2.5ml
    capacity: float = Field(..., gt=0)

    # Unit of measurement - STRICT validation
    # ONLY these three values are allowed:
    #   - "ml" for milliliters (liquids, serums, etc.)
    #   - "g" for grams (creams, powders, etc.)
    #   - "Pc." for pieces (items sold individually)
    # Literal type ensures compile-time and runtime validation
    unit: Literal["ml", "g", "Pc."]

    # Timestamps - managed by database triggers
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # =========================================================================
    # Validation Methods
    # =========================================================================

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """
        Validate that product name is not empty or whitespace-only.

        Product names are required and must have actual content.

        Args:
            v: The product name to validate

        Returns:
            The stripped product name

        Raises:
            ValueError: If name is empty after stripping whitespace
        """
        # Strip whitespace from both ends
        stripped = v.strip()

        # Ensure the name has actual content after stripping
        if not stripped:
            raise ValueError("Product name cannot be empty or only whitespace")

        return stripped

    @field_validator("capacity")
    @classmethod
    def validate_capacity_positive(cls, v: float) -> float:
        """
        Validate that capacity is a positive number.

        Capacity must be greater than 0 - we can't have products with
        zero or negative size. The Field constraint (gt=0) handles this,
        but we add this validator for clearer error messages.

        Args:
            v: The capacity to validate

        Returns:
            The validated capacity

        Raises:
            ValueError: If capacity is not positive
        """
        if v <= 0:
            raise ValueError(
                f"Capacity must be greater than 0. Got {v} which is invalid."
            )

        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and clean the description field.

        If a description is provided, ensure it's not just whitespace.
        Convert empty/whitespace-only strings to None for consistency.

        Args:
            v: The description to validate

        Returns:
            The stripped description, or None if empty
        """
        # If no description provided, return None
        if v is None:
            return None

        # Strip whitespace
        stripped = v.strip()

        # Return None for empty strings (instead of "")
        # This ensures database consistency (NULL vs empty string)
        if not stripped:
            return None

        return stripped

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def display_name(self) -> str:
        """
        Generate a formatted display name including capacity and unit.

        This creates a user-friendly string that includes both the product
        name and its size, which is useful for dropdowns, lists, and reports.

        Returns:
            Formatted string in the format "Name (Capacity Unit)"

        Example:
            >>> item = InventoryItem(
            ...     name="Retinol Serum",
            ...     capacity=30.0,
            ...     unit="ml"
            ... )
            >>> item.display_name()
            "Retinol Serum (30.0 ml)"
            >>>
            >>> item2 = InventoryItem(
            ...     name="Face Cream",
            ...     capacity=50.0,
            ...     unit="g"
            ... )
            >>> item2.display_name()
            "Face Cream (50.0 g)"
            >>>
            >>> item3 = InventoryItem(
            ...     name="Cotton Pads",
            ...     capacity=1.0,
            ...     unit="Pc."
            ... )
            >>> item3.display_name()
            "Cotton Pads (1.0 Pc.)"
        """
        # Format capacity as a number (removes trailing zeros if integer)
        # Use :g format to show minimal decimal places
        # Examples: 30.0 -> "30", 2.5 -> "2.5"
        capacity_str = f"{self.capacity:g}"

        # Combine name with capacity and unit in parentheses
        return f"{self.name} ({capacity_str} {self.unit})"

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
                "name": "Retinol Serum",
                "description": "Advanced anti-aging serum with 0.5% retinol",
                "capacity": 30.0,
                "unit": "ml",
                "created_at": "2024-01-15T14:30:00",
                "updated_at": "2024-01-15T14:30:00",
            }
        }
