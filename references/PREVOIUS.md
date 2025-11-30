# Cosmetics Records v3: Best of Both Worlds

## Executive Summary

This document outlines the plan for building a new version of the Cosmetics Salon application that combines:
- **From v1**: Cohesive visual design, professional aesthetics, polished UI components
- **From v2**: Mature architecture, database migrations, performance optimizations, code quality tooling

The result will be a production-ready, maintainable, and beautiful desktop application for salon management.

---

## 1. Core Technology Stack

### Framework & Language
- **Python 3.9+**: Modern Python with type hints
- **CustomTkinter 5.2.2**: Modern GUI framework with dark/light theme support
- **SQLite3**: Local database with migration system
- **Pydantic 2.0+**: Runtime validation and type safety

### Development Tools
- **pytest + pytest-cov**: Testing and coverage
- **black**: Code formatting (line-length=88)
- **flake8**: Linting with complexity checks
- **mypy**: Static type checking
- **PyInstaller**: Single-file executable packaging

### Supporting Libraries
- **Pillow 12.0.0**: Image processing
- **tkfontawesome 0.3.2**: Icon system
- **tkcalendar 1.6.1**: Date picker widgets
- **thefuzz 0.22.1 + python-Levenshtein**: Fuzzy search
- **Babel 2.17.0**: Internationalization (EN/DE)
- **darkdetect 0.8.0**: System theme detection
- **python-json-logger**: Structured logging

---

## 2. Architecture Design (From v2)

### Directory Structure

```
cosmetics-records/
├── src/cosmetics_records/
│   ├── app.py                       # Main application orchestrator
│   ├── config.py                    # Configuration management
│   ├── models/                      # Pydantic data models
│   │   ├── client.py
│   │   ├── treatment.py
│   │   ├── product.py
│   │   └── audit.py
│   ├── database/                    # Data access layer
│   │   ├── connection.py            # Database wrapper
│   │   └── migrations/              # Schema versioning
│   │       ├── migration_manager.py
│   │       ├── v001_initial_schema.py
│   │       └── v002_*.py
│   ├── controllers/                 # Business logic (MVC)
│   │   ├── client_controller.py
│   │   ├── treatment_controller.py
│   │   └── product_controller.py
│   ├── services/                    # Cross-cutting concerns
│   │   ├── audit_service.py         # Change tracking
│   │   └── backup_service.py        # Automated backups
│   ├── views/                       # UI components (MVC)
│   │   ├── components/              # Reusable UI elements
│   │   │   ├── navbar.py            # Collapsible navigation
│   │   │   ├── modal_overlay.py     # Base modal class
│   │   │   ├── date_picker.py       # Calendar widget
│   │   │   ├── tag_input.py         # Tag chips
│   │   │   └── icon_manager.py      # Cached icon system
│   │   ├── clients/                 # Client management
│   │   │   ├── client_list_view.py
│   │   │   └── client_detail_view.py
│   │   ├── inventory/
│   │   │   └── inventory_view.py
│   │   ├── audit/
│   │   │   └── audit_log_view.py
│   │   ├── settings/
│   │   │   └── settings_view.py
│   │   └── dialogs/                 # Modal dialogs
│   │       ├── add_client_dialog.py
│   │       ├── edit_client_dialog.py
│   │       ├── add_treatment_dialog.py
│   │       ├── add_product_record_dialog.py
│   │       ├── add_inventory_item_dialog.py
│   │       └── choice_dialog.py
│   ├── locales/                     # i18n translations
│   │   ├── en_US/LC_MESSAGES/
│   │   └── de_DE/LC_MESSAGES/
│   └── utils/                       # Helper functions
│       ├── keyboard_shortcuts.py
│       └── localization.py
├── tests/                           # Test suite
│   ├── unit/
│   └── integration/
├── scripts/                         # Build/dev scripts
│   ├── build.py
│   ├── extract_translations.py
│   └── compile_translations.py
├── .gitea/workflows/                # CI/CD
│   └── build.yml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── cosmetics_records.spec           # PyInstaller config
└── README.md
```

### Design Patterns

#### **MVC (Model-View-Controller)**
- **Models**: Pydantic classes with validation (`models/`)
- **Views**: CustomTkinter UI components (`views/`)
- **Controllers**: Business logic coordination (`controllers/`)

#### **Service Layer**
- `AuditService`: Change tracking with UI context
- `BackupService`: Automated backup with retention policies

#### **Repository Pattern**
- `DatabaseConnection` abstracts all SQL operations
- Single source of truth for queries
- Context manager for transaction safety

#### **Migration System**
- Sequential versioned migrations (`v001_*.py`, `v002_*.py`)
- User confirmation before schema changes
- Automatic pre-migration backups
- PyInstaller-compatible discovery

---

## 3. Visual Design System (From v1)

### Color Palette

#### Primary Colors
- **Blue Primary**: `#3B8ED0` (buttons, active states)
- **Blue Dark**: `#1F6AA5` (hover states)
- **Blue Accent**: `("blue", "darkblue")` (chips, tags)

#### Neutral Colors
- **Gray Light**: `gray70` (light theme backgrounds)
- **Gray Dark**: `gray30` (dark theme backgrounds)
- **Transparent**: `transparent` (container backgrounds)
- **Gray Secondary**: `gray` with `darkgray` hover (de-emphasized actions)

#### Semantic Colors
- **Success**: Green tones for confirmations
- **Warning**: Yellow/orange for alerts
- **Error**: Red for validation errors
- **Info**: Blue for informational messages

### Typography System

**5-Level Hierarchy**:
```python
# Level 1: Page titles
font=("", 24, "bold")

# Level 2: Dialog titles, section headers
font=("", 18, "bold")

# Level 3: Subsection headers
font=("", 16, "bold")

# Level 4: Navigation, primary actions
font=("", 14)

# Level 5: Body text, form fields
font=("", 13)

# Level 6: Secondary info, timestamps
font=("", 12)

# Level 7: Filter buttons, compact UI
font=("", 11)
```

### Spacing System

**Consistent Scale**:
- **5px**: Micro-spacing (button padding)
- **10px**: Small gaps (related elements)
- **20px**: Medium gaps (section padding)
- **30px**: Large gaps (page margins)
- **40px**: Extra-large (collapsible nav width)

### Shape Language

**Border Radius**:
- **0px**: Structural elements (navbar)
- **8px**: Cards, product tiles
- **15px**: Dialogs, tag chips (pill shape)

**Component Heights**:
- **35px**: Small buttons, input fields
- **40px**: Medium buttons
- **50px**: Client list items
- **30px**: Fixed-height headers (anti-wobble)

### Icon System

**FontAwesome Integration**:
- **24px**: Navigation icons
- **20px**: Button icons
- **18px**: Inline action icons

**Cached Rendering**:
```python
class IconManager:
    def __init__(self):
        self._cache = {}

    def get_icon(self, name: str, size: int, fill: str):
        key = f"{name}_{size}_{fill}"
        if key not in self._cache:
            self._cache[key] = self._render_icon(name, size, fill)
        return self._cache[key]
```

### Component Library

#### **Buttons**
- Primary: Blue background, white text
- Secondary: Gray background
- Danger: Red background (delete actions)
- Transparent: No background, hover state
- Fixed heights: 35px/40px

#### **Input Fields**
- Consistent 35-40px height
- Rounded corners (8px)
- Clear focus indicators
- Placeholder text in gray

#### **Cards/Frames**
- Transparent backgrounds for nested content
- Subtle contrast for distinct sections
- 8px corner radius
- 10-20px padding

#### **Modal Overlays**
```python
class ModalOverlay(ctk.CTkFrame):
    """Semi-transparent overlay with centered content"""
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=("gray90", "gray15"),
            corner_radius=0
        )
        # Click-outside-to-close behavior
        # Centered content area
        # Esc key to dismiss
```

#### **Tag Chips**
- Blue pill shape (15px radius)
- × remove button on hover
- Comma-triggered creation
- Visual feedback

#### **Collapsible Navigation**
- 40px collapsed (icon-only)
- 180px expanded (icon + text)
- Active page highlighting
- Smooth animation

---

## 4. Database Schema

### Tables

#### **clients**
```sql
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    date_of_birth DATE,
    allergies TEXT,                    -- Red warning display
    tags TEXT,                         -- Comma-separated
    planned_treatment TEXT,            -- Rich text area
    notes TEXT,                        -- Rich text area
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_clients_name ON clients(last_name, first_name);
```

#### **treatment_records**
```sql
CREATE TABLE treatment_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    treatment_date DATE NOT NULL,
    treatment_notes TEXT NOT NULL,     -- What was done
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
CREATE INDEX idx_treatments_client_date ON treatment_records(client_id, treatment_date DESC);
```

#### **product_records**
```sql
CREATE TABLE product_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    product_date DATE NOT NULL,
    product_text TEXT NOT NULL,        -- Free-text product description/notes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
CREATE INDEX idx_products_client_date ON product_records(client_id, product_date DESC);
```

**Note**: Product records are text-only entries. When adding a product sale, the UI suggests products from the inventory list, but the actual record stores only text. This keeps the history simple and prevents issues when inventory items are renamed or deleted.

#### **inventory**
```sql
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_inventory_name ON inventory(name);
```

**Note**: Inventory is a simple reference list of products currently carried. No quantity tracking - this is just a catalog for autocomplete suggestions when logging product sales.

#### **audit_log**
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,          -- Which table was changed
    record_id INTEGER NOT NULL,        -- Which record
    action TEXT NOT NULL,              -- CREATE, UPDATE, DELETE
    field_name TEXT,                   -- Which field (for UPDATE)
    old_value TEXT,                    -- Previous value
    new_value TEXT,                    -- New value
    ui_location TEXT,                  -- Which page made the change
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_timestamp ON audit_log(created_at DESC);
```

#### **schema_migrations**
```sql
CREATE TABLE schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Migration Strategy

**Initial Migration** (`v001_initial_schema.py`):
- Creates all tables with indexes
- Sets up foreign key constraints
- Initializes schema_migrations table

**Future Migrations**:
- Follow SQLite table recreation pattern (no ALTER COLUMN)
- User confirmation with backup before applying
- Downgrade functions optional but documented

---

## 5. Key Features

### Client Management

#### Client List View (Optimized from v2)
- **Searchable list**: Fuzzy search by name/tags (60% threshold)
- **Alphabet filter**: A-Z sidebar for quick navigation
- **Clickable rows**: Direct binding, no nested buttons
- **Visual hierarchy**: Name in bold, tags as blue chips
- **Performance**: Fixed-height frames with `pack_propagate(False)`

#### Client Detail View (Visual Design from v1)
- **2x2 Grid Layout**:
  - Top-left: Planned Treatment (rich text)
  - Top-right: Personal Notes (rich text)
  - Bottom-left: Treatment History (chronological list)
  - Bottom-right: Product History (chronological list)

- **Auto-save**: 1-second debounce on text changes
- **Edit Client Info**: Modal dialog with all demographics
- **Inline Add Buttons**: Always visible, not hover-dependent
- **Duplicate Prevention**: Clicking "Add" on existing date opens edit dialog
- **Timestamp Display**: Shows "Edited" if modified > 1 second after creation

### Treatment Tracking

**Features**:
- Date-based entries (default: today)
- Free-text notes field
- Edit existing entries (inline dialog)
- No duplicate dates (edit instead)
- History sorted by date DESC

**UI Pattern**:
```
[Treatment History]
┌────────────────────────────────────┐
│ 2025-11-26          [Edit] [Delete]│
│ Applied facial treatment with      │
│ hyaluronic acid serum             │
│ Created: 14:32 (Edited: 14:35)   │
├────────────────────────────────────┤
│ 2025-11-20          [Edit] [Delete]│
│ Consultation for new client       │
└────────────────────────────────────┘
[+ Add Treatment]
```

### Product Inventory

**Purpose**: A simple reference catalog of products currently carried by the salon.

**Features**:
- CRUD operations on products
- Searchable with fuzzy matching
- Alphabet/numeric filter (0-9, A-Z)
- Name and description fields only (no quantity tracking)
- Simple list for autocomplete/suggestion purposes

**Product Card Design**:
```
┌──────────────────────────┐
│ Hyaluronic Acid Serum   │
│ ─────────────────────── │
│ Premium anti-aging      │
│ treatment serum         │
│                         │
│ [Edit]         [Delete] │
└──────────────────────────┘
```

**No Quantity Tracking**: The inventory is just a catalog for reference and suggestions. Actual product usage/sales are logged as text-only records in client history.

### Product Records (Sales/Usage)

**Purpose**: Track what products were sold or used with each client as free-text entries.

**Features**:
- Date-based entries (default: today)
- Free-text product field with autocomplete suggestions
- Suggestions pulled from inventory catalog
- No links to inventory (text-only storage)
- Edit existing entries (inline dialog)
- No duplicate dates (edit instead)
- History sorted by date DESC

**Add Product Record Dialog**:
1. Select date (calendar picker, default: today)
2. Enter product text (autocomplete suggests from inventory)
3. Optional additional notes
4. Save as text-only record

**Why Text-Only**:
- Products can be renamed/deleted in inventory without breaking history
- Allows for one-off or discontinued products
- Simple and flexible
- Users can type anything, not limited to inventory

**UI Pattern**:
```
[Product History]
┌────────────────────────────────────┐
│ 2025-11-26          [Edit] [Delete]│
│ Hyaluronic Acid Serum - 1 bottle  │
│ Created: 14:32 (Edited: 14:35)   │
├────────────────────────────────────┤
│ 2025-11-20          [Edit] [Delete]│
│ Rose water toner                  │
└────────────────────────────────────┘
[+ Add Product]
```

### Audit Logging

**Purpose**: Provide a human-readable change history with meaningful summaries that show WHO changed WHAT, WHEN, and HOW.

**Tracked Events**:
- Client CRUD operations
- Treatment CRUD operations
- Product record CRUD operations
- Inventory changes
- Settings modifications

**Meaningful Audit Summaries**:

Instead of cryptic database field changes, the audit log displays contextual, readable summaries:

**Examples**:
```
✓ New treatment added for Jane Doe
  "Full facial, cut nails on right foot"
  2025-11-26 14:32 | Client Detail View

✓ Treatment updated for John Doe (2025-11-13)
  Changed from: "Full facial"
  Changed to: "Full facial and lymph drainage"
  2025-11-26 15:10 | Client Detail View

✓ Product record added for Sarah Smith
  "Hyaluronic Acid Serum - 1 bottle"
  2025-11-26 16:20 | Client Detail View

✓ Client created: Jane Doe
  Email: jane@example.com, DOB: 1985-03-15
  2025-11-26 09:00 | Client List View

✓ Client updated: John Doe
  Changed field: allergies
  From: (empty)
  To: "Sensitive to retinol"
  2025-11-26 11:45 | Client Info Dialog
```

**Implementation Strategy**:

The `AuditLog` model has a `get_description()` method that formats entries intelligently:

```python
class AuditLog(BaseModel):
    table_name: str
    record_id: int
    action: str  # CREATE, UPDATE, DELETE
    field_name: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    ui_location: str
    timestamp: datetime

    def get_description(self, db: DatabaseConnection) -> str:
        """Generate human-readable summary"""

        # Fetch related data (client name, treatment date, etc.)
        if self.table_name == "treatment_records":
            client_name = db.get_client_name(self.record_id)

            if self.action == "CREATE":
                return f"New treatment added for {client_name}\n\"{self.new_value}\""

            elif self.action == "UPDATE":
                treatment_date = db.get_treatment_date(self.record_id)
                return (f"Treatment updated for {client_name} ({treatment_date})\n"
                       f"Changed from: \"{self.old_value}\"\n"
                       f"Changed to: \"{self.new_value}\"")

            elif self.action == "DELETE":
                return f"Treatment deleted for {client_name}\n\"{self.old_value}\""

        elif self.table_name == "clients":
            client_name = self.new_value if self.action == "CREATE" else db.get_client_name(self.record_id)

            if self.action == "CREATE":
                return f"Client created: {client_name}"

            elif self.action == "UPDATE":
                return (f"Client updated: {client_name}\n"
                       f"Changed field: {self.field_name}\n"
                       f"From: {self.old_value or '(empty)'}\n"
                       f"To: {self.new_value}")

        # Similar logic for product_records, inventory, etc.
        ...
```

**Audit View Features**:
- **Chronological display**: Most recent first
- **Filterable**: By table, action type, date range, client name
- **Searchable**: Find specific changes
- **Contextual icons**: ✓ for CREATE, ✎ for UPDATE, ✗ for DELETE
- **Timestamp**: Human-readable format (e.g., "2 hours ago", "Today at 14:32")
- **UI location badge**: Shows which part of the app made the change
- **Retention cleanup**: Auto-delete old entries based on settings

### Backup & Export

**Auto-Backup** (from v2):
- Configurable interval (default: 60 minutes since last backup)
- Retention: Keep last N backups OR keep backups < N days
- ZIP compression with timestamp
- Pre-migration automatic backup

**Manual Backup**:
- On-demand backup button in settings
- CSV export (all tables to separate files)
- Database relocation with migration

### Settings & Preferences

**Appearance**:
- Theme: Dark/Light/System
- UI Zoom: 80%-200% scaling (apply button)
- Language: English/German (runtime switch)

**Backup Configuration**:
- Auto-backup on startup: Yes/No
- Backup interval: Minutes since last backup
- Retention count: Keep last N
- Retention days: Keep backups < N days old

**Paths**:
- Database location (custom path with migration)
- Backup directory
- Config directory (bootstrap file support)

**Advanced**:
- Audit log retention (keep last N entries)
- Export all data to CSV

---

## 6. Performance Optimizations (From v2)

### List View Optimizations

**Anti-Pattern (Avoid)**:
```python
# DON'T: Nested containers with hover states
container = CTkFrame()
    button_frame = CTkFrame()  # Hidden by default
        edit_btn = CTkButton()
    bind hover to show/hide button_frame
```

**Optimized Pattern**:
```python
# DO: Direct clickable frame with fixed height
frame = CTkFrame(height=50, cursor="hand2")
frame.pack_propagate(False)
frame.bind("<Button-1>", lambda e: self.view_client(client_id))
# Action buttons always visible at end
```

### Search Performance

**Fuzzy Search**:
- 60% threshold (balance precision/recall)
- Multi-field matching (name, tags, description)
- Relevance scoring with sorting
- Debounced input (300ms delay)

**Alphabet Filter**:
- Non-scrollable sidebar (A-Z always visible)
- Direct SQL: `WHERE name LIKE 'A%'`
- Active filter highlighting
- Instant results (no fuzzy matching needed)

### Pagination & Lazy Loading

**Client List**:
- Load first 20 clients initially
- "Load More" button at bottom of list
- Infinite scroll option (load next batch when near bottom)
- Search resets to first page

**Treatment/Product History**:
- Show most recent 20 entries per client
- "Show More" button to load additional entries
- `LIMIT 20 OFFSET 0` pattern for initial load

**Audit Log**:
- Paginated view: 50 entries per page
- Page navigation controls (1, 2, 3... Next)
- Jump to page input

**Implementation Pattern**:
```python
class ClientListView:
    def __init__(self):
        self.page_size = 20
        self.current_offset = 0

    def load_clients(self):
        clients = self.controller.get_clients(
            limit=self.page_size,
            offset=self.current_offset
        )
        self.render_clients(clients)

    def load_more(self):
        self.current_offset += self.page_size
        clients = self.controller.get_clients(
            limit=self.page_size,
            offset=self.current_offset
        )
        self.append_clients(clients)
```

### Database Indexing

**Critical Indexes for Pagination**:
```sql
-- Client list: ORDER BY last_name, first_name
CREATE INDEX idx_clients_name ON clients(last_name, first_name);

-- Treatment history: ORDER BY treatment_date DESC (most recent first)
CREATE INDEX idx_treatments_client_date
ON treatment_records(client_id, treatment_date DESC);

-- Product history: ORDER BY product_date DESC
CREATE INDEX idx_products_client_date
ON product_records(client_id, product_date DESC);

-- Audit log: ORDER BY created_at DESC
CREATE INDEX idx_audit_timestamp ON audit_log(created_at DESC);

-- Inventory autocomplete: ORDER BY name
CREATE INDEX idx_inventory_name ON inventory(name);
```

**Why DESC Indexes Matter**:
- SQLite can use descending indexes efficiently for `ORDER BY ... DESC LIMIT N`
- Makes "most recent 20" queries extremely fast
- No need to scan entire table to get latest entries

**Query Optimization**:
```sql
-- Fast query with proper index usage
SELECT * FROM treatment_records
WHERE client_id = ?
ORDER BY treatment_date DESC
LIMIT 20;
-- Uses idx_treatments_client_date (client_id, treatment_date DESC)
-- SQLite reads first 20 matching rows and stops

-- For pagination
SELECT * FROM treatment_records
WHERE client_id = ?
ORDER BY treatment_date DESC
LIMIT 20 OFFSET 20;
-- Still fast with index, but slightly slower than OFFSET 0
```

**Performance Benefits**:
- Initial load: ~1ms for 20 records (with index)
- Without index: ~50ms+ for 20 records from 10,000 row table
- With pagination: UI remains responsive even with 100K+ records

### UI Responsiveness

**Debounced Auto-Save**:
```python
def schedule_save(self):
    if self._save_timer:
        self._save_timer.cancel()
    self._save_timer = threading.Timer(1.0, self.save)
    self._save_timer.start()
```

**Mousewheel Scrolling**:
- Recursive binding to all child widgets
- Boundary checking (prevent over-scroll)
- Platform-specific delta handling

**Icon Caching**:
- Cache by `{name}_{size}_{fill}`
- Prevents re-rendering FontAwesome icons
- Significant performance gain on navigation

---

## 7. Code Quality & Testing

### Testing Strategy

**Unit Tests**:
- Pydantic model validation
- Controller business logic
- Service layer functions
- Utility functions

**Integration Tests**:
- Database operations (CRUD)
- Migration system
- Backup/restore functionality

**Coverage Target**: 80%+ for critical paths

### Code Quality Tools

**Pre-Commit Checks** (automated):
- `black`: Code formatting (line-length=88)
- `flake8`: Linting with complexity checks
- `mypy`: Static type checking

**CI/CD Pipeline**:
```yaml
# .gitea/workflows/build.yml
- Run tests (pytest)
- Check formatting (black --check)
- Lint (flake8)
- Type check (mypy)
- Build executable (PyInstaller)
```

### Type Hints

**Comprehensive Typing**:
```python
from typing import Optional, List, Dict
from datetime import date, datetime
from pydantic import BaseModel

class Client(BaseModel):
    id: Optional[int] = None
    first_name: str
    last_name: str
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    tags: List[str] = []

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

---

## 8. Internationalization (i18n)

### Translation System

**Babel Setup**:
```python
# locales/en_US/LC_MESSAGES/messages.po
msgid "Clients"
msgstr "Clients"

msgid "Add Treatment"
msgstr "Add Treatment"

# locales/de_DE/LC_MESSAGES/messages.po
msgid "Clients"
msgstr "Kunden"

msgid "Add Treatment"
msgstr "Behandlung hinzufügen"
```

**Runtime Usage**:
```python
from babel.support import Translations

translations = Translations.load('locales', [locale])
_ = translations.gettext

label = ctk.CTkLabel(text=_("Clients"))
```

**Date Formatting**:
- English: MM/DD/YYYY
- German: DD.MM.YYYY
- Use Babel's `format_date()` with locale

### Supported Languages

**Initial Release**:
- English (en_US)
- German (de_DE)

**Future Expansion**:
- Easy to add new `.po` files
- Translation extraction script: `scripts/extract_translations.py`
- Compilation script: `scripts/compile_translations.py`

### Emoji Usage

**Language Selector**: Use `CTkRadioButton` instead of `CTkOptionMenu` for flag emojis (`🇬🇧 English`, `🇩🇪 Deutsch`). Radio buttons handle emojis reliably; dropdowns have rendering issues.

**Safe to use**:
- Section headers: `🌍 Language`, `🔍 Accessibility`, `💾 Backup Settings`
- Radio buttons and labels
- Buttons (use sparingly)

**Avoid**:
- CTkOptionMenu dropdown values
- Data fields (keep data emoji-free)

---

## 9. Packaging & Distribution

### PyInstaller Configuration

**Single-File Executable**:
```python
# cosmetics_records.spec
a = Analysis(
    ['src/cosmetics_records/app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/cosmetics_records/locales', 'locales'),
        ('src/cosmetics_records/database/migrations', 'database/migrations'),
    ],
    hiddenimports=['babel.numbers', 'pydantic'],
    ...
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(pyz, ..., name='CosmeticsRecords', console=False)
```

**Platform-Specific Builds**:
- **Linux**: AppImage or standalone binary
- **Windows**: `.exe` with icon
- **macOS**: `.app` bundle

### Build Scripts

**`scripts/build.py`**:
```python
# 1. Run tests
# 2. Check formatting
# 3. Compile translations
# 4. Run PyInstaller
# 5. Verify executable
# 6. Package release
```

---

## 10. User Experience Enhancements

### Keyboard Shortcuts (From v1)

**Global Shortcuts**:
- `Ctrl/Cmd + A`: Select all (all text fields)
- `Ctrl/Cmd + C/V/X`: Copy/paste/cut
- `Escape`: Close modal dialogs
- `Enter`: Submit forms (dialogs)

**Context-Specific**:
- `Ctrl/Cmd + N`: New client (from client list)
- `Ctrl/Cmd + F`: Focus search field
- `Ctrl/Cmd + S`: Manual save (if debounce disabled)

### Accessibility Features

**UI Scaling**:
- 80%-200% zoom range
- 5% increments (24 steps)
- Apply button (doesn't auto-apply on slider)
- Settings persist across sessions

**Theme Support**:
- Dark mode (default)
- Light mode
- System detection on first launch

**Visual Indicators**:
- High contrast in both themes
- Focus indicators on all inputs
- Active state highlighting
- Clear button hover states

### Smart Defaults

**Client Creation**:
- Auto-focus on name field
- Date picker defaults to today
- Tags: comma-triggered creation

**Record Addition**:
- Date defaults to today
- Checks for existing entry (prevent duplicates)
- Auto-save after creation

**Settings**:
- Platform-aware default paths
- Bootstrap file for custom config location
- Sensible retention policies (keep last 10 backups)

---

## 11. Development Workflow

### Project Setup

**Initial Setup**:
```bash
# Clone repository
git clone <repo-url>
cd cosmetics-records

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run application
python src/cosmetics_records/app.py
```

### Development Commands

**Testing**:
```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/cosmetics_records --cov-report=html

# Specific test file
pytest tests/unit/test_client_model.py
```

**Code Quality**:
```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

**Translations**:
```bash
# Extract translatable strings
python scripts/extract_translations.py

# Compile .po to .mo
python scripts/compile_translations.py
```

**Build**:
```bash
# Create executable
python scripts/build.py

# Or manual PyInstaller
pyinstaller cosmetics_records.spec
```

### Git Workflow

**Branch Strategy**:
- `main`: Stable releases
- `develop`: Integration branch
- `feature/*`: New features
- `fix/*`: Bug fixes

**Commit Messages**:
- Follow conventional commits
- Examples:
  - `feat: Add audit log view`
  - `fix: Prevent duplicate treatment entries`
  - `refactor: Extract modal overlay base class`
  - `docs: Update README with build instructions`

---

## 12. Recent Updates (2025-11-29)

### Release v1.0.0 Preparation
**Status**: ✅ Completed

Prepared codebase for initial production release:

**Version Standardization**:
- Updated `pyproject.toml` from 3.0.0 to 1.0.0
- Updated application window title to "Cosmetics Records v1.0"
- Updated Settings view version display
- Synchronized version across all files and locales

**App Icons Added**:
- Copied icons from cc-cosmetics-records-2 reference project
- Added SVG source (cosmetics-records-icon.svg)
- Added PNG variants (256px, 64px, 32px)
- Added Windows ICO format (icon.ico)
- Ready for PyInstaller integration in `resources/icons/`

**Migration Consolidation**:
- Merged v001, v002, v003 into single comprehensive v001_initial_schema.py
- Removed redundant v002 (audit_log already in v001)
- Integrated inventory quantity system (capacity/unit) from v003 into v001
- Cleaner for new installations while preserving existing database compatibility

### Reusable UI Components Library
**Status**: ✅ Completed

Created standardized, reusable components for consistent UX:

**New Components**:
- `AlphabetFilter`: A-Z sidebar filter for client/inventory lists
- `AutocompleteEntry`: Input field with dropdown suggestions
- `SearchBar`: Unified search component with integrated button
- `InfiniteScrollPagination`: Automatic loading strategy for long lists

**Benefits**:
- Consistent behavior across all list views
- Reduced code duplication
- Easier maintenance and updates

### Client List & Detail Enhancements
**Status**: ✅ Completed

**Client List Improvements**:
- **Infinite scroll pagination**: Automatically loads next 20 clients when scrolling near bottom
- **Alphabet filter**: A-Z sidebar for quick navigation
- **SearchBar integration**: Unified search component
- **Bold last names**: Improved visual scanning hierarchy
- **Conditional tag display**: Tags only shown when matching search query
- **Full-width entries**: Removed horizontal padding for better space utilization

**Client Detail View**:
- Edit dialogs for treatments and product records
- Hover-based edit buttons with pen icon
- Improved timestamp displays (Created/Edited)
- Better layout and spacing

**Implementation**: `client_list_view.py`, `client_detail_view.py`
- Uses InfiniteScrollPagination strategy
- Detects when 3rd-to-last client scrolls into view
- Prevents multiple simultaneous loads with `is_loading` flag
- Tracks remaining items with `has_more` flag

### Dialog System Standardization
**Status**: ✅ Completed

**New Edit Dialogs**:
- `EditTreatmentDialog`: Edit existing treatment records
- `EditProductRecordDialog`: Edit existing product records
- Both follow consistent ModalOverlay pattern

**Improvements to All Dialogs**:
- Fixed content frame creation using `create_content_frame(width, height)`
- Proper error message display referencing `self.content`
- Consistent button layouts and validation
- Auto-dismiss errors after 3 seconds

**Client & Inventory Dialogs**:
- `EditClientDialog`: Uses DatePicker component, compact field spacing
- `EditInventoryItemDialog`: Integrated delete button, capacity/unit fields
- All dialogs support Enter key submission and Escape to cancel

### Navbar Redesign
**Status**: ✅ Completed

Complete navbar UX overhaul:

**Layout Changes**:
- Removed header/separator for cleaner appearance
- **Dynamic client detail button**: Appears only when viewing a specific client
- Shows client name when expanded, disappears on other pages
- Bottom-aligned settings and audit buttons using spacer frame

**Distinctive Icons** (Unicode symbols for collapsed mode):
- Clients: `☰` (list/hamburger)
- Client Detail: `☺` (user)
- Audit Log: `⟲` (history/refresh)
- Settings: `⚙` (gear/cog)
- Inventory: `■` (box/package)

**Technical Fix**:
- Switched from grid to pack layout in `app.py`
- Pack handles dynamic width changes more reliably
- Smooth transitions between 180px (expanded) and 60px (collapsed)
- Toggle button repositions correctly with place geometry

**Implementation**: `navbar.py`, `app.py`
- Split nav items into `top_nav_items` and `bottom_nav_items`
- Added `set_client_detail(client_id, client_name)` method
- Modified `_toggle_expanded()` to handle dynamic button visibility

### Inventory Quantity System
**Status**: ✅ Completed

Implemented comprehensive quantity tracking for inventory items:

**Database Schema** (integrated into v001_initial_schema.py):
- `capacity` field (REAL, NOT NULL) for amount/volume/count
- `unit` field (TEXT with CHECK constraint: 'ml', 'g', 'Pc.')
- Constraints ensure data integrity

**Model Updates** (`models/product.py`):
- `InventoryItem` now includes:
  - `capacity: float = Field(gt=0)` - Must be greater than 0
  - `unit: Literal["ml", "g", "Pc."]` - Type-safe enum
- `get_display_name()` method: Returns "Product Name (capacity unit)"

**UI Components**:
- **Add Dialog**: Capacity input + unit dropdown (ml/g/Pc.)
- **Edit Dialog**: Same fields, plus integrated delete button
- **List View**: Clickable rows showing capacity in display name
  - Row height: 60px fixed
  - Hover cursor change to "hand2"
  - Click anywhere to edit
  - Delete moved to edit dialog

**Benefits**:
- Track specific product sizes (e.g., 30ml vs 50ml bottles)
- Consistent UX with client list (clickable rows instead of buttons)
- Type-safe unit enforcement prevents invalid data
- Pydantic validation ensures capacity > 0

### Icon System Improvements
**Status**: ✅ Completed

**IconManager Enhancements**:
- Updated to use non-emoji Unicode characters for better cross-platform compatibility
- Improved font fallback chain:
  - Emoji fonts: NotoColorEmoji, NotoEmoji, Symbola
  - Regular fonts: DejaVuSans, LiberationSans, Unifont
- Cached rendering by `{name}_{size}_{fill}` for performance
- Consistent icon display across Linux, Windows, macOS

**Benefits**:
- More reliable rendering without emoji font dependencies
- Better performance through caching
- Cleaner appearance in collapsed navbar

### Component Refinements
**Status**: ✅ Completed

**DatePicker**:
- Calendar popup improvements
- Better modal behavior with grab_set timing
- Today button for quick selection

**Code Quality**:
- Standardized error handling patterns
- Consistent validation across all dialogs
- Improved type hints and documentation

---

## 13. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

**Architecture Setup**:
- [x] Create directory structure
- [ ] Set up `pyproject.toml` and dependencies
- [ ] Configure testing framework
- [ ] Set up CI/CD pipeline
- [ ] Create base `DatabaseConnection` class
- [ ] Implement migration system
- [ ] Write initial migration (`v001_initial_schema.py`)

**Core Models**:
- [ ] `Client` Pydantic model with validation
- [ ] `Treatment` model
- [ ] `ProductRecord` model (text-only)
- [ ] `InventoryItem` model
- [ ] `AuditLog` model

### Phase 2: UI Foundation (Weeks 3-4)

**Component Library**:
- [ ] `IconManager` with caching
- [ ] `ModalOverlay` base class
- [ ] `CollapsibleNavBar`
- [ ] `DatePicker` widget
- [ ] `TagInput` component
- [ ] Apply consistent styling (colors, fonts, spacing)

**Main Application**:
- [ ] `CosmeticsRecordsApp` main class
- [ ] Navigation routing
- [ ] Theme management
- [ ] i18n setup (English only initially)

### Phase 3: Client Management (Weeks 5-6)

**Client List**:
- [ ] `ClientListView` with optimized rendering
- [ ] Pagination: Load first 20 clients with "Load More" button
- [ ] Fuzzy search implementation (resets to page 1)
- [ ] Alphabet filter sidebar
- [ ] `AddClientDialog`
- [ ] Client deletion with confirmation

**Client Detail**:
- [ ] `ClientDetailView` with 2x2 grid layout
- [ ] Planned treatment auto-save
- [ ] Personal notes auto-save
- [ ] `EditClientInfoDialog` with all demographics
- [ ] Age calculation from DOB
- [ ] Allergy warning display (red text)

### Phase 4: Treatment & Product Records (Weeks 7-8)

**Treatment Tracking**:
- [ ] Treatment history display (most recent 20 entries)
- [ ] "Show More" button for pagination
- [ ] `AddTreatmentDialog` (inline)
- [ ] Edit existing treatments
- [ ] Duplicate date prevention
- [ ] Timestamp display (created/edited)
- [ ] Delete with confirmation

**Product Records**:
- [ ] Product history display (most recent 20 entries)
- [ ] "Show More" button for pagination
- [ ] `AddProductRecordDialog` with autocomplete
- [ ] Autocomplete from inventory catalog
- [ ] Edit/delete product records
- [ ] Duplicate date prevention
- [ ] Text-only storage (no foreign keys)

### Phase 5: Inventory (Week 9)

**Inventory Management**:
- [ ] `InventoryView` with simple list
- [ ] Fuzzy search
- [ ] Alphanumeric filter (0-9, A-Z)
- [ ] `AddInventoryItemDialog`
- [ ] Edit inventory item details
- [ ] Delete inventory items (no reference checking needed)

### Phase 6: Services & Logging (Week 10)

**Audit Service**:
- [ ] Implement `AuditService` with UI context tracking
- [ ] Add `get_description()` method to `AuditLog` model for meaningful summaries
- [ ] Implement context-aware formatting (client names, dates, field names)
- [ ] Integrate into all controllers (client, treatment, product, inventory)
- [ ] `AuditLogView` with pagination (50 entries per page)
- [ ] Page navigation controls (Previous, 1, 2, 3... Next)
- [ ] Filtering and search (resets to page 1)
- [ ] Contextual icons (✓ CREATE, ✎ UPDATE, ✗ DELETE)
- [ ] Human-readable timestamps ("2 hours ago", "Today at 14:32")
- [ ] Retention cleanup with configurable limits

**Backup Service**:
- [ ] `BackupService` with ZIP compression
- [ ] Auto-backup on startup (configurable)
- [ ] Retention policies (count + days)
- [ ] Manual backup button
- [ ] CSV export functionality

### Phase 7: Settings & Polish (Week 11)

**Settings Page**:
- [ ] Theme selector (Dark/Light/System)
- [ ] UI zoom slider (80%-200%)
- [ ] Language selector (EN/DE)
- [ ] Backup configuration
- [ ] Database path management
- [ ] Audit retention settings

**Final Polish**:
- [ ] Add German translations
- [ ] Keyboard shortcuts (all views)
- [ ] Mousewheel scrolling fixes
- [ ] Icon consistency pass
- [ ] Spacing consistency pass

### Phase 8: Testing & Packaging (Week 12)

**Testing**:
- [ ] Write unit tests for models
- [ ] Write integration tests for database
- [ ] Test migration system
- [ ] Test backup/restore
- [ ] Manual UI testing (all workflows)

**Packaging**:
- [ ] Configure PyInstaller spec
- [ ] Test executable on all platforms
- [ ] Create installation instructions
- [ ] Write user documentation
- [ ] Prepare release notes

---

## 13. Success Criteria

### Functional Requirements

**Must Have**:
- ✅ Client CRUD with search and filtering
- ✅ Treatment history tracking (text-only, with autocomplete)
- ✅ Product records (text-only, with autocomplete from inventory)
- ✅ Inventory management (simple catalog)
- ✅ Auto-save functionality
- ✅ Backup automation
- ✅ Dark/Light theme support
- ✅ English + German translations
- ✅ Pagination/lazy loading (20 items per page)
- ✅ Meaningful audit summaries

**Should Have**:
- ✅ Audit logging with retention
- ✅ UI scaling (accessibility)
- ✅ CSV export
- ✅ Database migration system
- ✅ Keyboard shortcuts
- ✅ Descending indexes for performance

**Out of Scope** (not needed for v3):
- ❌ PDF report generation
- ❌ Email integration
- ❌ Statistics/revenue dashboard
- ❌ Appointment scheduling

### Non-Functional Requirements

**Performance**:
- Client list loads < 200ms (500 clients)
- Search results < 100ms
- UI responsiveness (no freezing)
- Smooth scrolling (60 FPS target)

**Usability**:
- Intuitive navigation (< 3 clicks to any feature)
- Consistent visual language
- Clear error messages
- Reversible actions (with confirmation)

**Maintainability**:
- 80%+ test coverage
- Type hints on all public APIs
- Clear separation of concerns
- Documented complex logic

**Reliability**:
- No data loss (automatic backups)
- Transaction safety (SQLite ACID)
- Graceful error handling
- Migration safety (user confirmation + backup)

---

## 14. Risk Mitigation

### Technical Risks

**Risk**: Migration system breaks existing databases
**Mitigation**:
- Automatic pre-migration backup
- User confirmation before applying
- Downgrade functions (where feasible)
- Thorough testing on example database

**Risk**: PyInstaller packaging issues
**Mitigation**:
- Test builds early and often
- Explicit `datas` specification
- Hidden imports for dynamic modules
- Platform-specific testing

**Risk**: Performance degradation with large datasets
**Mitigation**:
- Database indexing strategy
- Pagination for long lists
- Efficient SQL queries
- Load testing with example database (75K records)

### UX Risks

**Risk**: Users don't understand migration prompts
**Mitigation**:
- Clear, non-technical language
- "What will happen" explanations
- Automatic backup reminder
- Option to defer migration

**Risk**: Data loss from auto-save failures
**Mitigation**:
- Visual feedback on save success/failure
- Retry logic with backoff
- "Last saved" timestamp display
- Manual save option

---

## 15. Future Enhancements

### Version 3.1 (Post-Launch)

**Analytics Dashboard**:
- Revenue tracking (product sales)
- Popular treatments chart
- Client retention metrics
- Appointment frequency analysis

**Reporting**:
- PDF client history export
- Monthly summary reports
- Inventory reorder alerts
- Revenue reports

### Version 3.2

**Multi-Location Support**:
- Location/branch management
- Per-location inventory
- Cross-location reporting
- Staff assignment

**Scheduling**:
- Appointment calendar view
- Recurring appointments
- Email/SMS reminders
- Conflict detection

### Version 4.0 (Major)

**Cloud Sync**:
- Optional cloud backup
- Multi-device sync
- Web dashboard (read-only)
- Mobile app integration

**Advanced Features**:
- Photo attachments (before/after)
- Treatment templates
- Product bundles/packages
- Discount/loyalty system

---

## 16. Conclusion

This plan combines:
- **v1's visual cohesion**: Professional design system, polished UI, thoughtful interactions
- **v2's mature architecture**: MVC pattern, migrations, services, code quality tooling

The result is a production-ready application that's:
- **Beautiful**: Consistent, professional, accessible
- **Maintainable**: Clean architecture, tested, typed
- **Reliable**: Automated backups, migration safety, audit trails
- **Performant**: Optimized list views, cached icons, indexed queries

By following this plan, we'll build a salon management application that's both a joy to use and a pleasure to maintain.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-26
**Author**: Claude (Anthropic)
