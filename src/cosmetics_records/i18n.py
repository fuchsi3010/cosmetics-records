"""Minimal i18n: English source strings, one German dict, no gettext toolchain.

ponytail: a dict beats .po/.mo compile steps at two languages; switch to
gettext if a third language ever lands.
"""

LANG = "en"


def set_language(lang: str) -> None:
    global LANG
    LANG = lang if lang in ("en", "de") else "en"


def tr(text: str) -> str:
    return DE.get(text, text) if LANG == "de" else text


DE = {
    # Navigation & window
    "Clients": "Kunden",
    "Inventory": "Inventar",
    "Change Log": "Protokoll",
    "Settings": "Einstellungen",
    # Client list & detail
    "Search (name or tag)…": "Suchen (Name oder Tag)…",
    "+ New Client": "+ Neuer Kunde",
    "← Back": "← Zurück",
    "Edit…": "Bearbeiten…",
    "Planned Treatment": "Geplante Behandlung",
    "Notes": "Notizen",
    "Treatments": "Behandlungen",
    "Products": "Produkte",
    "+ Treatment": "+ Behandlung",
    "+ Sale": "+ Verkauf",
    "Double-click to edit": "Doppelklick zum Bearbeiten",
    "Allergies": "Allergien",
    "Saved ✓": "Gespeichert ✓",
    "Birthdays": "Geburtstage",
    "today": "heute",
    "tomorrow": "morgen",
    "in {} days": "in {} Tagen",
    # Client dialog
    "New Client": "Neuer Kunde",
    "Edit Client": "Kunde bearbeiten",
    "First name*": "Vorname*",
    "Last name*": "Nachname*",
    "Email": "E-Mail",
    "Phone": "Telefon",
    "Address": "Adresse",
    "Date of birth": "Geburtsdatum",
    "Tags": "Tags",
    "e.g. VIP, sensitive skin": "z. B. VIP, empfindliche Haut",
    "YYYY-MM-DD": "TT.MM.JJJJ",
    "Delete…": "Löschen…",
    "Delete client and entire history permanently?": "Kunde und gesamte Historie unwiderruflich löschen?",  # noqa: E501
    "First and last name are required.": "Vor- und Nachname sind Pflichtfelder.",
    "Invalid email address.": "Ungültige E-Mail-Adresse.",
    "Please enter the date of birth as {}.": "Geburtsdatum bitte als {} angeben.",
    # Record dialog
    "Treatment": "Behandlung",
    "Product Sale": "Produktverkauf",
    "Date": "Datum",
    "Product": "Produkt",
    "Add": "Hinzufügen",
    "Please enter text.": "Bitte Text eingeben.",
    "An entry already exists for this date.\nSave anyway?": "Für dieses Datum existiert bereits ein Eintrag.\nTrotzdem speichern?",  # noqa: E501
    "Delete this entry permanently?": "Eintrag unwiderruflich löschen?",
    # Inventory
    "Search items…": "Artikel suchen…",
    "+ New Item": "+ Neuer Artikel",
    "New Item": "Neuer Artikel",
    "Edit Item": "Artikel bearbeiten",
    "Name*": "Name*",
    "Description": "Beschreibung",
    "Capacity*": "Inhalt*",
    "Unit*": "Einheit*",
    "Name is required.": "Name ist ein Pflichtfeld.",
    "Delete this item permanently?": "Artikel unwiderruflich löschen?",
    # Audit log
    "← Newer": "← Neuere",
    "Older →": "Ältere →",
    "Page {} of {} ({} entries)": "Seite {} von {} ({} Einträge)",
    "No entries.": "Keine Einträge.",
    "created": "erstellt",
    "changed": "geändert",
    "deleted": "gelöscht",
    "Client": "Kunde",
    "Product sale": "Produktverkauf",
    "First name": "Vorname",
    "Last name": "Nachname",
    "Planned treatment": "Geplante Behandlung",
    "Client no.": "Kunden-Nr.",
    "Treatment notes": "Behandlungsnotizen",
    "Name": "Name",
    "Capacity": "Inhalt",
    "Unit": "Einheit",
    # Settings
    "Appearance": "Darstellung",
    "Theme": "Farbschema",
    "Scaling": "Skalierung",
    "Date Format": "Datumsformat",
    "Automatic": "Automatisch",
    "System": "System",
    "Light": "Hell",
    "Dark": "Dunkel",
    "Language": "Sprache",
    "Takes effect after restarting.": "Wird nach einem Neustart wirksam.",
    "Backup": "Backup",
    "Automatic backup at startup": "Automatisches Backup beim Start",
    "Interval": "Intervall",
    " min": " Min.",
    "Backups to keep": "Anzahl behalten",
    "Back up now": "Jetzt sichern",
    "Restore backup…": "Backup wiederherstellen…",
    "Open backup folder": "Backup-Ordner öffnen",
    "Backup created:\n{}": "Backup erstellt:\n{}",
    "No backups available.": "Keine Backups vorhanden.",
    "Restore Backup": "Backup wiederherstellen",
    "Select backup:": "Backup auswählen:",
    "Current data will be replaced.\nA safety backup is created first.\nContinue?": "Aktuelle Daten werden ersetzt.\nVorher wird automatisch ein "  # noqa: E501
    "Sicherheits-Backup erstellt.\nFortfahren?",
    "Backup restored.": "Backup wiederhergestellt.",
    "Restore failed:\n{}": "Wiederherstellung fehlgeschlagen:\n{}",
    "Export": "Export",
    "Import": "Import",
    "Data": "Daten",
    "Import Data (CSV)…": "Daten importieren (CSV)…",
    "Choose the folder containing the CSV files": "Ordner mit den CSV-Dateien wählen",
    "Imports clients.csv, treatment_records.csv, product_records.csv "
    "and inventory.csv.\nExisting data is kept. Continue?": "Importiert clients.csv, treatment_records.csv, product_records.csv "  # noqa: E501
    "und inventory.csv.\nBestehende Daten bleiben erhalten. Fortfahren?",
    "Import failed:\n{}": "Import fehlgeschlagen:\n{}",
    "{} records imported.": "{} Einträge importiert.",
    "Change database location…": "Datenbank-Speicherort ändern…",
    "The database will be moved. A backup is created first.\nContinue?": "Die Datenbank wird verschoben. Vorher wird ein Backup erstellt.\n"  # noqa: E501
    "Fortfahren?",
    "Database moved.": "Datenbank verschoben.",
    "Move failed:\n{}": "Verschieben fehlgeschlagen:\n{}",
    "Retention": "Aufbewahrung",
    " days": " Tage",
    "Clean up now": "Jetzt aufräumen",
    "Applied automatically at startup.": "Wird beim Start automatisch angewendet.",
    "Delete all log entries older than {} days?": "Alle Protokolleinträge löschen, die älter als {} Tage sind?",  # noqa: E501
    "{} entries deleted.": "{} Einträge gelöscht.",
    "Mail Merge Export (CSV)…": "Serienbrief-Export (CSV)…",
    "Mail Merge Export": "Serienbrief-Export",
    "clients_mail_merge.csv": "kunden_serienbrief.csv",
    "Export All Data (CSV)…": "Alle Daten exportieren (CSV)…",
    "{} clients exported.": "{} Kunden exportiert.",
    "Choose destination folder": "Zielordner wählen",
    "{} files exported to:\n{}": "{} Dateien exportiert nach:\n{}",
    "Database: {}": "Datenbank: {}",
    # Shared
    "Error": "Fehler",
    "Confirm": "Bestätigen",
    "Automatic backup created ✓": "Automatisches Backup erstellt ✓",
}
