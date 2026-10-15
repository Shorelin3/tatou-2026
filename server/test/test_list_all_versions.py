from server import app


def test_list_all_versions_requires_authentication():
    client = app.test_client()

    response = client.get("/api/list-all-versions")

    assert response.status_code == 401