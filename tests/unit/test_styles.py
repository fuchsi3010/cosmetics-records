# =============================================================================
# Cosmetics Records - Styles Unit Tests
# =============================================================================
# This file contains unit tests for the QSS stylesheet generation functions.
#
# Key Tests:
#   - Test that get_scaled_sizes() returns correct scaled font sizes
#   - Test that get_theme() returns different stylesheets for different themes
#   - Test that get_theme() applies scaling correctly
#   - Test that generate_dark_theme() and generate_light_theme() work
#
# These tests ensure that the UI scaling feature works correctly and that
# theme generation produces valid stylesheets.
# =============================================================================

from cosmetics_records.views.styles import (
    get_scaled_sizes,
    get_theme,
    generate_dark_theme,
    generate_light_theme,
    BASE_SIZE_TITLE,
    BASE_SIZE_BODY,
)


class TestGetScaledSizes:
    """Tests for the get_scaled_sizes() function."""

    def test_default_scale_returns_base_sizes(self):
        """
        Test that scale=1.0 returns the base font sizes unchanged.

        At 100% scale, sizes should match the BASE_SIZE_* constants.
        """
        sizes = get_scaled_sizes(1.0)

        assert sizes["title"] == f"{BASE_SIZE_TITLE}pt"
        assert sizes["body"] == f"{BASE_SIZE_BODY}pt"

    def test_scale_150_percent(self):
        """
        Test that scale=1.5 returns 150% of base sizes.

        At 150% scale, a 24pt title becomes 36pt.
        """
        sizes = get_scaled_sizes(1.5)

        # 24 * 1.5 = 36
        expected_title = int(BASE_SIZE_TITLE * 1.5)
        assert sizes["title"] == f"{expected_title}pt"

        # 13 * 1.5 = 19.5, truncated to 19
        expected_body = int(BASE_SIZE_BODY * 1.5)
        assert sizes["body"] == f"{expected_body}pt"

    def test_scale_80_percent(self):
        """
        Test that scale=0.8 returns 80% of base sizes.

        At 80% scale, sizes should be smaller.
        """
        sizes = get_scaled_sizes(0.8)

        # 24 * 0.8 = 19.2, truncated to 19
        expected_title = int(BASE_SIZE_TITLE * 0.8)
        assert sizes["title"] == f"{expected_title}pt"

    def test_all_size_keys_present(self):
        """
        Test that all expected size keys are present in the result.

        The sizes dictionary should contain all typography sizes.
        """
        sizes = get_scaled_sizes(1.0)

        expected_keys = ["title", "header", "nav", "body", "secondary"]
        for key in expected_keys:
            assert key in sizes, f"Missing key: {key}"
            assert sizes[key].endswith("pt"), f"Size {key} should end with 'pt'"


class TestGenerateThemes:
    """Tests for the theme generation functions."""

    def test_generate_dark_theme_returns_string(self):
        """
        Test that generate_dark_theme() returns a non-empty string.
        """
        stylesheet = generate_dark_theme()

        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_generate_light_theme_returns_string(self):
        """
        Test that generate_light_theme() returns a non-empty string.
        """
        stylesheet = generate_light_theme()

        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_dark_theme_contains_dark_colors(self):
        """
        Test that dark theme stylesheet contains dark background colors.
        """
        stylesheet = generate_dark_theme()

        # Dark theme should contain dark background color (#2b2b2b)
        assert "#2b2b2b" in stylesheet or "#333333" in stylesheet

    def test_light_theme_contains_light_colors(self):
        """
        Test that light theme stylesheet contains light background colors.
        """
        stylesheet = generate_light_theme()

        # Light theme should contain light background color (#f5f5f5)
        assert "#f5f5f5" in stylesheet or "#ffffff" in stylesheet

    def test_dark_theme_with_scale(self):
        """
        Test that generate_dark_theme() applies scaling to font sizes.
        """
        # Generate with default scale
        stylesheet_100 = generate_dark_theme(1.0)

        # Generate with 150% scale
        stylesheet_150 = generate_dark_theme(1.5)

        # The stylesheets should be different (font sizes changed)
        assert stylesheet_100 != stylesheet_150

        # 150% stylesheet should contain larger font sizes
        # At 100%: 24pt for titles, at 150%: 36pt
        assert "24pt" in stylesheet_100
        assert "36pt" in stylesheet_150

    def test_light_theme_with_scale(self):
        """
        Test that generate_light_theme() applies scaling to font sizes.
        """
        stylesheet_100 = generate_light_theme(1.0)
        stylesheet_150 = generate_light_theme(1.5)

        assert stylesheet_100 != stylesheet_150
        assert "24pt" in stylesheet_100
        assert "36pt" in stylesheet_150


class TestGetTheme:
    """Tests for the get_theme() function."""

    def test_get_dark_theme(self):
        """
        Test that get_theme("dark") returns dark theme stylesheet.
        """
        stylesheet = get_theme("dark")

        assert isinstance(stylesheet, str)
        assert "#2b2b2b" in stylesheet or "#333333" in stylesheet

    def test_get_light_theme(self):
        """
        Test that get_theme("light") returns light theme stylesheet.
        """
        stylesheet = get_theme("light")

        assert isinstance(stylesheet, str)
        assert "#f5f5f5" in stylesheet or "#ffffff" in stylesheet

    def test_get_theme_with_scale(self):
        """
        Test that get_theme() applies scale parameter correctly.
        """
        stylesheet_100 = get_theme("dark", 1.0)
        stylesheet_150 = get_theme("dark", 1.5)

        # Different scales should produce different stylesheets
        assert stylesheet_100 != stylesheet_150

    def test_get_theme_invalid_falls_back_to_dark(self):
        """
        Test that get_theme() with invalid theme name falls back to dark.
        """
        stylesheet = get_theme("invalid_theme")

        # Should fall back to dark theme
        assert "#2b2b2b" in stylesheet or "#333333" in stylesheet

    def test_get_theme_system_returns_valid_stylesheet(self):
        """
        Test that get_theme("system") returns a valid stylesheet.

        Note: The actual system theme detection may vary by system,
        so we just verify it returns a non-empty stylesheet.
        """
        stylesheet = get_theme("system")

        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0
        # Should contain valid QSS content
        assert "QWidget" in stylesheet or "QMainWindow" in stylesheet
