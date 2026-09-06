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

## Delivery

- Pull Requests prüfen Tests und die Compose-Konfiguration.
- Pushes nach `main` bauen ein Image und veröffentlichen es als `ghcr.io/<owner>/<repo>:<commit-sha>`.
- Das Deployment erfolgt bewusst kontrolliert auf dem Zielsystem:
```bash
docker compose -f Docker/compose.yaml pull
docker compose -f Docker/compose.yaml up -d
```
Secrets gehören ausschließlich in die Laufzeitumgebung des Zielsystems, nie ins Repository oder Image.
