"""
Localization utilities for the Cosmetics Records application.

This module provides translation functions using Babel for internationalization (i18n).
It handles loading translation catalogs, managing the current locale, and providing
a simple API for translating strings throughout the application.

Architecture:
    - Uses GNU gettext format (.po files for source, .mo for compiled)
    - Translation files stored in src/cosmetics_records/locales/{locale}/LC_MESSAGES/
    - Falls back to English if requested locale is not available
    - Global state for current locale and translations

Supported Languages:
    - English (en) - Default
    - German (de) - Deutsch

Usage:
    # Initialize translations at application startup
    from cosmetics_records.utils.localization import init_translations, _

    # Initialize with desired locale
    init_translations("de")  # German

    # Use in views and components
    from cosmetics_records.utils.localization import _
    label = QLabel(_("Clients"))  # Will show "Kunden" in German

    # Get current locale
    from cosmetics_records.utils.localization import get_current_locale
    current = get_current_locale()  # Returns "de" or "en"

Adding New Translations:
    1. Add translatable strings to code using _("String")
    2. Extract strings: pybabel extract -o messages.pot src/
    3. Update PO files: pybabel update -i messages.pot -d src/cosmetics_records/locales
    4. Edit .po files with translations
    5. Compile: python scripts/compile_translations.py

Technical Notes:
    - babel.support.Translations handles the actual translation lookups
    - NullTranslations is used as a fallback when locale files are missing
    - The underscore function _() is the standard gettext convention
    - Module-level globals maintain state (thread-safe for PyQt6 single-thread model)
"""

import logging
from pathlib import Path
from typing import Optional, Union

from babel.support import NullTranslations, Translations

# Configure module logger
logger = logging.getLogger(__name__)

# =============================================================================
# Global State
# =============================================================================
# WHY globals: Simple singleton pattern for application-wide locale state
# This is safe because PyQt6 applications run in a single thread
_translations: Optional[Union[Translations, NullTranslations]] = None
_current_locale: str = "en"  # Default to English

# Path to locales directory
# WHY __file__: Gets the directory containing this module
_LOCALES_DIR = Path(__file__).parent.parent / "locales"


def init_translations(locale: str = "en") -> None:
    """
    Initialize translations for the given locale.

    This function should be called once at application startup, typically
    in the main application initialization code. It loads the appropriate
    translation catalog based on the requested locale.

    Args:
        locale: Language code (e.g., "en", "de"). Defaults to "en" (English)

    Behavior:
        - Attempts to load translations from locales/{locale}/LC_MESSAGES/messages.mo
        - Falls back to NullTranslations (pass-through) if locale not found
        - Updates global _translations and _current_locale state
        - Logs success or fallback information

    Example:
        # At application startup
        from cosmetics_records.config import Config
        config = Config.get_instance()
        init_translations(config.language)  # "en" or "de"

    Note:
        If the requested locale is not available, the function will fall back
        to English (returning untranslated strings). No exception is raised.
    """
    global _translations, _current_locale

    logger.info(f"Initializing translations for locale: {locale}")

    # Validate locale code
    # WHY whitelist: Prevents directory traversal or invalid locale codes
    available_locales = get_available_locales()
    if locale not in available_locales:
        logger.warning(
            f"Locale '{locale}' not available. "
            f"Available locales: {available_locales}. Falling back to English."
        )
        locale = "en"

    try:
        # Path to the .mo file for this locale
        # Structure: locales/{locale}/LC_MESSAGES/messages.mo
        # WHY LC_MESSAGES: Standard gettext directory structure
        locale_path = _LOCALES_DIR / locale / "LC_MESSAGES"

        if locale_path.exists():
            # Load translations using Babel
            # WHY Translations.load(): Handles .mo file parsing and provides
            # efficient string lookup via gettext mechanism
            _translations = Translations.load(
                dirname=str(_LOCALES_DIR),
                locales=[locale],
                domain="messages",  # Name of the .mo file (messages.mo)
            )
            _current_locale = locale
            logger.info(
                f"Successfully loaded translations for locale '{locale}' "
                f"from {locale_path}"
            )
        else:
            # Locale directory doesn't exist, use fallback
            logger.warning(
                f"Locale directory not found: {locale_path}. "
                f"Using NullTranslations (English strings)."
            )
            _translations = NullTranslations()
            _current_locale = "en"

    except Exception as e:
        # Handle any errors in loading translations
        logger.error(f"Failed to load translations for locale '{locale}': {e}")
        logger.info("Falling back to NullTranslations (English strings)")
        _translations = NullTranslations()
        _current_locale = "en"


def _(text: str) -> str:
    """
    Translate a string to the current locale.

    This is the main translation function used throughout the application.
    The underscore function name is the standard gettext convention and
    keeps translation calls concise.

    Args:
        text: The English source string to translate

    Returns:
        str: The translated string in the current locale, or the original
             English string if no translation is available

    Usage:
        from cosmetics_records.utils.localization import _

        # In a QLabel
        label = QLabel(_("Clients"))

        # In a button
        button = QPushButton(_("Add Client"))

        # In a message
        message = _("Client created successfully")

        # With formatting (translate first, then format)
        template = _("Deleted %d entries")
        message = template % count

    Technical Notes:
        - Returns original text if translations not initialized
        - Case-sensitive (translations must match exactly)
        - Formatting should be done AFTER translation
        - Keep strings simple and avoid concatenation

    Example:
        # Good
        message = _("Client created successfully")

        # Bad (string concatenation makes translation impossible)
        message = _("Client") + " " + _("created successfully")
    """
    # If translations not initialized, return original text
    # WHY: Graceful degradation - app works even if i18n not set up
    if _translations is None:
        logger.warning(
            "Translations not initialized. Call init_translations() first. "
            "Returning original text."
        )
        return text

    # Look up translation
    # WHY gettext(): Standard method provided by Babel's Translations class
    # It handles fallbacks, pluralization, and context automatically
    translated = _translations.gettext(text)

    return translated


def get_current_locale() -> str:
    """
    Return the current locale code.

    Returns:
        str: Current locale code (e.g., "en", "de")

    Usage:
        from cosmetics_records.utils.localization import get_current_locale

        current_locale = get_current_locale()
        if current_locale == "de":
            # German-specific logic

    Note:
        Returns "en" if translations have not been initialized.
    """
    return _current_locale


def get_available_locales() -> list:
    """
    Return list of available locale codes.

    Scans the locales directory to find all available translation catalogs.
    A locale is considered available if it has a messages.mo file in the
    correct directory structure.

    Returns:
        list: List of available locale codes (e.g., ["en", "de"])

    Usage:
        from cosmetics_records.utils.localization import get_available_locales

        # Populate a language selector
        locales = get_available_locales()
        for locale in locales:
            combo_box.addItem(locale)

    Directory Structure:
        locales/
            en/
                LC_MESSAGES/
                    messages.mo  <- English translations
            de/
                LC_MESSAGES/
                    messages.mo  <- German translations

    Note:
        - Only returns locales that have compiled .mo files
        - Directories without messages.mo are ignored
        - "en" is always included even if no .mo file exists (default)
    """
    available = []

    # Ensure locales directory exists
    if not _LOCALES_DIR.exists():
        logger.warning(f"Locales directory does not exist: {_LOCALES_DIR}")
        return ["en"]  # Always return English as fallback

    try:
        # Scan for locale directories
        # WHY iterdir(): Gets all items in the locales directory
        for item in _LOCALES_DIR.iterdir():
            # Check if it's a directory (locale code)
            if item.is_dir():
                # Check for messages.mo file
                mo_file = item / "LC_MESSAGES" / "messages.mo"
                if mo_file.exists():
                    # Valid locale with compiled translations
                    available.append(item.name)
                    logger.debug(f"Found locale: {item.name}")

    except Exception as e:
        logger.error(f"Error scanning locales directory: {e}")

    # Always ensure English is available (even without .mo file)
    # WHY: English is the source language and doesn't need translations
    if "en" not in available:
        available.append("en")

    # Sort for consistent ordering
    available.sort()

    logger.debug(f"Available locales: {available}")
    return available
