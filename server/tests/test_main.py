"""Endpoint tests for ``server/main.py``.

All Firestore / Firebase access is mocked via the ``client`` /
``auth_mock`` / ``db_mock`` fixtures from ``conftest.py``.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_doc(data: dict, doc_id: str = "doc-id"):
    """Return a mock Firestore document with ``to_dict`` / ``id`` / ``reference``."""

    doc = MagicMock()
    doc.to_dict.return_value = data
    doc.id = doc_id
    doc.reference = MagicMock(name=f"ref-{doc_id}")
    return doc


def _chain_returns(mock: MagicMock, final_value):
    """Make ``mock`` return ``final_value`` from any subsequent chained call.

    Convenience for setting up ``db.collection(...).where(...)....stream()``
    chains where we only care about the leaf value.
    """

    mock.return_value = final_value
    return mock


# ---------------------------------------------------------------------------
# POST /attendances/
# ---------------------------------------------------------------------------
class TestAttendances:
    def test_happy_path_records_attendance(self, client, db_mock):
        # No existing attendance today.
        db_mock.collection.return_value.where.return_value.where.return_value.where.return_value.stream.return_value = []
        attendance_ref = MagicMock()
        db_mock.collection.return_value.document.return_value = attendance_ref

        timestamp = int(datetime(2025, 1, 15, 9, 0, tzinfo=timezone.utc).timestamp())
        response = client.post(
            "/attendances/",
            json={"attendee_id": "student-1", "timestamp": timestamp},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["message"] == "Attendance recorded successfully"
        assert body["data"]["attendee_id"] == "student-1"
        assert body["data"]["timestamp"] == timestamp
        attendance_ref.set.assert_called_once_with(
            {"attendee_id": "student-1", "timestamp": timestamp}
        )

    def test_missing_attendee_id_returns_400(self, client, db_mock):
        response = client.post("/attendances/", json={"attendee_id": "", "timestamp": 1})
        assert response.status_code == 400
        assert "attendeeId is required" in response.json()["detail"]

    def test_duplicate_attendance_returns_400(self, client, db_mock):
        db_mock.collection.return_value.where.return_value.where.return_value.where.return_value.stream.return_value = [
            _make_doc({"attendee_id": "student-1", "timestamp": 1})
        ]

        response = client.post(
            "/attendances/",
            json={"attendee_id": "student-1", "timestamp": 1700000000},
        )
        assert response.status_code == 400
        assert "already attended" in response.json()["detail"]

    def test_zero_timestamp_uses_now(self, client, db_mock):
        db_mock.collection.return_value.where.return_value.where.return_value.where.return_value.stream.return_value = []
        attendance_ref = MagicMock()
        db_mock.collection.return_value.document.return_value = attendance_ref

        before = int(datetime.now(tz=timezone.utc).timestamp())
        response = client.post(
            "/attendances/",
            json={"attendee_id": "student-1", "timestamp": 0},
        )
        after = int(datetime.now(tz=timezone.utc).timestamp())

        assert response.status_code == 201
        recorded = attendance_ref.set.call_args[0][0]
        assert before <= recorded["timestamp"] <= after


# ---------------------------------------------------------------------------
# POST /students/
# ---------------------------------------------------------------------------
class TestRegister:
    def _no_existing_student(self, db_mock):
        db_mock.collection.return_value.document.return_value.get.return_value.exists = False
        return db_mock.collection.return_value.document.return_value

    def test_happy_path_without_image(self, client, db_mock, auth_mock):
        student_ref = self._no_existing_student(db_mock)

        response = client.post(
            "/students/",
            json={
                "email": "alice@kmitl.ac.th",
                "first_name": "Alice",
                "last_name": "Anderson",
                "password": "supersecret",
            },
        )

        assert response.status_code == 201, response.text
        assert response.json() == {"message": "Student registered successfully"}
        auth_mock.create_user.assert_called_once_with(
            uid="alice", email="alice@kmitl.ac.th", password="supersecret"
        )
        student_ref.set.assert_called_with(
            {"first_name": "Alice", "last_name": "Anderson"}
        )

    @pytest.mark.asyncio
    async def test_happy_path_with_image_via_handler(
        self, db_mock, auth_mock, tmp_path, monkeypatch
    ):
        """The image branch is unreachable through the JSON endpoint (see the
        note in ``test_invalid_image_via_handler``); invoke the handler
        directly to exercise the image-save path.
        """

        import main as main_module
        from fastapi import UploadFile

        self._no_existing_student(db_mock)
        monkeypatch.setattr(main_module, "db", db_mock)
        monkeypatch.setattr(main_module, "auth", auth_mock)
        monkeypatch.chdir(tmp_path)

        upload = UploadFile(
            filename="bob.png",
            file=io.BytesIO(b"fakepngbytes"),
            headers={"content-type": "image/png"},
        )
        student = main_module.Student.model_construct(
            email="bob@kmitl.ac.th",
            first_name="Bob",
            last_name="Brown",
            password="supersecret",
            image=upload,
        )

        result = await main_module.Register(student)

        assert result == {"message": "Student registered successfully"}
        assert (tmp_path / "faces" / "bob.png").exists()
        auth_mock.create_user.assert_called_once_with(
            uid="bob", email="bob@kmitl.ac.th", password="supersecret"
        )

    def test_missing_email_returns_400(self, client, db_mock):
        # `email` is mandatory at the pydantic layer, so the omission is
        # surfaced as a 422 by FastAPI.  Sending an explicit ``None`` lets us
        # exercise the in-handler validation that returns 400.
        response = client.post(
            "/students/",
            json={
                "email": None,
                "first_name": "X",
                "last_name": "Y",
                "password": "p",
            },
        )
        # pydantic v2 rejects ``None`` against ``str`` with 422; v1 would 400.
        assert response.status_code in (400, 422)

    def test_missing_password_returns_422_or_400(self, client, db_mock):
        response = client.post(
            "/students/",
            json={
                "email": "alice@kmitl.ac.th",
                "first_name": "A",
                "last_name": "B",
                "password": None,
            },
        )
        assert response.status_code in (400, 422)

    def test_wrong_email_domain_returns_400(self, client, db_mock):
        response = client.post(
            "/students/",
            json={
                "email": "alice@gmail.com",
                "first_name": "A",
                "last_name": "B",
                "password": "p",
            },
        )
        assert response.status_code == 400
        assert "domain" in response.json()["detail"]

    def test_already_exists_returns_400(self, client, db_mock):
        db_mock.collection.return_value.document.return_value.get.return_value.exists = True

        response = client.post(
            "/students/",
            json={
                "email": "alice@kmitl.ac.th",
                "first_name": "A",
                "last_name": "B",
                "password": "p",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_image_via_handler(self, db_mock, auth_mock, monkeypatch):
        """The route signature ``async def Register(student: Student)`` makes
        FastAPI parse the body as JSON, so the multipart-only ``image``
        field of the ``Student`` model is unreachable through the public
        HTTP surface today.  Until that endpoint signature is migrated to
        ``Annotated[Student, Form()]`` we exercise the validation branch
        here by calling the handler directly.
        """

        import main as main_module
        from fastapi import HTTPException, UploadFile

        self._no_existing_student(db_mock)
        monkeypatch.setattr(main_module, "db", db_mock)
        monkeypatch.setattr(main_module, "auth", auth_mock)

        bad_upload = UploadFile(
            filename="face.gif",
            file=io.BytesIO(b"giffy"),
            headers={"content-type": "image/gif"},
        )
        student = main_module.Student.model_construct(
            email="carol@kmitl.ac.th",
            first_name="Carol",
            last_name="C",
            password="p",
            image=bad_upload,
        )

        with pytest.raises(HTTPException) as exc:
            await main_module.Register(student)
        assert exc.value.status_code == 400
        assert ".jpg" in exc.value.detail


# ---------------------------------------------------------------------------
# POST /instructors/  (login)
# ---------------------------------------------------------------------------
class TestLogin:
    def _seed_instructor(self, db_mock, email: str = "prof@kmitl.ac.th"):
        instructor_doc = _make_doc(
            {"first_name": "Pat", "last_name": "Prof", "email": email},
            doc_id="prof",
        )
        db_mock.collection.return_value.where.return_value.limit.return_value.stream.return_value = [
            instructor_doc
        ]
        return instructor_doc

    def test_happy_path_returns_jwt(self, client, db_mock, auth_mock):
        self._seed_instructor(db_mock)
        auth_mock.get_user_by_email.return_value = MagicMock(uid="prof")

        response = client.post(
            "/instructors/",
            json={"email": "prof@kmitl.ac.th", "password": "pw"},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["message"] == "successfully login as an instructor"
        assert body["token"] and isinstance(body["token"], str)
        assert body["data"]["first_name"] == "Pat"
        assert body["data"]["last_name"] == "Prof"

    def test_missing_email_returns_400(self, client, auth_mock):
        response = client.post("/instructors/", json={"email": None, "password": "p"})
        assert response.status_code == 400

    def test_missing_password_returns_400(self, client, auth_mock):
        response = client.post(
            "/instructors/", json={"email": "prof@kmitl.ac.th", "password": None}
        )
        assert response.status_code == 400

    def test_user_not_found_returns_404(self, client, db_mock, auth_mock):
        auth_mock.get_user_by_email.side_effect = auth_mock.UserNotFoundError("nope")
        response = client.post(
            "/instructors/", json={"email": "ghost@kmitl.ac.th", "password": "p"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_instructor_doc_missing_returns_404(self, client, db_mock, auth_mock):
        auth_mock.get_user_by_email.return_value = MagicMock(uid="prof")
        db_mock.collection.return_value.where.return_value.limit.return_value.stream.return_value = []

        response = client.post(
            "/instructors/", json={"email": "prof@kmitl.ac.th", "password": "p"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Instructor not found"


# ---------------------------------------------------------------------------
# DELETE /students/{studentId}
# ---------------------------------------------------------------------------
class TestRemove:
    def test_happy_path(self, client, db_mock, auth_mock):
        # The middleware calls auth.get_user_by_email(jwt_email) AND the
        # handler calls it with the student's email — return a user record
        # whose uid matches the student id ("alice") in both cases.
        auth_mock.get_user_by_email.return_value = MagicMock(uid="alice")

        att_docs = [
            _make_doc({"attendee_id": "alice"}, "att1"),
            _make_doc({"attendee_id": "alice"}, "att2"),
        ]
        db_mock.collection.return_value.where.return_value.stream.return_value = att_docs
        transaction = MagicMock()
        db_mock.transaction.return_value = transaction
        student_ref = MagicMock(name="student-ref")
        db_mock.collection.return_value.document.return_value = student_ref

        token = _make_jwt("prof@kmitl.ac.th")
        response = client.delete(
            "/students/alice", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200, response.text
        assert response.json()["message"].startswith("Student and their attendances deleted")
        auth_mock.delete_user.assert_called_once_with("alice")
        # Each attendance ref + the student doc itself must be deleted.
        assert transaction.delete.call_count == len(att_docs) + 1
        transaction.commit.assert_called_once()

    def test_user_not_found_returns_404(self, client, db_mock, auth_mock):
        # The middleware looks up the JWT email; that must succeed.  Only the
        # student-id lookup performed by the handler should raise.
        def lookup(email: str):
            if email == "ghost@kmitl.ac.th":
                raise auth_mock.UserNotFoundError("not found")
            return MagicMock(uid=email.split("@")[0])

        auth_mock.get_user_by_email.side_effect = lookup

        token = _make_jwt("prof@kmitl.ac.th")
        response = client.delete(
            "/students/ghost", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"


# ---------------------------------------------------------------------------
# GET /attendances/
# ---------------------------------------------------------------------------
class TestGetAttendances:
    def _wire_attendance_docs(self, db_mock, docs):
        """Configure both the ``.stream()`` and ``.limit(5).stream()`` paths."""

        order_chain = db_mock.collection.return_value.where.return_value.where.return_value.order_by.return_value
        order_chain.stream.return_value = docs
        order_chain.limit.return_value.stream.return_value = docs

    def _student_lookup(self, db_mock, first_name="John", last_name="Doe"):
        student_doc = MagicMock()
        student_doc.exists = True
        student_doc.to_dict.return_value = {"first_name": first_name, "last_name": last_name}
        db_mock.collection.return_value.document.return_value.get.return_value = student_doc

    def test_without_recent_query(self, client, db_mock):
        att_doc = _make_doc({"attendee_id": "alice", "timestamp": 1700000000})
        self._wire_attendance_docs(db_mock, [att_doc])
        self._student_lookup(db_mock)

        response = client.get("/attendances/")
        assert response.status_code == 200, response.text
        body = response.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["first_name"] == "John"
        assert body["data"][0]["attendee_id"] == "alice"

    def test_with_recent_query_limits(self, client, db_mock):
        docs = [_make_doc({"attendee_id": "alice", "timestamp": 1700000000})]
        self._wire_attendance_docs(db_mock, docs)
        self._student_lookup(db_mock)

        response = client.get("/attendances/?recent=true")
        assert response.status_code == 200
        # When ``recent=true``, the handler should have appended ``.limit(5)``
        order_chain = db_mock.collection.return_value.where.return_value.where.return_value.order_by.return_value
        order_chain.limit.assert_called_with(5)

    def test_handles_missing_attendee_id_and_bad_timestamp(self, client, db_mock):
        att_doc = _make_doc({"timestamp": "not-an-int"})  # no attendee_id, bad ts
        self._wire_attendance_docs(db_mock, [att_doc])

        response = client.get("/attendances/")
        assert response.status_code == 200
        body = response.json()
        assert body["data"][0]["attendee_id"] == "Unknown"
        assert body["data"][0]["first_name"] == "Unknown"
        assert body["data"][0]["timestamp"] == 0


# ---------------------------------------------------------------------------
# GET /students/
# ---------------------------------------------------------------------------
class TestGetStudents:
    def test_with_head_default_returns_limited(self, client, db_mock):
        student_doc = _make_doc({"first_name": "Eve", "last_name": "E"}, doc_id="eve")
        db_mock.collection.return_value.limit.return_value.stream.return_value = [student_doc]
        # No attendance for eve today.
        db_mock.collection.return_value.where.return_value.where.return_value.where.return_value.limit.return_value.stream.return_value = []

        response = client.get("/students/")
        assert response.status_code == 200, response.text
        body = response.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["first_name"] == "Eve"
        assert body["data"][0]["attendee_id"] == "eve"
        assert body["data"][0]["timestamp"] == 0
        db_mock.collection.return_value.limit.assert_any_call(5)

    def test_with_head_false_returns_all(self, client, db_mock):
        docs = [_make_doc({"first_name": "Eve", "last_name": "E"}, doc_id="eve")]
        db_mock.collection.return_value.stream.return_value = docs
        attendance_doc = _make_doc({"attendee_id": "eve", "timestamp": 1700000000}, "att1")
        db_mock.collection.return_value.where.return_value.where.return_value.where.return_value.limit.return_value.stream.return_value = [
            attendance_doc
        ]

        response = client.get("/students/?head=false")
        assert response.status_code == 200
        body = response.json()
        assert body["data"][0]["timestamp"] == 1700000000


# ---------------------------------------------------------------------------
# GET /insights/
# ---------------------------------------------------------------------------
class TestInsights:
    def test_happy_path(self, client, db_mock):
        docs = [
            _make_doc({"timestamp": 1700000000}),
            _make_doc({"timestamp": 1700100000}),
        ]
        chain = (
            db_mock.collection.return_value
            .select.return_value
            .where.return_value
            .where.return_value
            .order_by.return_value
        )
        chain.stream.return_value = docs

        response = client.get("/insights/")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["data"] == [1700000000, 1700100000]

    def test_returns_500_on_exception(self, client, db_mock):
        db_mock.collection.side_effect = RuntimeError("firestore down")

        response = client.get("/insights/")
        assert response.status_code == 500
        assert "firestore down" in response.json()["detail"]


# ---------------------------------------------------------------------------
# JWT helper used by the protected-endpoint tests above.
# ---------------------------------------------------------------------------
def _make_jwt(email: str) -> str:
    """Mint a JWT that the AuthMiddleware will accept in tests."""

    import jwt
    from datetime import datetime, timedelta, timezone

    from auth_middleware import JWT_ALGORITHM, JWT_SECRET_KEY

    payload = {
        "sub": email,
        "email": email,
        "iat": int(datetime.now(tz=timezone.utc).timestamp()),
        "exp": int((datetime.now(tz=timezone.utc) + timedelta(minutes=60)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
