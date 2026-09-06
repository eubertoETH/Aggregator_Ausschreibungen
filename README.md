# Ausschreibungsaggregator

Sammelt Bekanntmachungen des Datenservice Öffentlicher Einkauf (DÖE), speichert
Rohdaten und normalisierte Metadaten in PostgreSQL und stellt eine filterbare
Übersicht bereit. Der erste Schnitt verwendet keine LLMs.

## Schnellstart
```bash
cp .env.example .env
make test && make up
# Nach dem Start: http://localhost:8080
# Tagesimport (DÖE stellt den Vortag bereit)
make import-today
# Markdown-Report unter dem Docker-Volume aggregator_data/reports
make report
```

Die Anwendung liegt in `Code/`, Laufzeitdateien in `Docker/` und verbindliche Projektdokumentation in `docs/specs/`.

## Filter

Die Übersicht unterstützt Freitext, Veröffentlichungszeitraum, CPV, NUTS-Region,
Verfahrensart und regelbasiert abgeleitete Tags (`bestand`, `sanierung`,
`fassade`, `energie`). PostgreSQL indiziert die häufigen strukturierten Filter
sowie CPV- und Tag-Arrays mit GIN-Indizes. Die Fachbegriffe liegen zentral in
`Code/app/importer.py` und können ohne Datenmigration erweitert werden.

## Betrieb

Der Import-Endpunkt akzeptiert ein Datum: `POST /imports/YYYY-MM-DD`. Der
mitgelieferte Scheduler läuft täglich um 02:15 Uhr und liest den Vortag plus die
zwei vorherigen Tage erneut ein. Das Upsert über Quelle, Bekanntmachungs-ID und
Version macht diese Wiederholung idempotent. Anschließend erstellt er den
Markdown-Report. `POST /reports/daily` kann ihn zusätzlich manuell erzeugen.

## Deployment

Auf dem Zielhost führt `make deploy` den bestehenden Git-sync-, Preflight- und
GHCR-Pull-Flow aus. Host-Konfiguration und Secrets liegen bewusst neben dem
Repository, nicht darin. Details stehen in `docs/deployment.md`.

## Delivery

- Pull Requests prüfen Tests und die Compose-Konfiguration.
- Pushes nach `main` bauen ein Image und veröffentlichen es als `ghcr.io/eubertoeth/aggregator_ausschreibungen:<commit-sha>`.
- Das Zielsystem erhält ausschließlich das Release-Bundle; dort läuft `docker compose pull && docker compose up -d`.
- Die host-spezifische `.env` (PostgreSQL-Passwort, Port und Image-Tag) gehört nie ins Repository oder Image.
