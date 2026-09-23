
from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json

import pymupdf

from watermarking_method import (
    InvalidKeyError,
    SecretNotFoundError,
    PdfSource,
    WatermarkingMethod,
    load_pdf_bytes,
)

class DuplicateWatermark(WatermarkingMethod):

    name = "duplicate_watermark"
    MARKER = "TATOUWM"

    def get_usage(self) -> str:
        return (
            "This watermarking method adds a visible watermark three times to the PDF page. "
        )

    @staticmethod
    def _make_tag(secret: str, key: str) -> str:
        return hmac.new(
            key.encode("utf-8"),
            secret.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _encode_watermark_data(secret: str, tag: str) -> str:
        watermark_data = json.dumps(
            {
                "secret": secret,
                "tag": tag,
             },
            separators=(",", ":"),
        ).encode("utf-8")

        return base64.urlsafe_b64encode(watermark_data).decode("ascii")

    @staticmethod
    def _decode_watermark_data(encoded: str) -> dict:
        try:
            decoded_data = base64.urlsafe_b64decode(
                    encoded.encode("ascii")
            )
            watermark_data = json.loads(decoded_data.decode("utf-8"))

            if not isinstance(watermark_data, dict):
                raise ValueError("Invalid watermark data")

            return watermark_data
            
        except Exception as exc:
            raise SecretNotFoundError(
                "Invalid watermark data"
            ) from exc

    def is_watermark_applicable(
        self,
        pdf: PdfSource,
        position: str | None = None, 
    ) -> bool:
        pdf_data = load_pdf_bytes(pdf)

        try:
            document = pymupdf.open(
                stream=pdf_data, 
                filetype="pdf",
            )

            pages = document.page_count > 0
            document.close()

            return pages

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
                raise ValueError("Secret must have a value")

            if not key:
                raise ValueError("Key must have a value")

            pdf_data = load_pdf_bytes(pdf)

            tag = self._make_tag(secret, key)
            encoded_watermark = self._encode_watermark_data(secret, tag)

            watermark_text = f"tatou + {secret}"

            document = pymupdf.open(
                stream=pdf_data, 
                filetype="pdf",
            )

            try:
                for page in document:
                    page_rect = page.rect

                    page_width = page_rect.width
                    page_height = page_rect.height

                    watermark_positions = [
                        (page_width * 0.50, page_height * 0.22),
                        (page_width * 0.60, page_height * 0.58),
                        (page_width * 0.50, page_height * 0.94),
                    ] 

                    for x_position, y_position in watermark_positions:
                        page.insert_text(
                            (x_position, y_position),
                            watermark_text,
                            fontsize=20,
                            fontname="times-roman",
                            color=(1, 0, 0),
                            rotate=90,
                            fill_opacity=0.5,
                            overlay=False,
                        )
                    
                pdf_metadata = document.metadata or {}

                pdf_metadata["keywords"] = (
                    f"{self.MARKER}:{encoded_watermark}"
                )

                document.set_metadata(pdf_metadata)

                output_pdf = io.BytesIO()
                document.save(output_pdf)

                return output_pdf.getvalue()

            finally:
                document.close()

    def read_secret(
        self,
        pdf: PdfSource,
        key: str,
    ) -> str:

        if not key:
            raise InvalidKeyError("Key cannot be empty")

        pdf_data = load_pdf_bytes(pdf)

        document = pymupdf.open(
            stream=pdf_data, 
            filetype="pdf",
        )

        try:
            pdf_metadata = document.metadata or {}
            keywords = pdf_metadata.get("keywords", "")

            prefix = f"{self.MARKER}:"

            if not keywords.startswith(prefix):
                raise SecretNotFoundError(
                    "Duplicate watermark not found"
                )
            
            encoded_watermark = keywords[len(prefix):]
          
            watermark_data = self._decode_watermark_data(encoded_watermark)

            secret = watermark_data.get("secret")
            stored_tag = watermark_data.get("tag")

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
            document.close()

