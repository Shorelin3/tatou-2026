import io
import uuid
import fitz

from server import app

def test_delete_document():
    client = app.test_client()

    def create_user():
        uid = uuid.uuid4().hex
        email = f"test-{uid}@example.com"
        password = "test-password"

        r = client.post("/api/create-user", json={
            "login": f"test-{uid}",
            "email": email,
            "password": password
        })
        assert r.status_code == 201

        r = client.post("/api/login", json={
            "email": email,
            "password": password
        })
        assert r.status_code == 200

        return {"Authorization": f"Bearer {r.get_json()['token']}"}

    owner = create_user()
    non_owner = create_user()

    # Create a valid PDF.
    with fitz.open() as pdf:
        pdf.new_page()
        pdf_bytes = pdf.tobytes()

    # Upload as owner.
    r = client.post(
        "/api/upload-document",
        headers=owner,
        data={"file": (io.BytesIO(pdf_bytes), "delete-test.pdf")}
    )
    assert r.status_code == 201
    doc_id = r.get_json()["id"]

    # 1. Unauthenticated deletion must fail.
    r = client.delete(f"/api/delete-document/{doc_id}")
    assert r.status_code == 401

    # 2. Non-owner must not be allowed to delete.
    r = client.delete(
        f"/api/delete-document/{doc_id}",
        headers=non_owner
    )
    assert r.status_code == 404

    # Verify document still exists for owner.
    r = client.get(
        f"/api/get-document/{doc_id}",
        headers=owner
    )
    assert r.status_code == 200

    # 3. Owner can delete.
    r = client.delete(
        f"/api/delete-document/{doc_id}",
        headers=owner
    )
    assert r.status_code == 200
    assert r.get_json()["deleted"] is True

    # 4. Document is no longer accessible.
    r = client.get(
        f"/api/get-document/{doc_id}",
        headers=owner
    )
    assert r.status_code == 404
