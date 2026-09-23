"""MicroDot PDF watermarking method."""

from __future__ import annotations

from typing import Final
import hashlib
import hmac
import pymupdf

from watermarking_method import (
    InvalidKeyError,
    SecretNotFoundError,
    WatermarkingMethod,
    PdfSource,
    load_pdf_bytes,
)


class MicroDotWatermark(WatermarkingMethod):
    """Embed a secret using small graphical markers inside a PDF."""

    name: Final[str] = "microdot"

    HEADER_BITS: Final[int] = 16
    TAG_BYTES: Final[int] = 8

    START_X: Final[float] = 50
    BASE_Y: Final[float] = 50
    SPACING: Final[float] = 3
    BIT_OFFSET: Final[float] = 3
    DOT_RADIUS: Final[float] = 0.7

    @staticmethod
    def get_usage() -> str:
        return (
            "MicroDot watermarking method. "
            "Encodes a UTF-8 secret as small graphical dots inside the PDF."
        )

    def is_watermark_applicable(
        self,
        pdf: PdfSource,
        position: str | None = None,
    ) -> bool:
        try:
            data = load_pdf_bytes(pdf)
            doc = pymupdf.open(stream=data, filetype="pdf")
            applicable = len(doc) > 0
            doc.close()
            return applicable
        except Exception:
            return False

    @staticmethod
    def _bytes_to_bits(data: bytes) -> str:
        return "".join(f"{byte:08b}" for byte in data)

    @staticmethod
    def _bits_to_bytes(bits: str) -> bytes:
        return bytes(
            int(bits[i:i + 8], 2)
            for i in range(0, len(bits), 8)
        )

    @staticmethod
    def _make_mask(key: str, length: int) -> str:
        """Create a deterministic bit mask from the key."""
        mask = ""
        counter = 0

        while len(mask) < length:
            digest = hashlib.sha256(
                key.encode("utf-8")
                + counter.to_bytes(4, "big")
            ).digest()

            mask += MicroDotWatermark._bytes_to_bits(digest)
            counter += 1

        return mask[:length]

    @staticmethod
    def _xor_bits(bits: str, mask: str) -> str:
        return "".join(
            "1" if bit != mask_bit else "0"
            for bit, mask_bit in zip(bits, mask)
        )

    def add_watermark(
        self,
        pdf: PdfSource,
        secret: str,
        key: str,
        position: str | None = None,
    ) -> bytes:

        if not secret:
            raise ValueError("Secret must be a non-empty string")

        if not key:
            raise ValueError("Key must be a non-empty string")

        data = load_pdf_bytes(pdf)
        secret_bytes = secret.encode("utf-8")

        # Authenticate the secret with the key.
        tag = hmac.new(
            key.encode("utf-8"),
            secret_bytes,
            hashlib.sha256,
        ).digest()[:self.TAG_BYTES]

        # Payload = secret + authentication tag.
        payload = secret_bytes + tag

        # The first 16 bits contain the secret length.
        length_bits = f"{len(secret_bytes):016b}"

        payload_bits = self._bytes_to_bits(payload)

        # Protect the payload bits using a deterministic mask
        # generated from the key.
        mask = self._make_mask(key, len(payload_bits))
        protected_bits = self._xor_bits(payload_bits, mask)

        bits = length_bits + protected_bits

        doc = pymupdf.open(stream=data, filetype="pdf")
        page = doc[0]

        for index, bit in enumerate(bits):
            x = self.START_X + (index * self.SPACING)

            if bit == "0":
                y = self.BASE_Y
            else:
                y = self.BASE_Y + self.BIT_OFFSET

            point = pymupdf.Point(x, y)

            page.draw_circle(
                point,
                radius=self.DOT_RADIUS,
                color=(0, 0, 0),
                fill=(0, 0, 0),
            )

        output = doc.tobytes()
        doc.close()

        return output

    def read_secret(
        self,
        pdf: PdfSource,
        key: str,
    ) -> str:

        if not key:
            raise ValueError("Key must be a non-empty string")

        data = load_pdf_bytes(pdf)

        doc = pymupdf.open(
            stream=data,
            filetype="pdf",
        )

        if len(doc) == 0:
            doc.close()
            raise SecretNotFoundError(
                "PDF contains no pages"
            )

        page = doc[0]
        drawings = page.get_drawings()

        dots = []

        for drawing in drawings:
            rect = drawing.get("rect")
            fill = drawing.get("fill")

            if rect is None:
                continue

            is_small = (
                1.0 <= rect.width <= 2.0
                and 1.0 <= rect.height <= 2.0
            )

            is_black = (
                fill is not None
                and all(value < 0.1 for value in fill)
            )

            if is_small and is_black:
                center_x = (rect.x0 + rect.x1) / 2
                center_y = (rect.y0 + rect.y1) / 2

                if 45 <= center_y <= 58:
                    dots.append((center_x, center_y))

        doc.close()

        if not dots:
            raise SecretNotFoundError(
                "No MicroDot watermark found"
            )

        dots.sort(key=lambda dot: dot[0])

        bits = ""

        for _, y in dots:
            if y < self.BASE_Y + (self.BIT_OFFSET / 2):
                bits += "0"
            else:
                bits += "1"

        if len(bits) < self.HEADER_BITS:
            raise SecretNotFoundError(
                "Incomplete MicroDot watermark"
            )

        # Decode the 16-bit length header.
        secret_length = int(
            bits[:self.HEADER_BITS],
            2,
        )

        # Payload contains secret + HMAC tag.
        payload_bytes_needed = (
            secret_length + self.TAG_BYTES
        )

        payload_bits_needed = payload_bytes_needed * 8

        protected_bits = bits[
            self.HEADER_BITS:
            self.HEADER_BITS + payload_bits_needed
        ]

        if len(protected_bits) != payload_bits_needed:
            raise SecretNotFoundError(
                "Incomplete MicroDot watermark"
            )

        # Recreate the key-derived mask.
        mask = self._make_mask(
            key,
            len(protected_bits),
        )

        payload_bits = self._xor_bits(
            protected_bits,
            mask,
        )

        payload = self._bits_to_bytes(payload_bits)

        secret_bytes = payload[:secret_length]
        stored_tag = payload[
            secret_length:
            secret_length + self.TAG_BYTES
        ]

        expected_tag = hmac.new(
            key.encode("utf-8"),
            secret_bytes,
            hashlib.sha256,
        ).digest()[:self.TAG_BYTES]

        if not hmac.compare_digest(
            stored_tag,
            expected_tag,
        ):
            raise InvalidKeyError(
                "Invalid key for MicroDot watermark"
            )

        try:
            return secret_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SecretNotFoundError(
                "Could not decode MicroDot secret"
            ) from exc