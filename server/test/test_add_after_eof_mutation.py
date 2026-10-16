from pathlib import Path
import pytest

from add_after_eof import AddAfterEOF


def test_add_watermark(tmp_path: Path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")

    method = AddAfterEOF()
    result = method.add_watermark(
        pdf,
        secret="test-secret",
        key="test-key",
    )

    assert isinstance(result, bytes)
    assert result.startswith(b"%PDF-")
    assert len(result) > len(pdf.read_bytes())


def test_read_secret_roundtrip(tmp_path: Path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")

    method = AddAfterEOF()

    watermarked = method.add_watermark(
        pdf,
        secret="test-secret",
        key="test-key",
    )

    output = tmp_path / "watermarked.pdf"
    output.write_bytes(watermarked)

    assert method.read_secret(output, key="test-key") == "test-secret"


def test_read_secret_without_watermark_raises(tmp_path: Path):
    from watermarking_method import SecretNotFoundError

    pdf = tmp_path / "no_watermark.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")

    method = AddAfterEOF()

    with pytest.raises(SecretNotFoundError):
        method.read_secret(pdf, key="test-key")


def test_empty_key_rejected(tmp_path: Path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")

    method = AddAfterEOF()

    with pytest.raises(ValueError):
        method.add_watermark(pdf, secret="test-secret", key="")


def test_watermark_newline_structure(tmp_path: Path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF")

    method = AddAfterEOF()
    result = method.add_watermark(
        pdf,
        secret="test-secret",
        key="test-key",
    )

    assert b"%%EOF\n\n%%WM-ADD-AFTER-EOF:v1\n" in result

