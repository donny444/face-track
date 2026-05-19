# syntax=docker/dockerfile:1.7
#
# FaceTrack FastAPI server image.
#
# Multi-stage build:
#   * builder  - installs Python deps into a virtualenv on python:3.12-slim.
#   * runtime  - copies the prebuilt venv into a minimal python:3.12-slim,
#                runs as a non-root user, and execs uvicorn via the
#                docker-entrypoint.sh shim.
#
# Notes:
#   * The Pi-side face recognition stack (opencv-python, face-recognition,
#     numpy, requests) lives in requirements.txt for local dev only. This
#     image installs ONLY the server-side deps from requirements.server.txt
#     so no dlib/cmake build chain is needed.
#   * Secrets (Firebase service account, JWT key) are mounted via Docker
#     secrets at /run/secrets/* and consumed by docker-entrypoint.sh.

# ---------- builder stage ----------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.server.txt ./requirements.server.txt
RUN pip install --upgrade pip \
 && pip install -r requirements.server.txt

# ---------- runtime stage ----------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    JWT_TOKEN_TTL_MINUTES=60 \
    VALID_EMAIL_DOMAIN=@kmitl.ac.th

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 1001 appuser \
 && useradd --system --uid 1001 --gid appuser --home /app --shell /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

COPY --chown=appuser:appuser auth_middleware.py main.py ./
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
 && mkdir -p /app/faces \
 && chown -R appuser:appuser /app

VOLUME ["/app/faces"]

USER appuser

EXPOSE 8000

# /openapi.json is unauthenticated (listed in EXEMPT_ROUTES) and does not
# touch Firestore, so it is a safe liveness probe.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail --silent --show-error http://127.0.0.1:8000/openapi.json > /dev/null || exit 1

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
