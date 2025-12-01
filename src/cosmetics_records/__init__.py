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

# Package version - keep in sync with pyproject.toml
__version__ = "0.9.0-alpha2"

# Package metadata
__author__ = "Daniel"
__description__ = "A desktop application for cosmetics salon client management"
