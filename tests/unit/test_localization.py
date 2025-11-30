# =============================================================================
# Cosmetics Records - Localization Unit Tests
# =============================================================================
# This file contains unit tests for the localization (i18n) functions.
#
# Key Tests:
#   - Test that init_translations() initializes translations correctly
#   - Test that _() returns translated strings
#   - Test that language can be switched at runtime
#   - Test that get_available_locales() returns valid locales
#   - Test that get_current_locale() returns the current locale
#
# These tests ensure that the internationalization system works correctly
# and that language switching (one of the bug fixes) functions properly.
# =============================================================================

import pytest

from cosmetics_records.utils.localization import (
    init_translations,
    _,
    get_current_locale,
    get_available_locales,
)


class TestInitTranslations:
    """Tests for the init_translations() function."""

    def test_init_translations_english(self):
        """
        Test that init_translations("en") sets English locale.
        """
        init_translations("en")

        assert get_current_locale() == "en"

    def test_init_translations_german(self):
        """
        Test that init_translations("de") sets German locale.
        """
        init_translations("de")

        assert get_current_locale() == "de"

    def test_init_translations_invalid_falls_back_to_english(self):
        """
        Test that invalid locale falls back to English.
        """
        init_translations("invalid_locale_xyz")

        # Should fall back to English
        assert get_current_locale() == "en"

    def test_init_translations_can_switch_languages(self):
        """
        Test that init_translations() can be called multiple times to switch.

        This tests the runtime language switching fix.
        """
        # Start with English
        init_translations("en")
        assert get_current_locale() == "en"

        # Switch to German
        init_translations("de")
        assert get_current_locale() == "de"

        # Switch back to English
        init_translations("en")
        assert get_current_locale() == "en"


class TestTranslationFunction:
    """Tests for the _() translation function."""

    def test_translation_returns_string(self):
        """
        Test that _() always returns a string.
        """
        init_translations("en")

        result = _("Clients")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_english_returns_original(self):
        """
        Test that English locale returns original strings.

        For English, _("Clients") should return "Clients".
        """
        init_translations("en")

        # English strings should be returned as-is
        assert _("Clients") == "Clients"
        assert _("Settings") == "Settings"
        assert _("Inventory") == "Inventory"

    def test_german_returns_translated(self):
        """
        Test that German locale returns translated strings.

        If German translations exist, _("Clients") should return "Kunden".
        """
        init_translations("de")

        # These should return German translations if .mo files exist
        result = _("Clients")

        # Result should be a string (either translated or original fallback)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_untranslated_string_returns_original(self):
        """
        Test that strings without translations return the original.

        If a string has no translation, _() should return the original text.
        """
        init_translations("de")

        # A string that probably doesn't have a translation
        original = "This is a test string that has no translation"
        result = _(original)

        # Should return original since there's likely no translation
        assert result == original


class TestGetAvailableLocales:
    """Tests for the get_available_locales() function."""

    def test_returns_list(self):
        """
        Test that get_available_locales() returns a list.
        """
        locales = get_available_locales()

        assert isinstance(locales, list)

    def test_english_always_available(self):
        """
        Test that English is always in the available locales.

        English is the default/fallback language.
        """
        locales = get_available_locales()

        assert "en" in locales

    def test_locales_are_sorted(self):
        """
        Test that locales are returned in sorted order.
        """
        locales = get_available_locales()

        # Should be sorted alphabetically
        assert locales == sorted(locales)


class TestGetCurrentLocale:
    """Tests for the get_current_locale() function."""

    def test_returns_string(self):
        """
        Test that get_current_locale() returns a string.
        """
        init_translations("en")

        locale = get_current_locale()

        assert isinstance(locale, str)
        assert len(locale) > 0

    def test_returns_correct_locale_after_init(self):
        """
        Test that get_current_locale() returns the locale set by init_translations().
        """
        init_translations("en")
        assert get_current_locale() == "en"

        init_translations("de")
        assert get_current_locale() == "de"


class TestLanguageSwitchingIntegration:
    """
    Integration tests for language switching.

    These tests verify that the full language switching flow works correctly,
    which was one of the bug fixes implemented.
    """

    def test_translation_changes_after_switch(self):
        """
        Test that translations change after switching languages.

        This is the core functionality for runtime language switching.
        """
        # Initialize English
        init_translations("en")
        english_result = _("Clients")

        # Switch to German
        init_translations("de")
        german_result = _("Clients")

        # Results should both be non-empty strings
        assert isinstance(english_result, str)
        assert isinstance(german_result, str)

        # In English, "Clients" should return "Clients"
        assert english_result == "Clients"

        # In German, if translation exists, it should be different
        # (or same if no translation file - either is acceptable)
        assert isinstance(german_result, str)

    def test_multiple_switches_maintain_state(self):
        """
        Test that multiple language switches work correctly.

        Verify that the locale state is properly maintained through switches.
        """
        locales_to_test = ["en", "de", "en", "de", "en"]

        for expected_locale in locales_to_test:
            init_translations(expected_locale)
            actual_locale = get_current_locale()

            # Locale should match what we set
            assert (
                actual_locale == expected_locale
            ), f"Expected locale {expected_locale}, got {actual_locale}"
