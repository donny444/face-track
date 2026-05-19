# Server test suite

The server-side unit tests live in `server/tests/` and are driven by
[pytest](https://docs.pytest.org/).  They cover:

| File                              | What it covers                                    |
| --------------------------------- | ------------------------------------------------- |
| `tests/test_main.py`              | All FastAPI endpoints in `main.py`                |
| `tests/test_auth_middleware.py`   | JWT bearer middleware in `auth_middleware.py`     |
| `tests/test_face_detection.py`    | `sync_faces_from_server`, `post_attendance`, `draw_feedback` |

`tests/conftest.py` installs `firebase_admin` / `google.cloud.firestore_v1`
shims *before* importing `main.py` so the suite runs without real Firebase
credentials.

## Quick start

```bash
cd server

# (optional but recommended) create a virtualenv
python -m venv .venv
source .venv/Scripts/activate          # Git Bash on Windows
# source .venv/bin/activate            # macOS / Linux

# install runtime deps + test deps
pip install -r requirements.txt -r requirements-dev.txt

# run the suite
pytest -q
```

If installing the full `requirements.txt` is too heavy (e.g. `face-recognition`
needs `dlib` which is painful on Windows), the test suite only needs the
following packages installed for the imports to succeed:

```bash
pip install fastapi "uvicorn[standard]" PyJWT python-dotenv pytest pytest-asyncio httpx requests
```

`cv2` and `face_recognition` are stubbed in `tests/test_face_detection.py`
when they are missing, so they are not required to run the tests.

## Notes

* `face_detection.py`'s main loop is wrapped in `if __name__ == "__main__":`
  to keep `import face_detection` side-effect free (this was a small but
  necessary refactor for testability).
* The test suite creates a `faces/` directory next to wherever pytest is
  invoked from, because `main.py` mounts `StaticFiles(directory="faces")`
  at import time.
