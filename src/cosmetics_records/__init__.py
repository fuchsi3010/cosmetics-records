# =============================================================================
# Cosmetics Records - Main Package
# =============================================================================
# This is the main package for the Cosmetics Records application.
# It provides a desktop application for cosmetics salons to manage their
# client information, treatment history, and product sales.
#
# The application follows the MVC (Model-View-Controller) architecture:
#   - models/      : Pydantic data models for validation
#   - views/       : PyQt6 UI components
#   - controllers/ : Business logic connecting models and views
#   - services/    : Cross-cutting concerns (audit, backup, export)
#   - database/    : SQLite database layer with migrations
# =============================================================================

import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    # Python 3.9/3.10 fallback - tomllib is not available
    # We'll read the version from a simpler approach
    tomllib = None

from pathlib import Path


def _get_version() -> str:
    """
    Get the version from pyproject.toml.

    Returns:
        str: The version string from pyproject.toml, or "0.0.0" if not found.
    """
    try:
        # Find pyproject.toml - it's in the project root
        # This file is at src/cosmetics_records/__init__.py
        # So pyproject.toml is at ../../pyproject.toml relative to this file
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        if not pyproject_path.exists():
            # When running from installed package or PyInstaller bundle,
            # pyproject.toml won't be available - use fallback
            return "0.9.0-alpha3"

        if tomllib is not None:
            # Python 3.11+ - use tomllib
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            return data.get("project", {}).get("version", "0.0.0")
        else:
            # Python 3.9/3.10 - parse manually (simple approach)
            with open(pyproject_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("version"):
                        # Parse: version = "0.9.0-alpha3"
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            return parts[1].strip().strip('"').strip("'")
            return "0.0.0"

    except Exception:
        # Any error reading version - return fallback
        return "0.9.0-alpha3"


# Package version - read from pyproject.toml
__version__ = _get_version()

# Package metadata
__author__ = "Daniel"
__description__ = "A desktop application for cosmetics salon client management"
