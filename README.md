# Veriloop

**Self-hosted AI testing agents that turn specs, PRDs, and app exploration into validated Playwright tests.**

Describe a user flow, import a PRD or OpenAPI file, or let an agent explore a running app. Veriloop plans the flow, generates Playwright TypeScript, validates it in a real browser, and repairs selector or timing failures when it can.

The output is ordinary repository code: review it, commit it, and run it in CI without any model calls.

## Requirements

- Docker with Compose v2 (recommended), or Python 3.10+ and Node.js 20+ for a local install
- **An Anthropic-compatible LLM API key** (Anthropic, Z.ai, or OpenRouter). All test-generation, healing, and exploration agents run on the Claude Agent SDK.
- Optional: an OpenAI API key for memory embeddings (semantic search), DeepEval metrics, and OpenAI-routed assistant chat

## Quick start

```bash
git clone <your-repo-url>
cd <your-repo>
cp .env.prod.example .env.prod
# Edit .env.prod: set VERILOOP_LLM_API_KEY, VERILOOP_LLM_BASE_URL, JWT_SECRET_KEY, POSTGRES_PASSWORD
make check-env
make dev
```

Open the dashboard at <http://localhost:3000>. API docs are at <http://localhost:8001/docs>.

| Command | Purpose |
|---------|---------|
| `make dev` | Full Docker development stack with local code mounted and frontend hot reload |
| `make start` | Server runtime; put your own DNS/TLS reverse proxy in front of it |
| `make stop` | Stop the running stacks |
| `make help` | List every available target |

## From spec to Playwright

Input spec:

```markdown
# Test: Login Form Validation

## Steps
1. Navigate to https://the-internet.herokuapp.com/login
2. Enter "tomsmith" into the Username field
3. Enter "SuperSecretPassword!" into the Password field
4. Click the "Login" button
5. Verify the page displays "Secure Area" heading
6. Click the "Logout" button
```

Generated output:

```ts
import { test, expect } from '@playwright/test';

test('logs in with valid credentials and logs out', async ({ page }) => {
  await page.goto('https://the-internet.herokuapp.com/login');
  await page.getByLabel('Username').fill('tomsmith');
  await page.getByLabel('Password').fill('SuperSecretPassword!');
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page.getByRole('heading', { name: 'Secure Area' })).toBeVisible();
  await page.getByRole('link', { name: 'Logout' }).click();
});
```

Run a spec from the command line:

```bash
python orchestrator/cli.py specs/examples/hello-world.md            # native pipeline
python orchestrator/cli.py specs/examples/hello-world.md --hybrid   # with extended healing
```

## Features

| Area | What it covers |
|------|----------------|
| Test generation | Plain-English specs to Playwright, browser-backed planning, validation, Smart Check reuse, hybrid healing, visual regression, reusable `@include` templates |
| PRD and coverage | PRD upload, feature extraction, requirements generation, duplicate detection, traceability matrix, gap analysis, suggested tests |
| Autonomous agents | App discovery, live browser state, generated task artifacts, recurring missions, long-running workflows, approval gates |
| Specialized testing | OpenAPI/API tests, k6 load tests, quick/Nuclei/ZAP security scans, database checks, mobile smoke flows, LLM evaluations |
| Quality intelligence | Regression batches, flaky test detection, pass-rate trends, failure classification, analytics, reports |
| Operations | Project isolation, RBAC, encrypted credentials, browser pool, Redis queues, Temporal workflows, MinIO storage, backups, schedules, GitHub/GitLab/Jira/TestRail integrations |

## Project layout

| Path | Contents |
|------|----------|
| `orchestrator/` | FastAPI backend, agent workflows, services, Alembic migrations, Python tests |
| `web/` | Next.js dashboard |
| `.claude/agents/` | Agent prompts and tool permissions |
| `specs/`, `templates/` | Example specs and reusable spec templates |
| `docs/` | MkDocs documentation (`pip install -r requirements-docs.txt && mkdocs serve`) |
| `docker/`, `nginx/`, `docker-compose*.yml` | Container images and runtime stacks |

## Development

```bash
make lint      # ruff (Python) + eslint (frontend)
make format    # ruff format
make test      # Python test suite
npm --prefix web run typecheck
npm --prefix web test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development conventions and the [documentation](docs/index.md) for architecture details.

## License

No license has been chosen yet. Until one is added, all rights are reserved.
