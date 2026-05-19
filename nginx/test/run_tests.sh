#!/bin/sh
# nginx/test/run_tests.sh
#
# End-to-end smoke test for the FaceTrack nginx reverse-proxy config.
# Runs inside the `tester` container of docker-compose.test.yml. Each
# assertion uses `curl -sf` so any non-2xx response (except where we
# explicitly want a 404) is treated as a failure.

set -u

if ! command -v curl >/dev/null 2>&1; then
    apk add --no-cache curl >/dev/null
fi

NGINX="http://nginx"
FAILED=0
PASSED=0

assert() {
    label="$1"
    cmd="$2"
    if eval "$cmd" >/dev/null 2>&1; then
        echo "  PASS  $label"
        PASSED=$((PASSED + 1))
    else
        echo "  FAIL  $label"
        echo "        command: $cmd"
        # Re-run with output so we can see what went wrong.
        eval "$cmd" || true
        FAILED=$((FAILED + 1))
    fi
}

# Wait briefly for nginx to be ready (compose already health-checks it
# but belt and suspenders never hurt).
for _ in $(seq 1 15); do
    if curl -sf "$NGINX/healthz" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "== FaceTrack nginx smoke tests =="

# Nginx-served health check.
assert "GET /healthz returns ok" \
    "curl -sf $NGINX/healthz | grep -q '^ok$'"

# SPA fallback to the web upstream.
assert "GET / -> web upstream (WEB_OK)" \
    "curl -sf $NGINX/ | grep -q WEB_OK"

# THE key assertion: /api prefix-strip works.
assert "GET /api/attendances/ -> upstream /attendances/" \
    "curl -sf $NGINX/api/attendances/ | grep -q '\"path\": \"/attendances/\"'"

# Query string survives the rewrite.
assert "GET /api/students/?head=true preserves query" \
    "curl -sf '$NGINX/api/students/?head=true' | grep -q '\"path\": \"/students/?head=true\"'"

# Other REST resources reachable.
assert "GET /api/instructors/ reachable" \
    "curl -sf $NGINX/api/instructors/ | grep -q '\"path\": \"/instructors/\"'"

assert "GET /api/insights/ reachable" \
    "curl -sf $NGINX/api/insights/ | grep -q '\"path\": \"/insights/\"'"

# FastAPI docs / openapi / redoc all use the same prefix-strip rule.
assert "GET /api/docs -> upstream /docs" \
    "curl -sf $NGINX/api/docs | grep -q '\"path\": \"/docs\"'"

assert "GET /api/openapi.json -> upstream /openapi.json" \
    "curl -sf $NGINX/api/openapi.json | grep -q '\"path\": \"/openapi.json\"'"

assert "GET /api/redoc -> upstream /redoc" \
    "curl -sf $NGINX/api/redoc | grep -q '\"path\": \"/redoc\"'"

# /faces/ static mount preserves the full path (no prefix strip).
assert "GET /faces/abc.jpg preserves /faces/ path" \
    "curl -sf $NGINX/faces/abc.jpg | grep -q '\"path\": \"/faces/abc.jpg\"'"

# POST also flows through the /api/ rewrite (mirrors the real upload path).
assert "POST /api/attendances/ -> upstream /attendances/" \
    "curl -sf -X POST $NGINX/api/attendances/ -d 'x=1' | grep -q '\"path\": \"/attendances/\"'"

# Hashed Next.js assets get the immutable Cache-Control header.
assert "GET /_next/static/foo.js sets immutable Cache-Control" \
    "curl -sfI $NGINX/_next/static/foo.js | tr -d '\r' | grep -i '^cache-control:' | grep -q 'immutable'"

# Standard security headers - one assert per header for clearer failures.
assert "X-Frame-Options header on /" \
    "curl -sfI $NGINX/ | tr -d '\r' | grep -qi '^x-frame-options: SAMEORIGIN'"
assert "X-Content-Type-Options header on /" \
    "curl -sfI $NGINX/ | tr -d '\r' | grep -qi '^x-content-type-options: nosniff'"
assert "Referrer-Policy header on /" \
    "curl -sfI $NGINX/ | tr -d '\r' | grep -qi '^referrer-policy: strict-origin-when-cross-origin'"
assert "Permissions-Policy header on /" \
    "curl -sfI $NGINX/ | tr -d '\r' | grep -qi '^permissions-policy:'"

# Unmatched SPA route falls through to web (Next.js client-side routing).
assert "Unknown path falls through to SPA catch-all" \
    "curl -sf $NGINX/some/spa/route | grep -q WEB_OK"

# Upstream 404s propagate through nginx unchanged.
# `curl -sf` returns non-zero on 4xx, so we cannot use -f here. We
# capture the status code with -w '%{http_code}' instead.
assert "Upstream 404 propagates as 404" \
    "test \"\$(curl -s -o /dev/null -w '%{http_code}' $NGINX/api/notfound/xyz)\" = '404'"

echo
echo "== Result: $PASSED passed, $FAILED failed =="

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi
exit 0
