import uuid

from server import app

def test_healthz_route():
    client = app.test_client()
    resp = client.get("/healthz")

    assert resp.status_code == 200
    assert resp.is_json
    
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