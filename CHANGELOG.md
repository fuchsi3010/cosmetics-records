# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-31

### Highlights

First stable release! This version includes all features from the beta releases with additional bug fixes and improvements.

### Fixed
- Product sale edit dialog now properly displays existing products
- Code formatting compliance with black

### Changed
- Improved client search threshold from 70% to 80% for more precise results

### Documentation
- Added demo video to README

---

## [1.0.0-beta.1] - 2025-12-11

### Highlights

This is the first beta release of Cosmetics Records, a desktop application for cosmetics salon client management. The application has been completely rewritten using PyQt6 for a modern, cross-platform experience.

### Added

- **Client Management**
  - Create, edit, and delete client records
  - Store contact information (name, email, phone, address)
  - Track date of birth with automatic age calculation
  - Record allergies with visual highlighting
  - Tag clients for easy categorization
  - Fuzzy search with 70% match threshold
  - Alphabetical filtering (A-Z)

- **Treatment History**
  - Log treatments with date and detailed notes
  - Edit and delete treatment records
  - Automatic timestamp tracking (created/updated)
  - Pagination with infinite scroll

- **Product Sales History**
  - Record product sales with quantity (1x-10x)
  - Free-text product entry with inventory suggestions
  - Autocomplete from inventory items
  - Edit and delete product records

- **Inventory Management**
  - Maintain product catalog
  - Track product name, description, capacity, and unit
  - Units support: ml, g, Pc. (pieces)

- **Audit Logging**
  - Comprehensive change tracking for all data modifications
  - Records old and new values for updates
  - Tracks creation and deletion events
  - Links changes to specific clients

- **Data Import/Export**
  - Import clients, treatments, and product sales from CSV
  - Export clients for mail merge (with sorting and limit options)
  - Export all data types to CSV
  - UTF-8 with BOM for Excel compatibility

- **Backup System**
  - Automatic backups every 2 hours (configurable)
  - Retain last 25 backups (configurable)
  - Manual backup creation
  - Backup restoration with integrity verification

- **Localization**
  - English (en_US) and German (de_DE) language support
  - Localized date formatting
  - Configurable date format (language-based, ISO 8601, US, DE)

- **Themes**
  - Dark theme (default)
  - Light theme
  - System theme detection

- **UI Features**
  - Scalable UI (80% - 200%)
  - Auto-saving text fields with visual feedback
  - Keyboard navigation support
  - Responsive layout

### Technical Features

- **Architecture**: Clean MVC (Model-View-Controller) pattern
- **Database**: SQLite with migration system
- **Validation**: Pydantic 2.0+ for data validation
- **Type Safety**: Full type hints with MyPy strict mode
- **Cross-Platform**: Windows, macOS (Intel + Apple Silicon), Linux

### Security

- SQL injection prevention via parameterized queries
- Path traversal protection in backup operations
- Foreign key constraint enforcement
- Transaction rollback on errors

---

## [0.9.0-alpha9] - 2025-12-11

### Added
- Mail merge export with sorting by recent activity and client limit options
- Treatment and product sale content now included in audit log entries
- Date picker localization for German language

### Changed
- Default backup interval changed from 60 to 120 minutes
- Default backup retention changed from 5 to 25 backups
- Increased history entry date/time font size from 11px to 13px

### Fixed
- History entries now properly calculate height for wrapped text
- Scroll wheel events pass through history entries to parent scroll area
- Inventory export now uses correct table name
- Search threshold increased from 60% to 70% to reduce false positives

---

## [0.9.0-alpha8] - 2025-12-10

### Added
- Visual feedback for AutoSaveTextEdit component (saving indicator)
- Layout constants to replace magic numbers

### Changed
- Refactored all dialogs to use BaseDialog error helpers
- Aligned inventory view layout with client list view

---

## [0.9.0-alpha7] - 2025-12-09

### Fixed
- Database migrations now work correctly in PyInstaller bundles
- Windows build icon display
- Version number display in packaged application

---

## Previous Alpha Releases

Earlier alpha releases focused on:
- Initial PyQt6 migration from CustomTkinter
- Core CRUD functionality implementation
- Database schema design
- UI component development
- Testing infrastructure setup

---

## Roadmap

### 1.0.0 (Stable Release)
- Human testing feedback incorporated
- Documentation improvements
- Performance optimizations for large datasets

### Future Releases
- PDF export for treatment history
- Appointment scheduling integration
- Statistics and reporting dashboard
- Cloud backup options
