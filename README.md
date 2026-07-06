# Cosmetics Records

Kundenkartei für ein Ein-Personen-Kosmetikstudio: Kundendaten, Behandlungshistorie und Produktverkäufe. Python 3.10+ und PyQt6, zwei Quelldateien, keine weiteren Laufzeitabhängigkeiten.

Version 2.0 ist eine Neuimplementierung mit Fokus auf Geschwindigkeit und Sicherheit. Sie öffnet bestehende Datenbanken der Version 1.x unverändert.

## Funktionen

- **Kunden**: Stammdaten, Allergien (prominent angezeigt), Tags, Suche (umlautfest)
- **Behandlungen & Produktverkäufe**: Historie pro Kunde, Produkteingabe mit Vorschlägen aus dem Inventar
- **Geplante Behandlung / Notizen**: Freitextfelder, automatisch gespeichert beim Verlassen des Feldes
- **Inventar**: Artikelkatalog (ml, g, Pc.)
- **Protokoll**: lückenlose Änderungshistorie — direkt in der Datenbank per Trigger erzeugt, von keiner Codestelle umgehbar
- **Backups**: automatisch beim Start (konfigurierbares Intervall), konsistente Snapshots auch bei laufender Anwendung, Wiederherstellung per Klick
- **CSV-Export**: Serienbrief (Name + Adresse) und Komplettexport aller Tabellen

## Sicherheit

- Datenbank, Konfiguration und Backups mit `0600`-Dateirechten, Datenordner `0700`
- `PRAGMA secure_delete`: gelöschte Kundendaten sind nicht aus freien Datenbankseiten rekonstruierbar
- Durchgängig parametrisierte SQL-Abfragen
- Keine Logdatei — Behandlungsnotizen landen nirgendwo außerhalb der Datenbank
- Für Verschlüsselung im Ruhezustand: Festplattenverschlüsselung (LUKS/BitLocker) verwenden

## Starten

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/cosmetics_records/app.py
```

Unter NixOS: `nix-shell --run 'python src/cosmetics_records/app.py'`

## Entwicklung

```bash
pip install -r requirements-dev.txt
pytest            # Tests
black src tests   # Formatierung
```

Daten liegen unter `~/.local/share/cosmetics_records/` (Linux), `%APPDATA%\cosmetics_records\` (Windows) bzw. `~/Library/Application Support/cosmetics_records/` (macOS).

## Lizenz

Apache-2.0
