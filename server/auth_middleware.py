import os
from typing import Iterable, Optional

from dotenv import load_dotenv
import jwt
from fastapi import HTTPException, status, Request, Response
from firebase_admin import auth
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

load_dotenv(".env.local")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
	raise RuntimeError("JWT_SECRET_KEY environment variable must be set")
JWT_ALGORITHM = "HS256"

EXEMPT_ROUTES: dict[str, set[str] | None] = {
    "/attendances/": None,
    "/students/": {"GET", "POST"},
    "/instructors/": None,
    "/insights/": None,
    "/docs": None,
    "/openapi.json": None,
    "/redoc": None,
}

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, exempt_paths: dict[str, set[str] | None] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or {}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        allowed_methods = self.exempt_paths.get(path)
        if allowed_methods is None and path in self.exempt_paths:
            return await call_next(request)
        if isinstance(allowed_methods, set) and request.method in allowed_methods:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid authorization header")

        token = auth_header.split(" ", 1)[1]

        if not JWT_SECRET_KEY:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT secret key is not configured")

        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token payload missing email")

        try:
            user_record = auth.get_user_by_email(email)
        except auth.UserNotFoundError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        except Exception as exc:  # pragma: no cover - unexpected Firebase errors
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

        request.state.user = user_record
        request.state.token_payload = payload

        return await call_next(request)
