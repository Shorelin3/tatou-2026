from types import SimpleNamespace
from unittest.mock import MagicMock

from itsdangerous import URLSafeTimedSerializer

from server import app


def make_auth_headers():
    """Create a valid authentication token for a test user."""
    serializer = URLSafeTimedSerializer(
        app.config["SECRET_KEY"],
        salt="tatou-auth",
    )
    token = serializer.dumps(
        {
            "uid": 1,
            "login": "test@example.com",
            "email": "test@example.com",
        }
    )
    return {"Authorization": f"Bearer {token}"}


def make_engine(rows):
    
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value.all.return_value = rows
    return engine


def test_list_versions_with_document_id_requires_authentication():
    
    client = app.test_client()

    response = client.get("/api/list-versions/1")

    assert response.status_code == 401


def test_list_versions_without_document_id_requires_authentication():
    
    client = app.test_client()

    response = client.get("/api/list-versions")

    assert response.status_code == 401


def test_list_versions_requires_document_id_when_authenticated():
    
    client = app.test_client()

    response = client.get(
        "/api/list-versions",
        headers=make_auth_headers(),
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == "document id required"


def test_list_versions_rejects_invalid_document_id():
    
    client = app.test_client()

    response = client.get(
        "/api/list-versions?id=abc",
        headers=make_auth_headers(),
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == "document id required"


def test_list_versions_with_path_document_id_returns_versions(monkeypatch):
    
    rows = [
        SimpleNamespace(
            id=10,
            documentid=1,
            link="abc123",
            intended_for="Group_02",
            secret="test-secret",
            method="visible-hmac",
        )
    ]

    engine = make_engine(rows)
    monkeypatch.setitem(app.config, "_ENGINE", engine)

    client = app.test_client()
    response = client.get(
        "/api/list-versions/1",
        headers=make_auth_headers(),
    )

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    assert "versions" in data
    assert len(data["versions"]) == 1

    version = data["versions"][0]

    assert version["id"] == 10
    assert version["documentid"] == 1
    assert version["link"] == "abc123"
    assert version["intended_for"] == "Group_02"
    assert version["secret"] == "test-secret"
    assert version["method"] == "visible-hmac"


def test_list_versions_accepts_id_query_parameter(monkeypatch):
    
    engine = make_engine([])
    monkeypatch.setitem(app.config, "_ENGINE", engine)

    client = app.test_client()
    response = client.get(
        "/api/list-versions?id=1",
        headers=make_auth_headers(),
    )

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {"versions": []}


def test_list_versions_accepts_documentid_query_parameter(monkeypatch):
    
    engine = make_engine([])
    monkeypatch.setitem(app.config, "_ENGINE", engine)

    client = app.test_client()
    response = client.get(
        "/api/list-versions?documentid=1",
        headers=make_auth_headers(),
    )

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {"versions": []}


def test_list_versions_returns_empty_list_when_no_versions_exist(monkeypatch):
    
    engine = make_engine([])
    monkeypatch.setitem(app.config, "_ENGINE", engine)

    client = app.test_client()
    response = client.get(
        "/api/list-versions/999",
        headers=make_auth_headers(),
    )

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {"versions": []}