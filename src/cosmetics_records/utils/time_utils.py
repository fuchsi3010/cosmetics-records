# =============================================================================
# Cosmetics Records - Time Utilities
# =============================================================================
# This module provides utility functions for working with dates and times.
#
# Key Features:
#   - Relative timestamp formatting ("2 hours ago", "Yesterday at 14:32")
#   - Human-readable date/time formatting
#   - Consistent time display across the application
#
# Usage Example:
#   from cosmetics_records.utils.time_utils import format_relative_time
#   from datetime import datetime
#
#   timestamp = datetime(2024, 1, 15, 14, 30, 0)
#   formatted = format_relative_time(timestamp)
#   # Returns: "2 hours ago" or "Jan 15, 2024 14:30" depending on age
# =============================================================================

from datetime import datetime, timedelta


def format_relative_time(dt: datetime) -> str:
    """
    Format a datetime as a relative time string.

    This creates user-friendly time descriptions like "just now", "2 hours ago",
    "Yesterday at 14:32", or absolute dates for older timestamps.

    Args:
        dt: The datetime to format

    Returns:
        A human-readable relative time string

    Examples:
        >>> now = datetime.now()
        >>> format_relative_time(now)
        'just now'

        >>> two_hours_ago = now - timedelta(hours=2)
        >>> format_relative_time(two_hours_ago)
        '2 hours ago'

        >>> yesterday = now - timedelta(days=1)
        >>> format_relative_time(yesterday)
        'Yesterday at 14:32'  # (time varies)

        >>> last_week = now - timedelta(days=7)
        >>> format_relative_time(last_week)
        'Jan 15, 2024 14:32'  # (date varies)
    """
    now = datetime.now()
    delta = now - dt

    # Just now (less than 1 minute)
    if delta.total_seconds() < 60:
        return "just now"

    # Minutes ago (less than 1 hour)
    if delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"

    # Hours ago (less than 24 hours)
    if delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"

    # Yesterday (between 24 and 48 hours ago, and on the previous day)
    # WHY check date: "Yesterday" should be the previous calendar day,
    # not just "24 hours ago"
    if delta.total_seconds() < 172800:  # Less than 48 hours
        yesterday = now - timedelta(days=1)
        if dt.date() == yesterday.date():
            return f"Yesterday at {dt.strftime('%H:%M')}"

    # Last 7 days (show day name with time)
    if delta.total_seconds() < 604800:  # Less than 7 days
        return dt.strftime("%A at %H:%M")  # "Monday at 14:32"

    # Older than 7 days (show full date with time)
    # Format: "Jan 15, 2024 14:32"
    return dt.strftime("%b %d, %Y %H:%M")


def format_date(dt: datetime) -> str:
    """
    Format a datetime as a date string.

    Args:
        dt: The datetime to format

    Returns:
        A formatted date string (e.g., "Jan 15, 2024")

    Example:
        >>> dt = datetime(2024, 1, 15, 14, 30, 0)
        >>> format_date(dt)
        'Jan 15, 2024'
    """
    return dt.strftime("%b %d, %Y")


def format_time(dt: datetime) -> str:
    """
    Format a datetime as a time string.

    Args:
        dt: The datetime to format

    Returns:
        A formatted time string (e.g., "14:32")

    Example:
        >>> dt = datetime(2024, 1, 15, 14, 30, 0)
        >>> format_time(dt)
        '14:30'
    """
    return dt.strftime("%H:%M")


def format_datetime(dt: datetime) -> str:
    """
    Format a datetime as a full date and time string.

    Args:
        dt: The datetime to format

    Returns:
        A formatted datetime string (e.g., "Jan 15, 2024 14:32")

    Example:
        >>> dt = datetime(2024, 1, 15, 14, 30, 0)
        >>> format_datetime(dt)
        'Jan 15, 2024 14:32'
    """
    return dt.strftime("%b %d, %Y %H:%M")


# Date format strings for each format setting
DATE_FORMATS = {
    "iso8601": "%Y-%m-%d",       # 2024-12-31
    "us": "%m/%d/%Y",            # 12/31/2024
    "de": "%d.%m.%Y",            # 31.12.2024
}

# Language defaults (what "language" setting uses per language)
LANGUAGE_DATE_FORMATS = {
    "en": "%m/%d/%Y",            # US format for English
    "de": "%d.%m.%Y",            # German format for German
}


def format_date_localized(d) -> str:
    """
    Format a date according to the user's date format preference.

    Uses the date_format setting from Config to determine the output format.
    If set to "language", uses the language-appropriate default.

    Args:
        d: A date or datetime object to format

    Returns:
        A formatted date string according to user preferences

    Examples:
        >>> from datetime import date
        >>> d = date(2024, 12, 31)
        >>> format_date_localized(d)
        '12/31/2024'  # if format is "us" or language="en" with format="language"
        '31.12.2024'  # if format is "de" or language="de" with format="language"
        '2024-12-31'  # if format is "iso8601"
    """
    from cosmetics_records.config import Config

    config = Config.get_instance()
    date_format_setting = config.date_format

    if date_format_setting == "language":
        # Use language-specific default
        language = config.language
        fmt = LANGUAGE_DATE_FORMATS.get(language, "%Y-%m-%d")
    else:
        # Use explicit format setting
        fmt = DATE_FORMATS.get(date_format_setting, "%Y-%m-%d")

    return d.strftime(fmt)
