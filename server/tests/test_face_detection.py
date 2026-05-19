"""Tests for ``server/face_detection.py``.

``face_detection.py`` imports the heavyweight ``cv2`` and ``face_recognition``
libraries.  We shim them with ``MagicMock`` *before* the module is imported
so the test suite can run on machines that don't have those compiled
extensions installed (notably Windows where ``dlib`` is painful to build).

The module's main loop is already wrapped in ``if __name__ == "__main__":``,
so simply importing it is side-effect free apart from creating ``FACE_DIR``.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Module-level import (with cv2 / face_recognition shims when missing)
# ---------------------------------------------------------------------------
def _install_optional_shims():
    if "cv2" not in sys.modules:
        cv2_shim = MagicMock(name="cv2")
        cv2_shim.FONT_HERSHEY_SIMPLEX = 0
        cv2_shim.FONT_HERSHEY_DUPLEX = 0
        cv2_shim.COLOR_BGR2RGB = 4
        cv2_shim.FILLED = -1
        cv2_shim.getTextSize.return_value = ((100, 20), 0)
        sys.modules["cv2"] = cv2_shim
    if "face_recognition" not in sys.modules:
        sys.modules["face_recognition"] = MagicMock(name="face_recognition")


_install_optional_shims()

import face_detection  # noqa: E402  (import after shimming)


# ---------------------------------------------------------------------------
# post_attendance
# ---------------------------------------------------------------------------
class TestPostAttendance:
    def test_already_in_sent_short_circuits(self):
        sent = {"alice"}
        result = face_detection.post_attendance("alice", sent)
        assert result == "ALREADY_ATTENDED"
        assert sent == {"alice"}

    def test_success_path_posts_and_records(self):
        sent: set[str] = set()
        with patch.object(face_detection.requests, "post") as post:
            response = MagicMock()
            response.raise_for_status = MagicMock()
            response.status_code = 201
            post.return_value = response

            result = face_detection.post_attendance("alice", sent)

        assert result == "SUCCESS"
        assert "alice" in sent
        post.assert_called_once()
        url, = post.call_args.args
        assert url.endswith("/attendances/")
        kwargs = post.call_args.kwargs
        assert kwargs["json"]["attendee_id"] == "alice"
        assert isinstance(kwargs["json"]["timestamp"], int)

    def test_http_400_treated_as_already_attended(self):
        sent: set[str] = set()
        # Build a fake HTTPError whose `.response.status_code` is 400.
        fake_response = MagicMock(status_code=400)
        http_err = face_detection.requests.exceptions.HTTPError("400 Bad Request")
        http_err.response = fake_response

        response = MagicMock()
        response.raise_for_status.side_effect = http_err

        with patch.object(face_detection.requests, "post", return_value=response):
            result = face_detection.post_attendance("alice", sent)

        assert result == "ALREADY_ATTENDED"
        assert "alice" in sent

    def test_http_500_returns_network_error(self):
        sent: set[str] = set()
        fake_response = MagicMock(status_code=500)
        http_err = face_detection.requests.exceptions.HTTPError("500 boom")
        http_err.response = fake_response

        response = MagicMock()
        response.raise_for_status.side_effect = http_err

        with patch.object(face_detection.requests, "post", return_value=response):
            result = face_detection.post_attendance("alice", sent)

        assert result == "NETWORK_ERROR"
        assert "alice" not in sent

    def test_generic_request_exception_returns_network_error(self):
        sent: set[str] = set()
        with patch.object(
            face_detection.requests,
            "post",
            side_effect=face_detection.requests.exceptions.ConnectionError("unreachable"),
        ):
            result = face_detection.post_attendance("alice", sent)
        assert result == "NETWORK_ERROR"
        assert "alice" not in sent


# ---------------------------------------------------------------------------
# sync_faces_from_server
# ---------------------------------------------------------------------------
class TestSyncFacesFromServer:
    def test_successful_sync_downloads_missing_images(self, tmp_path, monkeypatch):
        # Redirect FACE_DIR so we don't pollute the workspace.
        monkeypatch.setattr(face_detection, "FACE_DIR", str(tmp_path))

        students = [
            {
                "student_id": "alice",
                "image_url": "http://example.com/faces/alice.png",
                "first_name": "Alice",
            },
            # Missing student_id — should be silently skipped.
            {"image_url": "http://example.com/faces/bob.png"},
        ]
        list_response = MagicMock()
        list_response.raise_for_status = MagicMock()
        list_response.json.return_value = students

        img_response = MagicMock()
        img_response.raise_for_status = MagicMock()
        img_response.raw = MagicMock()

        def fake_get(url, *args, **kwargs):
            if url.endswith("/students/"):
                return list_response
            return img_response

        with patch.object(face_detection.requests, "get", side_effect=fake_get):
            with patch.object(face_detection.shutil, "copyfileobj") as copy:
                cache = face_detection.sync_faces_from_server()

        assert "alice" in cache
        assert cache["alice"]["first_name"] == "Alice"
        copy.assert_called_once()  # exactly one image downloaded

    def test_skips_download_when_local_image_exists(self, tmp_path, monkeypatch):
        monkeypatch.setattr(face_detection, "FACE_DIR", str(tmp_path))
        (tmp_path / "alice.png").write_bytes(b"x")

        students = [
            {
                "student_id": "alice",
                "image_url": "http://example.com/faces/alice.png",
                "first_name": "Alice",
            }
        ]
        list_response = MagicMock()
        list_response.raise_for_status = MagicMock()
        list_response.json.return_value = students

        with patch.object(face_detection.requests, "get", return_value=list_response) as get:
            with patch.object(face_detection.shutil, "copyfileobj") as copy:
                cache = face_detection.sync_faces_from_server()

        assert "alice" in cache
        # Only the /students/ listing should have been fetched.
        assert get.call_count == 1
        copy.assert_not_called()

    def test_connection_error_returns_empty_dict(self):
        with patch.object(
            face_detection.requests,
            "get",
            side_effect=face_detection.requests.exceptions.ConnectionError("nope"),
        ):
            cache = face_detection.sync_faces_from_server()
        assert cache == {}


# ---------------------------------------------------------------------------
# draw_feedback
# ---------------------------------------------------------------------------
class TestDrawFeedback:
    def test_does_not_raise_on_small_frame(self):
        # Build a tiny numpy-shaped object; if numpy is unavailable in the
        # test env we fall back to a MagicMock that exposes `.shape`.
        try:
            import numpy as np

            frame = np.zeros((48, 64, 3), dtype="uint8")
        except Exception:  # pragma: no cover - numpy is in the prod reqs
            frame = MagicMock()
            frame.shape = (48, 64, 3)

        # Should not raise.  cv2 is shimmed so the calls are no-ops.
        face_detection.draw_feedback(frame, "hello", (0, 255, 0))
