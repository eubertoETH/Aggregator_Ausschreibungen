# Deployment

`make deploy-package IMAGE_TAG=<commit-sha>` creates a release bundle with `compose.yaml`,
`.env.example` and this document. The target host pulls the immutable image from GHCR.

## Responsibility split

GitHub Actions runs tests, validates Compose, builds the image and publishes its immutable
commit tag to GHCR. It does **not** connect to the target host and there is no GitHub
deployment password in this workflow. The host deliberately pulls and starts an approved tag.

## GitHub

1. Push the reviewed commit to `main`.
2. Wait for the GitHub Actions run to succeed; its commit SHA is the `IMAGE_TAG`.
3. Create the release bundle with that SHA and transfer it to the host.

GitHub Actions uses the automatic `GITHUB_TOKEN` to publish the image. No manually managed
repository secret is required for the current build/publish workflow.

1. Install Docker Engine plus Docker Compose on the host. Copy the generated archive to the
   host and unpack it.
2. Copy `.env.example` to `.env`. Set `IMAGE_TAG` and a unique `POSTGRES_PASSWORD`.
   The same password must appear in `DATABASE_URL`; do this only on the host.
3. If GHCR is private, authenticate Docker to `ghcr.io` on the host.
4. Run `docker compose pull && docker compose up -d`.

The application binds to `127.0.0.1:8080` by default. Keep it private or put an authenticated
reverse proxy in front of it before exposing it externally; the prototype currently has no
application login.

## Credentials

- **PostgreSQL password:** required, but only for the app/scheduler-to-database connection
  inside Compose. PostgreSQL has no published host port.
- **GHCR read access:** only needed on the host when the container package is private; this is
  Docker's registry credential, not an application credential.
- **DÖE:** no credential required. The current prototype has no LLM, mail, SharePoint or other
  external-service credential.
- **Automated GitHub-to-host deployment:** not configured. It would require a separate,
  narrowly scoped host-access mechanism (for example a deploy key or a self-hosted runner) and
  an explicit decision to enable automatic deployment.

Only `.env` and, if needed, Docker's registry credential are host-specific. They are ignored by
Git and excluded from the bundle. Docker named volumes retain PostgreSQL, raw exports and reports
across container updates.
