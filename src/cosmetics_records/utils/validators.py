# =============================================================================
# Cosmetics Records - Validation Utilities
# =============================================================================
# This module provides reusable validation functions for common data formats.
#
# Key Features:
#   - Email validation with standard RFC-compliant pattern
#   - Centralized validation logic to avoid code duplication
#   - Consistent validation behavior across models and UI
#
# Usage Example:
#   from cosmetics_records.utils.validators import is_valid_email
#
#   if email and not is_valid_email(email):
#       show_error("Invalid email format")
# =============================================================================

import re
from typing import Pattern

# Compiled email pattern for performance
# WHY compile: Regex compilation is expensive, so we do it once at module load
# Pattern breakdown:
#   - ^[a-zA-Z0-9._%+-]+  : Local part (before @) - letters, numbers, special chars
#   - @                    : Required @ symbol
#   - [a-zA-Z0-9.-]+      : Domain name - letters, numbers, dots, hyphens
#   - \.                   : Required dot before TLD
#   - [a-zA-Z]{2,}$       : TLD - at least 2 letters (com, org, co.uk, etc.)
EMAIL_PATTERN: Pattern[str] = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def is_valid_email(email: str) -> bool:
    """
    Validate an email address format.

    Uses a standard regex pattern that covers most common email formats
    while being permissive enough for real-world addresses.

    Args:
        email: The email address string to validate

    Returns:
        True if the email format is valid, False otherwise

    Examples:
        >>> is_valid_email("user@example.com")
        True
        >>> is_valid_email("user.name+tag@example.co.uk")
        True
        >>> is_valid_email("invalid-email")
        False
        >>> is_valid_email("")
        False

    Note:
        This validates format only, not whether the email actually exists.
        Empty strings return False.
    """
    if not email:
        return False
    return bool(EMAIL_PATTERN.match(email))
