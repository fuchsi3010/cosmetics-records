# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cosmetics Records is a desktop application for a one-person cosmetics salon to manage client information, treatment history, and product sales. Python 3.10+, PyQt6, SQLite. German-only UI (the salon's language).

### Core User Story
A client arrives → user looks them up → views treatment plan and history → performs treatment → logs the treatment → recommends products based on purchase history → logs the sale.

## Architecture

Deliberately minimal — two source files, stdlib + PyQt6 only:

- `src/cosmetics_records/db.py` — schema, audit triggers, queries, config, backups, CSV export. No ORM, no validation framework; the DB enforces constraints (CHECK, FK, triggers).
- `src/cosmetics_records/app.py` — all UI: tabs (Kunden, Inventar, Protokoll, Einstellungen), dialogs. Native Qt widgets, no custom styling (Fusion follows the system theme).
- `tests/test_db.py` — end-to-end data-layer test.

Key decisions:
- **Schema is drop-in compatible** with the 1.x releases (migrations v001+v002 baked in, `schema_migrations` seeded). Don't change columns without a migration story.
- **Audit logging is done by SQLite triggers**, not application code. UPDATE audit rows store whole-row JSON snapshots (field_name NULL); the UI diffs them at display time and still renders legacy per-field rows.
- **Security posture**: parameterized SQL only, 0600/0700 file permissions, `secure_delete` on, no log files (treatment notes must not leak outside the DB), backup restore only accepts files inside the backup dir.

## Commands

```bash
python src/cosmetics_records/app.py   # run (use nix-shell on NixOS)
pytest                                # tests
black src tests && flake8 src tests   # format + lint (line length 88)
```

## Code Style

- black (88 chars), type hints on public functions
- Keep it lazy: stdlib/native Qt/DB constraints before new code; no new dependencies
- Deliberate simplifications are marked with `ponytail:` comments — read them before "fixing"

## Git Workflow

Conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`), atomic and focused.
