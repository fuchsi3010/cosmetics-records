# Cosmetics Records

A desktop application for cosmetics salon client management, built with Python 3.9+ and PyQt6.

## Features

- **Client Management**: Track client information including name, contact details, allergies, and tags
- **Treatment History**: Log and view treatment records for each client
- **Product Sales**: Track products sold/used with autocomplete from inventory
- **Inventory Management**: Maintain a catalog of products with quantities (ml, g, Pc.)
- **Audit Logging**: Full change history with human-readable summaries
- **CSV Export**: Export client data for mail merge
- **Multi-language**: English and German support
- **Themes**: Dark/Light/System theme options

## Installation

### Development Setup

```bash
# Clone the repository
git clone <repo-url>
cd cosmetics-records

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements-dev.txt

# Run the application
python src/cosmetics_records/app.py
```

## Development

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/cosmetics_records --cov-report=html

# Run specific test file
pytest tests/unit/test_client_model.py
```

### Building

```bash
# Build standalone executable
python scripts/build.py
```

## Architecture

The application follows the MVC (Model-View-Controller) pattern:

- **Models** (`src/cosmetics_records/models/`): Pydantic data models with validation
- **Views** (`src/cosmetics_records/views/`): PyQt6 UI components
- **Controllers** (`src/cosmetics_records/controllers/`): Business logic
- **Services** (`src/cosmetics_records/services/`): Cross-cutting concerns (audit, backup, export)
- **Database** (`src/cosmetics_records/database/`): SQLite with migrations

## License

MIT License
