from __future__ import annotations

import base64
import hashlib
import hmac
import json

import fitz

from watermarking_method import (
    InvalidKeyError,
    SecretNotFoundError,
    WatermarkingMethod,
    load_pdf_bytes,
)


class VisibleHMAC(WatermarkingMethod):
    name = "visible-hmac"

    _MAGIC = "WM-VISIBLE-HMAC:v1:"
    _CONTEXT = b"wm:visible-hmac:v1:"

    @staticmethod
    def get_usage() -> str:
        return (
            "Embeds a visible HMAC-authenticated watermark into the PDF "
            "page content. Position may specify placement."
        )

    def add_watermark(
        self,
        pdf,
        secret: str,
        key: str,
        position: str | None = None,
    ) -> bytes:
        data = load_pdf_bytes(pdf)

        if not secret:
            raise ValueError("Secret must be a non-empty string")

        if not isinstance(key, str) or not key:
            raise ValueError("Key must be a non-empty string")

        key_bytes = key.encode("utf-8")
        secret_bytes = secret.encode("utf-8")

        mac = hmac.new(
            key_bytes,
            self._CONTEXT + secret_bytes,
            hashlib.sha256,
        ).hexdigest()

        payload = {
            "secret": secret,
            "mac": mac,
        }

        encoded = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        ).decode("ascii")

        watermark_text = self._MAGIC + encoded

        doc = fitz.open(stream=data, filetype="pdf")

        try:
            doc.set_metadata({
                **doc.metadata,
                "keywords": watermark_text,
            })

            for page in doc:
                rect = page.rect

                text = "WATERMARKED • 7F3A91C2"
                fontsize = 28

                text_width = fitz.get_text_length(
                    text,
                    fontname="helv",
                    fontsize=fontsize,
                )

                text_height = fontsize  # Approximation; could use font metrics for precision

                page_center = fitz.Point(
                    rect.width / 2,
                    rect.height / 2,
                )

                start = fitz.Point(
                    page_center.x - text_width / 2,
                    page_center.y + text_height / 2,
                )

                text_center = fitz.Point(
                    page_center.x,
                    page_center.y,
                )

                page.insert_text(
                    start,
                    text,
                    fontsize=fontsize,
                    fontname="helv",
                    morph=(
                        text_center,
                        fitz.Matrix(1, 1).prerotate(45),
                    ),
                    fill_opacity=0.3,
                )

            return doc.tobytes()
        finally:
            doc.close()

    def is_watermark_applicable(
        self,
        pdf,
        position: str | None = None,
    ) -> bool:
        data = load_pdf_bytes(pdf)

        try:
            doc = fitz.open(stream=data, filetype="pdf")
            doc.close()
            return True
        except Exception:
            return False

    def read_secret(self, pdf, key: str) -> str:
        if not isinstance(key, str) or not key:
            raise InvalidKeyError("Key must be a non-empty string")

        data = load_pdf_bytes(pdf)

        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise SecretNotFoundError("Could not open PDF") from exc

        try:
            watermark_text = doc.metadata.get("keywords", "")
        finally:
            doc.close()

        marker = self._MAGIC

        if marker not in watermark_text:
            raise SecretNotFoundError("Visible-HMAC watermark not found")

        encoded = watermark_text.split(marker, 1)[1].split()[0]

        try:
            encoded += "=" * (-len(encoded) % 4)
            decoded = base64.urlsafe_b64decode(encoded).decode("utf-8")
            payload = json.loads(decoded)
            stored_secret = payload["secret"]
            stored_mac = payload["mac"]
        except (ValueError, KeyError, UnicodeDecodeError) as exc:
            raise SecretNotFoundError("Invalid Visible-HMAC watermark") from exc

        expected_mac = hmac.new(
            key.encode("utf-8"),
            self._CONTEXT + stored_secret.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(stored_mac, expected_mac):
            raise InvalidKeyError("Invalid key or modified watermark")

        return stored_secret