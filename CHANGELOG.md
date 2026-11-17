# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Light and dark themes with a toggle in the sidebar, mobile top bar, and sign-in pages; the choice persists per browser. Charts, the code editor, toasts, and status colors follow the active theme.
- New product logo and favicon.
- Unit tests for the Temporal connection fail-fast window.

### Changed

- The product is now named **Veriloop** ("Autonomous AI Test Automation"). Configuration uses the `VERILOOP_` prefix (for example `VERILOOP_LLM_API_KEY`, `VERILOOP_INTERNAL_TOKEN`), and Docker images, containers, storage buckets, Temporal task queues, and the subset-test CI workflow (`veriloop-subset-tests.yml`) use the new name.
- Redesigned sign-in and registration pages: consistent spacing, labelled inputs with icons, show/hide password, live password requirements, and inline validation.
- Floating AI assistant button: compact gradient button with its keyboard shortcut in a hover/focus tooltip; hidden on the full-page assistant, and toasts no longer appear underneath it.
- Thin, theme-aware scrollbars; the sidebar scrollbar stays hidden until the navigation is hovered.
- Tailwind CSS utilities are now compiled (they were previously inert), and element base styles moved into a cascade layer so spacing utilities apply.
- Form controls use the app typeface; select menus always reserve room for their arrow.
- Reporting shows a neutral dash instead of a red 0% when there are no runs yet.
- The "Temporal unavailable" notice is styled as a warning.

### Fixed

- Agent queue status and other Temporal health checks no longer wait about 2 seconds on every request while Temporal is down; failed connections are retried after 10 seconds.
- AI assistant welcome cards align in their grid, the welcome screen no longer clips inside the chat panel, and the scroll-to-bottom button hides when already at the bottom.
- Toasts were rendered twice while the assistant panel was open.

### Removed

- AI coding-assistant guides (`CLAUDE.md`, `AGENTS.md`). They are no longer copied into the backend image or loaded into agent context as project instructions; development conventions now live in `CONTRIBUTING.md`.
- Unused example prompts in `.claude/prompts/`.
- Outdated VS Code dev container configuration.

## [0.1.0]

Initial baseline.

### Security

- Global authentication gate: with `REQUIRE_AUTH=true`, every API route and the `/artifacts` mount require a valid token; only login/refresh/logout, `/auth/status`, health checks, signed CI webhooks, and API docs are public.
- Project permission checks fail closed for anonymous requests when authentication is enforced.
- The AI assistant's runtime LLM settings require a server-side shared secret (`VERILOOP_INTERNAL_TOKEN`); the dashboard proxy strips internal headers from browser requests, and platform-wide settings changes are superuser-only.
- Assistant chat and tool-execution routes reject anonymous callers when authentication is enforced.
- Path traversal protection (`safe_join`) for spec, test, script, and artifact file endpoints.
- Live browser view (VNC) password support via `VNC_PASSWORD`, served to superusers only.
- Open-redirect protection on the login and registration pages.
- Assistant action tokens no longer fall back to a well-known signing secret.
- Password hashing uses `bcrypt` directly (replaces the unmaintained `passlib`; existing hashes remain valid).

### Added

- Route-level loading, error, and 404 pages; mobile navigation drawer; toast notifications instead of browser alerts.
- `.gitattributes` enforcing LF line endings so scripts and Docker builds work from Windows checkouts.
- Frontend unit tests run in CI.

### Changed

- Python 3.12 for CI and Docker images (Python 3.10 reached end of life); Node.js 22 in CI.
- Fonts are bundled locally instead of fetched from Google at build time.
- API responses use forward-slash relative paths on every platform.
- `--split` works on its own (no longer requires the removed standard pipeline).

### Fixed

- Startup run sync no longer imports infrastructure folders under `runs/` as test runs.
- `/regression/batches/trend` was unreachable (shadowed by `/regression/batches/{batch_id}`).
- Pages no longer call project-scoped APIs before the active project has loaded.
- Agents history no longer reports an error when an in-flight request is superseded.
- The coding agent defaults to this project's root instead of a hard-coded developer path.

### Removed

- Legacy standard pipeline, `--validate-only`/`--dry-run`, the unused browser-worker container and job queue, Kubernetes and Docker Swarm manifests, extra Compose variants, and the private deploy kit.
