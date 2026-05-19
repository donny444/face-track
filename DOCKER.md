# FaceTrack — Docker Compose stack

This document covers running FaceTrack locally with Docker Compose. The
compose file defines three services (`server`, `web`, `nginx`) wired on a
private bridge network, a named volume for face uploads, and Docker secrets
for the Firebase service account and the JWT signing key.

The Raspberry-Pi face detection client (`server/face_detection.py`) is
intentionally **not** part of this stack — see [below](#raspberry-pi-client).

## Topology

```
                    ┌─────────────────────────────────────┐
                    │            facetrack-net            │
                    │                                     │
   browser ──► nginx:80 ──► web:3000   (Next.js, SSR/UI)  │
                    │     └► server:8000  (FastAPI)       │
                    │                  │                  │
                    │                  ▼                  │
                    │           face_uploads (volume)     │
                    │           /run/secrets/* (RO)       │
                    └─────────────────────────────────────┘
```

| Service  | Image                  | Internal port | Host port | Purpose                                |
| -------- | ---------------------- | ------------- | --------- | -------------------------------------- |
| `server` | `face-track/server:dev`| `8000`        | —         | FastAPI app (auth, students, insights) |
| `web`    | `face-track/web:dev`   | `3000`        | —         | Next.js UI (Chart.js, Redux, Bootstrap)|
| `nginx`  | `nginx:alpine`         | `80`          | `80`      | Reverse proxy for `/api/*` and `/`     |

Only `nginx` publishes a port on the host. `server` and `web` are reachable
only through the proxy (and through the docker network).

## Prerequisites

* Docker Desktop running (Windows / macOS) or Docker Engine + Compose v2
  (Linux). Verify with `docker compose version`.
* `./server/firebase.json` — Firebase Admin SDK service-account JSON.
  Download from the Firebase console (Project settings → Service accounts →
  Generate new private key).
* `./secrets/jwt_secret.txt` — single-line random string used as
  `JWT_SECRET_KEY`. A starter dummy sits at
  `./secrets/jwt_secret.example.txt`. To generate a strong value:

  ```sh
  python -c "import secrets; print(secrets.token_urlsafe(48))" > secrets/jwt_secret.txt
  ```

* Optional `.env` — copy `.env.docker.example` and tweak. Compose picks it
  up automatically from the project directory.

## Bring the stack up

```sh
docker compose up --build
```

(Add `-d` to detach.) On first run the images build from scratch, which can
take a few minutes — the server image installs Python deps and the web
image runs `npm ci` + `next build`.

Once healthy, browse to <http://localhost/>. The Next.js client talks to
`http://localhost/api`, which `nginx` rewrites to `http://server:8000/`
inside the docker network.

### Bring it down

```sh
docker compose down            # stop containers, keep volume
docker compose down -v         # ALSO drop face_uploads (deletes uploaded faces!)
```

### Just validate the YAML

```sh
docker compose config --quiet
```

This is what was run on this branch — see the commit message. A full
`docker compose up --build` was deliberately **not** executed (image builds
are slow and network-flaky).

## Secrets

Both secrets are passed to the `server` container as files under
`/run/secrets/`. The container's entrypoint
(`server/docker-entrypoint.sh`) materializes them into the runtime
locations the application expects:

| Compose secret name    | Host file                       | Where the app reads it             |
| ---------------------- | ------------------------------- | ---------------------------------- |
| `firebase_credentials` | `./server/firebase.json`        | Copied to `/app/firebase.json` (read by `main.py`'s `credentials.Certificate("firebase.json")`). |
| `jwt_secret`           | `./secrets/jwt_secret.txt`      | Exported as `JWT_SECRET_KEY` env var (read by `auth_middleware.py`).        |

`./secrets/jwt_secret.txt` is in `.gitignore` and must never be committed.
`./server/firebase.json` was already in `.gitignore` before this branch.

## Environment

Variables loaded by compose from `.env` (or `.env.docker.example` as
reference):

| Variable                   | Consumer | Notes |
| -------------------------- | -------- | ----- |
| `JWT_TOKEN_TTL_MINUTES`    | server   | Lifetime of issued instructor JWTs. Default `60`. |
| `VALID_EMAIL_DOMAIN`       | server   | Required email suffix. Default `@kmitl.ac.th`. |
| `NEXT_PUBLIC_SERVER_URL`   | web (build-time) | Baked into the JS bundle at build time. Default `http://localhost/api`. Rebuild `web` if changed. |

## Volumes

* `face_uploads` → `/app/faces` in the `server` container. Persists
  registration photos written by `main.py`'s `/students/` upload handler
  across container recreations.

## Image notes

### `server/Dockerfile`

* Multi-stage build on `python:3.12-slim` (builder installs to a venv;
  runtime copies only the venv + source).
* Installs `server/requirements.server.txt`, **not** the dev
  `requirements.txt` — the Pi-only packages (`opencv-python`,
  `face-recognition`, `numpy`, `requests`) are deliberately excluded, which
  avoids the heavy `dlib`/`cmake` toolchain.
* Runs as non-root user `appuser` (UID 1001).
* Healthcheck hits `/openapi.json` (an exempt route that requires no
  Firestore access).

### Root `Dockerfile` (web)

* Multi-stage build on `node:20-alpine`: `deps` → `builder` → `runtime`.
* `NEXT_PUBLIC_SERVER_URL` is a build-arg; Next.js inlines `NEXT_PUBLIC_*`
  at build time, so changing it requires `docker compose build web`.
* If `src/data/global_variables.ts` is absent in the build context (it is
  gitignored), the builder stubs it to read `NEXT_PUBLIC_SERVER_URL`.
* Runs as non-root user `nextjs` (UID 1001).

### `docker/nginx/default.conf`

Intentionally minimal — just enough to validate the topology
(`/api/* → server:8000/*` with prefix strip; `/* → web:3000`). The
dedicated `nginx-conf` branch will ship the comprehensive version
(gzip, TLS, caching, rate limits, etc.).

## Raspberry-Pi client

`server/face_detection.py` runs on a Raspberry Pi with a USB camera and
uses `opencv-python` + `face-recognition` + `dlib` to recognize students
and POST attendance to the server. **It is not part of this compose
stack** because:

1. It needs direct USB camera access (`/dev/video0`) on the Pi.
2. `dlib`/`face-recognition` wheels are huge and architecture-specific
   (Pi is ARM); building them inside the server image would bloat it for
   no reason.
3. It runs at the edge, not as part of the web stack.

On the Pi, install dependencies from `server/requirements.txt` into a
local venv and run `python face_detection.py`, with `SERVER_API_BASE_URL`
pointing at this stack's public hostname (e.g. `http://<server-host>/api`).

## Troubleshooting

* `docker compose up` fails with "open server/firebase.json: no such file":
  download the service-account JSON and place it at `./server/firebase.json`.
* `entrypoint] ERROR: JWT secret not found ...`: create
  `./secrets/jwt_secret.txt` (see [Secrets](#secrets)).
* Web shows API errors / CORS / cannot reach server: confirm `nginx` is
  running (`docker compose ps`) and the build-time `NEXT_PUBLIC_SERVER_URL`
  matches the URL the browser uses. Rebuild `web` after changing it.
* Want to reset uploaded faces: `docker compose down -v` (drops the
  `face_uploads` volume).
