"""End-to-end check of the data layer: schema, audit triggers, backup/restore."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from cosmetics_records import db, i18n  # noqa: E402


def test_translations_cover_all_ui_strings():
    """Every tr() literal and every TABLE_/FIELD_LABELS value has a German entry."""
    app_py = Path(__file__).parent.parent / "src" / "cosmetics_records" / "app.py"
    keys = set()
    for node in ast.walk(ast.parse(app_py.read_text("utf-8"))):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "tr"
            and node.args
        ):
            arg = node.args[0]
            if isinstance(arg, ast.Constant):
                keys.add(arg.value)
            elif isinstance(arg, ast.Subscript) and isinstance(arg.value, ast.Dict):
                keys |= {
                    v.value for v in arg.value.values if isinstance(v, ast.Constant)
                }
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in ("TABLE_LABELS", "FIELD_LABELS")
            for t in node.targets
        ):
            keys |= {v.value for v in node.value.values if isinstance(v, ast.Constant)}
    missing = {k for k in keys if isinstance(k, str)} - set(i18n.DE)
    assert not missing, f"untranslated: {sorted(missing)}"
    i18n.set_language("de")
    assert i18n.tr("Clients") == "Kunden"
    i18n.set_language("en")
    assert i18n.tr("Clients") == "Clients"


def test_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "data_dir", lambda: tmp_path)
    path = tmp_path / "test.db"
    conn = db.connect(path)

    # client CRUD + audit triggers
    cid = db.save_client(
        conn,
        {
            "first_name": "Anna",
            "last_name": "Müller",
            "email": "anna@example.com",
            "tags": "VIP",
        },
    )
    db.save_client(
        conn,
        {
            "first_name": "Anna",
            "last_name": "Schmidt",
            "email": "anna@example.com",
            "tags": "VIP",
        },
        cid,
    )
    db.update_client_field(conn, cid, "notes", "empfindliche Haut")

    entries, total = db.audit_page(conn, 0)
    assert total == 3
    assert entries[2]["action"] == "CREATE"
    # trigger UPDATE rows carry a display-ready field diff
    assert ("last_name", "Müller", "Schmidt") in entries[1]["changes"]
    assert entries[0]["client_name"] == "Anna Schmidt"

    # no-op update writes no audit row
    db.update_client_field(conn, cid, "notes", "empfindliche Haut")
    assert db.audit_page(conn, 0)[1] == 3

    # umlaut-insensitive search
    assert len(db.search_clients(conn, "schMIDT")) == 1
    assert len(db.search_clients(conn, "vip")) == 1
    assert not db.search_clients(conn, "nobody")

    # records + duplicate check + cascade delete audited
    db.save_record(conn, "treatment_records", cid, "2026-07-01", "Peeling")
    assert db.record_exists(conn, "treatment_records", cid, "2026-07-01")
    db.save_inventory(conn, "Serum", None, 30.5, "ml")

    # exports
    assert db.export_mail_merge(conn, tmp_path / "mail.csv") == 1
    assert len(db.export_all(conn, tmp_path)) == 5
    assert "Schmidt" in (tmp_path / "clients.csv").read_text("utf-8-sig")

    # backup, destroy, restore
    backup = db.create_backup(conn, path)
    assert backup.exists() and db.list_backups() == [backup]
    db.delete_client(conn, cid)
    assert not db.search_clients(conn)
    assert any(
        e["action"] == "DELETE" and e["table_name"] == "treatment_records"
        for e in db.audit_page(conn, 0)[0]
    )  # cascade was audited
    conn.close()
    db.restore_backup(backup, path)
    conn = db.connect(path)
    assert db.search_clients(conn)[0]["last_name"] == "Schmidt"

    # restore refuses paths outside the backup dir
    outside = tmp_path.parent / "evil.zip"
    outside.write_bytes(backup.read_bytes())
    try:
        db.restore_backup(outside, path)
        raise AssertionError("outside path accepted")
    except ValueError:
        pass
    conn.close()


def test_config_and_permissions(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "data_dir", lambda: tmp_path)
    db.save_config({"auto_backup": True, "fremder_schluessel": 1})
    assert db.load_config()["fremder_schluessel"] == 1  # unknown keys survive
    assert (tmp_path / "config.json").stat().st_mode & 0o777 == 0o600
    conn = db.connect(db.db_path({}))
    assert db.db_path({}).stat().st_mode & 0o777 == 0o600
    assert not db.auto_backup_if_due(conn, {"auto_backup": False}, db.db_path({}))
    cfg = {}
    assert db.auto_backup_if_due(conn, cfg, db.db_path({}))  # never backed up → due
    assert not db.auto_backup_if_due(conn, cfg, db.db_path({}))  # just ran → not due
    conn.close()
