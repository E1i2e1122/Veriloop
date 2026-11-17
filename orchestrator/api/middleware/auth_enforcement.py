"""
Global authentication gate.

When ``REQUIRE_AUTH=true`` every HTTP request must carry a valid access token,
except for a small allowlist of public endpoints (login, token refresh, health
checks, signed CI webhooks, API docs). This closes the gap where individual
routers forgot to declare an auth dependency.

Token sources:
- ``Authorization: Bearer <token>`` header (all methods)
- the ``access_token`` session cookie, for safe read-only methods only
  (GET/HEAD). Browsers cannot attach headers to ``<img>``, ``<video>``,
  download links, or ``EventSource`` streams, so the cookie covers those;
  restricting it to read-only methods avoids cross-site request forgery.
"""

from __future__ import annotations

import logging
from http.cookies import SimpleCookie

from sqlmodel import Session
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from . import auth as auth_settings

logger = logging.getLogger(__name__)

SESSION_COOKIE_NAME = "access_token"

PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/auth/login",
        "/auth/register",
        "/auth/refresh",
        "/auth/logout",
        "/auth/status",
        "/github/webhook/github",
        "/gitlab/webhook/gitlab",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/openapi.json",
    }
)
PUBLIC_PREFIXES = ("/health/",)
SAFE_METHODS = frozenset({"GET", "HEAD"})


def is_public_path(path: str) -> bool:
    normalized = path.rstrip("/") or "/"
    return normalized in PUBLIC_PATHS or any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def _header(scope: Scope, name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key == name:
            return value.decode("latin-1")
    return None


def extract_request_token(scope: Scope) -> str | None:
    """Return the access token from the Authorization header, or the session cookie on GET/HEAD."""
    authorization = _header(scope, b"authorization")
    if authorization:
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() == "bearer" and credentials.strip():
            return credentials.strip()

    if scope.get("method", "GET").upper() in SAFE_METHODS:
        raw_cookie = _header(scope, b"cookie")
        if raw_cookie:
            cookie = SimpleCookie()
            try:
                cookie.load(raw_cookie)
            except Exception:
                return None
            morsel = cookie.get(SESSION_COOKIE_NAME)
            if morsel and morsel.value:
                return morsel.value
    return None


def _active_user_id(token: str) -> str | None:
    """Validate an access token and return the active user's id, or None."""
    from ..db import engine
    from ..models_auth import User
    from ..security import decode_token

    token_data = decode_token(token)
    if not token_data or token_data.type != "access":
        return None
    with Session(engine) as session:
        user = session.get(User, token_data.sub)
        if not user or not user.is_active:
            return None
        return user.id


class AuthEnforcementMiddleware:
    """Reject unauthenticated HTTP requests to non-public paths when REQUIRE_AUTH is enabled."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or not auth_settings.REQUIRE_AUTH
            or scope.get("method") == "OPTIONS"
            or is_public_path(scope.get("path", ""))
        ):
            await self.app(scope, receive, send)
            return

        token = extract_request_token(scope)
        user_id = await run_in_threadpool(_active_user_id, token) if token else None
        if not user_id:
            response = JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"},
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        scope.setdefault("state", {})["auth_user_id"] = user_id
        await self.app(scope, receive, send)
