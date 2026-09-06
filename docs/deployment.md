# Deployment

`make deploy-package IMAGE_TAG=<commit-sha>` creates a release bundle with `compose.yaml`,
`.env.example` and this document. The target host pulls the immutable image from GHCR.

1. Copy the generated archive to the host and unpack it.
2. Copy `.env.example` to `.env`. Set `IMAGE_TAG` and a unique `POSTGRES_PASSWORD`.
   The same password must appear in `DATABASE_URL`; do this only on the host.
3. If GHCR is private, authenticate Docker to `ghcr.io` on the host.
4. Run `docker compose pull && docker compose up -d`.

Only `.env` is host-specific. It is ignored by Git and excluded from the bundle. Docker
named volumes retain PostgreSQL, raw exports and reports across container updates.
