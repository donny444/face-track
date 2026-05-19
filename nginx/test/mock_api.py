"""Minimal stdlib HTTP server used as the FastAPI stand-in for smoke
tests of the nginx reverse-proxy config.

It listens on 0.0.0.0:8000 and replies to every request with a JSON
body of the form ``{"ok": true, "path": "<request-path>"}``. This lets
the test runner assert on the exact path nginx forwarded upstream
(particularly that the /api prefix was stripped and /faces/ was
preserved).
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class MockAPIHandler(BaseHTTPRequestHandler):
    def _respond(self) -> None:
        # Reserved test path for verifying that upstream 404s propagate
        # through nginx unchanged.
        if self.path.startswith("/notfound"):
            status = 404
            payload = json.dumps({"ok": False, "path": self.path}).encode("utf-8")
        else:
            status = 200
            payload = json.dumps({"ok": True, "path": self.path}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    # Map every HTTP verb to the same handler so /attendances/ POSTs,
    # /students/ DELETEs, etc. all succeed.
    do_GET = _respond
    do_POST = _respond
    do_PUT = _respond
    do_PATCH = _respond
    do_DELETE = _respond
    do_OPTIONS = _respond
    do_HEAD = _respond

    def log_message(self, fmt: str, *args: object) -> None:
        # Quieter logs - one line per request is plenty for the smoke
        # test, and keeps the docker compose output readable.
        print(f"mock_api {self.command} {self.path} -> 200", flush=True)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 8000), MockAPIHandler)
    print("mock_api listening on 0.0.0.0:8000", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
