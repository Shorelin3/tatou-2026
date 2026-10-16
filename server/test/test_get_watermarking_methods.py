from server import app


def test_get_watermarking_methods():
    client = app.test_client()

    response = client.get("/api/get-watermarking-methods")

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    assert "methods" in data
    assert "count" in data
    assert isinstance(data["methods"], list)
    assert data["count"] == len(data["methods"])

    for method in data["methods"]:
        assert "name" in method
        assert "description" in method


