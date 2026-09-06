# Runbook

## Release
1. Commit-Image in GHCR identifizieren.
2. Auf dem Zielsystem die gewünschte Version in der lokalen Compose-Umgebung setzen.
3. `docker compose pull && docker compose up -d` ausführen.
4. Gesundheitscheck und Logs prüfen.

## Rollback
Den vorherigen unveränderlichen Commit-Tag setzen und die Release-Schritte wiederholen.
