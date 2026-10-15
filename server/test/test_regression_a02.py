import io
import pytest

from sqlalchemy import text
from server import app
from pathlib import Path
from test_baseline_a02 import make_pdf, make_user, safe_test_file

BODY = {
    "method": "visible-hmac",
    "intended_for": "a02-regression@example.com",
    "secret": "a02-regression-secret",
    "key": "a02-regression-key",
}

@pytest.fixture
def scenario():
    client = app.test_client()
    user_ids = []
    doc_id = None

    try:
        owner_id, owner_headers = make_user(client)
        user_ids.append(owner_id)

        other_id, other_headers = make_user(client)
        user_ids.append(other_id)

        upload = client.post(
            "/api/upload-document",
            headers=owner_headers,
            data={
                "file": (
                    io.BytesIO(make_pdf()),
                    "a02-regression.pdf"
                )
            },
        )

        assert upload.status_code == 201, (
            upload.status_code,
            upload.get_json()
        )

        doc_id = upload.get_json()["id"]

        yield client, doc_id, owner_headers, other_headers

    finally:
        engine = app.config.get("_ENGINE")

        if engine is not None:
            root = Path(app.config["STORAGE_DIR"]).resolve()

            if doc_id is not None:
                with engine.begin() as conn:
                    versions = conn.execute(
                        text(
                            "SELECT path FROM Versions "
                            "WHERE documentid = :id"
                        ),
                        {"id": doc_id},
                    ).fetchall()

                    document = conn.execute(
                        text(
                            "SELECT path FROM Documents "
                            "WHERE id = :id"
                        ),
                        {"id": doc_id},
                    ).first()

                    conn.execute(
                        text(
                            "DELETE FROM Versions "
                            "WHERE documentid = :id"
                        ),
                        {"id": doc_id},
                    )

                    conn.execute(
                        text(
                            "DELETE FROM Documents "
                            "WHERE id = :id"
                        ),
                        {"id": doc_id},
                    )

                for version in versions:
                    safe_test_file(version.path, root)

                if document:
                    safe_test_file(document.path, root)

            with engine.begin() as conn:
                for user_id in user_ids:
                    conn.execute(
                        text("DELETE FROM Users WHERE id = :id"),
                        {"id": user_id},
                    )

def count_versions(document_id):
    with app.config["_ENGINE"].connect() as conn:
        return conn.execute(
            text(
                "SELECT COUNT(*) FROM Versions "
                "WHERE documentid = :id"
            ),
            {"id": document_id},
        ).scalar_one()

def test_owner_can_create_watermark(scenario):
    client, doc_id, owner_headers, _ = scenario

    response = client.post(
        f"/api/create-watermark/{doc_id}",
        json=BODY,
        headers=owner_headers,
    )

    assert response.status_code == 201, (
        response.status_code,
        response.get_json(),
    )

    assert response.get_json()["documentid"] == doc_id
    assert count_versions(doc_id) == 1

def test_nonowner_cannot_create_watermark_with_path_id(scenario):
    client, doc_id, _, other_headers = scenario

    response = client.post(
        f"/api/create-watermark/{doc_id}",
        json=BODY,
        headers=other_headers,
    )

    assert response.status_code == 404, (
        response.status_code,
        response.get_json(),
    )

    assert count_versions(doc_id) == 0

def test_nonowner_cannot_create_watermark_with_json_id(scenario):
    client, doc_id, _, other_headers = scenario

    response = client.post(
        "/api/create-watermark",
        json={**BODY, "id": doc_id},
        headers=other_headers,
    )

    assert response.status_code == 404, (
        response.status_code,
        response.get_json(),
    )

    assert count_versions(doc_id) == 0

def test_unauthenticated_user_cannot_create_watermark(scenario):
    client, doc_id, _, _ = scenario

    response = client.post(
        f"/api/create-watermark/{doc_id}",
        json=BODY,
    )

    assert response.status_code in (401, 403), (
        response.status_code,
        response.get_json(),
    )

    assert count_versions(doc_id) == 0

def test_rejects_invalid_intended_for_type(scenario):
    client, doc_id, owner_headers, _ = scenario

    response = client.post(
        f"/api/create-watermark/{doc_id}",
        json={
            **BODY,
            "intended_for": ["invalid", "recipient"]
        },
        headers=owner_headers,
    )

    assert response.status_code == 400, (
        response.status_code,
        response.get_json(),
    )

    assert count_versions(doc_id) == 0
    
@pytest.mark.parametrize("field", ["secret", "key"])
def test_rejects_empty_watermark_credentials(scenario, field):
    client, doc_id, owner_headers, _ = scenario

    response = client.post(
        f"/api/create-watermark/{doc_id}",
        json={**BODY, field: ""},
        headers=owner_headers,
    )

    assert response.status_code == 400, (
        response.status_code,
        response.get_json(),
    )
    assert count_versions(doc_id) == 0