# Service Template

Startpunkt für containerisierte Services mit klarer Dokumentation, lokaler Compose-Umgebung und GitHub Actions.

## Schnellstart
```bash
cp .env.example .env
make test
make up
```

Die Anwendung liegt in `Code/`, Laufzeitdateien in `Docker/` und verbindliche Projektdokumentation in `docs/specs/`.

## Delivery

- Pull Requests prüfen Tests und die Compose-Konfiguration.
- Pushes nach `main` bauen ein Image und veröffentlichen es als `ghcr.io/<owner>/<repo>:<commit-sha>`.
- Das Deployment erfolgt bewusst kontrolliert auf dem Zielsystem:
```bash
docker compose -f Docker/compose.yaml pull
docker compose -f Docker/compose.yaml up -d
```
Secrets gehören ausschließlich in die Laufzeitumgebung des Zielsystems, nie ins Repository oder Image.
