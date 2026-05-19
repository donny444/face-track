"""Shared pytest fixtures and import-time shims for the FastAPI server tests.

This module patches `firebase_admin` (and friends) *before* importing the
server modules so that we don't need real Firebase credentials to run the
test suite.  It also exposes a `client` fixture that yields a fresh
`fastapi.testclient.TestClient` with isolated mock `db` / `auth` objects.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Environment bootstrap.  Must happen BEFORE any server module is imported,
# because `auth_middleware.py` reads JWT_SECRET_KEY at import-time and
# `main.py` calls `firebase_admin.credentials.Certificate("firebase.json")`.
# ---------------------------------------------------------------------------
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests")
os.environ.setdefault("JWT_TOKEN_TTL_MINUTES", "60")
os.environ.setdefault("VALID_EMAIL_DOMAIN", "@kmitl.ac.th")
os.environ.setdefault("SERVER_API_BASE_URL", "http://test-server")
os.environ.setdefault("FACE_DIR", "faces")

# Ensure the `server/` directory is on `sys.path` so that `from main import app`
# and `from auth_middleware import ...` resolve when pytest is invoked from
# elsewhere.
SERVER_DIR = Path(__file__).resolve().parent.parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

# `main.py` calls `app.mount("/faces", StaticFiles(directory="faces"), ...)`
# at import time; the directory must therefore exist relative to CWD.
os.makedirs("faces", exist_ok=True)


# ---------------------------------------------------------------------------
# Stub external SDKs so importing the server modules has no side-effects.
# ---------------------------------------------------------------------------
def _install_firebase_shims() -> None:
    """Insert fake ``firebase_admin`` and ``google.cloud.firestore_v1`` modules."""

    # firebase_admin --------------------------------------------------------
    fake_firebase_admin = types.ModuleType("firebase_admin")
    fake_firebase_admin.initialize_app = MagicMock()

    # credentials submodule with Certificate(...) factory.
    fake_credentials = types.ModuleType("firebase_admin.credentials")
    fake_credentials.Certificate = MagicMock(return_value=MagicMock(name="Certificate"))
    fake_firebase_admin.credentials = fake_credentials

    # auth submodule.  UserNotFoundError MUST be a real exception class
    # because production code does `except auth.UserNotFoundError:`.
    fake_auth = types.ModuleType("firebase_admin.auth")

    class _UserNotFoundError(Exception):
        """Mirror of firebase_admin.auth.UserNotFoundError used by tests."""

    fake_auth.UserNotFoundError = _UserNotFoundError
    fake_auth.create_user = MagicMock()
    fake_auth.get_user_by_email = MagicMock()
    fake_auth.delete_user = MagicMock()
    fake_firebase_admin.auth = fake_auth

    # firestore submodule.  Needs `.client()` and `.Query.DESCENDING`.
    fake_firestore = types.ModuleType("firebase_admin.firestore")
    fake_firestore.client = MagicMock(return_value=MagicMock(name="firestore_client"))

    class _Query:  # pragma: no cover - simple constants holder
        ASCENDING = "ASCENDING"
        DESCENDING = "DESCENDING"

    fake_firestore.Query = _Query
    fake_firebase_admin.firestore = fake_firestore

    sys.modules["firebase_admin"] = fake_firebase_admin
    sys.modules["firebase_admin.credentials"] = fake_credentials
    sys.modules["firebase_admin.auth"] = fake_auth
    sys.modules["firebase_admin.firestore"] = fake_firestore

    # google.cloud.firestore_v1 (only FieldFilter is consumed) --------------
    if "google" not in sys.modules:
        sys.modules["google"] = types.ModuleType("google")
    if "google.cloud" not in sys.modules:
        sys.modules["google.cloud"] = types.ModuleType("google.cloud")

    fake_gcfs = types.ModuleType("google.cloud.firestore_v1")
    fake_gcfs.FieldFilter = MagicMock(name="FieldFilter")
    sys.modules["google.cloud.firestore_v1"] = fake_gcfs


_install_firebase_shims()


# Importing here (after the shims) is intentional.  Tests can import these
# objects directly from `tests.conftest` if they want, but the common path
# is to rely on the fixtures below.
from fastapi.testclient import TestClient  # noqa: E402

import main as main_module  # noqa: E402
import auth_middleware as auth_middleware_module  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def auth_mock(monkeypatch):
    """Replace the `auth` symbol used by ``main`` with a fresh mock.

    The mock preserves the real ``UserNotFoundError`` class so that production
    code can still raise / catch it.
    """

    fresh = MagicMock(name="firebase_auth")
    fresh.UserNotFoundError = sys.modules["firebase_admin.auth"].UserNotFoundError
    monkeypatch.setattr(main_module, "auth", fresh)
    monkeypatch.setattr(auth_middleware_module, "auth", fresh)
    return fresh


@pytest.fixture
def db_mock(monkeypatch):
    """Replace the Firestore client used by ``main`` with a fresh MagicMock."""

    fresh = MagicMock(name="firestore_db")
    monkeypatch.setattr(main_module, "db", fresh)
    return fresh


@pytest.fixture
def client(auth_mock, db_mock):
    """A `TestClient` wired up with isolated mock Firestore/auth objects."""

    with TestClient(main_module.app) as test_client:
        yield test_client


@pytest.fixture
def app():
    """Expose the raw FastAPI app for tests that build their own client."""

    return main_module.app
