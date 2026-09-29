"""Data layer: schema, audit triggers, queries, config, backups, CSV export.

Stdlib only. Schema is identical to the old v001+v002 migrations, so this
opens existing databases unchanged.
"""

from __future__ import annotations

import csv
import json
import os
import platform
import shutil
import sqlite3
import zipfile
from datetime import date, datetime
from pathlib import Path

VERSION = "2.0.0-beta.1"

# ponytail: schema copied verbatim from the old migrations for drop-in
# compatibility; audit_log gains client_id inline (was migration v002).
SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    date_of_birth DATE,
    allergies TEXT,
    tags TEXT,
    planned_treatment TEXT,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(last_name, first_name);

CREATE TABLE IF NOT EXISTS treatment_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    treatment_date DATE NOT NULL,
    treatment_notes TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_treatment_records_client_date
    ON treatment_records(client_id, treatment_date DESC);

CREATE TABLE IF NOT EXISTS product_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    product_date DATE NOT NULL,
    product_text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_product_records_client_date
    ON product_records(client_id, product_date DESC);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    capacity REAL NOT NULL,
    unit TEXT NOT NULL CHECK(unit IN ('ml', 'g', 'Pc.')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_inventory_name ON inventory(name);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('CREATE', 'UPDATE', 'DELETE')),
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    ui_location TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    client_id INTEGER
);
CREATE INDEX IF NOT EXISTS idx_audit_log_table_record
    ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at
    ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_client_id ON audit_log(client_id);

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT OR IGNORE INTO schema_migrations (version) VALUES ('v001'), ('v002');
"""

# Business columns snapshotted into audit rows (timestamps excluded as noise).
AUDITED = {
    "clients": (
        "first_name",
        "last_name",
        "email",
        "phone",
        "address",
        "date_of_birth",
        "allergies",
        "tags",
        "planned_treatment",
        "notes",
    ),
    "treatment_records": ("client_id", "treatment_date", "treatment_notes"),
    "product_records": ("client_id", "product_date", "product_text"),
    "inventory": ("name", "description", "capacity", "unit"),
}


def _audit_triggers() -> str:
    """Audit logging as DB triggers: cannot be bypassed by any code path,
    and cascade deletes get audited for free. UPDATE rows store whole-row
    JSON snapshots (field_name NULL); the UI diffs them at display time.
    Legacy per-field rows written by the old app still render as before."""
    ddl = []
    for table, cols in AUDITED.items():

        def snap(p: str) -> str:
            return "json_object(" + ", ".join(f"'{c}', {p}.{c}" for c in cols) + ")"

        def cid(p: str) -> str:
            if table == "clients":
                return f"{p}.id"
            return f"{p}.client_id" if "client_id" in cols else "NULL"

        ddl.append(f"""
CREATE TRIGGER IF NOT EXISTS audit_{table}_insert AFTER INSERT ON {table} BEGIN
    INSERT INTO audit_log (table_name, record_id, action, new_value, client_id)
    VALUES ('{table}', NEW.id, 'CREATE', {snap('NEW')}, {cid('NEW')});
END;
CREATE TRIGGER IF NOT EXISTS audit_{table}_update AFTER UPDATE ON {table}
WHEN {snap('OLD')} <> {snap('NEW')} BEGIN
    INSERT INTO audit_log
        (table_name, record_id, action, old_value, new_value, client_id)
    VALUES ('{table}', NEW.id, 'UPDATE', {snap('OLD')}, {snap('NEW')}, {cid('NEW')});
END;
CREATE TRIGGER IF NOT EXISTS audit_{table}_delete AFTER DELETE ON {table} BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_value, client_id)
    VALUES ('{table}', OLD.id, 'DELETE', {snap('OLD')}, {cid('OLD')});
END;""")
    return "\n".join(ddl)


# --------------------------------------------------------------------------
# Paths and config (same locations and JSON keys as the old app)
# --------------------------------------------------------------------------


def data_dir() -> Path:
    base = {
        "Windows": Path.home() / "AppData" / "Roaming",
        "Darwin": Path.home() / "Library" / "Application Support",
    }.get(platform.system(), Path.home() / ".local" / "share")
    return base / "cosmetics_records"


def load_config() -> dict:
    try:
        return json.loads((data_dir() / "config.json").read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(cfg: dict) -> None:
    path = data_dir() / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), "utf-8")
    os.chmod(path, 0o600)


def db_path(cfg: dict) -> Path:
    custom = cfg.get("database_path")
    return Path(custom) if custom else data_dir() / "cosmetics_records.db"


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.isolation_level = (
        None  # autocommit: single-user app, one statement = one change
    )
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        "PRAGMA secure_delete=ON"
    )  # deleted health data is not recoverable from free pages
    conn.executescript(SCHEMA)
    try:  # DBs from the old app that never ran migration v002
        conn.execute("ALTER TABLE audit_log ADD COLUMN client_id INTEGER")
    except sqlite3.OperationalError:
        pass
    conn.executescript(_audit_triggers())
    os.chmod(path, 0o600)
    return conn


# --------------------------------------------------------------------------
# Clients
# --------------------------------------------------------------------------

CLIENT_FIELDS = AUDITED["clients"]


def search_clients(conn: sqlite3.Connection, text: str = "") -> list[sqlite3.Row]:
    rows = conn.execute(
        "SELECT * FROM clients ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE"
    ).fetchall()
    if not text:
        return rows
    # ponytail: casefold substring match in Python — correct for umlauts where
    # SQL LIKE is not, instant at one-salon scale. FTS5 if this ever drags.
    needle = text.casefold()
    return [
        r
        for r in rows
        if needle in f"{r['first_name']} {r['last_name']} {r['tags'] or ''}".casefold()
    ]


def upcoming_birthdays(
    conn: sqlite3.Connection, days: int = 7, today: date | None = None
) -> list[tuple[int, sqlite3.Row]]:
    """(days until, client) for birthdays within the next `days` days, 0 = today."""
    today = today or date.today()
    out = []
    for r in conn.execute(
        "SELECT id, first_name, last_name, date_of_birth FROM clients"
        " WHERE date_of_birth > ''"
    ):
        born = date.fromisoformat(r["date_of_birth"])
        for year in (today.year, today.year + 1):  # December looks into January
            try:
                bday = born.replace(year=year)
            except ValueError:  # 29 February in a non-leap year
                bday = date(year, 2, 28)
            if 0 <= (bday - today).days <= days:
                out.append(((bday - today).days, r))
                break
    return sorted(out, key=lambda x: x[0])


def save_client(
    conn: sqlite3.Connection, fields: dict, client_id: int | None = None
) -> int:
    if client_id is None:
        cur = conn.execute(
            f"INSERT INTO clients ({', '.join(CLIENT_FIELDS)}) "
            f"VALUES ({', '.join('?' * len(CLIENT_FIELDS))})",
            [fields.get(f) for f in CLIENT_FIELDS],
        )
        return cur.lastrowid
    sets = ", ".join(f"{f} = ?" for f in CLIENT_FIELDS)
    conn.execute(
        f"UPDATE clients SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [fields.get(f) for f in CLIENT_FIELDS] + [client_id],
    )
    return client_id


def update_client_field(
    conn: sqlite3.Connection, client_id: int, field: str, value: str
) -> None:
    assert field in CLIENT_FIELDS
    conn.execute(
        f"UPDATE clients SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (value, client_id),
    )


def get_client(conn: sqlite3.Connection, client_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()


def delete_client(conn: sqlite3.Connection, client_id: int) -> None:
    conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))  # cascades


# --------------------------------------------------------------------------
# Treatment / product records (identical shape, one code path)
# --------------------------------------------------------------------------

RECORD_COLS = {
    "treatment_records": ("treatment_date", "treatment_notes"),
    "product_records": ("product_date", "product_text"),
}


def records(conn: sqlite3.Connection, table: str, client_id: int) -> list[sqlite3.Row]:
    date_col, _ = RECORD_COLS[table]
    return conn.execute(
        f"SELECT * FROM {table} WHERE client_id = ? ORDER BY {date_col} DESC, id DESC",
        (client_id,),
    ).fetchall()


def record_exists(
    conn: sqlite3.Connection, table: str, client_id: int, date: str
) -> bool:
    date_col, _ = RECORD_COLS[table]
    return (
        conn.execute(
            f"SELECT 1 FROM {table} WHERE client_id = ? AND {date_col} = ?",
            (client_id, date),
        ).fetchone()
        is not None
    )


def save_record(
    conn: sqlite3.Connection,
    table: str,
    client_id: int,
    date: str,
    text: str,
    record_id: int | None = None,
) -> None:
    date_col, text_col = RECORD_COLS[table]
    if record_id is None:
        conn.execute(
            f"INSERT INTO {table} (client_id, {date_col}, {text_col}) VALUES (?, ?, ?)",
            (client_id, date, text),
        )
    else:
        conn.execute(
            f"UPDATE {table} SET {date_col} = ?, {text_col} = ?, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (date, text, record_id),
        )


def delete_record(conn: sqlite3.Connection, table: str, record_id: int) -> None:
    conn.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))


# --------------------------------------------------------------------------
# Inventory
# --------------------------------------------------------------------------


def search_inventory(conn: sqlite3.Connection, text: str = "") -> list[sqlite3.Row]:
    rows = conn.execute(
        "SELECT * FROM inventory ORDER BY name COLLATE NOCASE"
    ).fetchall()
    needle = text.casefold()
    return [r for r in rows if needle in r["name"].casefold()] if text else rows


def save_inventory(
    conn: sqlite3.Connection,
    name: str,
    description: str,
    capacity: float,
    unit: str,
    item_id: int | None = None,
) -> None:
    if item_id is None:
        conn.execute(
            "INSERT INTO inventory (name, description, capacity, unit) VALUES (?, ?, ?, ?)",
            (name, description, capacity, unit),
        )
    else:
        conn.execute(
            "UPDATE inventory SET name = ?, description = ?, capacity = ?, unit = ?, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (name, description, capacity, unit, item_id),
        )


def delete_inventory(conn: sqlite3.Connection, item_id: int) -> None:
    conn.execute("DELETE FROM inventory WHERE id = ?", (item_id,))


# --------------------------------------------------------------------------
# Audit log
# --------------------------------------------------------------------------


def audit_page(
    conn: sqlite3.Connection, page: int, per_page: int = 50
) -> tuple[list[dict], int]:
    """One page of audit entries (newest first) with client names resolved."""
    total = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    rows = conn.execute(
        "SELECT a.*, c.first_name || ' ' || c.last_name AS client_name "
        "FROM audit_log a LEFT JOIN clients c ON c.id = a.client_id "
        "ORDER BY a.id DESC LIMIT ? OFFSET ?",
        (per_page, page * per_page),
    ).fetchall()
    entries = []
    for r in rows:
        e = dict(r)
        if e["field_name"] is None and e["action"] == "UPDATE":
            try:  # trigger-written rows: whole-row JSON → show only changed fields
                old, new = json.loads(e["old_value"]), json.loads(e["new_value"])
                e["changes"] = [
                    (k, old[k], new[k]) for k in old if old[k] != new.get(k)
                ]
            except (ValueError, TypeError):  # legacy free-text rows
                e["changes"] = None
        else:
            e["changes"] = None
        entries.append(e)
    return entries, total


# --------------------------------------------------------------------------
# CSV export (utf-8-sig so Excel opens umlauts correctly)
# --------------------------------------------------------------------------


def export_mail_merge(conn: sqlite3.Connection, path: Path) -> int:
    rows = conn.execute(
        "SELECT c.first_name, c.last_name, c.address, c.email FROM clients c "
        "ORDER BY (SELECT MAX(treatment_date) FROM treatment_records WHERE client_id = c.id) DESC, "
        "c.last_name COLLATE NOCASE, c.first_name COLLATE NOCASE"
    ).fetchall()
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["first_name", "last_name", "address", "email"])
        w.writerows([tuple(r) for r in rows])
    return len(rows)


def cleanup_audit(conn: sqlite3.Connection, days: int) -> int:
    """Privacy: delete audit entries older than `days`. With secure_delete on,
    the freed pages are scrubbed, so the data is really gone."""
    cur = conn.execute(
        "DELETE FROM audit_log WHERE created_at < datetime('now', ?)",
        (f"-{days} days",),
    )
    return cur.rowcount


def _csv_rows(path: Path) -> list[dict]:
    if not path.exists():  # missing file = nothing to import
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        try:  # German Excel writes semicolons
            dialect = csv.Sniffer().sniff(f.read(4096), delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        f.seek(0)
        return list(csv.DictReader(f, dialect=dialect))


def import_csv_dir(conn: sqlite3.Connection, directory: Path) -> int:
    """Import the CSVs that export_all writes (same filenames and columns).
    Client ids are remapped on the fly; record rows may reference imported
    ids or ids already in the DB (the FK rejects anything else). Any bad row
    aborts the whole import — all or nothing."""
    imported = 0
    id_map: dict[str, int] = {}
    conn.execute("BEGIN")
    try:
        for row in _csv_rows(directory / "clients.csv"):
            fields = {f: (row.get(f) or "").strip() or None for f in CLIENT_FIELDS}
            if not fields["first_name"] or not fields["last_name"]:
                raise ValueError(f"clients.csv: first_name/last_name required: {row}")
            if fields["date_of_birth"]:
                datetime.strptime(fields["date_of_birth"], "%Y-%m-%d")
            new_id = save_client(conn, fields)
            if (row.get("id") or "").strip():
                id_map[row["id"].strip()] = new_id
            imported += 1
        for table in ("treatment_records", "product_records"):
            date_col, text_col = RECORD_COLS[table]
            for row in _csv_rows(directory / f"{table}.csv"):
                raw = (row.get("client_id") or "").strip()
                day = (row.get(date_col) or "").strip()
                text = (row.get(text_col) or "").strip()
                datetime.strptime(day, "%Y-%m-%d")
                if not text:
                    raise ValueError(f"{table}.csv: {text_col} required: {row}")
                save_record(conn, table, id_map.get(raw, raw and int(raw)), day, text)
                imported += 1
        for row in _csv_rows(directory / "inventory.csv"):
            name = (row.get("name") or "").strip()
            capacity = float(row.get("capacity") or 0)
            if not name or capacity <= 0:
                raise ValueError(
                    f"inventory.csv: name and capacity > 0 required: {row}"
                )
            save_inventory(
                conn,
                name,
                (row.get("description") or "").strip() or None,
                capacity,
                (row.get("unit") or "").strip(),
            )
            imported += 1
        conn.execute("COMMIT")
    except BaseException:  # also rolls back on KeyboardInterrupt
        conn.execute("ROLLBACK")
        raise
    return imported


def export_all(conn: sqlite3.Connection, directory: Path) -> list[Path]:
    written = []
    for table in (
        "clients",
        "treatment_records",
        "product_records",
        "inventory",
        "audit_log",
    ):
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        path = directory / f"{table}.csv"
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(
                rows[0].keys()
                if rows
                else [c[1] for c in conn.execute(f"PRAGMA table_info({table})")]
            )
            w.writerows([tuple(r) for r in rows])
        written.append(path)
    return written


# --------------------------------------------------------------------------
# Backups: zip of a consistent snapshot, same naming scheme as the old app
# --------------------------------------------------------------------------


def backups_dir() -> Path:
    d = data_dir() / "backups"
    d.mkdir(parents=True, exist_ok=True)
    os.chmod(d, 0o700)
    return d


def create_backup(conn: sqlite3.Connection, source: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp = backups_dir() / f".snapshot_{stamp}.db"
    snap = sqlite3.connect(tmp)
    with snap:
        conn.backup(snap)  # consistent even mid-write, unlike a file copy
    snap.close()
    target = backups_dir() / f"cosmetics_records_backup_v{VERSION}_{stamp}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(tmp, source.name)
    tmp.unlink()
    os.chmod(target, 0o600)
    return target


def list_backups() -> list[Path]:
    return sorted(
        backups_dir().glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True
    )


def cleanup_backups(keep: int) -> None:
    for old in list_backups()[keep:]:
        old.unlink()


def restore_backup(backup: Path, target: Path) -> None:
    """Extract the .db from a backup zip over the live DB. Caller must have
    closed the connection and should back up beforehand."""
    backup = backup.resolve()
    if backup.parent != backups_dir().resolve():  # no paths from outside the backup dir
        raise ValueError("Backup liegt nicht im Backup-Ordner")
    with zipfile.ZipFile(backup) as z:
        names = [n for n in z.namelist() if n.endswith(".db") and "/" not in n]
        if len(names) != 1 or z.testzip() is not None:
            raise ValueError("Ungültige Backup-Datei")
        tmp = target.with_suffix(".restore_tmp")
        tmp.write_bytes(z.read(names[0]))
    for wal in (
        target.with_name(target.name + "-wal"),
        target.with_name(target.name + "-shm"),
    ):
        wal.unlink(missing_ok=True)
    shutil.move(tmp, target)
    os.chmod(target, 0o600)


def auto_backup_if_due(conn: sqlite3.Connection, cfg: dict, source: Path) -> bool:
    if not cfg.get("auto_backup", True):
        return False
    last = cfg.get("last_backup_time")
    try:
        elapsed = (datetime.now() - datetime.fromisoformat(last)).total_seconds() / 60
    except (TypeError, ValueError):
        elapsed = float("inf")
    if elapsed < cfg.get("backup_interval_minutes", 120):
        return False
    create_backup(conn, source)
    cfg["last_backup_time"] = datetime.now().isoformat()
    save_config(cfg)
    cleanup_backups(cfg.get("backup_retention_count", 25))
    return True
