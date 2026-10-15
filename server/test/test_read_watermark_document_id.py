
import io
import uuid
import fitz
import pytest

from server import app

def test_read_watermark_document_id():
    client = app.test_client()

    def create_user():
        uid = uuid.uuid4().hex
        email = f"test-{uid}@example.com"
        password = "test-password"

        response = client.post("/api/create-user", json={
            "login": f"test-{uid}",
            "email": email,
            "password": password,
        })
        assert response.status_code == 201

        response = client.post("/api/login", json={
            "email": email,
            "password": password,
        })
        assert response.status_code == 200

        return {
            "Authorization": f"Bearer {response.get_json()['token']}"
        }

    owner = create_user()
    non_owner = create_user()

    # Create a valid PDF containing a watermark.
    from watermarking_utils import apply_watermark

    secret = "read-watermark-test-secret"
    key = "read-watermark-test-key"

    with fitz.open() as pdf:
        pdf.new_page()
        pdf_bytes = pdf.tobytes()

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "original.pdf"
        pdf_path.write_bytes(pdf_bytes)

        pdf_bytes = apply_watermark(
            pdf=str(pdf_path),
            secret=secret,
            key=key,
            method="visible-hmac",
            position=None,
        )

    # Upload the PDF as the owner.
    response = client.post(
        "/api/upload-document",
        headers=owner,
        data={"file": (io.BytesIO(pdf_bytes), "read-test.pdf")},
    )
    assert response.status_code == 201
    doc_id = response.get_json()["id"]

    # Create a watermarked version.
    secret = "read-watermark-test-secret"
    key = "read-watermark-test-key"

    response = client.post(
        f"/api/create-watermark/{doc_id}",
        headers=owner,
        json={
            "method": "visible-hmac",
            "intended_for": "test-recipient@example.com",
            "secret": secret,
            "key": key,
        },
    )
    assert response.status_code == 201

    # 1. Unauthenticated access must fail.
    response = client.post(
        f"/api/read-watermark/{doc_id}",
        json={"method": "visible-hmac", "key": key},
    )
    assert response.status_code == 401

    # 2. Non-owner must not be able to read the document.
    response = client.post(
        f"/api/read-watermark/{doc_id}",
        headers=non_owner,
        json={"method": "visible-hmac", "key": key},
    )
    print("NON-OWNER RESPONSE:", response.status_code, response.get_json())
    assert response.status_code == 404

    # 3. Check the owner's response.
    response = client.post(
        f"/api/read-watermark/{doc_id}",
        headers=owner,
        json={"method": "visible-hmac", "key": key},
    )

    print("OWNER RESPONSE:", response.status_code, response.get_json())
    assert response.status_code == 201
    data = response.get_json()

    assert data["documentid"] == doc_id
    assert data["method"] == "visible-hmac"
    assert isinstance(data["secret"], str)

    # 4. Invalid parameters must be rejected.
    response = client.post(
        f"/api/read-watermark/{doc_id}",
        headers=owner,
        json={"key": key},
    )
    assert response.status_code == 400
