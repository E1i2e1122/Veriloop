# Makefile Reference

![Veriloop dashboard shown after running local development commands](../assets/ui/dashboard-overview.png)

<p class="caption">Veriloop dashboard shown after running local development commands.</p>


Complete reference for all `make` targets in Veriloop. Run `make help` for the built-in summary; the repository-root `Makefile` is the source of truth.

## Setup & Development

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make setup` | Install Python venv, Node deps, Playwright browsers, database | -- | `make setup` |
| `make setup-skills` | Install Playwright skill dependencies (npm + Chromium) | `.claude/skills/playwright` directory | `make setup-skills` |
| `make dev` | Start the full Docker development stack with local code mounts and frontend hot reload (`docker-compose.prod.yml` + `docker-compose.dev-override.yml`) | Docker, `.env.prod` | `make dev` |
| `make start` | Start the server app runtime for external-nginx deployment (`docker-compose.prod.yml`) | Docker, `.env.prod`, your own reverse proxy | `make start` |
| `make restart` | Stop and restart the server runtime | Docker, `.env.prod` | `make restart` |
| `make restart-agent-worker` | Restart backend uvicorn and queued agent workers inside the running backend container | Running backend container | `make restart-agent-worker` |
| `make deploy-check` | Verify local external-nginx runtime readiness | Running stack | `make deploy-check` |
| `make run SPEC=...` | Run a specific test spec via CLI (native pipeline) | `make setup`, venv | `make run SPEC=specs/examples/hello-world.md` |
| `make run-skill S=...` | Run a Playwright skill script | `make setup-skills`, venv | `make run-skill S=path/to/script.js` |
| `make load-test SPEC=...` | Generate and run K6 load test from spec | venv, k6 installed | `make load-test SPEC=specs/load/api-test.md` |
| `make agent-runtime-ready` | Verify the API and Temporal agent workers are ready | Running stack | `make agent-runtime-ready` |
| `make agent-temporal-smoke-up` | Start Docker services needed for agent Temporal smoke | Docker | `make agent-temporal-smoke-up` |
| `make agent-temporal-smoke` | Run deterministic standalone agent Temporal smoke | Docker services or equivalent Temporal/Postgres | `make agent-temporal-smoke` |
| `make agent-temporal-smoke-logs` | Tail Temporal and custom workflow worker logs | Docker | `make agent-temporal-smoke-logs` |
| `make autonomous-soak` | Run a bounded autonomous product-UI soak (`SOAK_*` variables tune it) | Running stack | `make autonomous-soak` |

## Docker (Legacy Local Compose)

These targets use the legacy `docker-compose.yml`. Use `make dev` or `make start` for supported runtimes.

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make docker-up` | Unsupported legacy `docker-compose.yml` path; prints guidance and exits | -- | `make docker-up` |
| `make docker-down` | Stop all `docker-compose.yml` services | Docker | `make docker-down` |
| `make docker-build` | Rebuild `docker-compose.yml` images (no cache) | Docker | `make docker-build` |
| `make dev-k6-workers-up` | Start dev K6 workers (volume-mounted code) | Docker | `make dev-k6-workers-up` |
| `make dev-k6-workers-down` | Stop dev K6 workers | Docker | `make dev-k6-workers-down` |
| `make dev-k6-workers-logs` | Tail dev K6 worker logs | Docker | `make dev-k6-workers-logs` |

## Docker (Production)

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make prod-env-bootstrap` | Create `.env.prod` from `.env.prod.example` and generate private values | -- | `make prod-env-bootstrap` |
| `make prod-up` | Guarded legacy repo-managed nginx path; not used for server deployment | Docker, `.env.prod`, `VERILOOP_ENABLE_REPO_NGINX=1` | `VERILOOP_ENABLE_REPO_NGINX=1 make prod-up` |
| `make prod` | Alias for guarded `make prod-up` | Docker, `.env.prod` | `VERILOOP_ENABLE_REPO_NGINX=1 make prod` |
| `make prod-dev` | Compatibility alias for `make dev` | Docker, `.env.prod` | `make prod-dev` |
| `make prod-dev-build` | Rebuild frontend, backend, and worker images for the dev stack | Docker, `.env.prod` | `make prod-dev-build` |
| `make prod-down` | Stop production services (30s graceful timeout) | Docker | `make prod-down` |
| `make prod-down-safe` | Stop with backup first | Docker | `make prod-down-safe` |
| `make prod-restart` | Restart backend and frontend (picks up mounted code changes) | Docker | `make prod-restart` |
| `make prod-logs` | Tail backend, frontend, and worker logs | Docker | `make prod-logs` |
| `make prod-build` | Rebuild production images (with cache) | Docker | `make prod-build` |
| `make prod-build-no-cache` | Rebuild production images (fresh, no cache) | Docker | `make prod-build-no-cache` |
| `make prod-status` | Show service status and health | Docker | `make prod-status` |

### Production Services

`make start` starts the external-nginx app runtime:

| Service | Port | Description |
|---------|------|-------------|
| Dashboard | 3000 (direct/proxy target) | Next.js frontend |
| API | 8001 | FastAPI backend |
| API Docs | 8001/docs | Swagger UI |
| PostgreSQL | internal, host depends on compose file | Primary production database |
| Redis | internal | Queues, workers, rate limiting, distributed execution |
| VNC View | 6080 | Live browser view (websockify) |
| MinIO API | 9000 | S3-compatible artifact and backup storage |
| MinIO Console | 9001 | Object storage admin |
| Temporal | 7233 | Durable workflow engine for autonomous missions, custom workflows, and standalone agent runs |
| Temporal UI | 8233 | Workflow inspection UI |

AutoPilot, autonomous missions, and agents run inside this same runtime; there are no separate AutoPilot targets.

!!! warning
    `.env.prod.example` uses placeholders. Set `JWT_SECRET_KEY`, database passwords, MinIO passwords, initial admin credentials, `ALLOWED_ORIGINS`, and `VNC_PUBLIC_WS_URL` before exposing a deployment.

## Backup & Recovery

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make backup` | Database-only backup | `make start` | `make backup` |
| `make backup-full` | Full backup (DB + specs + tests + PRDs + ChromaDB) | `make start` | `make backup-full` |
| `make backup-status` | Show backup status and history | `make start` | `make backup-status` |
| `make restore-list` | List available backups | `make start` | `make restore-list` |
| `make restore TS=...` | Restore from specific timestamp | `make start` | `make restore TS=20240115_143022` |
| `make restore-from-minio TS=...` | Download and restore from MinIO | `make start`, MinIO | `make restore-from-minio TS=20240115_143022` |

## Storage Management

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make storage-health` | Check storage health (DB, MinIO, local) | `make start` | `make storage-health` |
| `make archival` | Run artifact archival (30-day retention) | `make start` | `make archival` |
| `make archival-dry-run` | Preview archival without changes | `make start` | `make archival-dry-run` |
| `make minio-console` | Open MinIO console in browser | `make start` | `make minio-console` |

## Worker Containers

These targets use the `workers` Compose profile: `backend-slim` (API without local browsers), scalable `agent-worker` containers, and `custom-workflow-worker`.

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make workers-build` | Build `agent-worker`, `custom-workflow-worker`, and `backend-slim` images | Docker | `make workers-build` |
| `make workers-up` | Start production services with dedicated worker containers (default: 2 agent workers) | Docker, `.env.prod` | `make workers-up` |
| `make workers-down` | Stop worker services | Docker | `make workers-down` |
| `make workers-scale N=...` | Scale `agent-worker` containers | Docker | `make workers-scale N=4` |
| `make workers-status` | Check worker status and resource usage | Docker | `make workers-status` |
| `make workers-logs` | Tail `agent-worker`, `custom-workflow-worker`, and `backend-slim` logs | Docker | `make workers-logs` |

Default agent workers: `WORKERS=2` (overridable).

## K6 Load Test Workers

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make k6-workers-up` | Start K6 worker containers | Docker, `.env.prod` | `make k6-workers-up` |
| `make k6-workers-down` | Stop K6 workers | Docker | `make k6-workers-down` |
| `make k6-workers-scale N=...` | Scale K6 workers | Docker | `make k6-workers-scale N=3` |
| `make k6-workers-status` | Check K6 worker status and resources | Docker | `make k6-workers-status` |
| `make k6-workers-logs` | Tail K6 worker logs | Docker | `make k6-workers-logs` |

Default K6 workers: `K6_WORKERS=1` (overridable).

## Security Testing (ZAP)

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make zap-up` | Start OWASP ZAP security scanner daemon | Docker | `make zap-up` |
| `make zap-down` | Stop ZAP scanner | Docker | `make zap-down` |
| `make zap-status` | Check ZAP scanner status and API health | Docker | `make zap-status` |
| `make zap-logs` | Tail ZAP logs | Docker | `make zap-logs` |

## Database Migrations

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make db-migrate M=...` | Generate new Alembic migration | PostgreSQL, Alembic | `make db-migrate M="add user preferences"` |
| `make db-upgrade` | Run pending migrations | PostgreSQL, Alembic | `make db-upgrade` |
| `make db-downgrade` | Roll back one migration | PostgreSQL, Alembic | `make db-downgrade` |
| `make db-history` | Show migration history | PostgreSQL, Alembic | `make db-history` |
| `make alembic-upgrade` | Alias for `make db-upgrade` | PostgreSQL, Alembic | `make alembic-upgrade` |
| `make alembic-history` | Alias for `make db-history` | PostgreSQL, Alembic | `make alembic-history` |
| `make db-stamp R=...` | Stamp DB at revision (for existing DBs) | PostgreSQL, Alembic | `make db-stamp R=001` |
| `make db-demo-seed` | Seed Database Testing demo content | PostgreSQL dev database | `make db-demo-seed` |

## Linting & Testing

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make lint` | Run Python linting (ruff) + frontend linting | venv, node_modules | `make lint` |
| `make format` | Format Python code (ruff format) | venv | `make format` |
| `make test` | Run all Python tests (`pytest orchestrator/tests -v`) | venv | `make test` |
| `make backend-unit` | Run backend tests not marked `integration` | venv | `make backend-unit` |
| `make backend-integration` | Run backend tests marked `integration` | venv, services | `make backend-integration` |
| `make frontend-static` | Run frontend lint, typecheck, and production build | `web/node_modules` | `make frontend-static` |
| `make frontend-unit` | Run frontend unit tests | `web/node_modules` | `make frontend-unit` |
| `make playwright-e2e` | Run dashboard Playwright E2E tests in `tests/e2e` | Running stack, Playwright browsers | `make playwright-e2e` |
| `make playwright-generated` | Run generated Playwright tests in `tests/generated` | Generated tests, Playwright browsers | `make playwright-generated` |

`PLAYWRIGHT_PROJECT` selects the Playwright project for the last two targets (default: `chromium`).

## Documentation

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make docs-check` | Run docs drift checks and a strict MkDocs build | `requirements-docs.txt` | `make docs-check` |
| `make docs-serve` | Start MkDocs development server | `requirements-docs.txt` | `make docs-serve` |
| `make docs-build` | Build MkDocs documentation (strict mode) | `requirements-docs.txt` | `make docs-build` |
| `make docs-deploy` | Publish the built docs with `mkdocs gh-deploy` | `requirements-docs.txt`, a configured Git remote | `make docs-deploy` |

## Maintenance & Operations

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make health-check` | Hit all health endpoints and report status | Services running | `make health-check` |
| `make docker-prune` | Remove dangling images, stopped containers, build cache | Docker | `make docker-prune` |
| `make volume-sizes` | Show sizes of all Docker volumes | Docker | `make volume-sizes` |
| `make db-vacuum` | Run VACUUM ANALYZE on PostgreSQL | Docker, PostgreSQL | `make db-vacuum` |

### Upgrade Procedure

Back up with `make backup-full`, update your checkout to the new version, then
rebuild and restart with `make prod-build && make restart`. Finish with
`make deploy-check` and `make health-check`. See
[Deployment](../guides/deployment.md#upgrading-production) for rollback steps.

## Utilities

| Command | Description | Prerequisites | Example |
|---------|-------------|---------------|---------|
| `make check-env` | Validate environment configuration (.env, .env.prod, venv, deps) | -- | `make check-env` |
| `make logs` | Tail backend and frontend logs | Services running | `make logs` |
| `make stop` | Stop local dev and server Compose stacks, then any local processes (graceful then force) | -- | `make stop` |
| `make clean` | Remove run artifacts and logs (`runs/*`, `api.log`, `web.log`) | -- | `make clean` |
| `make help` | Print the built-in command summary | -- | `make help` |

## Makefile Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCKER_COMPOSE` | `docker compose` | Docker Compose command for the legacy `docker-compose.yml` targets |
| `PROD_COMPOSE` | `docker compose --env-file .env.prod -f docker-compose.prod.yml` | Production compose command |
| `APP_COMPOSE` | `$(PROD_COMPOSE) -f docker-compose.dev-override.yml` | Dev stack compose command used by `make dev` |
| `ALEMBIC_RUNNER` | `python -m orchestrator.scripts.alembic_runner` | Alembic entry point for migration targets |
| `WORKERS` | `2` | Default agent worker count for `make workers-up` |
| `K6_WORKERS` | `1` | Default K6 worker count |

Override any variable:

```bash
make workers-up WORKERS=4
make k6-workers-scale N=3
```

## Related

- [CLI Reference](cli.md)
- [Environment Variables](environment-variables.md)
