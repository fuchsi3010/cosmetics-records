"""Cosmetics Records — Kundenkartei für ein Ein-Personen-Kosmetikstudio.

Single-window PyQt6 app on top of db.py. German UI (the salon's language).
Run: python src/cosmetics_records/app.py
"""

from __future__ import annotations

import html
import json
import re
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path

from PyQt6.QtCore import QDate, Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

sys.path.insert(0, str(Path(__file__).parent.parent))
from cosmetics_records import db  # noqa: E402

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

TABLE_LABELS = {
    "clients": "Kunde",
    "treatment_records": "Behandlung",
    "product_records": "Produktverkauf",
    "inventory": "Inventar",
    "inventory_items": "Inventar",  # legacy table name in old audit rows
}
FIELD_LABELS = {
    "first_name": "Vorname",
    "last_name": "Nachname",
    "email": "E-Mail",
    "phone": "Telefon",
    "address": "Adresse",
    "date_of_birth": "Geburtsdatum",
    "allergies": "Allergien",
    "tags": "Tags",
    "planned_treatment": "Geplante Behandlung",
    "notes": "Notizen",
    "client_id": "Kunden-Nr.",
    "treatment_date": "Datum",
    "treatment_notes": "Behandlungsnotizen",
    "product_date": "Datum",
    "product_text": "Produkte",
    "name": "Name",
    "description": "Beschreibung",
    "capacity": "Inhalt",
    "unit": "Einheit",
}


def fmt_date(iso: str | None) -> str:
    d = QDate.fromString(iso or "", Qt.DateFormat.ISODate)
    return d.toString("dd.MM.yyyy") if d.isValid() else (iso or "")


def parse_dob(text: str) -> str | None:
    """'31.12.1980' or '1980-12-31' → ISO; empty → None; invalid → ValueError."""
    text = text.strip()
    if not text:
        return None
    for pattern in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            pass
    raise ValueError(text)


def confirm(parent: QWidget, text: str) -> bool:
    return (
        QMessageBox.question(
            parent,
            "Bestätigen",
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        == QMessageBox.StandardButton.Yes
    )


class SaveOnBlur(QPlainTextEdit):
    """Speichert beim Verlassen des Feldes — ein Audit-Eintrag pro Sitzung."""

    def __init__(self, on_save):
        super().__init__()
        self._on_save = on_save
        self._loaded = ""

    def load(self, text: str | None) -> None:
        self._loaded = text or ""
        self.setPlainText(self._loaded)

    def focusOutEvent(self, event) -> None:
        if self.toPlainText() != self._loaded:
            self._loaded = self.toPlainText()
            self._on_save(self._loaded)
        super().focusOutEvent(event)


# --------------------------------------------------------------------------
# Dialogs
# --------------------------------------------------------------------------


class ClientDialog(QDialog):
    def __init__(self, win: "MainWindow", client_id: int | None = None):
        super().__init__(win)
        self.win, self.client_id, self.deleted = win, client_id, False
        self.setWindowTitle("Kunde bearbeiten" if client_id else "Neuer Kunde")
        self.setMinimumWidth(420)

        self.first = QLineEdit()
        self.last = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.address = QPlainTextEdit()
        self.address.setFixedHeight(60)
        self.dob = QLineEdit(placeholderText="TT.MM.JJJJ")
        self.allergies = QPlainTextEdit()
        self.allergies.setFixedHeight(60)
        self.tags = QLineEdit(placeholderText="z. B. VIP, empfindliche Haut")

        form = QFormLayout(self)
        form.addRow("Vorname*", self.first)
        form.addRow("Nachname*", self.last)
        form.addRow("E-Mail", self.email)
        form.addRow("Telefon", self.phone)
        form.addRow("Adresse", self.address)
        form.addRow("Geburtsdatum", self.dob)
        form.addRow("Allergien", self.allergies)
        form.addRow("Tags", self.tags)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if client_id:
            delete = buttons.addButton(
                "Löschen…", QDialogButtonBox.ButtonRole.DestructiveRole
            )
            delete.clicked.connect(self._delete)
            row = db.get_client(win.conn, client_id)
            self.first.setText(row["first_name"])
            self.last.setText(row["last_name"])
            self.email.setText(row["email"] or "")
            self.phone.setText(row["phone"] or "")
            self.address.setPlainText(row["address"] or "")
            self.dob.setText(fmt_date(row["date_of_birth"]))
            self.allergies.setPlainText(row["allergies"] or "")
            self.tags.setText(row["tags"] or "")
        form.addRow(buttons)

    def _delete(self) -> None:
        if confirm(self, "Kunde und gesamte Historie unwiderruflich löschen?"):
            db.delete_client(self.win.conn, self.client_id)
            self.deleted = True
            QDialog.accept(self)

    def accept(self) -> None:
        if not self.first.text().strip() or not self.last.text().strip():
            return QMessageBox.warning(
                self, "Fehler", "Vor- und Nachname sind Pflichtfelder."
            )
        email = self.email.text().strip()
        if email and not EMAIL_RE.match(email):
            return QMessageBox.warning(self, "Fehler", "Ungültige E-Mail-Adresse.")
        try:
            dob = parse_dob(self.dob.text())
        except ValueError:
            return QMessageBox.warning(
                self, "Fehler", "Geburtsdatum bitte als TT.MM.JJJJ angeben."
            )
        fields = {
            "first_name": self.first.text().strip(),
            "last_name": self.last.text().strip(),
            "email": email or None,
            "phone": self.phone.text().strip() or None,
            "address": self.address.toPlainText().strip() or None,
            "date_of_birth": dob,
            "allergies": self.allergies.toPlainText().strip() or None,
            "tags": self.tags.text().strip() or None,
        }
        if (
            self.client_id
        ):  # planned_treatment/notes werden in der Detailansicht gepflegt
            row = db.get_client(self.win.conn, self.client_id)
            fields["planned_treatment"] = row["planned_treatment"]
            fields["notes"] = row["notes"]
        self.client_id = db.save_client(self.win.conn, fields, self.client_id)
        super().accept()


class RecordDialog(QDialog):
    """Behandlung oder Produktverkauf anlegen/bearbeiten."""

    def __init__(
        self, win: "MainWindow", table: str, client_id: int, record: dict | None = None
    ):
        super().__init__(win)
        self.win, self.table, self.client_id = win, table, client_id
        self.record_id = record["id"] if record else None
        is_product = table == "product_records"
        self.setWindowTitle("Produktverkauf" if is_product else "Behandlung")
        self.setMinimumWidth(420)
        date_col, text_col = db.RECORD_COLS[table]

        self.date = QDateEdit(calendarPopup=True)
        self.date.setDisplayFormat("dd.MM.yyyy")
        self.date.setMaximumDate(QDate.currentDate())
        self.date.setDate(
            QDate.fromString(record[date_col], Qt.DateFormat.ISODate)
            if record
            else QDate.currentDate()
        )
        self.text = QPlainTextEdit(record[text_col] if record else "")

        form = QFormLayout(self)
        form.addRow("Datum", self.date)
        if is_product:  # Produktzeile: Menge + Name (mit Vorschlägen aus dem Inventar)
            names = [
                f"{r['name']} ({r['capacity']:g} {r['unit']})"
                for r in db.search_inventory(win.conn)
            ]
            self.qty = QSpinBox(minimum=1, maximum=99, suffix="x")
            self.product = QLineEdit()
            completer = QCompleter(names)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.product.setCompleter(completer)
            add = QPushButton("Hinzufügen")
            add.clicked.connect(self._add_product_line)
            self.product.returnPressed.connect(self._add_product_line)
            row = QHBoxLayout()
            row.addWidget(self.qty)
            row.addWidget(self.product, 1)
            row.addWidget(add)
            form.addRow("Produkt", row)
        form.addRow("Produkte" if is_product else "Notizen", self.text)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if self.record_id:
            delete = buttons.addButton(
                "Löschen…", QDialogButtonBox.ButtonRole.DestructiveRole
            )
            delete.clicked.connect(self._delete)
        form.addRow(buttons)

    def _add_product_line(self) -> None:
        name = self.product.text().strip()
        if name:
            self.text.appendPlainText(f"{self.qty.value()}x {name}")
            self.product.clear()

    def _delete(self) -> None:
        if confirm(self, "Eintrag unwiderruflich löschen?"):
            db.delete_record(self.win.conn, self.table, self.record_id)
            QDialog.accept(self)

    def accept(self) -> None:
        text = self.text.toPlainText().strip()
        if not text:
            return QMessageBox.warning(self, "Fehler", "Bitte Text eingeben.")
        iso = self.date.date().toString(Qt.DateFormat.ISODate)
        if (
            self.record_id is None
            and db.record_exists(self.win.conn, self.table, self.client_id, iso)
            and not confirm(
                self,
                "Für dieses Datum existiert bereits ein Eintrag.\n"
                "Trotzdem speichern?",
            )
        ):
            return
        db.save_record(
            self.win.conn, self.table, self.client_id, iso, text, self.record_id
        )
        super().accept()


class InventoryDialog(QDialog):
    def __init__(self, win: "MainWindow", item: dict | None = None):
        super().__init__(win)
        self.win = win
        self.item_id = item["id"] if item else None
        self.setWindowTitle("Artikel bearbeiten" if item else "Neuer Artikel")
        self.setMinimumWidth(380)

        self.name = QLineEdit(item["name"] if item else "")
        self.description = QPlainTextEdit((item["description"] or "") if item else "")
        self.description.setFixedHeight(60)
        self.capacity = QDoubleSpinBox(minimum=0.1, maximum=999999, decimals=1)
        self.capacity.setValue(item["capacity"] if item else 30)
        self.unit = QComboBox()
        self.unit.addItems(["ml", "g", "Pc."])  # von der DB per CHECK erzwungen
        if item:
            self.unit.setCurrentText(item["unit"])

        form = QFormLayout(self)
        form.addRow("Name*", self.name)
        form.addRow("Beschreibung", self.description)
        form.addRow("Inhalt*", self.capacity)
        form.addRow("Einheit*", self.unit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if self.item_id:
            delete = buttons.addButton(
                "Löschen…", QDialogButtonBox.ButtonRole.DestructiveRole
            )
            delete.clicked.connect(self._delete)
        form.addRow(buttons)

    def _delete(self) -> None:
        if confirm(self, "Artikel unwiderruflich löschen?"):
            db.delete_inventory(self.win.conn, self.item_id)
            QDialog.accept(self)

    def accept(self) -> None:
        name = self.name.text().strip()
        if not name:
            return QMessageBox.warning(self, "Fehler", "Name ist ein Pflichtfeld.")
        db.save_inventory(
            self.win.conn,
            name,
            self.description.toPlainText().strip() or None,
            self.capacity.value(),
            self.unit.currentText(),
            self.item_id,
        )
        super().accept()


# --------------------------------------------------------------------------
# Kunden-Tab: Liste links, Detail rechts
# --------------------------------------------------------------------------


class ClientDetail(QWidget):
    def __init__(self, win: "MainWindow", on_change):
        super().__init__()
        self.win, self.on_change, self.client_id = win, on_change, None

        self.stack = QStackedWidget()
        placeholder = QLabel("Kundin/Kunde auswählen")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(placeholder)

        page = QWidget()
        self.header = QLabel()
        self.header.setFont(QFont(self.font().family(), 15, QFont.Weight.Bold))
        self.allergies = QLabel()
        self.allergies.setStyleSheet("color: #cc2222; font-weight: bold;")
        self.allergies.setWordWrap(True)
        edit = QPushButton("Bearbeiten…")
        edit.clicked.connect(self._edit_client)

        self.planned = SaveOnBlur(lambda t: self._save_field("planned_treatment", t))
        self.notes = SaveOnBlur(lambda t: self._save_field("notes", t))
        self.treatments = QListWidget(wordWrap=True)
        self.products = QListWidget(wordWrap=True)
        for lst, table in (
            (self.treatments, "treatment_records"),
            (self.products, "product_records"),
        ):
            lst.setToolTip("Doppelklick zum Bearbeiten")
            lst.itemDoubleClicked.connect(
                lambda item, t=table: self._edit_record(t, item)
            )

        def titled(title: str, widget: QWidget, button=None) -> QWidget:
            box = QWidget()
            lay = QVBoxLayout(box)
            lay.setContentsMargins(0, 0, 0, 0)
            head = QHBoxLayout()
            label = QLabel(title)
            label.setFont(QFont(self.font().family(), 11, QFont.Weight.Bold))
            head.addWidget(label)
            head.addStretch()
            if button:
                head.addWidget(button)
            lay.addLayout(head)
            lay.addWidget(widget)
            return box

        add_treatment = QPushButton("+ Behandlung")
        add_treatment.clicked.connect(lambda: self._add_record("treatment_records"))
        add_product = QPushButton("+ Verkauf")
        add_product.clicked.connect(lambda: self._add_record("product_records"))

        grid = QGridLayout()
        grid.addWidget(titled("Geplante Behandlung", self.planned), 0, 0)
        grid.addWidget(titled("Notizen", self.notes), 0, 1)
        grid.addWidget(titled("Behandlungen", self.treatments, add_treatment), 1, 0)
        grid.addWidget(titled("Produkte", self.products, add_product), 1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 2)

        lay = QVBoxLayout(page)
        top = QHBoxLayout()
        top.addWidget(self.header)
        top.addStretch()
        top.addWidget(edit)
        lay.addLayout(top)
        lay.addWidget(self.allergies)
        lay.addLayout(grid)
        self.stack.addWidget(page)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.stack)

    def load(self, client_id: int | None) -> None:
        self.client_id = client_id
        row = db.get_client(self.win.conn, client_id) if client_id else None
        self.stack.setCurrentIndex(1 if row else 0)
        if not row:
            return
        age = ""
        if row["date_of_birth"]:
            born = date.fromisoformat(row["date_of_birth"])
            today = date.today()
            years = (
                today.year
                - born.year
                - ((today.month, today.day) < (born.month, born.day))
            )
            age = f" ({years})"
        self.header.setText(f"{row['first_name']} {row['last_name']}{age}")
        self.allergies.setText(
            f"Allergien: {row['allergies']}" if row["allergies"] else ""
        )
        self.allergies.setVisible(bool(row["allergies"]))
        self.planned.load(row["planned_treatment"])
        self.notes.load(row["notes"])
        for lst, table in (
            (self.treatments, "treatment_records"),
            (self.products, "product_records"),
        ):
            date_col, text_col = db.RECORD_COLS[table]
            lst.clear()
            for r in db.records(self.win.conn, table, self.client_id):
                item = QListWidgetItem(f"{fmt_date(r[date_col])}\n{r[text_col]}")
                item.setData(Qt.ItemDataRole.UserRole, dict(r))
                lst.addItem(item)

    def _save_field(self, field: str, value: str) -> None:
        db.update_client_field(
            self.win.conn, self.client_id, field, value.strip() or None
        )
        self.win.statusBar().showMessage("Gespeichert ✓", 2000)

    def _edit_client(self) -> None:
        dialog = ClientDialog(self.win, self.client_id)
        if dialog.exec():
            self.load(None if dialog.deleted else self.client_id)
            self.on_change()

    def _add_record(self, table: str) -> None:
        if RecordDialog(self.win, table, self.client_id).exec():
            self.load(self.client_id)

    def _edit_record(self, table: str, item: QListWidgetItem) -> None:
        record = item.data(Qt.ItemDataRole.UserRole)
        if RecordDialog(self.win, table, self.client_id, record).exec():
            self.load(self.client_id)


class ClientsTab(QWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        self.search = QLineEdit(placeholderText="Suchen (Name oder Tag)…")
        self.search.textChanged.connect(self.refresh)
        self.list = QListWidget()
        self.list.currentItemChanged.connect(
            lambda item, _: self.detail.load(
                item.data(Qt.ItemDataRole.UserRole) if item else None
            )
        )
        add = QPushButton("+ Neuer Kunde")
        add.clicked.connect(self._add)
        self.detail = ClientDetail(win, on_change=self.refresh)

        left = QWidget()
        lay = QVBoxLayout(left)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.search)
        lay.addWidget(self.list)
        lay.addWidget(add)
        split = QSplitter()
        split.addWidget(left)
        split.addWidget(self.detail)
        split.setStretchFactor(1, 1)
        split.setSizes([280, 720])
        outer = QHBoxLayout(self)
        outer.addWidget(split)
        self.refresh()

    def refresh(self) -> None:
        selected = self.detail.client_id
        self.list.blockSignals(True)
        self.list.clear()
        for r in db.search_clients(self.win.conn, self.search.text()):
            item = QListWidgetItem(f"{r['last_name']}, {r['first_name']}")
            item.setData(Qt.ItemDataRole.UserRole, r["id"])
            if r["tags"]:
                item.setToolTip(r["tags"])
            self.list.addItem(item)
            if r["id"] == selected:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        if self.list.currentItem() is None:
            self.detail.load(None)

    def _add(self) -> None:
        dialog = ClientDialog(self.win)
        if dialog.exec():
            self.detail.client_id = dialog.client_id
            self.refresh()


# --------------------------------------------------------------------------
# Inventar-Tab
# --------------------------------------------------------------------------


class InventoryTab(QWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        self.search = QLineEdit(placeholderText="Artikel suchen…")
        self.search.textChanged.connect(self.refresh)
        self.list = QListWidget()
        self.list.setToolTip("Doppelklick zum Bearbeiten")
        self.list.itemDoubleClicked.connect(self._edit)
        add = QPushButton("+ Neuer Artikel")
        add.clicked.connect(self._add)

        lay = QVBoxLayout(self)
        lay.addWidget(self.search)
        lay.addWidget(self.list)
        lay.addWidget(add)
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for r in db.search_inventory(self.win.conn, self.search.text()):
            text = f"{r['name']} ({r['capacity']:g} {r['unit']})"
            if r["description"]:
                text += f" — {r['description'][:80]}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, dict(r))
            self.list.addItem(item)

    def _add(self) -> None:
        if InventoryDialog(self.win).exec():
            self.refresh()

    def _edit(self, item: QListWidgetItem) -> None:
        if InventoryDialog(self.win, item.data(Qt.ItemDataRole.UserRole)).exec():
            self.refresh()


# --------------------------------------------------------------------------
# Protokoll-Tab (Audit-Log)
# --------------------------------------------------------------------------


class AuditTab(QWidget):
    PER_PAGE = 50

    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win, self.page = win, 0
        self.view = QTextBrowser()
        self.prev = QPushButton("← Neuere")
        self.next = QPushButton("Ältere →")
        self.label = QLabel()
        self.prev.clicked.connect(lambda: self._go(-1))
        self.next.clicked.connect(lambda: self._go(1))

        nav = QHBoxLayout()
        nav.addWidget(self.prev)
        nav.addWidget(self.label)
        nav.addStretch()
        nav.addWidget(self.next)
        lay = QVBoxLayout(self)
        lay.addWidget(self.view)
        lay.addLayout(nav)

    def showEvent(self, event) -> None:
        self.refresh()
        super().showEvent(event)

    def _go(self, step: int) -> None:
        self.page = max(0, self.page + step)
        self.refresh()

    def refresh(self) -> None:
        entries, total = db.audit_page(self.win.conn, self.page, self.PER_PAGE)
        pages = max(1, -(-total // self.PER_PAGE))
        self.page = min(self.page, pages - 1)
        self.label.setText(f"Seite {self.page + 1} von {pages} ({total} Einträge)")
        self.prev.setEnabled(self.page > 0)
        self.next.setEnabled(self.page < pages - 1)
        self.view.setHtml(
            "".join(self._render(e) for e in entries) or "<p>Keine Einträge.</p>"
        )

    @staticmethod
    def _field_line(field: str, old, new) -> str:
        label = html.escape(FIELD_LABELS.get(field, field))
        return (
            f"<div><b>{label}:</b> <s>{html.escape(str(old or '—'))}</s> → "
            f"<b>{html.escape(str(new or '—'))}</b></div>"
        )

    def _render(self, e: dict) -> str:
        verb = {"CREATE": "erstellt", "UPDATE": "geändert", "DELETE": "gelöscht"}[
            e["action"]
        ]
        table = TABLE_LABELS.get(e["table_name"], e["table_name"])
        who = f" — {html.escape(e['client_name'])}" if e["client_name"] else ""
        body = ""
        if e["changes"]:  # Trigger-Zeilen: JSON-Diff der geänderten Felder
            body = "".join(
                self._field_line(f, old, new) for f, old, new in e["changes"]
            )
        elif e["field_name"]:  # Alt-Zeilen der Vorgängerversion: ein Feld pro Zeile
            body = self._field_line(e["field_name"], e["old_value"], e["new_value"])
        elif e["action"] in ("CREATE", "DELETE"):
            snapshot = e["new_value"] if e["action"] == "CREATE" else e["old_value"]
            try:
                fields = json.loads(snapshot or "")
                body = "".join(
                    f"<div><b>{html.escape(FIELD_LABELS.get(f, f))}:</b> "
                    f"{html.escape(str(v))}</div>"
                    for f, v in fields.items()
                    if v not in (None, "")
                )
            except ValueError:
                body = html.escape(snapshot or "")
        return (
            f"<p><span style='opacity:.6'>{html.escape(str(e['created_at']))}</span> "
            f"&nbsp; <b>{table} {verb}</b>{who}<br>{body}</p><hr>"
        )


# --------------------------------------------------------------------------
# Einstellungen-Tab
# --------------------------------------------------------------------------


class SettingsTab(QWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        cfg = win.cfg

        self.auto = QCheckBox("Automatisches Backup beim Start")
        self.auto.setChecked(cfg.get("auto_backup", True))
        self.interval = QSpinBox(minimum=1, maximum=1440, suffix=" Min.")
        self.interval.setValue(cfg.get("backup_interval_minutes", 120))
        self.keep = QSpinBox(minimum=1, maximum=100)
        self.keep.setValue(cfg.get("backup_retention_count", 25))
        for widget, key in (
            (self.auto, "auto_backup"),
            (self.interval, "backup_interval_minutes"),
            (self.keep, "backup_retention_count"),
        ):
            signal = (
                widget.toggled if isinstance(widget, QCheckBox) else widget.valueChanged
            )
            signal.connect(lambda value, k=key: self._set(k, value))

        backup_now = QPushButton("Jetzt sichern")
        backup_now.clicked.connect(self._backup_now)
        restore = QPushButton("Backup wiederherstellen…")
        restore.clicked.connect(self._restore)
        open_dir = QPushButton("Backup-Ordner öffnen")
        open_dir.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(db.backups_dir())))
        )

        backup_box = QGroupBox("Backup")
        form = QFormLayout(backup_box)
        form.addRow(self.auto)
        form.addRow("Intervall", self.interval)
        form.addRow("Anzahl behalten", self.keep)
        row = QHBoxLayout()
        row.addWidget(backup_now)
        row.addWidget(restore)
        row.addWidget(open_dir)
        form.addRow(row)

        mail_merge = QPushButton("Serienbrief-Export (CSV)…")
        mail_merge.clicked.connect(self._mail_merge)
        full_export = QPushButton("Alle Daten exportieren (CSV)…")
        full_export.clicked.connect(self._export_all)
        export_box = QGroupBox("Export")
        export_lay = QHBoxLayout(export_box)
        export_lay.addWidget(mail_merge)
        export_lay.addWidget(full_export)

        info = QLabel(f"Datenbank: {win.path}\nVersion {db.VERSION}")
        info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        lay = QVBoxLayout(self)
        lay.addWidget(backup_box)
        lay.addWidget(export_box)
        lay.addWidget(info)
        lay.addStretch()

    def _set(self, key: str, value) -> None:
        self.win.cfg[key] = value
        db.save_config(self.win.cfg)

    def _backup_now(self) -> None:
        path = db.create_backup(self.win.conn, self.win.path)
        db.cleanup_backups(self.keep.value())
        self.win.cfg["last_backup_time"] = datetime.now().isoformat()
        db.save_config(self.win.cfg)
        QMessageBox.information(self, "Backup", f"Backup erstellt:\n{path.name}")

    def _restore(self) -> None:
        backups = db.list_backups()
        if not backups:
            return QMessageBox.information(self, "Backup", "Keine Backups vorhanden.")
        name, ok = QInputDialog.getItem(
            self,
            "Backup wiederherstellen",
            "Backup auswählen:",
            [p.name for p in backups],
            0,
            False,
        )
        if not ok or not confirm(
            self,
            "Aktuelle Daten werden ersetzt.\n"
            "Vorher wird automatisch ein Sicherheits-Backup erstellt.\nFortfahren?",
        ):
            return
        try:
            self.win.restore(db.backups_dir() / name)
            QMessageBox.information(self, "Backup", "Backup wiederhergestellt.")
        except (ValueError, OSError, zipfile.BadZipFile) as err:
            QMessageBox.critical(
                self, "Fehler", f"Wiederherstellung fehlgeschlagen:\n{err}"
            )

    def _mail_merge(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Serienbrief-Export", "kunden_serienbrief.csv", "CSV (*.csv)"
        )
        if path:
            count = db.export_mail_merge(self.win.conn, Path(path))
            QMessageBox.information(self, "Export", f"{count} Kunden exportiert.")

    def _export_all(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Zielordner wählen")
        if directory:
            files = db.export_all(self.win.conn, Path(directory))
            QMessageBox.information(
                self, "Export", f"{len(files)} Dateien exportiert nach:\n{directory}"
            )


# --------------------------------------------------------------------------
# Hauptfenster
# --------------------------------------------------------------------------


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = db.load_config()
        self.path = db.db_path(self.cfg)
        self.conn = db.connect(self.path)

        self.setWindowTitle("Cosmetics Records")
        self.resize(1100, 700)
        self.clients = ClientsTab(self)
        self.inventory = InventoryTab(self)
        tabs = QTabWidget()
        tabs.addTab(self.clients, "Kunden")
        tabs.addTab(self.inventory, "Inventar")
        tabs.addTab(AuditTab(self), "Protokoll")
        tabs.addTab(SettingsTab(self), "Einstellungen")
        self.setCentralWidget(tabs)
        self.statusBar()

        # Backup nach dem ersten Anzeigen — der Start bleibt sofort bedienbar
        QTimer.singleShot(0, self._startup_backup)

    def _startup_backup(self) -> None:
        if db.auto_backup_if_due(self.conn, self.cfg, self.path):
            self.statusBar().showMessage("Automatisches Backup erstellt ✓", 4000)

    def restore(self, backup: Path) -> None:
        db.create_backup(self.conn, self.path)  # Sicherheitskopie des Ist-Stands
        self.conn.close()
        try:
            db.restore_backup(backup, self.path)
        finally:
            self.conn = db.connect(self.path)
        self.clients.refresh()
        self.inventory.refresh()

    def closeEvent(self, event) -> None:
        self.conn.close()
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Cosmetics Records")
    app.setStyle("Fusion")  # folgt ab Qt 6.5 dem hellen/dunklen Systemschema
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
