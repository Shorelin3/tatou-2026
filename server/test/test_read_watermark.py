
import io
import uuid
import tempfile
import fitz

from pathlib import Path
from watermarking_utils import apply_watermark
from server import app

def test_read_watermark():
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

    secret = "read-body-test-secret"
    key = "read-body-test-key"

    # Create an already-watermarked PDF.
    with fitz.open() as pdf:
        pdf.new_page()
        pdf_bytes = pdf.tobytes()

    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "original.pdf"
        pdf_path.write_bytes(pdf_bytes)

        watermarked_bytes = apply_watermark(
            pdf=str(pdf_path),
            secret=secret,
            key=key,
            method="visible-hmac",
            position=None,
        )

    # Upload the watermarked PDF.
    response = client.post(
        "/api/upload-document",
        headers=owner,
        data={
            "file": (io.BytesIO(watermarked_bytes), "read-body-test.pdf")
        },
    )
    assert response.status_code == 201
    doc_id = response.get_json()["id"]

    payload = {
        "id": doc_id,
        "method": "visible-hmac",
        "key": key,
    }

    # 1. Unauthenticated access must fail.
    response = client.post(
        "/api/read-watermark",
        json=payload,
    )
    assert response.status_code == 401

    # 2. Non-owner must not read the document.
    response = client.post(
        "/api/read-watermark",
        headers=non_owner,
        json=payload,
    )
    assert response.status_code == 404

    # 3. Owner must retrieve the correct secret.
    response = client.post(
        "/api/read-watermark",
        headers=owner,
        json=payload,
    )
    assert response.status_code == 201

    data = response.get_json()
    assert data["documentid"] == doc_id
    assert data["method"] == "visible-hmac"
    assert data["secret"] == secret

    # 4. Missing document ID must fail.
    response = client.post(
        "/api/read-watermark",
        headers=owner,
        json={"method": "visible-hmac", "key": key},
    )
    assert response.status_code == 400

    # 5. Invalid document ID must fail.
    response = client.post(
        "/api/read-watermark",
        headers=owner,
        json={"id": "invalid", "method": "visible-hmac", "key": key},
    )
    assert response.status_code == 400
