#!/usr/bin/env python3
"""Wait until the local agent execution runtime is actually ready."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_ENV_FILE = Path(__file__).resolve().parent.parent / ".env.prod"


def _fetch_json(
    url: str | urllib.request.Request, timeout: float = 5.0, token: str | None = None
) -> tuple[dict[str, Any] | None, str | None]:
    request = url if isinstance(url, urllib.request.Request) else urllib.request.Request(url)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    label = request.full_url
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code} from {label}"
    except Exception as exc:
        return None, f"{label}: {exc}"

    try:
        return json.loads(body), None
    except json.JSONDecodeError as exc:
        return None, f"{label}: invalid JSON: {exc}"


def _env_file_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return values
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _credentials(env_file: Path) -> tuple[str, str] | None:
    """Credentials for the auth-protected health endpoints; env vars win over the env file."""
    file_values = _env_file_values(env_file)

    def pick(*keys: str) -> str:
        for key in keys:
            value = os.environ.get(key) or file_values.get(key, "")
            if value:
                return value
        return ""

    email = pick("VERILOOP_READY_EMAIL", "INITIAL_ADMIN_EMAIL")
    password = pick("VERILOOP_READY_PASSWORD", "INITIAL_ADMIN_PASSWORD")
    return (email, password) if email and password else None


def _login(api_base: str, credentials: tuple[str, str]) -> tuple[str | None, str | None, bool]:
    """Return (access_token, error, retryable)."""
    email, password = credentials
    request = urllib.request.Request(
        f"{api_base}/auth/login",
        data=json.dumps({"email": email, "password": password}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10.0) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # 4xx (wrong credentials, lockout, rate limit) won't fix itself, and every
        # failed attempt counts toward the account lockout, so only retry 5xx.
        return None, f"HTTP {exc.code} from {request.full_url}", exc.code >= 500
    except Exception as exc:
        return None, f"{request.full_url}: {exc}", True

    token = payload.get("access_token") if isinstance(payload, dict) else None
    if token:
        return str(token), None, False
    return None, "login response had no access_token", False


def _poller_summary(payload: dict[str, Any] | None) -> str:
    if not payload:
        return "pollers unavailable"
    pollers = payload.get("worker_pollers") or {}
    queue_status = payload.get("task_queue_status") or {}
    workflow = pollers.get("workflow", queue_status.get("workflow_pollers", 0))
    activity = pollers.get("activity", queue_status.get("activity_pollers", 0))
    return f"workflow={workflow}, activity={activity}"


def _ready(payload: dict[str, Any] | None) -> bool:
    return bool(payload and payload.get("available") is True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default="http://localhost:8001")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_FILE,
        help="Env file with INITIAL_ADMIN_EMAIL/INITIAL_ADMIN_PASSWORD, used to log in when auth is required",
    )
    args = parser.parse_args()

    api_base = args.api_base.rstrip("/")
    deadline = time.monotonic() + args.timeout
    last_status = ""
    credentials = _credentials(args.env_file)
    token: str | None = None
    login_error: str | None = None
    login_retryable = True

    while time.monotonic() < deadline:
        health, health_error = _fetch_json(f"{api_base}/health")
        # The temporal health endpoints require auth when REQUIRE_AUTH=true; log in once the API is up.
        if health is not None and credentials and token is None and login_retryable:
            token, login_error, login_retryable = _login(api_base, credentials)
        agent, agent_error = _fetch_json(f"{api_base}/api/agents/temporal/health", token=token)
        workflows, workflows_error = _fetch_json(f"{api_base}/workflows/temporal/health", token=token)

        if health is not None and _ready(agent) and _ready(workflows):
            print(
                "Agent runtime ready: "
                f"agent pollers {_poller_summary(agent)}; "
                f"workflow pollers {_poller_summary(workflows)}."
            )
            return 0

        status_parts = []
        if health_error:
            status_parts.append(f"api={health_error}")
        if login_error and token is None:
            status_parts.append(f"login={login_error}")
        if agent_error:
            status_parts.append(f"agent={agent_error}")
        elif agent:
            status_parts.append(
                f"agent={agent.get('status')} ({_poller_summary(agent)}; {agent.get('error') or 'waiting'})"
            )
        if workflows_error:
            status_parts.append(f"workflows={workflows_error}")
        elif workflows:
            status_parts.append(
                f"workflows={workflows.get('status')} ({_poller_summary(workflows)}; {workflows.get('error') or 'waiting'})"
            )
        status = "; ".join(status_parts) or "waiting for API"
        if status != last_status:
            print(f"Waiting for agent runtime: {status}")
            last_status = status
        time.sleep(args.interval)

    print("Agent runtime did not become ready before timeout.", file=sys.stderr)
    print(f"Last status: {last_status or 'no status available'}", file=sys.stderr)
    if login_error and token is None:
        print(
            "Login for the health checks failed. If the initial admin password was changed, "
            "set VERILOOP_READY_EMAIL and VERILOOP_READY_PASSWORD.",
            file=sys.stderr,
        )
    print(
        "Check logs with: make prod-logs "
        "(backend, autonomous-mission-worker, custom-workflow-worker)",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
