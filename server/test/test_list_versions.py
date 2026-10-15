from server import app


def test_list_versions_requires_authentication():
    client = app.test_client()

    response = client.get("/api/list-versions/1")

    assert response.status_code == 401