# FaceTrack Nginx reverse proxy

Nginx fronts the two FaceTrack services and exposes a single host port:

- **Next.js client** on `web:3000` (the SPA + Next.js static assets).
- **FastAPI server** on `server:8000` (REST API at `/attendances/`,
  `/students/`, `/instructors/`, `/insights/`, plus the `/faces/` static
  mount and FastAPI's `/docs`, `/redoc`, `/openapi.json`).

The public surface served by nginx is HTTP on port `80` (plus a
ready-to-uncomment `443` block for TLS).

## File layout

```
nginx/
├── nginx.conf              # http{} block: gzip, logging, proxy defaults
├── conf.d/
│   ├── upstreams.conf      # upstream pools (web:3000, server:8000)
│   ├── default.conf        # the port-80 server block + route map
│   └── tls.conf            # commented-out TLS stub for port 443
├── README.md               # this file
└── test/
    ├── docker-compose.test.yml   # mock_web + mock_api + nginx + tester
    ├── mock_api.py               # stdlib HTTP server posing as FastAPI
    ├── mock_web/nginx.conf       # one-line static nginx posing as Next.js
    ├── run_tests.sh              # the curl assertions
    ├── run.sh                    # `bash run.sh` -> bring up + assert
    └── Makefile                  # `make test` -> same thing
```

### What each config does

| File | Role |
| --- | --- |
| `nginx.conf` | Tunes worker model, gzip, logging (combined + JSON), proxy defaults (Host/X-Forwarded-*, keepalive), and a `client_max_body_size 10M;` cap to allow face image uploads. Pulls in everything in `conf.d/`. |
| `conf.d/upstreams.conf` | Defines `facetrack_web` (Next.js) and `facetrack_api` (FastAPI) upstream pools with `keepalive 16;` connections. |
| `conf.d/default.conf` | The public route map. `/api/` strips its prefix and forwards to FastAPI; `/faces/` preserves the path; `/_next/static/` is cached for a year; the SPA catch-all sends everything else to Next.js. Adds standard security headers. |
| `conf.d/tls.conf` | Commented-out TLS server block for port `443`. Includes modern protocol/cipher choices and HSTS. See the comments at the top of the file for the steps to enable. |

### Routing reference

| URL on nginx | Forwarded to | Notes |
| --- | --- | --- |
| `GET /healthz` | nginx (no upstream) | returns `ok\n`, used by Docker health checks and load balancers. |
| `GET /api/attendances/` | `server:8000/attendances/` | `/api` prefix is stripped. |
| `GET /api/students/?head=true` | `server:8000/students/?head=true` | Query strings survive. |
| `GET /api/docs` | `server:8000/docs` | FastAPI's Swagger UI. See caveat below. |
| `GET /api/openapi.json` | `server:8000/openapi.json` | |
| `GET /api/redoc` | `server:8000/redoc` | |
| `GET /faces/abc.jpg` | `server:8000/faces/abc.jpg` | Path preserved (no strip). |
| `GET /_next/static/<hash>.js` | `web:3000/_next/static/<hash>.js` | `Cache-Control: public, immutable, max-age=31536000`. |
| `GET /favicon.ico` | `web:3000/favicon.ico` | 1-hour browser cache, access log silenced. |
| `GET /icons/*`, `/fonts/*` | `web:3000/...` | 1-hour browser cache. |
| `GET /<anything-else>` | `web:3000/<anything-else>` | SPA catch-all. |

> **FastAPI docs caveat.** FastAPI's `/docs` HTML page references
> `/openapi.json` _relative to root_, not to the prefix nginx adds. If
> you actually want the Swagger UI usable through `https://host/api/docs`,
> instantiate the app with
> `FastAPI(docs_url="/docs", openapi_url="/openapi.json", root_path="/api")`,
> or add a dedicated `location = /openapi.json { proxy_pass ...; }`. The
> nginx config itself routes both URLs correctly; only the in-page link
> needs a small change.

## Local non-Docker testing

If you want to run nginx on the host machine against `next start` and
`uvicorn` running on `127.0.0.1`, edit `conf.d/upstreams.conf` and
replace the upstream `server` directives with:

```nginx
upstream facetrack_web { server 127.0.0.1:3000; keepalive 16; }
upstream facetrack_api { server 127.0.0.1:8000; keepalive 16; }
```

(or drop in an override file with the same upstream names).

## Syntax check

From the repo root, on any machine with Docker:

```bash
docker run --rm \
  -v "$(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf:ro" \
  -v "$(pwd)/nginx/conf.d:/etc/nginx/conf.d:ro" \
  nginx:alpine nginx -t
```

A successful run prints:

```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

`make -C nginx/test syntax` runs the same command.

## End-to-end smoke test

A self-contained `docker compose` stack in `nginx/test/` brings up two
mocks (one for the Next.js client, one for the FastAPI server) behind a
real nginx instance using the production `nginx.conf` and `conf.d/`,
then runs `curl` assertions:

```bash
make -C nginx/test test
# or:
bash nginx/test/run.sh
```

The compose file deliberately uses the same Docker service names as the
production stack (`web`, `server`) so `conf.d/upstreams.conf` does not
need to be patched for tests.

The tester container asserts, among other things:

- `GET /healthz` returns the nginx-served `ok` body.
- `GET /` reaches the web upstream (returns `WEB_OK`).
- `GET /api/attendances/` forwards upstream as `/attendances/` (the
  critical prefix-strip behavior).
- Query strings (`?head=true`) survive the rewrite.
- `/api/docs`, `/api/openapi.json`, `/api/redoc` all forward correctly.
- `/faces/abc.jpg` is preserved verbatim upstream.
- `POST /api/attendances/` works.
- `/_next/static/...` carries the immutable `Cache-Control` header.
- Standard security headers are present on every response.
- Upstream 404s propagate as 404s through nginx.

The compose run exits with the tester container's status code, so CI
can do:

```bash
docker compose -f nginx/test/docker-compose.test.yml \
    up --build --abort-on-container-exit --exit-code-from tester
```

If Docker is not available on the machine, both the syntax check and
the smoke test are skipped - they have no `apt`/`brew`/`choco` fallback
because nginx is intentionally shipped as a container in this repo.

## TLS

Disabled by default. See `conf.d/tls.conf` for the step-by-step enable
checklist (mount certs, uncomment server block, redirect 80 -> 443,
enable HSTS in `default.conf`).
