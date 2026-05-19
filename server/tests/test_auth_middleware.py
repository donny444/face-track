"""Tests for ``server/auth_middleware.py``.

``AuthMiddleware`` raises :class:`fastapi.HTTPException` inside its
``dispatch`` method.  Because ``BaseHTTPMiddleware`` runs *outside* the
``ExceptionMiddleware`` layer that FastAPI uses to turn ``HTTPException``
into a JSON response, those exceptions surface as raw Python exceptions
when driven through ``TestClient``.  Rather than fighting that, the tests
below exercise ``dispatch`` directly with stub request / call_next
objects, which is the standard unit-test pattern for ASGI middleware.

A couple of integration-style tests still use a real ``TestClient`` to
verify that exempt routes are forwarded through to the inner app.
"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import auth_middleware as auth_middleware_module
from auth_middleware import (
    AuthMiddleware,
    EXEMPT_ROUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _token(email: str = "prof@kmitl.ac.th", *, exp_offset_min: int = 60) -> str:
    payload = {
        "sub": email,
        "email": email,
        "iat": int(datetime.now(tz=timezone.utc).timestamp()),
        "exp": int(
            (datetime.now(tz=timezone.utc) + timedelta(minutes=exp_offset_min)).timestamp()
        ),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _request(method: str, path: str, *, headers: dict[str, str] | None = None):
    """Build a stub object that quacks like ``starlette.requests.Request``."""

    headers = headers or {}
    state = SimpleNamespace()
    return SimpleNamespace(
        method=method,
        url=SimpleNamespace(path=path),
        headers=SimpleNamespace(get=headers.get),
        state=state,
    )


async def _ok_call_next(request):
    """A ``call_next`` that mimics a successful downstream response."""

    return SimpleNamespace(status_code=200, body=b"")


@pytest.fixture
def middleware():
    return AuthMiddleware(MagicMock(name="asgi_app"), exempt_paths=EXEMPT_ROUTES)


@pytest.fixture
def patched_auth(monkeypatch):
    """Patch the ``auth`` symbol used inside ``auth_middleware``."""

    fresh = MagicMock(name="middleware-auth")
    fresh.UserNotFoundError = sys.modules["firebase_admin.auth"].UserNotFoundError
    monkeypatch.setattr(auth_middleware_module, "auth", fresh)
    return fresh


# ---------------------------------------------------------------------------
# Direct-dispatch tests
# ---------------------------------------------------------------------------
class TestExemptRoutes:
    @pytest.mark.parametrize("method", ["GET", "POST"])
    def test_students_get_and_post_are_exempt(self, middleware, method):
        request = _request(method, "/students/")
        response = asyncio.run(middleware.dispatch(request, _ok_call_next))
        assert response.status_code == 200

    def test_delete_students_is_NOT_exempt(self, middleware):
        request = _request("DELETE", "/students/")
        with pytest.raises(HTTPException) as exc:
            asyncio.run(middleware.dispatch(request, _ok_call_next))
        assert exc.value.status_code == 401

    def test_attendances_is_fully_exempt(self, middleware):
        request = _request("DELETE", "/attendances/")
        response = asyncio.run(middleware.dispatch(request, _ok_call_next))
        assert response.status_code == 200

    def test_options_always_passes_through(self, middleware):
        request = _request("OPTIONS", "/protected/")
        response = asyncio.run(middleware.dispatch(request, _ok_call_next))
        assert response.status_code == 200


class TestAuthHeader:
    def test_missing_header_returns_401(self, middleware):
        request = _request("GET", "/protected/")
        with pytest.raises(HTTPException) as exc:
            asyncio.run(middleware.dispatch(request, _ok_call_next))
        assert exc.value.status_code == 401
        assert "Missing or invalid" in exc.value.detail

    def test_non_bearer_scheme_returns_401(self, middleware):
        request = _request("GET", "/protected/", headers={"Authorization": "Basic abc"})
        with pytest.raises(HTTPException) as exc:
            asyncio.run(middleware.dispatch(request, _ok_call_next))
        assert exc.value.status_code == 401

    def test_valid_jwt_passes_through(self, middleware, patched_auth):
        user_record = MagicMock(uid="prof")
        patched_auth.get_user_by_email.return_value = user_record

        token = _token()
        request = _request("GET", "/protected/", headers={"Authorization": f"Bearer {token}"})
        response = asyncio.run(middleware.dispatch(request, _ok_call_next))

        assert response.status_code == 200
        patched_auth.get_user_by_email.assert_called_once_with("prof@kmitl.ac.th")
        # The middleware enriches request.state with the verified user.
        assert request.state.user is user_record
        assert request.state.token_payload["email"] == "prof@kmitl.ac.th"

    def test_expired_token_returns_401(self, middleware, patched_auth):
        payload = {
            "sub": "prof@kmitl.ac.th",
            "email": "prof@kmitl.ac.th",
            "iat": int(time.time()) - 7200,
            "exp": int(time.time()) - 3600,
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        request = _request("GET", "/protected/", headers={"Authorization": f"Bearer {token}"})
        with pytest.raises(HTTPException) as exc:
            asyncio.run(middleware.dispatch(request, _ok_call_next))
        assert exc.value.status_code == 401
        assert "expired" in exc.value.detail.lower()

    def test_invalid_token_returns_401(self, middleware, patched_auth):
        request = _request(
            "GET", "/protected/", headers={"Authorization": "Bearer not-a-real-jwt"}
        )
        with pytest.raises(HTTPException) as exc:
            asyncio.run(middleware.dispatch(request, _ok_call_next))
        assert exc.value.status_code == 401
        assert "invalid" in exc.value.detail.lower()

    def test_payload_missing_email_returns_401(self, middleware, patched_auth):
        payload = {
            "sub": "prof@kmitl.ac.th",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        request = _request("GET", "/protected/", headers={"Authorization": f"Bearer {token}"})
        with pytest.raises(HTTPException) as exc:
            asyncio.run(middleware.dispatch(request, _ok_call_next))
        assert exc.value.status_code == 401
        assert "missing email" in exc.value.detail.lower()

    def test_user_not_found_returns_401(self, middleware, patched_auth):
        patched_auth.get_user_by_email.side_effect = patched_auth.UserNotFoundError(
            "no such user"
        )
        token = _token()
        request = _request("GET", "/protected/", headers={"Authorization": f"Bearer {token}"})
        with pytest.raises(HTTPException) as exc:
            asyncio.run(middleware.dispatch(request, _ok_call_next))
        assert exc.value.status_code == 401
        assert exc.value.detail == "User not found"


# ---------------------------------------------------------------------------
# Integration smoke test: exempt routes are forwarded all the way through.
# ---------------------------------------------------------------------------
class TestIntegration:
    def test_exempt_route_through_real_app(self):
        app = FastAPI()
        app.add_middleware(AuthMiddleware, exempt_paths=EXEMPT_ROUTES)

        @app.get("/students/")
        async def get_students():
            return {"ok": True}

        with TestClient(app) as http:
            assert http.get("/students/").status_code == 200
