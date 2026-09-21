
from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json

import fitz

from watermarking_method import (
    InvalidKeyError,
    SecretNotFoundError,
    PdfSource,
    WatermarkingMethod,
    load_pdf_bytes,
)

class visibleWatermark(WatermarkingMethod):

    name ="repeated-visible"
    MARKER = "TATOU-RW-1"

    def get_usage(self) -> str:
        return (
        
        )

    @staticmethod
    def _make_tag(secret: str, key: str) -> str:
        return hmac.new(
            key.encode("utf-8"),
            secret.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _encode_payload(secret: str, tag: str) -> str:
        payload = json.dumps(
            {
                "secret": secret,
                "tag": tag,
             },
            separators=(",", ":"),
        ).encode("utf-8")

        return base64.urlsafe_b64encode(payload).decode("ascii")

    @staticmethod
    def _decode_payload(encoded: str) -> dict:
        try:
            raw = base64.urlsafe_b64decode(
                    encoded.encode("ascii")
            )
            payload = json.loads(raw.decode("utf-8"))

            if not isinstance(payload, dict):
                    raise ValueError("Invalid payload")

            return payload
            
        except Exception as exc:
            raise SecretNotFoundError(
                "Invalid watermark payload"
            ) from exc

    def is_watermark_applicable(
        self,
        pdf: PdfSource,
        position: str | None = None, 
    ) -> bool:
        data = load_pdf_bytes(pdf)

        try:
            doc = fitz.open(
                stream=data, 
                filetype="pdf",
            )

            applicable = doc.page_count > 0
            doc.close()

            return applicable

        except Exception:
                return False
        
    def add_watermark(
            self,
            pdf: PdfSource,
            secret: str,
            key: str,
            position: str | None = None,
        ) -> bytes:


            if not secret:
                raise ValueError("Secret cannot be empty")

            if not key:
                raise ValueError("Key cannot be empty")

            data = load_pdf_bytes(pdf)

            tag = self._make_tag(secret, key)
            encoded = self._encode_payload(secret, tag)

            watermark_text = f"TATOU + {secret}"

            doc = fitz.open(
                stream=data, 
                filetype="pdf",
            )

            try:
                for page in doc:
                    rect = page.rect

                    width = rect.width
                    height = rect.height

                    positions = [
                        (width * 0.15, height * 0.25),
                        (width * 0.35, height * 0.55),
                        (width * 0.15, height * 0.85),
                    ] 

                    for x, y in positions:
                        page.insert_text(
                            (x, y),
                            watermark_text,
                            fontsize=22,
                            fontname="helv",
                            color=(0.65, 0.65, 0.65),
                            rotate=90,
                            overlay=False,
                        )
                    
                metadata = doc.metadata or {}

                metadata["keywords"] = (
                    f"{self.MARKER}:{encoded}"
                )

                doc.set_metadata(metadata)

                output = io.BytesIO()
                doc.save(output)

                return output.getvalue()

            finally:
                doc.close()

    def read_secret(
        self,
        pdf: PdfSource,
        key: str,
    ) -> str:

        if not key:
            raise InvalidKeyError("Key cannot be empty")

        data = load_pdf_bytes(pdf)

        doc = fitz.open(
            stream=data, 
            filetype="pdf",
        )

        try:
            metadata = doc.metadata or {}
            keywords = metadata.get("keywords", "")

            prefix = f"{self.MARKER}:"

            if not keywords.startswith(prefix):
                raise SecretNotFoundError(
                    "Repeated visible watermark not found"
                )
            
            encoded = keywords[len(prefix):]
          
            payload = self._decode_payload(encoded)

            secret = payload.get("secret")
            stored_tag = payload.get("tag")

            if not isinstance(secret, str):
                raise SecretNotFoundError(
                    "Invalid secret in watermark"
                )

            expected_tag = self._make_tag(
                secret, 
                key,
            )

            if not hmac.compare_digest(
                stored_tag or "",
                expected_tag,
            ):

                raise InvalidKeyError("Invalid key")

            return secret
        
        finally:
            doc.close()



    