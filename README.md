# Cosmetics Records

A desktop client-records app for a one-person cosmetics salon: client data, treatment history, and product sales. Python 3.10+ and PyQt6, four source files, no other runtime dependencies.

Version 2.0 is a ground-up reimplementation focused on speed and security. It opens existing 1.x databases unchanged.

## Features

- **Clients**: contact data, allergies (shown prominently), tags, umlaut-safe search
- **Treatments & product sales**: per-client history, product entry with inventory autocomplete
- **Planned treatment / notes**: free-text fields, saved automatically when leaving the field
- **Inventory**: product catalog (ml, g, Pc.)
- **Change log**: complete audit history — written by database triggers, impossible for any code path to bypass
- **Backups**: automatic on startup (configurable interval), consistent snapshots even while the app is running, one-click restore
- **CSV export**: mail merge (name + address) and full export of all tables
- **Languages**: English and German (auto-detected from the system, switchable in Settings)
- **Themes**: Dark, Light, or follow the system

## Security

- Database, config, and backups get `0600` file permissions; the data directory `0700`
- `PRAGMA secure_delete`: deleted client data cannot be recovered from free database pages
- Parameterized SQL throughout
- No log file — treatment notes never land anywhere outside the database
- For encryption at rest, use full-disk encryption (LUKS/BitLocker)

## Running

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/cosmetics_records/app.py
```

On NixOS: `nix-shell --run 'python src/cosmetics_records/app.py'`

## Development

```bash
pip install -r requirements-dev.txt
pytest            # tests (includes a translation-completeness check)
black src tests   # formatting
```

Data lives in `~/.local/share/cosmetics_records/` (Linux), `%APPDATA%\cosmetics_records\` (Windows), or `~/Library/Application Support/cosmetics_records/` (macOS).

## License

Apache-2.0
