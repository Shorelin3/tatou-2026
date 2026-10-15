from types import SimpleNamespace
from unittest.mock import MagicMock

from itsdangerous import URLSafeTimedSerializer

from server import app


def make_auth_headers():
    
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


def test_list_all_versions_requires_authentication():
    
    client = app.test_client()

    response = client.get("/api/list-all-versions")

    assert response.status_code == 401


def test_list_all_versions_returns_empty_list(monkeypatch):
    
    engine = make_engine([])
    monkeypatch.setitem(app.config, "_ENGINE", engine)

    client = app.test_client()
    response = client.get(
        "/api/list-all-versions",
        headers=make_auth_headers(),
    )

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {"versions": []}


def test_list_all_versions_returns_version(monkeypatch):
    
    rows = [
        SimpleNamespace(
            id=10,
            documentid=1,
            link="abc123",
            intended_for="Group_02",
            method="visible-hmac",
        )
    ]

    engine = make_engine(rows)
    monkeypatch.setitem(app.config, "_ENGINE", engine)

    client = app.test_client()
    response = client.get(
        "/api/list-all-versions",
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
    assert version["method"] == "visible-hmac"


def test_list_all_versions_returns_multiple_versions(monkeypatch):
    
    rows = [
        SimpleNamespace(
            id=10,
            documentid=1,
            link="abc123",
            intended_for="Group_02",
            method="visible-hmac",
        ),
        SimpleNamespace(
            id=11,
            documentid=2,
            link="def456",
            intended_for="Group_03",
            method="add-after-eof",
        ),
    ]

    engine = make_engine(rows)
    monkeypatch.setitem(app.config, "_ENGINE", engine)

    client = app.test_client()
    response = client.get(
        "/api/list-all-versions",
        headers=make_auth_headers(),
    )

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    assert len(data["versions"]) == 2

    assert data["versions"][0]["id"] == 10
    assert data["versions"][0]["documentid"] == 1
    assert data["versions"][0]["link"] == "abc123"

    assert data["versions"][1]["id"] == 11
    assert data["versions"][1]["documentid"] == 2
    assert data["versions"][1]["link"] == "def456"


def test_list_all_versions_uses_authenticated_user(monkeypatch):
    
    engine = make_engine([])
    monkeypatch.setitem(app.config, "_ENGINE", engine)

    client = app.test_client()
    response = client.get(
        "/api/list-all-versions",
        headers=make_auth_headers(),
    )

    assert response.status_code == 200

    connection = engine.connect.return_value.__enter__.return_value

    assert connection.execute.call_count == 1

    _, parameters = connection.execute.call_args.args

    assert parameters["glogin"] == "test@example.com"


def test_list_all_versions_returns_503_on_database_error(monkeypatch):
    
    engine = MagicMock()
    engine.connect.side_effect = RuntimeError("simulated database failure")

    monkeypatch.setitem(app.config, "_ENGINE", engine)

    client = app.test_client()
    response = client.get(
        "/api/list-all-versions",
        headers=make_auth_headers(),
    )

    assert response.status_code == 503
    assert response.is_json
    assert "database error" in response.get_json()["error"]