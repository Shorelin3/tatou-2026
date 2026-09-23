import json
import os
import tempfile
import urllib.request
from pathlib import Path

import sys

sys.path.insert(0, "server/src")

import watermarking_utils as WMUtils
from rmap import RMAPClient


BASE_URL = "http://127.0.0.1:5000"
IDENTITY = "Group_15"
PRIVATE_KEY = "server/keys/server-private.asc"
PUBLIC_KEY = "server/keys/server-public.asc"


def load_env():
    values = {}

    with open(".env", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            values[key] = value

    return values


def post_json(endpoint, payload):
    request = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read())


def get_pdf(endpoint):
    request = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        method="GET",
    )

    with urllib.request.urlopen(request) as response:
        return response.status, response.read()


def main():
    env = load_env()

    passphrase = env.get("RMAP_KEY_PASSPHRASE")
    watermark_key = env.get("RMAP_WATERMARK_KEY")
    watermark_method = env.get(
        "RMAP_WATERMARK_METHOD",
        "visible-hmac",
    )

    if not passphrase:
        raise RuntimeError("RMAP_KEY_PASSPHRASE not found in .env")

    if not watermark_key:
        raise RuntimeError("RMAP_WATERMARK_KEY not found in .env")

    client = RMAPClient(
        IDENTITY,
        PRIVATE_KEY,
        PUBLIC_KEY,
        passphrase=passphrase,
    )

    # ------------------------------------------------------------
    # 1. Message 1 -> Response 1
    # ------------------------------------------------------------

    msg1 = client.build_msg1()
    resp1 = post_json("/rmap-initiate", msg1)
    client.process_resp1(resp1)

    print("[PASS] Message 1 -> Response 1")
    print(f"[PASS] Expected link: {client.expected_link}")

    # ------------------------------------------------------------
    # 2. Message 2 -> Response 2
    # ------------------------------------------------------------

    msg2 = client.build_msg2()
    resp2 = post_json("/rmap-get-link", msg2)
    link = client.process_resp2(resp2)

    print("[PASS] Message 2 -> Response 2")
    print(f"[PASS] Returned link: {link}")

    # ------------------------------------------------------------
    # 3. Verify RMAP link
    # ------------------------------------------------------------

    assert link == client.expected_link
    assert len(link) == 32
    assert all(c in "0123456789abcdef" for c in link)

    print("[PASS] Returned link matches expected RMAP link")
    print("[PASS] Link is 32 lowercase hexadecimal characters")

    # ------------------------------------------------------------
    # 4. Retrieve the generated PDF
    # ------------------------------------------------------------

    status, pdf_bytes = get_pdf(f"/api/get-version/{link}")

    assert status == 200
    assert pdf_bytes.startswith(b"%PDF")

    print("[PASS] Generated PDF retrieved through /api/get-version")
    print(f"[PASS] HTTP status: {status}")
    print(f"[PASS] PDF size: {len(pdf_bytes)} bytes")

    # ------------------------------------------------------------
    # 5. Verify the watermark
    # ------------------------------------------------------------

    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False,
    ) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(pdf_bytes)

    try:
        watermark = WMUtils.read_watermark(
            method=watermark_method,
            pdf=str(temp_path),
            key=watermark_key,
        )

        assert watermark == IDENTITY

        print("[PASS] Watermark successfully read from generated PDF")
        print("[PASS] Watermark identity matches Group_15")

    finally:
        temp_path.unlink(missing_ok=True)

    print()
    print("RMAP END-TO-END TEST: SUCCESS")


if __name__ == "__main__":
    main()