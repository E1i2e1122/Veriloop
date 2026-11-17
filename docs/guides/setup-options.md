# How to Choose a Setup Path

![Veriloop dashboard overview after setup is complete](../assets/ui/dashboard-overview.png)

<p class="caption">Veriloop dashboard overview after setup is complete.</p>


Choose the smallest setup that matches what you need to prove. You can move from one path to another later without changing how specs are written.

## Setup Matrix

| Path | Use when | Database | Main command | Trade-off |
|------|----------|----------|--------------|-----------|
| Local development | You want the dashboard, queues, storage, VNC, and frontend hot reload locally | PostgreSQL | `make dev` | More RAM and disk usage |
| Production/server | You are running behind your own DNS/TLS/reverse proxy in external-nginx mode | PostgreSQL | `make start` | Requires real secrets, backups, and operational care |
| Dedicated worker containers | You need agent and workflow execution isolated from the API container | PostgreSQL | `make workers-up` | More containers to monitor |
| Repo-managed nginx | You explicitly need the legacy single-host nginx container | PostgreSQL | `VERILOOP_ENABLE_REPO_NGINX=1 make prod-up` | Guarded; not the recommended server path |

## Recommended Defaults

Start with **Local development** (`make dev`) to evaluate the product, security scanning, backup storage, VNC live browser viewing, Redis-backed queues, multi-user behavior, or source changes. It uses `docker-compose.prod.yml` plus `docker-compose.dev-override.yml`, so it matches the server runtime while mounting your local code.

Use **Local native dev** (`make setup`, then the CLI or `start-ui.sh`) only when you are debugging backend/frontend behavior closely outside Docker. It is the most flexible path, but it asks more of your host machine.

Use **Production/server** for a real team deployment. Server deployments are external-nginx mode: your own DNS/TLS/reverse proxy forwards to the Compose app, `make start` starts the app runtime from `docker-compose.prod.yml`, and the repo-managed nginx container stays disabled unless explicitly requested.

## Prerequisites by Path

| Path | Required |
|------|----------|
| Local development | Docker Compose v2, 8 GB+ available Docker memory. `make dev` can create `.env.prod` from `.env.prod.example` for local evaluation; edit it with your provider token before real use. |
| Local native dev | Python 3.10+, Node.js 20+, Playwright browsers, optional Docker for PostgreSQL |
| Production/server | Docker Compose v2, `.env.prod` with rotated secrets, backup location, your own reverse proxy/TLS, same-origin browser API routing |

## Upgrade Path

1. Evaluate with `make dev` on a workstation.
2. Use Production/server external-nginx mode (`make start`) for a team deployment.
3. Add dedicated worker containers (`make workers-up`) when agent or workflow load contends with the API.
4. Add K6 workers (`make k6-workers-up`) when load tests need distributed execution.

## Verification

After starting any setup:

```bash
make check-env
make health-check
```

Then open the dashboard at [http://localhost:3000](http://localhost:3000) and run a small spec from `specs/examples/hello-world.md`.

For server deployments, also verify that `VERILOOP_PUBLIC_API_URL=` and `NEXT_PUBLIC_API_URL=` are blank, `VNC_PUBLIC_WS_URL` points to your public `/websockify` route, and direct `3000`, `8001`, and `6080` ports are private to the app server or trusted network.

## Related

- [Getting Started](../tutorials/getting-started.md)
- [Deployment](deployment.md)
- [Troubleshooting](troubleshooting.md)
