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

### Pre-built Binaries

Download the latest release from the [Releases page](https://github.com/fuchsi3010/cosmetics-records/releases).

#### Linux

The Linux binary is a standalone PyInstaller executable (not an AppImage).

1. **Download and make executable:**
   ```bash
   # Download the binary
   wget https://github.com/fuchsi3010/cosmetics-records/releases/latest/download/CosmeticsRecords-Linux

   # Make it executable
   chmod +x CosmeticsRecords-Linux

   # Run it
   ./CosmeticsRecords-Linux
   ```

2. **Install to a permanent location (optional):**
   ```bash
   # Move to a local bin directory
   mkdir -p ~/.local/bin
   mv CosmeticsRecords-Linux ~/.local/bin/cosmetics-records

   # Ensure ~/.local/bin is in your PATH (add to ~/.bashrc or ~/.zshrc if not)
   export PATH="$HOME/.local/bin:$PATH"
   ```

3. **Create a desktop entry (optional):**

   To have the app appear in your application menu, create a `.desktop` file:

   ```bash
   # Download the icon (or extract from the binary's resources)
   mkdir -p ~/.local/share/icons
   # You can download the icon from the repo or use any 256x256 PNG
   wget -O ~/.local/share/icons/cosmetics-records.png \
     https://raw.githubusercontent.com/fuchsi3010/cosmetics-records/main/src/cosmetics_records/resources/icons/icon-256.png

   # Create the desktop entry
   cat > ~/.local/share/applications/cosmetics-records.desktop << 'EOF'
   [Desktop Entry]
   Name=Cosmetics Records
   Comment=Client management for cosmetics salons
   Exec=/home/YOUR_USERNAME/.local/bin/cosmetics-records
   Icon=/home/YOUR_USERNAME/.local/share/icons/cosmetics-records.png
   Terminal=false
   Type=Application
   Categories=Office;Database;
   Keywords=cosmetics;salon;client;management;
   EOF

   # Replace YOUR_USERNAME with your actual username
   sed -i "s/YOUR_USERNAME/$USER/g" ~/.local/share/applications/cosmetics-records.desktop

   # Update desktop database (may require logout/login to take effect)
   update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
   ```

   The application should now appear in your desktop environment's application menu.

#### Windows

Download `CosmeticsRecords-Windows.exe` and run it directly. No installation required.

**Note:** If you see a "DLL load failed" error, install the [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) (2015-2022, x64).

#### macOS

1. Download the appropriate zip file:
   - `CosmeticsRecords-macOS-AppleSilicon.zip` for M1/M2/M3 Macs
   - `CosmeticsRecords-macOS-Intel.zip` for Intel Macs

2. Extract the zip file and move `CosmeticsRecords.app` to your Applications folder.

3. **First run:** Right-click the app and select "Open" to bypass Gatekeeper (the app is not signed).

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
