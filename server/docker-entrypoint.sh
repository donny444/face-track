#!/bin/sh
# FaceTrack server entrypoint.
#
# Responsibilities:
#   1. Materialize the Firebase service account secret into /app/firebase.json
#      because main.py reads the credentials file relative to the working dir.
#   2. Load the JWT secret from /run/secrets/jwt_secret into JWT_SECRET_KEY
#      (auth_middleware.py reads it from the environment at import time).
#   3. Exec uvicorn so it becomes PID 1 and receives signals correctly.
set -eu

FIREBASE_SECRET_PATH="${FIREBASE_SECRET_PATH:-/run/secrets/firebase_credentials}"
JWT_SECRET_PATH="${JWT_SECRET_PATH:-/run/secrets/jwt_secret}"
FIREBASE_TARGET="/app/firebase.json"

if [ ! -f "$FIREBASE_SECRET_PATH" ]; then
	echo "[entrypoint] ERROR: Firebase credentials secret not found at $FIREBASE_SECRET_PATH" >&2
	echo "[entrypoint]        Provide ./server/firebase.json on the host; docker compose mounts it as a secret." >&2
	exit 1
fi

cp "$FIREBASE_SECRET_PATH" "$FIREBASE_TARGET"
chmod 600 "$FIREBASE_TARGET" || true

if [ -f "$JWT_SECRET_PATH" ]; then
	JWT_SECRET_KEY="$(tr -d '\r\n' < "$JWT_SECRET_PATH")"
	export JWT_SECRET_KEY
elif [ -z "${JWT_SECRET_KEY:-}" ]; then
	echo "[entrypoint] ERROR: JWT secret not found at $JWT_SECRET_PATH and JWT_SECRET_KEY env var is unset." >&2
	echo "[entrypoint]        Create ./secrets/jwt_secret.txt or set JWT_SECRET_KEY in the environment." >&2
	exit 1
fi

mkdir -p /app/faces

exec uvicorn main:app --host 0.0.0.0 --port 8000 "$@"
