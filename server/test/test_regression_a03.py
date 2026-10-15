import uuid
import pytest
from sqlalchemy import text
from server import app

@pytest.fixture
def login_user():
    """Create an isolated test user and remove it afterwards."""
    client = app.test_client()
    unique = uuid.uuid4().hex

    email = f"a03-regression-{unique}@example.com"
    login = f"a03-regression-{unique}"
    password = "a03-test-password"
    user_id = None

    try:
        response = client.post(
            "/api/create-user",
            json={
                "email": email,
                "login": login,
                "password": password,
            },
        )

        assert response.status_code == 201, (
            response.status_code,
            response.get_json(silent=True),
        )

        user_id = response.get_json()["id"]

        yield client, email, password

    finally:
        if user_id is not None:
            with app.config["_ENGINE"].begin() as conn:
                conn.execute(
                    text("DELETE FROM Users WHERE id = :id"),
                    {"id": user_id},
                )

def test_valid_login_returns_token_and_ttl(login_user):
    client, email, password = login_user

    response = client.post(
        "/api/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200

    result = response.get_json()
    assert isinstance(result["token"], str)
    assert result["token"]
    assert result["token_type"] == "bearer"
    assert isinstance(result["expires_in"], int)
    assert not isinstance(result["expires_in"], bool)

@pytest.mark.parametrize("missing_field", ["email", "password"])
def test_missing_credentials_are_rejected(login_user, missing_field):
    client, email, password = login_user
    body = {"email": email, "password": password}
    del body[missing_field]

    response = client.post("/api/login", json=body)

    assert response.status_code == 400

@pytest.mark.parametrize("invalid_case", ["wrong_password", "unknown_email"])
def test_invalid_credentials_are_rejected(login_user, invalid_case):
    client, email, password = login_user

    body = {"email": email, "password": password}

    if invalid_case == "wrong_password":
        body["password"] = "incorrect-password"
    else:
        body["email"] = f"unknown-{uuid.uuid4().hex}@example.com"

    response = client.post("/api/login", json=body)

    assert response.status_code == 401

@pytest.mark.parametrize(
    "field,value",
    [
        ("email", ["invalid@example.com"]),
        ("email", {"value": "invalid@example.com"}),
        ("email", True),
        ("password", ["invalid-password"]),
        ("password", {"value": "invalid-password"}),
        ("password", True),
    ],
)
def test_invalid_credential_types_are_rejected(login_user, field, value):
    client, email, password = login_user

    body = {"email": email, "password": password}
    body[field] = value

    response = client.post("/api/login", json=body)

    assert response.status_code == 400

@pytest.mark.parametrize(
    "body",
    [
        ["unexpected"],
        "unexpected",
        123,
        True,
    ],
)
def test_non_object_json_is_rejected(login_user, body):
    client, _, _ = login_user

    response = client.post("/api/login", json=body)

    assert response.status_code == 400