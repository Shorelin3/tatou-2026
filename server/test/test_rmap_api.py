
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import fitz
import server as server_module

@pytest.fixture
def rmap_setup(monkeypatch, tmp_path):
    class FakeRmapServer:
        def __init__(self, *args, **kwargs):
            pass

        def loadIdentities(self, directory):
            pass

        def receiveMsg1(self, payload):
            if payload == {"invalid": True}:
                raise ValueError("Invalid authentication")
            return "alice", {"message": "msg2"}

        def receiveMsg2(self, payload):
            if payload == {"invalid": True}:
                raise ValueError("Invalid authentication")
            return "alice", "test-link", {"link": "test-link"}

    monkeypatch.setattr(server_module, "RMAPServer", FakeRmapServer)

    public_key = tmp_path / "public.pem"
    private_key = tmp_path / "private.pem"
    public_key.touch()
    private_key.touch()

    monkeypatch.setenv("RMAP_SERVER_PUBLIC_KEY", str(public_key))
    monkeypatch.setenv("RMAP_SERVER_PRIVATE_KEY", str(private_key))
    monkeypatch.setenv("RMAP_KEYS_DIR", str(tmp_path / "identities"))
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))

    app = server_module.create_app()
    app.config["TESTING"] = True

    return app

def test_rmap_initiate_success(rmap_setup):
    response = rmap_setup.test_client().post(
        "/api/rmap-initiate",
        json={"message": "msg1"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"message": "msg2"}


def test_rmap_initiate_authentication_failure(rmap_setup):
    response = rmap_setup.test_client().post(
        "/api/rmap-initiate",
        json={"invalid": True},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "RMAP authentication failed"


def test_rmap_get_link_authentication_failure(rmap_setup):
    response = rmap_setup.test_client().post(
        "/api/rmap-get-link",
        json={"invalid": True},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "RMAP authentication failed"


def test_rmap_get_link_success(rmap_setup, monkeypatch, tmp_path):
    pdf_path = tmp_path / "original.pdf"

    with fitz.open() as doc:
        doc.new_page()
        doc.save(pdf_path)

    app = rmap_setup
    monkeypatch.setitem(app.config, "STORAGE_DIR", str(tmp_path))
    monkeypatch.setitem(app.config, "RMAP_DOCUMENT_ID", 1)
    monkeypatch.setitem(app.config, "RMAP_WATERMARK_METHOD", "visible-hmac")
    monkeypatch.setitem(app.config, "RMAP_WATERMARK_KEY", "test-key")

    row = SimpleNamespace(id=1, name="original.pdf", path=str(pdf_path))

    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.execute.return_value.first.return_value = row

    monkeypatch.setitem(app.config, "_ENGINE", engine)

    monkeypatch.setattr(
        server_module.WMUtils,
        "is_watermarking_applicable",
        lambda **kwargs: True,
    )

    monkeypatch.setattr(
        server_module.WMUtils,
        "apply_watermark",
        lambda **kwargs: pdf_path.read_bytes(),
    )

    response = app.test_client().post(
        "/api/rmap-get-link",
        json={"message": "msg2"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"link": "test-link"}

    engine.begin.return_value.__enter__.return_value.execute.assert_called_once()

    output_files = list((tmp_path / "watermarks").glob("*.pdf"))
    assert len(output_files) == 1
    assert output_files[0].read_bytes() == pdf_path.read_bytes()
