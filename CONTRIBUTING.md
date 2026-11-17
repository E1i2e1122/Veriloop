# Contributing

Conventions for working on the Veriloop codebase. Architecture, features, and operations are documented in [`docs/`](docs/index.md); start with the [system overview](docs/explanation/system-overview.md).

## Development setup

| Goal | Command |
|------|---------|
| Full stack with hot reload (Docker, recommended) | `make dev` |
| Production images locally | `make start` |
| Native backend + dashboard (no Docker) | `make setup`, then `./start-ui.sh` |
| Stop everything | `make stop` |

The test-execution engine and AI agents need Linux process features, so run them through Docker or on a Linux host. See [setup options](docs/guides/setup-options.md).

## Repository layout

| Path | Contents |
|------|----------|
| `orchestrator/` | FastAPI backend, pipeline workflows, agent runtime, CLI |
| `web/` | Next.js dashboard |
| `.claude/agents/`, `.claude/skills/` | AI agent definitions and the Playwright skill, loaded by the agent runtime and copied into Docker images |
| `.mcp.json` | MCP servers (Playwright browser control, Appium, Mermaid) available to agents |
| `tools/agent_note_mcp/` | Note-taking MCP server used during agent runs |
| `specs/` | Example and benchmark test specs |
| `scripts/` | Deployment, backup, health-check, and benchmark utilities |
| `tests/e2e/` | Playwright end-to-end tests for the dashboard |
| `docs/` | MkDocs documentation site |

## Coding conventions

**Python**: ruff enforces style (`orchestrator/pyproject.toml`): 120-character lines, double quotes, sorted imports. Run `make lint` and `make format`.

**Logging**: use `logging.getLogger(__name__)`; never `print()` in backend code. `info` for progress, `warning` for recoverable problems, `error` for failures.

**Credentials**: AI credentials load from `.env` through `orchestrator/load_env.py`; workflows call `setup_claude_env()` before using the Agent SDK. Never hard-code secrets. Specs reference secrets as `{{LOGIN_PASSWORD}}`, and generated tests read them from `process.env`.

**Agents**: run agents through `AgentRunner` (`orchestrator/utils/agent_runner.py`) for timeouts, logging, and SDK cleanup. Give each agent a least-privilege tool profile in `orchestrator/utils/agent_tool_allowlists.py`. Agents return JSON in fenced code blocks; parse it with `extract_json_from_markdown()` from `orchestrator/utils/json_utils.py`.

**Pipeline stages** run as separate subprocesses (spawned by `orchestrator/cli.py`) so each stage gets a clean Agent SDK lifecycle.

**Generated tests** prefer resilient locators: `getByRole`, then `getByLabel`, then `getByText`. Avoid CSS-class selectors.

**Frontend**: ESLint and TypeScript strict checks (`npm run lint`, `npm run typecheck` in `web/`). Use theme tokens instead of hard-coded colors so both light and dark themes work; see [Dashboard UI patterns](docs/reference/dashboard-ui-patterns.md#theming).

## Security rules

With `REQUIRE_AUTH=true` (production):

- `orchestrator/api/middleware/auth_enforcement.py` protects every route by default, including the `/artifacts` mount. Do not add public paths without a reason.
- Project permission checks fail closed: anonymous requests get `401`.
- The httpOnly session cookie is accepted only for `GET`/`HEAD` (images, downloads, event streams); all other calls use bearer tokens.
- `/settings/runtime-chat` requires the internal service token (`VERILOOP_INTERNAL_TOKEN`); the dashboard proxy strips internal headers from browser requests.
- Join user-supplied names onto directories with `safe_join` / `is_within` from `orchestrator/api/path_safety.py`, never with a bare `/`.

Details: [security model](docs/explanation/security-model.md).

## Common changes

**AI pipeline stage**: update `orchestrator/workflows/native_<stage>.py`, adjust the agent prompt in `.claude/agents/playwright-test-<stage>.md`, update `schemas/plan.schema.json` if the plan format changes, then run `python orchestrator/cli.py specs/examples/hello-world.md`.

**Dashboard feature**: add the endpoint under `orchestrator/api/`, the page under `web/src/app/(dashboard)/<route>/page.tsx`, and document it in [Web Dashboard](docs/reference/web-dashboard.md). See [adding a dashboard feature](docs/guides/adding-dashboard-feature.md).

## Checks before a pull request

| Check | Command |
|-------|---------|
| Backend unit tests (what CI runs) | `make backend-unit` |
| Frontend lint, types, and build | `make frontend-static` |
| Frontend unit tests | `make frontend-unit` |
| Dashboard end-to-end tests | `make playwright-e2e` |
| Documentation drift | `make docs-check` |

Record user-visible changes in [`CHANGELOG.md`](CHANGELOG.md) under `Unreleased`.
