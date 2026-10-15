import logging
import uuid

from server import app, create_app

def test_healthz_route(monkeypatch):
    class WorkingEngine:
        def connect(self):
            class Connection:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

                def execute(self, statement):
                    return 1

            return Connection()

    monkeypatch.setitem(app.config, "_ENGINE", WorkingEngine())

    client = app.test_client()
    resp = client.get("/api/healthz")

    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json()["db_connected"] is True

def test_healthz_returns_503_when_database_is_unavailable(monkeypatch, caplog):
    class FailingEngine:
        def connect(self):
            raise RuntimeError("simulated database failure")

    monkeypatch.setitem(app.config, "_ENGINE", FailingEngine())

    with caplog.at_level(logging.ERROR, logger="server"):
        client = app.test_client()
        resp = client.get("/api/healthz")

    assert resp.status_code == 503
    assert resp.is_json
    assert resp.get_json()["db_connected"] is False
    assert "Health check failed: database unavailable" in caplog.text

def test_authenticated_access_requires_successful_authentication():
    client = app.test_client()

    # Create a unique test user.
    unique_id = uuid.uuid4().hex
    user_data = {
        "email": f"fiau2-{unique_id}@example.com",
        "login": f"fiau2-{unique_id}",
        "password": "fiau2-test-password",
    }

    create_resp = client.post("/api/create-user", json=user_data)

    # Print the response for debugging purposes.
    #print("\nCREATE USER RESPONSE:")
    #print("Status:", create_resp.status_code)
    #print("Body:", create_resp.get_json())

    assert create_resp.status_code == 201

    # Unauthenticated access must be rejected.
    unauthenticated_resp = client.get("/api/list-documents")

    # Print the response for debugging purposes.
    #print("\nUNAUTHENTICATED RESPONSE:")
    #print("Status:", unauthenticated_resp.status_code)
    #print("Body:", unauthenticated_resp.get_json())

    assert unauthenticated_resp.status_code == 401

    # Authenticate the test user.
    login_resp = client.post(
        "/api/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
        },
    )

    # Print the response for debugging purposes.
    #print("\nLOGIN RESPONSE:")
    #print("Status:", login_resp.status_code)
    #print("Body:", login_resp.get_json())

    assert login_resp.status_code == 200

    token = login_resp.get_json()["token"]

    # The same protected operation should be allowed after authentication.
    authenticated_resp = client.get(
        "/api/list-documents",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Print the response for debugging purposes.
    #print("\nAUTHENTICATED RESPONSE:")
    #print("Status:", authenticated_resp.status_code)
    #print("Body:", authenticated_resp.get_json())

    assert authenticated_resp.status_code == 200

def test_load_missing_plugin_returns_404():
    client = app.test_client()

    unique_id = uuid.uuid4().hex
    user_data = {
        "email": f"plugin-test-{unique_id}@example.com",
        "login": f"plugin-test-{unique_id}",
        "password": "plugin-test-password",
    }

    create_resp = client.post("/api/create-user", json=user_data)
    assert create_resp.status_code == 201

    login_resp = client.post(
        "/api/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
        },
    )
    assert login_resp.status_code == 200

    token = login_resp.get_json()["token"]

    response = client.post(
        "/api/load-plugin",
        json={"filename": "definitely_missing_test_plugin.pkl"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert "plugin file not found" in response.get_json()["error"]

