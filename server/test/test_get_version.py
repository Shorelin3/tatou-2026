
from unittest.mock import MagicMock
from server import app

def test_get_version_not_found(monkeypatch):
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.execute.return_value.first.return_value = None

    monkeypatch.setitem(app.config, "_ENGINE", engine)

    response = app.test_client().get("/api/get-version/nonexistent-link")

    assert response.status_code == 404
    assert response.get_json() == {"error": "document not found"}

def test_get_version_success(monkeypatch, tmp_path):
    # Create a temporary PDF inside the storage directory.
    pdf_path = tmp_path / "watermarked.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nTest content\n%%EOF")

    # Simulate a matching version in the database.
    from types import SimpleNamespace

    row = SimpleNamespace(
        link="test-version-link",
        path=str(pdf_path),
    )

    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.execute.return_value.first.return_value = row

    monkeypatch.setitem(app.config, "_ENGINE", engine)
    monkeypatch.setitem(app.config, "STORAGE_DIR", tmp_path)

    response = app.test_client().get(
        "/api/get-version/test-version-link"
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data == pdf_path.read_bytes()
    assert response.headers["Cache-Control"] == "private, max-age=0"

def test_get_version_file_missing(monkeypatch, tmp_path):
    from types import SimpleNamespace

    # Database contains a version, but its file does not exist.
    missing_pdf = tmp_path / "missing.pdf"

    row = SimpleNamespace(
        link="missing-file-link",
        path=str(missing_pdf),
    )

    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.execute.return_value.first.return_value = row

    monkeypatch.setitem(app.config, "_ENGINE", engine)
    monkeypatch.setitem(app.config, "STORAGE_DIR", tmp_path)

    response = app.test_client().get(
        "/api/get-version/missing-file-link"
    )

    assert response.status_code == 410
    assert response.get_json() == {"error": "file missing on disk"}

def test_get_version_invalid_path(monkeypatch, tmp_path):
    from types import SimpleNamespace

    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    # Simulate a database record pointing outside storage.
    outside_pdf = tmp_path / "outside.pdf"
    outside_pdf.write_bytes(b"%PDF-1.4\n%%EOF")

    row = SimpleNamespace(
        link="invalid-path-link",
        path=str(outside_pdf),
    )

    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.execute.return_value.first.return_value = row

    monkeypatch.setitem(app.config, "_ENGINE", engine)
    monkeypatch.setitem(app.config, "STORAGE_DIR", storage_dir)

    response = app.test_client().get(
        "/api/get-version/invalid-path-link"
    )

    assert response.status_code == 500
    assert response.get_json() == {"error": "document path invalid"}

def test_get_version_database_error(monkeypatch):
    engine = MagicMock()

    # Simulate a database connection failure.
    engine.connect.side_effect = RuntimeError("simulated database failure")

    monkeypatch.setitem(app.config, "_ENGINE", engine)

    response = app.test_client().get(
        "/api/get-version/test-link"
    )

    assert response.status_code == 503
    assert "database error" in response.get_json()["error"]

def test_get_version_served_inline(monkeypatch, tmp_path):
    from types import SimpleNamespace

    pdf_path = tmp_path / "watermarked.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nTest content\n%%EOF")

    row = SimpleNamespace(
        link="inline-test",
        path=str(pdf_path),
    )

    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.execute.return_value.first.return_value = row

    monkeypatch.setitem(app.config, "_ENGINE", engine)
    monkeypatch.setitem(app.config, "STORAGE_DIR", tmp_path)

    response = app.test_client().get("/api/get-version/inline-test")

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert "attachment" not in response.headers.get("Content-Disposition", "").lower()
    assert "inline" in response.headers.get("Content-Disposition", "").lower()
    assert response.headers.get("Content-Disposition", "").endswith("inline-test.pdf")