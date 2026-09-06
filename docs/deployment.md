# Deployment

GitHub Actions runs tests, validates Compose, builds an immutable private GHCR image and publishes
it with the commit SHA. The host has a checkout of this repository and deploys with `make deploy`.

1. Install Docker Engine, Docker Compose and Git on the host. Create a sparse checkout containing
   only `Makefile`, `Docker/` and `deploy/`; the application source is inside the pulled image and
   is not needed on the host:

   ```bash
   cd /opt/docker
   git clone --filter=blob:none --no-checkout https://github.com/eubertoETH/Aggregator_Ausschreibungen.git aggregator-ausschreibungen
   cd aggregator-ausschreibungen
   git sparse-checkout init --cone
   git sparse-checkout set Docker deploy Makefile
   git checkout main
   ```
2. Create the adjacent host-owned directory `<repository>-host/` and copy
   `deploy/.env.example` to `<repository>-host/.env`.
3. Create the non-empty file configured by `POSTGRES_PASSWORD_HOST_FILE` (for example
   `<repository>-host/secrets/postgres_password`) through the host's protected secret mechanism.
4. Set `AGGREGATOR_IMAGE` in the host `.env` to the approved immutable GHCR commit tag.
5. Authenticate Docker on the host for read access to private GHCR images. This credential belongs
   to Docker's credential store for the host user running `make deploy`, never to the project `.env`.
6. Run `make deploy` in the repository checkout. It syncs the checkout with `git pull --ff-only`,
   validates the host configuration and secret path, pulls images and recreates only app/scheduler.

Before cloning, the existing GHCR permission can be checked without changing the host:

```bash
docker pull ghcr.io/eubertoeth/aggregator_ausschreibungen:0fc35c3af9527c255dd0d89775ac1fe56ca42e92
```

Success means that the Docker credential for the current host user has read access. An
authentication failure means the normal host-level GHCR login needs to be configured first; it is
not a project setting and must not be added to `.env`.

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
