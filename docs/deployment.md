# Deployment

GitHub Actions runs tests, validates Compose, builds an immutable private GHCR image and publishes
it with the commit SHA. The host has a checkout of this repository and deploys with `make deploy`.

1. Install Docker Engine, Docker Compose and Git on the host. Clone the private repository.
2. Create the adjacent host-owned directory `<repository>-host/` and copy
   `deploy/.env.example` to `<repository>-host/.env`.
3. Create the non-empty file configured by `POSTGRES_PASSWORD_HOST_FILE` (for example
   `<repository>-host/secrets/postgres_password`) through the host's protected secret mechanism.
4. Set `AGGREGATOR_IMAGE` in the host `.env` to the approved immutable GHCR commit tag.
5. Authenticate Docker on the host for read access to private GHCR images.
6. Run `make deploy` in the repository checkout. It syncs the checkout with `git pull --ff-only`,
   validates the host configuration and secret path, pulls images and recreates only app/scheduler.

The application binds to `127.0.0.1:8080` by default. Keep it private or put an authenticated
reverse proxy in front of it before exposing it externally; the prototype currently has no
application login.

## Credentials

- **PostgreSQL password:** host-owned secret file; mounted as a Docker secret into PostgreSQL,
  app and scheduler. PostgreSQL has no published host port.
- **GHCR read access:** Docker registry credential on the host because the package is private.
- **DÖE:** no credential required. The current prototype has no LLM, mail, SharePoint or other
  external-service credential.

The host `.env`, secret file and Docker registry credential never enter Git. Docker named volumes
retain PostgreSQL, raw exports and reports across deployments.
