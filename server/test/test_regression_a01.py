
import io
import uuid
import fitz
import pytest

from sqlalchemy import text
from pathlib import Path
from server import app

UPLOAD_ENDPOINT = "/api/upload-document"

def make_valid_pdf():
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((50, 50), "Regression test")
        return pdf.tobytes()

@pytest.fixture(scope="module")
def test_account():
    client = app.test_client()
    unique_id = uuid.uuid4().hex
    login = f"regression-{unique_id}"

    user_data = {
        "email": f"{login}@example.com",
        "login": login,
        "password": "regression-test-password",
    }

    response = client.post("/api/create-user", json=user_data)
    assert response.status_code == 201

    user_id = response.get_json()["id"]

    response = client.post(
        "/api/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
        },
    )

    assert response.status_code == 200

    headers = {
        "Authorization": f"Bearer {response.get_json()['token']}"
    }

    engine = app.config["_ENGINE"]
    user_dir = (
        Path(app.config["STORAGE_DIR"]) / "files" / login
    ).resolve()

    try:
        yield client, headers

    finally:
        with engine.connect() as conn:
            paths = conn.execute(
                text(
                    "SELECT path FROM Documents "
                    "WHERE ownerid = :uid"
                ),
                {"uid": user_id},
            ).scalars().all()

        # Only delete files owned by this unique test account.
        for stored_path in paths:
            path = Path(stored_path).resolve()
            if not path.is_relative_to(user_dir):
                raise RuntimeError(
                    f"Unsafe cleanup path: {path}"
                )

        with engine.begin() as conn:
            conn.execute(
                text(
                    "DELETE FROM Documents WHERE ownerid = :uid"
                ),
                {"uid": user_id},
            )

        for path in paths:
            path = Path(path).resolve()
            if path.is_file():
                path.unlink()

        # Remove files left behind by failed uploads.
        if user_dir.is_dir():
            for path in user_dir.iterdir():
                if path.is_symlink() or path.is_file():
                    path.unlink()
            user_dir.rmdir()

        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM Users WHERE id = :uid"),
                {"uid": user_id},
            )

def upload(client, content, headers):
    return client.post(
        UPLOAD_ENDPOINT,
        headers=headers,
        data={
            "file": (
                io.BytesIO(content),
                "regression.pdf",
            )
        },
    )

def test_rejects_plain_text(test_account):
    client, headers = test_account

    response = upload(
        client,
        b"Hello, this is not a PDF",
        headers,
    )

    assert 400 <= response.status_code < 500

def test_rejects_empty_file(test_account):
    client, headers = test_account

    response = upload(client, b"", headers)

    assert 400 <= response.status_code < 500

def test_rejects_malformed_pdf(test_account):
    client, headers = test_account

    response = upload(
        client,
        b"%PDF-1.7\nbroken content",
        headers,
    )

    assert 400 <= response.status_code < 500

def test_accepts_valid_pdf(test_account):
    client, headers = test_account

    response = upload(
        client,
        make_valid_pdf(),
        headers,
    )

    assert response.status_code == 201

def test_requires_authentication(test_account):
    client, _ = test_account

    response = upload(
        client,
        make_valid_pdf(),
        {},
    )

    assert response.status_code == 401

def test_rejects_invalid_token(test_account):
    client, _ = test_account

    response = upload(
        client,
        make_valid_pdf(),
        {"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
