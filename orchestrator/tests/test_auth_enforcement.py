"""Security regression tests: global auth gate, fail-closed permissions, path safety, internal endpoints."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from orchestrator.api.middleware import auth as auth_settings
from orchestrator.api.middleware import auth_enforcement
from orchestrator.api.middleware.auth_enforcement import (
    SESSION_COOKIE_NAME,
    AuthEnforcementMiddleware,
    extract_request_token,
    is_public_path,
)
from orchestrator.api.path_safety import is_within, safe_join

VALID_TOKEN = "valid-access-token"


def _gate_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/specs")
    def list_specs():
        return {"specs": []}

    @app.post("/specs")
    def create_spec():
        return {"status": "created"}

    @app.get("/github/webhook/github")
    def webhook():
        return {"ok": True}

    @app.post("/runs/{run_id}/progress")
    def run_progress(run_id: str):
        return {"status": "updated"}

    @app.post("/runs/{run_id}/agentic-summary")
    def run_agentic_summary(run_id: str):
        return {"status": "updated"}

    @app.get("/runs/{run_id}/progress")
    def read_run_progress(run_id: str):
        return {"stage": "planning"}

    app.add_middleware(AuthEnforcementMiddleware)
    return app


@pytest.fixture
def enforced(monkeypatch):
    monkeypatch.setattr(auth_settings, "REQUIRE_AUTH", True)
    monkeypatch.setattr(
        auth_enforcement, "_active_user_id", lambda token: "user-1" if token == VALID_TOKEN else None
    )


def test_gate_is_inactive_when_auth_disabled(monkeypatch):
    monkeypatch.setattr(auth_settings, "REQUIRE_AUTH", False)
    client = TestClient(_gate_app())
    assert client.get("/specs").status_code == 200
    assert client.post("/specs").status_code == 200


def test_gate_rejects_anonymous_requests(enforced):
    client = TestClient(_gate_app())
    response = client.get("/specs")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert client.post("/specs").status_code == 401


def test_gate_rejects_invalid_tokens(enforced):
    client = TestClient(_gate_app())
    assert client.get("/specs", headers={"Authorization": "Bearer forged"}).status_code == 401


def test_gate_allows_valid_bearer_token(enforced):
    client = TestClient(_gate_app())
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    assert client.get("/specs", headers=headers).status_code == 200
    assert client.post("/specs", headers=headers).status_code == 200


def test_gate_keeps_public_paths_open(enforced):
    client = TestClient(_gate_app())
    assert client.get("/health").status_code == 200
    assert client.get("/github/webhook/github").status_code == 200


def test_session_cookie_only_authenticates_read_only_requests(enforced):
    client = TestClient(_gate_app())
    client.cookies.set(SESSION_COOKIE_NAME, VALID_TOKEN)
    assert client.get("/specs").status_code == 200
    # Cookie auth on state-changing requests would allow cross-site request forgery.
    assert client.post("/specs").status_code == 401


def test_cors_preflight_is_not_blocked(enforced):
    client = TestClient(_gate_app())
    assert client.options("/specs").status_code != 401


def test_public_path_matching():
    assert is_public_path("/health")
    assert is_public_path("/health/storage")
    assert is_public_path("/auth/login")
    assert is_public_path("/auth/status")
    assert not is_public_path("/auth/me")
    assert not is_public_path("/settings/runtime-chat")
    assert not is_public_path("/artifacts/run-1/report.html")
    assert not is_public_path("/healthcheck-bypass")


def test_extract_request_token_prefers_bearer_header():
    scope = {
        "method": "GET",
        "headers": [(b"authorization", b"Bearer header-token"), (b"cookie", f"{SESSION_COOKIE_NAME}=cookie-token".encode())],
    }
    assert extract_request_token(scope) == "header-token"


def test_extract_request_token_ignores_cookie_on_unsafe_methods():
    scope = {"method": "DELETE", "headers": [(b"cookie", f"{SESSION_COOKIE_NAME}=cookie-token".encode())]}
    assert extract_request_token(scope) is None


def test_check_project_access_fails_closed_when_auth_required(monkeypatch):
    from orchestrator.api.middleware.permissions import check_project_access

    monkeypatch.setattr(auth_settings, "REQUIRE_AUTH", True)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(check_project_access("default", None, ["admin"], session=None))
    assert exc.value.status_code == 401


def test_check_project_access_allows_anonymous_in_development(monkeypatch):
    from orchestrator.api.middleware.permissions import check_project_access

    monkeypatch.setattr(auth_settings, "REQUIRE_AUTH", False)
    assert asyncio.run(check_project_access("default", None, ["admin"], session=None)) is None


@pytest.mark.parametrize("name", ["../.env", "../../etc/passwd", "/etc/passwd", "a/../../outside.md"])
def test_safe_join_rejects_traversal(tmp_path, name):
    base = tmp_path / "specs"
    base.mkdir()
    with pytest.raises(HTTPException) as exc:
        safe_join(base, name)
    assert exc.value.status_code == 400


def test_safe_join_allows_nested_paths(tmp_path):
    base = tmp_path / "specs"
    base.mkdir()
    joined = safe_join(base, "folder/login.md")
    assert joined == base / "folder" / "login.md"
    assert is_within(base, joined)


def test_runtime_chat_requires_internal_token_when_auth_enforced(monkeypatch):
    from orchestrator.api import settings as settings_api

    monkeypatch.delenv("VERILOOP_INTERNAL_TOKEN", raising=False)
    monkeypatch.setattr(auth_settings, "REQUIRE_AUTH", True)
    # The well-known header alone is never enough once authentication is enforced.
    assert not settings_api._internal_chat_caller_allowed("web-chat", None)

    monkeypatch.setenv("VERILOOP_INTERNAL_TOKEN", "s3cret")
    assert not settings_api._internal_chat_caller_allowed("web-chat", "wrong")
    assert not settings_api._internal_chat_caller_allowed("other", "s3cret")
    assert settings_api._internal_chat_caller_allowed("web-chat", "s3cret")


def test_runtime_chat_header_only_allowed_in_development(monkeypatch):
    from orchestrator.api import settings as settings_api

    monkeypatch.delenv("VERILOOP_INTERNAL_TOKEN", raising=False)
    monkeypatch.setattr(auth_settings, "REQUIRE_AUTH", False)
    assert settings_api._internal_chat_caller_allowed("web-chat", None)
    assert not settings_api._internal_chat_caller_allowed(None, None)


def test_run_callbacks_accept_the_internal_token(enforced, monkeypatch):
    monkeypatch.setenv("VERILOOP_INTERNAL_TOKEN", "s3cret")
    client = TestClient(_gate_app())
    headers = {"X-Veriloop-Internal-Token": "s3cret"}

    assert client.post("/runs/2026-11-17_15-41-32/progress", headers=headers).status_code == 200
    assert client.post("/runs/2026-11-17_15-41-32/agentic-summary", headers=headers).status_code == 200


def test_run_callbacks_reject_a_missing_or_wrong_internal_token(enforced, monkeypatch):
    client = TestClient(_gate_app())

    monkeypatch.delenv("VERILOOP_INTERNAL_TOKEN", raising=False)
    assert client.post("/runs/r1/progress").status_code == 401
    assert client.post("/runs/r1/progress", headers={"X-Veriloop-Internal-Token": ""}).status_code == 401

    monkeypatch.setenv("VERILOOP_INTERNAL_TOKEN", "s3cret")
    assert client.post("/runs/r1/progress").status_code == 401
    assert client.post("/runs/r1/progress", headers={"X-Veriloop-Internal-Token": "wrong"}).status_code == 401
    non_ascii = {"X-Veriloop-Internal-Token": "s3crét".encode("latin-1")}
    assert client.post("/runs/r1/progress", headers=non_ascii).status_code == 401


def test_internal_token_does_not_open_other_routes(enforced, monkeypatch):
    monkeypatch.setenv("VERILOOP_INTERNAL_TOKEN", "s3cret")
    client = TestClient(_gate_app())
    headers = {"X-Veriloop-Internal-Token": "s3cret"}

    assert client.post("/specs", headers=headers).status_code == 401
    assert client.get("/specs", headers=headers).status_code == 401
    assert client.get("/runs/r1/progress", headers=headers).status_code == 401


def test_full_app_enforces_auth_on_previously_open_routes(monkeypatch):
    from orchestrator.api.main import app

    monkeypatch.setattr(auth_settings, "REQUIRE_AUTH", True)
    client = TestClient(app, raise_server_exceptions=False)

    for path in ("/specs", "/runs", "/settings", "/settings/runtime-chat", "/api-testing/specs"):
        assert client.get(path, headers={"X-Veriloop-Internal-Caller": "web-chat"}).status_code == 401, path
    assert client.get("/artifacts/does-not-matter.txt").status_code == 401

    status = client.get("/auth/status")
    assert status.status_code == 200
    assert status.json() == {"require_auth": True, "authenticated": False, "user_id": None, "is_superuser": False}


def test_coding_agent_repo_root_defaults_to_project():
    from orchestrator.services.coding_agent import DEFAULT_REPO_ROOT

    assert (Path(DEFAULT_REPO_ROOT) / "orchestrator" / "cli.py").exists()
