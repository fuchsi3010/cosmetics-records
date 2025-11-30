# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cosmetics Records is a desktop application for a one-person cosmetics salon to manage client information, treatment history, and product sales. Built with Python 3.9+ and PyQt6 (migrated from CustomTkinter).

### Core User Story
A client arrives → user looks them up → views treatment plan and history → performs treatment → logs the treatment → recommends products based on purchase history → logs the sale.

## Technology Stack

- **Python 3.9+** with type hints
- **PyQt6** for GUI
- **SQLite3** with migration system
- **Pydantic 2.0+** for validation
- **pytest + pytest-cov** for testing
- **black** (line-length=88), **flake8**, **mypy** for code quality

## Build & Development Commands

```bash
# Setup
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run application
python src/cosmetics_records/app.py

# Testing
pytest                                    # Run all tests
pytest --cov=src/cosmetics_records       # With coverage
pytest tests/unit/test_client_model.py   # Single test file

# Code quality
black src/ tests/                        # Format code
flake8 src/ tests/                       # Lint
mypy src/                                # Type check

# Translations
python scripts/extract_translations.py   # Extract strings
python scripts/compile_translations.py   # Compile .po to .mo

# Build executable
python scripts/build.py
```

## Architecture

### Design Pattern: MVC (Model-View-Controller)
- **Models** (`models/`): Pydantic classes with validation
- **Views** (`views/`): PyQt6 UI components
- **Controllers** (`controllers/`): Business logic coordination

### Directory Structure
```
src/cosmetics_records/
├── app.py                    # Main application orchestrator
├── config.py                 # Configuration management
├── models/                   # Pydantic data models
├── database/                 # SQLite wrapper + migrations
├── controllers/              # Business logic (MVC)
├── services/                 # Cross-cutting (audit, backup)
├── views/                    # UI components (MVC)
│   ├── components/           # Reusable widgets
│   └── dialogs/              # Modal dialogs
├── locales/                  # i18n (en_US, de_DE)
└── utils/                    # Helpers
```

### Key Patterns
- **Repository Pattern**: `DatabaseConnection` abstracts SQL operations
- **Migration System**: Versioned migrations (`v001_*.py`) with user confirmation
- **Service Layer**: `AuditService` for change tracking, `BackupService` for backups

## Database Schema

Five main tables: `clients`, `treatment_records`, `product_records`, `inventory`, `audit_log`.

Key relationships:
- `treatment_records` and `product_records` reference `clients` via `client_id`
- Product records are text-only (no foreign key to inventory) for flexibility

## Code Style Guidelines

- Follow PEP 8 with black formatting (88 char line length)
- Add comprehensive comments for beginner comprehension
- Emphasize code reuse - extract common patterns into components
- Use type hints on all public APIs
- Keep solutions simple - avoid over-engineering

## UI Design System

### Typography (5 levels)
- Level 1: 24pt bold (page titles)
- Level 2: 18pt bold (dialog/section headers)
- Level 3: 16pt bold (subsections)
- Level 4: 14pt (navigation, primary actions)
- Level 5: 13pt (body text, forms)

### Spacing Scale
- 5px: micro (button padding)
- 10px: small (related elements)
- 20px: medium (section padding)
- 30px: large (page margins)

### Component Patterns
- Fixed-height list items (50px) with `pack_propagate(False)` equivalent
- Debounced auto-save (1 second delay)
- Fuzzy search with 60% threshold
- Pagination: 20 items per page with "Load More"

## i18n Support

Two languages: English (en_US) and German (de_DE). Use Babel for translations.

## Special Features

- **CSV Export**: Export client names and addresses for mail merge
- **Audit Logging**: Human-readable change history with context
- **Auto-backup**: Configurable interval with retention policies
- **Theme Support**: Dark/Light/System detection

## Git Workflow

Commit progress regularly throughout development:
- Commit after completing each logical unit of work (feature, component, fix)
- Use conventional commit messages: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Keep commits atomic and focused on a single change
