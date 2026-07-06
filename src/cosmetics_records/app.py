"""Cosmetics Records — client records app for a one-person cosmetics salon.

Single-window PyQt6 app on top of db.py. English/German UI (i18n.py),
1.x look reproduced in style.py. Run: python src/cosmetics_records/app.py
"""

from __future__ import annotations

import html
import json
import re
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path

from PyQt6.QtCore import QDate, QLocale, Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon
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
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

sys.path.insert(0, str(Path(__file__).parent.parent))
from cosmetics_records import db, i18n, style  # noqa: E402
from cosmetics_records.i18n import tr  # noqa: E402

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
ICON = Path(__file__).parent / "resources" / "icons" / "icon-256.png"

# English source labels; rendered through tr() at display time.
TABLE_LABELS = {
    "clients": "Client",
    "treatment_records": "Treatment",
    "product_records": "Product sale",
    "inventory": "Inventory",
    "inventory_items": "Inventory",  # legacy table name in old audit rows
}
FIELD_LABELS = {
    "first_name": "First name",
    "last_name": "Last name",
    "email": "Email",
    "phone": "Phone",
    "address": "Address",
    "date_of_birth": "Date of birth",
    "allergies": "Allergies",
    "tags": "Tags",
    "planned_treatment": "Planned treatment",
    "notes": "Notes",
    "client_id": "Client no.",
    "treatment_date": "Date",
    "treatment_notes": "Treatment notes",
    "product_date": "Date",
    "product_text": "Products",
    "name": "Name",
    "description": "Description",
    "capacity": "Capacity",
    "unit": "Unit",
}


def date_format() -> str:
    return "dd.MM.yyyy" if i18n.LANG == "de" else "yyyy-MM-dd"


def fmt_date(iso: str | None) -> str:
    d = QDate.fromString(iso or "", Qt.DateFormat.ISODate)
    return d.toString(date_format()) if d.isValid() else (iso or "")


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
            tr("Confirm"),
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        == QMessageBox.StandardButton.Yes
    )


class SaveOnBlur(QPlainTextEdit):
    """Saves when focus leaves the field — one audit entry per editing session."""

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
        self.setWindowTitle(tr("Edit Client") if client_id else tr("New Client"))
        self.setMinimumWidth(420)

        self.first = QLineEdit()
        self.last = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.address = QPlainTextEdit()
        self.address.setFixedHeight(60)
        self.dob = QLineEdit(placeholderText=tr("YYYY-MM-DD"))
        self.allergies = QPlainTextEdit()
        self.allergies.setFixedHeight(60)
        self.tags = QLineEdit(placeholderText=tr("e.g. VIP, sensitive skin"))

        form = QFormLayout(self)
        form.addRow(tr("First name*"), self.first)
        form.addRow(tr("Last name*"), self.last)
        form.addRow(tr("Email"), self.email)
        form.addRow(tr("Phone"), self.phone)
        form.addRow(tr("Address"), self.address)
        form.addRow(tr("Date of birth"), self.dob)
        form.addRow(tr("Allergies"), self.allergies)
        form.addRow(tr("Tags"), self.tags)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if client_id:
            delete = buttons.addButton(
                tr("Delete…"), QDialogButtonBox.ButtonRole.DestructiveRole
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
        if confirm(self, tr("Delete client and entire history permanently?")):
            db.delete_client(self.win.conn, self.client_id)
            self.deleted = True
            QDialog.accept(self)

    def accept(self) -> None:
        if not self.first.text().strip() or not self.last.text().strip():
            return QMessageBox.warning(
                self, tr("Error"), tr("First and last name are required.")
            )
        email = self.email.text().strip()
        if email and not EMAIL_RE.match(email):
            return QMessageBox.warning(self, tr("Error"), tr("Invalid email address."))
        try:
            dob = parse_dob(self.dob.text())
        except ValueError:
            return QMessageBox.warning(
                self,
                tr("Error"),
                tr("Please enter the date of birth as {}.").format(tr("YYYY-MM-DD")),
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
        if self.client_id:  # planned_treatment/notes are edited in the detail view
            row = db.get_client(self.win.conn, self.client_id)
            fields["planned_treatment"] = row["planned_treatment"]
            fields["notes"] = row["notes"]
        self.client_id = db.save_client(self.win.conn, fields, self.client_id)
        super().accept()


class RecordDialog(QDialog):
    """Create or edit a treatment / product sale record."""

    def __init__(
        self, win: "MainWindow", table: str, client_id: int, record: dict | None = None
    ):
        super().__init__(win)
        self.win, self.table, self.client_id = win, table, client_id
        self.record_id = record["id"] if record else None
        is_product = table == "product_records"
        self.setWindowTitle(tr("Product Sale") if is_product else tr("Treatment"))
        self.setMinimumWidth(420)
        date_col, text_col = db.RECORD_COLS[table]

        self.date = QDateEdit(calendarPopup=True)
        self.date.setDisplayFormat(date_format())
        self.date.setMaximumDate(QDate.currentDate())
        self.date.setDate(
            QDate.fromString(record[date_col], Qt.DateFormat.ISODate)
            if record
            else QDate.currentDate()
        )
        self.text = QPlainTextEdit(record[text_col] if record else "")

        form = QFormLayout(self)
        form.addRow(tr("Date"), self.date)
        if is_product:  # product row: quantity + name (inventory suggestions)
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
            add = QPushButton(tr("Add"))
            add.clicked.connect(self._add_product_line)
            self.product.returnPressed.connect(self._add_product_line)
            row = QHBoxLayout()
            row.addWidget(self.qty)
            row.addWidget(self.product, 1)
            row.addWidget(add)
            form.addRow(tr("Product"), row)
        form.addRow(tr("Products") if is_product else tr("Notes"), self.text)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if self.record_id:
            delete = buttons.addButton(
                tr("Delete…"), QDialogButtonBox.ButtonRole.DestructiveRole
            )
            delete.clicked.connect(self._delete)
        form.addRow(buttons)

    def _add_product_line(self) -> None:
        name = self.product.text().strip()
        if name:
            self.text.appendPlainText(f"{self.qty.value()}x {name}")
            self.product.clear()

    def _delete(self) -> None:
        if confirm(self, tr("Delete this entry permanently?")):
            db.delete_record(self.win.conn, self.table, self.record_id)
            QDialog.accept(self)

    def accept(self) -> None:
        text = self.text.toPlainText().strip()
        if not text:
            return QMessageBox.warning(self, tr("Error"), tr("Please enter text."))
        iso = self.date.date().toString(Qt.DateFormat.ISODate)
        if (
            self.record_id is None
            and db.record_exists(self.win.conn, self.table, self.client_id, iso)
            and not confirm(
                self, tr("An entry already exists for this date.\nSave anyway?")
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
        self.setWindowTitle(tr("Edit Item") if item else tr("New Item"))
        self.setMinimumWidth(380)

        self.name = QLineEdit(item["name"] if item else "")
        self.description = QPlainTextEdit((item["description"] or "") if item else "")
        self.description.setFixedHeight(60)
        self.capacity = QDoubleSpinBox(minimum=0.1, maximum=999999, decimals=1)
        self.capacity.setValue(item["capacity"] if item else 30)
        self.unit = QComboBox()
        self.unit.addItems(["ml", "g", "Pc."])  # enforced by the DB CHECK constraint
        if item:
            self.unit.setCurrentText(item["unit"])

        form = QFormLayout(self)
        form.addRow(tr("Name*"), self.name)
        form.addRow(tr("Description"), self.description)
        form.addRow(tr("Capacity*"), self.capacity)
        form.addRow(tr("Unit*"), self.unit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if self.item_id:
            delete = buttons.addButton(
                tr("Delete…"), QDialogButtonBox.ButtonRole.DestructiveRole
            )
            delete.clicked.connect(self._delete)
        form.addRow(buttons)

    def _delete(self) -> None:
        if confirm(self, tr("Delete this item permanently?")):
            db.delete_inventory(self.win.conn, self.item_id)
            QDialog.accept(self)

    def accept(self) -> None:
        name = self.name.text().strip()
        if not name:
            return QMessageBox.warning(self, tr("Error"), tr("Name is required."))
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
# Clients page: list on the left, detail on the right
# --------------------------------------------------------------------------


class ClientDetail(QWidget):
    def __init__(self, win: "MainWindow", on_change, on_back):
        super().__init__()
        self.win, self.on_change, self.client_id = win, on_change, None

        back = QPushButton(tr("← Back"))
        back.clicked.connect(on_back)
        self.header = QLabel(objectName="PageTitle")
        self.allergies = QLabel(objectName="Allergy")
        self.allergies.setWordWrap(True)
        edit = QPushButton(tr("Edit…"))
        edit.clicked.connect(self._edit_client)

        self.planned = SaveOnBlur(lambda t: self._save_field("planned_treatment", t))
        self.notes = SaveOnBlur(lambda t: self._save_field("notes", t))
        self.treatments = QListWidget(wordWrap=True)
        self.products = QListWidget(wordWrap=True)
        for lst, table in (
            (self.treatments, "treatment_records"),
            (self.products, "product_records"),
        ):
            lst.setToolTip(tr("Double-click to edit"))
            lst.itemDoubleClicked.connect(
                lambda item, t=table: self._edit_record(t, item)
            )

        def titled(title: str, widget: QWidget, button=None) -> QWidget:
            box = QWidget()
            lay = QVBoxLayout(box)
            lay.setContentsMargins(0, 0, 0, 0)
            head = QHBoxLayout()
            head.addWidget(QLabel(title, objectName="SectionTitle"))
            head.addStretch()
            if button:
                head.addWidget(button)
            lay.addLayout(head)
            lay.addWidget(widget)
            return box

        add_treatment = QPushButton(tr("+ Treatment"))
        add_treatment.clicked.connect(lambda: self._add_record("treatment_records"))
        add_product = QPushButton(tr("+ Sale"))
        add_product.clicked.connect(lambda: self._add_record("product_records"))

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.addWidget(titled(tr("Planned Treatment"), self.planned), 0, 0)
        grid.addWidget(titled(tr("Notes"), self.notes), 0, 1)
        grid.addWidget(titled(tr("Treatments"), self.treatments, add_treatment), 1, 0)
        grid.addWidget(titled(tr("Products"), self.products, add_product), 1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 2)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout()
        top.addWidget(back)
        top.addSpacing(8)
        top.addWidget(self.header)
        top.addStretch()
        top.addWidget(edit)
        lay.addLayout(top)
        lay.addWidget(self.allergies)
        lay.addLayout(grid)

    def load(self, client_id: int | None) -> None:
        self.client_id = client_id
        row = db.get_client(self.win.conn, client_id) if client_id else None
        if not row:
            self.client_id = None
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
            f"⚠ {tr('Allergies')}: {row['allergies']}" if row["allergies"] else ""
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
        self.win.statusBar().showMessage(tr("Saved ✓"), 2000)

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


class ClientsPage(QWidget):
    """List view first; clicking a client opens the full-width detail view."""

    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        self.search = QLineEdit(placeholderText=tr("Search (name or tag)…"))
        self.search.textChanged.connect(self.refresh)
        self.list = QListWidget()
        self.list.itemClicked.connect(self._open)
        add = QPushButton(tr("+ New Client"))
        add.clicked.connect(self._add)
        self.detail = ClientDetail(win, on_change=self._changed, on_back=self.show_list)

        list_page = QWidget()
        lay = QVBoxLayout(list_page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(QLabel(tr("Clients"), objectName="PageTitle"))
        lay.addSpacing(8)
        lay.addWidget(self.search)
        lay.addWidget(self.list)
        lay.addWidget(add)

        self.stack = QStackedWidget()
        self.stack.addWidget(list_page)
        self.stack.addWidget(self.detail)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 16)
        outer.addWidget(self.stack)
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for r in db.search_clients(self.win.conn, self.search.text()):
            item = QListWidgetItem(f"{r['last_name']}, {r['first_name']}")
            item.setData(Qt.ItemDataRole.UserRole, r["id"])
            if r["tags"]:
                item.setToolTip(r["tags"])
            self.list.addItem(item)

    def show_list(self) -> None:
        self.stack.setCurrentIndex(0)
        self.list.clearSelection()
        self.refresh()

    def _open(self, item: QListWidgetItem) -> None:
        self.detail.load(item.data(Qt.ItemDataRole.UserRole))
        self.stack.setCurrentIndex(1)

    def _changed(self) -> None:  # after the edit dialog closed
        self.refresh()
        if self.detail.client_id is None:  # client was deleted
            self.stack.setCurrentIndex(0)

    def _add(self) -> None:
        dialog = ClientDialog(self.win)
        if dialog.exec():
            self.refresh()
            self.detail.load(dialog.client_id)
            self.stack.setCurrentIndex(1)


# --------------------------------------------------------------------------
# Inventory page
# --------------------------------------------------------------------------


class InventoryPage(QWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        self.search = QLineEdit(placeholderText=tr("Search items…"))
        self.search.textChanged.connect(self.refresh)
        self.list = QListWidget()
        self.list.setToolTip(tr("Double-click to edit"))
        self.list.itemDoubleClicked.connect(self._edit)
        add = QPushButton(tr("+ New Item"))
        add.clicked.connect(self._add)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 16)
        lay.addWidget(QLabel(tr("Inventory"), objectName="PageTitle"))
        lay.addSpacing(8)
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
# Change log page (audit log)
# --------------------------------------------------------------------------


class AuditPage(QWidget):
    PER_PAGE = 50

    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win, self.page = win, 0
        self.view = QTextBrowser()
        self.prev = QPushButton(tr("← Newer"))
        self.next = QPushButton(tr("Older →"))
        self.label = QLabel(objectName="Muted")
        self.prev.clicked.connect(lambda: self._go(-1))
        self.next.clicked.connect(lambda: self._go(1))

        nav = QHBoxLayout()
        nav.addWidget(self.prev)
        nav.addWidget(self.label)
        nav.addStretch()
        nav.addWidget(self.next)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 16)
        lay.addWidget(QLabel(tr("Change Log"), objectName="PageTitle"))
        lay.addSpacing(8)
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
        self.label.setText(
            tr("Page {} of {} ({} entries)").format(self.page + 1, pages, total)
        )
        self.prev.setEnabled(self.page > 0)
        self.next.setEnabled(self.page < pages - 1)
        self.view.setHtml(
            "".join(self._render(e) for e in entries) or f"<p>{tr('No entries.')}</p>"
        )

    @staticmethod
    def _field_line(field: str, old, new) -> str:
        label = html.escape(tr(FIELD_LABELS.get(field, field)))
        return (
            f"<div><b>{label}:</b> <s>{html.escape(str(old or '—'))}</s> → "
            f"<b>{html.escape(str(new or '—'))}</b></div>"
        )

    def _render(self, e: dict) -> str:
        verb = tr(
            {"CREATE": "created", "UPDATE": "changed", "DELETE": "deleted"}[e["action"]]
        )
        table = tr(TABLE_LABELS.get(e["table_name"], e["table_name"]))
        who = f" — {html.escape(e['client_name'])}" if e["client_name"] else ""
        body = ""
        if e["changes"]:  # trigger rows: JSON diff of changed fields
            body = "".join(
                self._field_line(f, old, new) for f, old, new in e["changes"]
            )
        elif e["field_name"]:  # legacy 1.x rows: one field per row
            body = self._field_line(e["field_name"], e["old_value"], e["new_value"])
        elif e["action"] in ("CREATE", "DELETE"):
            snapshot = e["new_value"] if e["action"] == "CREATE" else e["old_value"]
            try:
                fields = json.loads(snapshot or "")
                body = "".join(
                    f"<div><b>{html.escape(tr(FIELD_LABELS.get(f, f)))}:</b> "
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
# Settings page
# --------------------------------------------------------------------------


class SettingsPage(QWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        cfg = win.cfg

        self.theme = QComboBox()
        self.theme.setFixedWidth(220)
        for label, value in (
            (tr("System"), "system"),
            (tr("Light"), "light"),
            (tr("Dark"), "dark"),
        ):
            self.theme.addItem(label, value)
        self.theme.setCurrentIndex(self.theme.findData(cfg.get("theme", "system")))
        self.theme.currentIndexChanged.connect(self._theme_changed)

        self.language = QComboBox()
        self.language.setFixedWidth(220)
        self.language.addItem("English", "en")
        self.language.addItem("Deutsch", "de")
        self.language.setCurrentIndex(self.language.findData(i18n.LANG))
        self.language.currentIndexChanged.connect(self._language_changed)
        self.restart_hint = QLabel("", objectName="Muted")

        appearance_box = QGroupBox(tr("Appearance"))
        appearance = QFormLayout(appearance_box)
        appearance.addRow(tr("Theme"), self.theme)
        lang_row = QHBoxLayout()
        lang_row.addWidget(self.language)
        lang_row.addWidget(self.restart_hint, 1)
        appearance.addRow(tr("Language"), lang_row)

        self.auto = QCheckBox(tr("Automatic backup at startup"))
        self.auto.setChecked(cfg.get("auto_backup", True))
        self.interval = QSpinBox(minimum=1, maximum=1440, suffix=tr(" min"))
        self.interval.setFixedWidth(120)
        self.interval.setValue(cfg.get("backup_interval_minutes", 120))
        self.keep = QSpinBox(minimum=1, maximum=100)
        self.keep.setFixedWidth(120)
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

        backup_now = QPushButton(tr("Back up now"))
        backup_now.clicked.connect(self._backup_now)
        restore = QPushButton(tr("Restore backup…"))
        restore.clicked.connect(self._restore)
        open_dir = QPushButton(tr("Open backup folder"))
        open_dir.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(db.backups_dir())))
        )

        backup_box = QGroupBox(tr("Backup"))
        form = QFormLayout(backup_box)
        form.addRow(self.auto)
        form.addRow(tr("Interval"), self.interval)
        form.addRow(tr("Backups to keep"), self.keep)
        row = QHBoxLayout()
        row.addWidget(backup_now)
        row.addWidget(restore)
        row.addWidget(open_dir)
        form.addRow(row)

        mail_merge = QPushButton(tr("Mail Merge Export (CSV)…"))
        mail_merge.clicked.connect(self._mail_merge)
        full_export = QPushButton(tr("Export All Data (CSV)…"))
        full_export.clicked.connect(self._export_all)
        export_box = QGroupBox(tr("Export"))
        export_lay = QHBoxLayout(export_box)
        export_lay.addWidget(mail_merge)
        export_lay.addWidget(full_export)

        info = QLabel(
            tr("Database: {}").format(win.path) + f"\nCosmetics Records {db.VERSION}",
            objectName="Muted",
        )
        info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 16)
        lay.addWidget(QLabel(tr("Settings"), objectName="PageTitle"))
        lay.addSpacing(8)
        lay.addWidget(appearance_box)
        lay.addWidget(backup_box)
        lay.addWidget(export_box)
        lay.addWidget(info)
        lay.addStretch()

    def _set(self, key: str, value) -> None:
        self.win.cfg[key] = value
        db.save_config(self.win.cfg)

    def _theme_changed(self) -> None:
        self._set("theme", self.theme.currentData())
        style.apply_theme(self.theme.currentData())

    def _language_changed(self) -> None:
        self._set("language", self.language.currentData())
        self.restart_hint.setText(tr("Takes effect after restarting."))

    def _backup_now(self) -> None:
        path = db.create_backup(self.win.conn, self.win.path)
        db.cleanup_backups(self.keep.value())
        self.win.cfg["last_backup_time"] = datetime.now().isoformat()
        db.save_config(self.win.cfg)
        QMessageBox.information(
            self, tr("Backup"), tr("Backup created:\n{}").format(path.name)
        )

    def _restore(self) -> None:
        backups = db.list_backups()
        if not backups:
            return QMessageBox.information(
                self, tr("Backup"), tr("No backups available.")
            )
        name, ok = QInputDialog.getItem(
            self,
            tr("Restore Backup"),
            tr("Select backup:"),
            [p.name for p in backups],
            0,
            False,
        )
        if not ok or not confirm(
            self,
            tr(
                "Current data will be replaced.\nA safety backup is created first.\nContinue?"
            ),
        ):
            return
        try:
            self.win.restore(db.backups_dir() / name)
            QMessageBox.information(self, tr("Backup"), tr("Backup restored."))
        except (ValueError, OSError, zipfile.BadZipFile) as err:
            QMessageBox.critical(
                self, tr("Error"), tr("Restore failed:\n{}").format(err)
            )

    def _mail_merge(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Mail Merge Export"), tr("clients_mail_merge.csv"), "CSV (*.csv)"
        )
        if path:
            count = db.export_mail_merge(self.win.conn, Path(path))
            QMessageBox.information(
                self, tr("Export"), tr("{} clients exported.").format(count)
            )

    def _export_all(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, tr("Choose destination folder")
        )
        if directory:
            files = db.export_all(self.win.conn, Path(directory))
            QMessageBox.information(
                self,
                tr("Export"),
                tr("{} files exported to:\n{}").format(len(files), directory),
            )


# --------------------------------------------------------------------------
# Main window: sidebar navigation + stacked pages
# --------------------------------------------------------------------------


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = db.load_config()
        self.path = db.db_path(self.cfg)
        self.conn = db.connect(self.path)

        self.setWindowTitle("Cosmetics Records")
        self.resize(1150, 720)

        self.clients = ClientsPage(self)
        self.inventory = InventoryPage(self)
        self.pages = QStackedWidget()
        for page in (self.clients, self.inventory, AuditPage(self), SettingsPage(self)):
            self.pages.addWidget(page)

        self.nav = QListWidget(objectName="Nav")
        for name in ("Clients", "Inventory", "Change Log"):
            self.nav.addItem(tr(name))
        self.nav_settings = QListWidget(objectName="Nav")  # pinned at the bottom
        self.nav_settings.addItem(tr("Settings"))
        self.nav_settings.setFixedHeight(self.nav_settings.sizeHintForRow(0) + 16)
        self.nav.currentRowChanged.connect(self._nav_main)
        self.nav_settings.currentRowChanged.connect(self._nav_settings)
        self.nav.setCurrentRow(0)

        sidebar = QWidget(objectName="Sidebar")
        sidebar.setFixedWidth(210)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(0, 0, 0, 0)
        side.addWidget(QLabel("Cosmetics Records", objectName="AppTitle"))
        side.addWidget(self.nav, 1)
        side.addWidget(self.nav_settings)

        central = QWidget()
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(sidebar)
        lay.addWidget(self.pages, 1)
        self.setCentralWidget(central)
        self.statusBar()

        # backup after first paint — startup stays instantly usable
        QTimer.singleShot(0, self._startup_backup)

    def _nav_main(self, row: int) -> None:
        if row >= 0:
            self.nav_settings.blockSignals(True)
            self.nav_settings.setCurrentRow(-1)
            self.nav_settings.blockSignals(False)
            self.pages.setCurrentIndex(row)

    def _nav_settings(self, row: int) -> None:
        if row >= 0:
            self.nav.blockSignals(True)
            self.nav.setCurrentRow(-1)
            self.nav.blockSignals(False)
            self.pages.setCurrentIndex(3)

    def _startup_backup(self) -> None:
        if db.auto_backup_if_due(self.conn, self.cfg, self.path):
            self.statusBar().showMessage(tr("Automatic backup created ✓"), 4000)

    def restore(self, backup: Path) -> None:
        db.create_backup(self.conn, self.path)  # safety copy of the current state
        self.conn.close()
        try:
            db.restore_backup(backup, self.path)
        finally:
            self.conn = db.connect(self.path)
        self.clients.show_list()
        self.inventory.refresh()

    def closeEvent(self, event) -> None:
        self.conn.close()
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Cosmetics Records")
    app.setStyle("Fusion")
    if ICON.exists():
        app.setWindowIcon(QIcon(str(ICON)))

    cfg = db.load_config()
    default = "de" if QLocale.system().name().startswith("de") else "en"
    i18n.set_language(cfg.get("language") or default)
    style.apply_theme(cfg.get("theme", "system"))

    window = MainWindow()
    app.styleHints().colorSchemeChanged.connect(
        lambda *_: window.cfg.get("theme", "system") == "system"
        and style.apply_theme("system")
    )
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
