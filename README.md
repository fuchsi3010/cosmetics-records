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

Two options are available:

1. **Installer (Recommended):** Download `CosmeticsRecords-Windows-Setup.exe`
   - Installs to Program Files with Start Menu shortcuts
   - Includes uninstaller (Add/Remove Programs)
   - Automatically upgrades previous versions

2. **Portable:** Download `CosmeticsRecords-Windows-Portable.exe`
   - Run directly without installation
   - Good for USB drives or restricted environments

**Note:** If you see a "DLL load failed" error, install the [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) (2015-2022, x64).

#### macOS

Two options are available for each architecture:

1. **DMG Installer (Recommended):**
   - `CosmeticsRecords-macOS-AppleSilicon-Setup.dmg` for M1/M2/M3 Macs
   - `CosmeticsRecords-macOS-Intel-Setup.dmg` for Intel Macs
   - Open the DMG and drag the app to Applications
   - To upgrade: just replace the app in Applications

2. **ZIP Archive:**
   - `CosmeticsRecords-macOS-AppleSilicon.zip` for M1/M2/M3 Macs
   - `CosmeticsRecords-macOS-Intel.zip` for Intel Macs
   - Extract and move to Applications

**First run:** Right-click the app and select "Open" to bypass Gatekeeper (the app is not signed).

### Development Setup

```bash
# Clone the repository
git clone https://github.com/fuchsi3010/cosmetics-records.git
cd cosmetics-records

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements-dev.txt

# Install package in development mode (required for imports to work)
pip install -e .

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

## Configuration

The application stores its configuration in a `config.json` file:

| OS | Location |
|----|----------|
| Linux | `~/.config/cosmetics_records/config.json` |
| macOS | `~/Library/Application Support/cosmetics_records/config.json` |
| Windows | `%APPDATA%\cosmetics_records\config.json` |

### Available Settings

| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `theme` | `"dark"`, `"light"`, `"system"` | `"system"` | UI color theme |
| `language` | `"en"`, `"de"` | `"en"` | Interface language |
| `date_format` | `"language"`, `"iso8601"`, `"us"`, `"de"` | `"language"` | Date display format |
| `ui_scale` | `0.8` - `2.0` | `1.0` | UI scaling factor |
| `auto_backup` | `true`, `false` | `true` | Enable automatic backups |
| `backup_interval_minutes` | Any positive integer | `60` | Minutes between auto-backups |
| `backup_retention_count` | Any positive integer | `5` | Number of backups to keep |

### Example Configuration

```json
{
  "theme": "dark",
  "language": "en",
  "date_format": "iso8601",
  "ui_scale": 1.2,
  "auto_backup": true,
  "backup_interval_minutes": 30,
  "backup_retention_count": 10
}
```

## Database Schema

The application uses SQLite with the following tables:

### Tables Overview

```
┌─────────────────┐     ┌────────────────────┐
│     clients     │──┬──│  treatment_records │
│                 │  │  │                    │
│ id (PK)         │  │  │ id (PK)            │
│ first_name      │  │  │ client_id (FK)     │
│ last_name       │  │  │ treatment_date     │
│ email           │  │  │ treatment_notes    │
│ phone           │  │  │ created_at         │
│ address         │  │  │ updated_at         │
│ date_of_birth   │  │  └────────────────────┘
│ allergies       │  │
│ tags            │  │  ┌────────────────────┐
│ planned_treatment│ └──│   product_records  │
│ notes           │     │                    │
│ created_at      │     │ id (PK)            │
│ updated_at      │     │ client_id (FK)     │
└─────────────────┘     │ product_date       │
                        │ product_text       │
┌─────────────────┐     │ created_at         │
│    inventory    │     │ updated_at         │
│                 │     └────────────────────┘
│ id (PK)         │
│ name            │     ┌────────────────────┐
│ description     │     │     audit_log      │
│ capacity        │     │                    │
│ unit            │     │ id (PK)            │
│ created_at      │     │ table_name         │
│ updated_at      │     │ record_id          │
└─────────────────┘     │ action             │
                        │ field_name         │
                        │ old_value          │
                        │ new_value          │
                        │ ui_location        │
                        │ created_at         │
                        └────────────────────┘
```

### Key Relationships

- `treatment_records.client_id` → `clients.id` (CASCADE DELETE)
- `product_records.client_id` → `clients.id` (CASCADE DELETE)

### Data Storage Location

| OS | Database Location |
|----|-------------------|
| Linux | `~/.local/share/cosmetics_records/cosmetics_records.db` |
| macOS | `~/Library/Application Support/cosmetics_records/cosmetics_records.db` |
| Windows | `%APPDATA%\cosmetics_records\cosmetics_records.db` |

## Troubleshooting

### Windows: "DLL load failed" Error

**Symptom:** Application fails to start with an error about missing DLLs.

**Solution:** Install the [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) (2015-2022, x64 version).

### macOS: "App is damaged" or Gatekeeper Warning

**Symptom:** macOS refuses to open the application.

**Solution:** Right-click the app and select "Open", then click "Open" in the dialog. You only need to do this once. Alternatively, run:
```bash
xattr -cr /Applications/Cosmetics\ Records.app
```

### Database Locked Error

**Symptom:** Error message about database being locked.

**Causes & Solutions:**
1. **Another instance running:** Close other Cosmetics Records windows
2. **Cloud sync conflict:** Move the database out of synced folders (Dropbox, OneDrive, iCloud)
3. **Crashed process:** Restart your computer to release locks

### Backup Restoration

**To restore from backup:**
1. Open Settings → Backup Management
2. Select a backup from the list
3. Click "Restore" and confirm

**Manual restoration:**
1. Close the application
2. Navigate to the data folder (see "Data Storage Location" above)
3. Find backups in the `backups/` subfolder
4. Replace `cosmetics_records.db` with your backup file

### Import/Export Issues

**CSV Import fails:**
- Ensure the CSV uses UTF-8 encoding
- Check that required columns exist (first_name, last_name for clients)
- Date columns should use ISO format (YYYY-MM-DD)

**Export is empty:**
- Select clients using the checkboxes before exporting
- Use "Select All" if exporting entire database

### Application Crashes on Start

**Possible causes:**
1. **Corrupted config:** Delete `config.json` (see location above) and restart
2. **Database corruption:** Restore from backup or delete the database to start fresh
3. **Graphics driver issues:** Try running with software rendering:
   ```bash
   QT_QUICK_BACKEND=software ./CosmeticsRecords-Linux
   ```

### Translation/Language Issues

**Missing translations:**
- Check Settings → Language is set correctly
- Restart the application after changing language
- Some system strings may remain in English (Qt library strings)

## License

MIT License
