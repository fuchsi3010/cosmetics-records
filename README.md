# Cosmetics Records

A desktop client-records app for a one-person cosmetics salon: client data, treatment history, and product sales. Python 3.10+, four source files, two runtime dependencies (PyQt6, qtawesome for icons).

Version 2.0 is a ground-up reimplementation focused on speed and security. It opens existing 1.x databases unchanged.

## Features

- **Clients**: contact data, allergies (shown prominently), tags, umlaut-safe search
- **Treatments & product sales**: per-client history, product entry with inventory autocomplete
- **Planned treatment / notes**: free-text fields, saved automatically when leaving the field
- **Inventory**: product catalog (ml, g, Pc.)
- **Change log**: complete audit history — written by database triggers, impossible for any code path to bypass
- **Backups**: automatic on startup (configurable interval), consistent snapshots even while the app is running, one-click restore
- **CSV import/export**: mail merge (name + address), full export of all tables, and re-import of the exported files (also usable for bringing data in from other tools)
- **Log retention**: audit entries older than a configurable age are removed automatically at startup (privacy)
- **Database relocation**: move the database file from within Settings
- **Languages**: English and German (auto-detected from the system, switchable in Settings)
- **Themes**: Dark, Light, or follow the system

## Security

- Database, config, and backups get `0600` file permissions; the data directory `0700`
- `PRAGMA secure_delete`: deleted client data cannot be recovered from free database pages
- Parameterized SQL throughout
- No log file — treatment notes never land anywhere outside the database
- For encryption at rest, use full-disk encryption (LUKS/BitLocker)

## Installation

Download from the [Releases page](https://github.com/fuchsi3010/cosmetics-records/releases):

- **Windows**: `CosmeticsRecords-Windows-Setup.exe` — installs, and upgrades an existing 1.x installation in place (data is kept). `CosmeticsRecords-Windows.exe` is the portable no-install variant.
- **macOS**: unzip `CosmeticsRecords-macOS.zip` and drag the app to Applications.
- **Linux**: `CosmeticsRecords-Linux`, `chmod +x` and run.

## Running from source

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/cosmetics_records/app.py
```

On NixOS: `nix-shell --run 'python src/cosmetics_records/app.py'`

## Migrating from other software

1. Export your data from the old tool (CSV or Excel — anything tabular).
2. Run Cosmetics Records once and use *Settings → Export All Data (CSV)* on the empty database — the generated files **are** the import template.
3. Reshape your old export into those files. A spreadsheet, a small script, or an LLM ("here are my columns, produce these CSVs") all work. Only a few columns are required:
   - `clients.csv`: `first_name`, `last_name` (everything else optional; `id` is a temporary key that links the record files and is remapped on import)
   - `treatment_records.csv` / `product_records.csv`: `client_id`, `treatment_date`/`product_date` (`YYYY-MM-DD`), `treatment_notes`/`product_text`
   - `inventory.csv`: `name`, `capacity`, `unit` (`ml`, `g`, `Pc.`)

   Comma and semicolon delimiters both work (German Excel exports import as-is).
4. *Settings → Back up now*, then *Import Data (CSV)* and pick the folder. Every row is validated and the import is all-or-nothing — one bad row aborts with the offending file and row in the message, and nothing is written. Fix the CSV and try again.
5. Import looks wrong anyway? Restore the backup from step 4 — importing only ever adds records, it never merges or overwrites.

The import itself lands in the change log (one entry per record), so the migration stays traceable. Coming from version 1.x of this app: skip all of this — 2.0 opens the existing database directly.

## Development

```bash
pip install -r requirements-dev.txt
pytest            # tests (includes a translation-completeness check)
black src tests   # formatting
```

Data lives in `~/.local/share/cosmetics_records/` (Linux), `%APPDATA%\cosmetics_records\` (Windows), or `~/Library/Application Support/cosmetics_records/` (macOS).

## License

Apache-2.0
