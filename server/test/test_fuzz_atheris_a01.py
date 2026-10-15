
import atheris
import io
import sys
import uuid
import fitz
import shutil
import atexit 

from pathlib import Path
from sqlalchemy import text

with atheris.instrument_imports():
    from server import app

UPLOAD_ENDPOINT = "/api/upload-document"
PDF_SEED_PATH = Path(__file__).with_name("seed_valid_a01.pdf")
CORPUS_DIR = Path(__file__).with_name("corpus_a01_valid")

def create_authenticated_client():
    client = app.test_client()
    unique_id = uuid.uuid4().hex

    user_data = {
        "email": f"atheris-{unique_id}@example.com",
        "login": f"atheris-{unique_id}",
        "password": "atheris-test-password",
    }

    response = client.post("/api/create-user", json=user_data)
    if response.status_code != 201:
        raise RuntimeError(
            f"User creation failed: {response.status_code}"
        )

    response = client.post(
        "/api/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
        },
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Login failed: {response.status_code}"
        )

    token = response.get_json()["token"]
    engine = app.config["_ENGINE"]

    with engine.connect() as conn:
        test_user_id = conn.execute(
            text("SELECT id FROM Users WHERE login = :login"),
            {"login": user_data["login"]},
        ).scalar_one()

    user_dir = (
        Path(app.config["STORAGE_DIR"])
        / "files"
        / user_data["login"]
    ).resolve()

    return (
        client,
        {"Authorization": f"Bearer {token}"},
        test_user_id,
        engine,
        user_dir,
    )

CLIENT, HEADERS, TEST_USER_ID, ENGINE, USER_DIR = (
    create_authenticated_client()
)

def cleanup_test_documents():
    # Only retrieve documents owned by this Atheris test account.
    with ENGINE.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT id, path FROM Documents "
                "WHERE ownerid = :owner_id"
            ),
            {"owner_id": TEST_USER_ID},
        ).fetchall()

    # Verify every stored path belongs to this test user's directory.
    for row in rows:
        path = Path(row.path).resolve()
        try:
            path.relative_to(USER_DIR)
        except ValueError:
            raise RuntimeError(
                f"Refusing to delete a file outside the test directory: {path}"
            )

    # Delete only files inside this dedicated test user's directory.
    for row in rows:
        path = Path(row.path).resolve()
        if path.is_file():
            path.unlink()

    # Remove only this test user's document records.
    with ENGINE.begin() as conn:
        conn.execute(
            text(
                "DELETE FROM Documents WHERE ownerid = :owner_id"
            ),
            {"owner_id": TEST_USER_ID},
        )

    # Remove orphaned files from this test user's directory.
    if USER_DIR.is_dir():
        for path in USER_DIR.iterdir():
            if path.is_symlink():
                path.unlink()
            elif path.is_file():
                path.unlink()

def cleanup_test_user():
    try:
        cleanup_test_documents()

        with ENGINE.begin() as conn:
            conn.execute(
                text("DELETE FROM Users WHERE id = :id"),
                {"id": TEST_USER_ID},
            )

        if USER_DIR.is_dir() and not any(USER_DIR.iterdir()):
            USER_DIR.rmdir()

        print("A-01 test user cleanup finished.", flush=True)

    except Exception as exc:
        print("A-01 cleanup error:", repr(exc), flush=True)

def is_parseable_pdf(data):
    try:
        with fitz.open(stream=data, filetype="pdf") as pdf:
            return pdf.is_pdf and pdf.page_count >= 1
    except Exception:
        return False
    
def make_valid_pdf(data):
    pdf = fitz.open()
    try:
        page = pdf.new_page(width=300, height=300)

        text_content = "Fuzz input: " + data[:128].hex()
        page.insert_text(
            (30, 50),
            text_content,
            fontsize=8,
        )

        return pdf.tobytes()
    finally:
        pdf.close()

TOTAL_TESTS = 0
INVALID_ACCEPTED = 0
VALID_ACCEPTED = 0
VALID_REJECTED = 0

def TestOneInput(data):
    global TOTAL_TESTS, INVALID_ACCEPTED
    global VALID_ACCEPTED, VALID_REJECTED

    try:
        # Test 1: Raw mutated bytes from Atheris
        response = CLIENT.post(
            UPLOAD_ENDPOINT,
            headers=HEADERS,
            data={
                "file": (
                    io.BytesIO(data),
                    "atheris-mutated.pdf",
                )
            },
        )

        valid_pdf = is_parseable_pdf(data)

        if response.status_code == 201:
            if valid_pdf:
                VALID_ACCEPTED += 1
            else:
                INVALID_ACCEPTED += 1

        if response.status_code >= 500:
            raise AssertionError(
                f"Server error for mutated input: HTTP {response.status_code}"
            )

        # Test 2: A valid PDF generated from fuzz input
        generated_pdf = make_valid_pdf(data)

        assert is_parseable_pdf(generated_pdf), (
            "Generated PDF is not valid"
        )

        response = CLIENT.post(
            UPLOAD_ENDPOINT,
            headers=HEADERS,
            data={
                "file": (
                    io.BytesIO(generated_pdf),
                    "atheris-valid.pdf",
                )
            },
        )

        if response.status_code == 201:
            VALID_ACCEPTED += 1
        else:
            VALID_REJECTED += 1
            raise AssertionError(
                f"Valid PDF rejected: HTTP {response.status_code}"
            )

        TOTAL_TESTS += 1

        if TOTAL_TESTS % 1000 == 0:
            print(
                f"Iterations: {TOTAL_TESTS} | "
                f"Invalid accepted: {INVALID_ACCEPTED} | "
                f"Valid accepted: {VALID_ACCEPTED} | "
                f"Valid rejected: {VALID_REJECTED}",
                flush=True,
            )

    finally:
        cleanup_test_documents()

def run_baseline_tests():
    print("\n=== Upload-document baseline tests ===", flush=True)

    valid_pdf = make_valid_pdf(b"baseline")

    test_cases = [
        ("Plain text", b"Hello, this is not a PDF"),
        ("Empty file", b""),
        ("Malformed PDF", b"%PDF-1.7\nbroken content"),
        ("Valid PDF", valid_pdf),
    ]

    try:
        for label, content in test_cases:
            response = CLIENT.post(
                UPLOAD_ENDPOINT,
                headers=HEADERS,
                data={
                    "file": (
                        io.BytesIO(content),
                        "baseline.pdf",
                    )
                },
            )

            valid = is_parseable_pdf(content)
            expected = 201 if valid else 400
            passed = (
                response.status_code == 201
                if valid
                else 400 <= response.status_code < 500
            )

            print(
                f"{label}: HTTP {response.status_code} | "
                f"Expected: {'201' if valid else '4xx'} | "
                f"{'PASS' if passed else 'FAIL'}",
                flush=True,
            )

        for label, headers in [
            ("No authentication", {}),
            ("Invalid token", {"Authorization": "Bearer invalid-token"}),
        ]:
            response = CLIENT.post(
                UPLOAD_ENDPOINT,
                headers=headers,
                data={
                    "file": (
                        io.BytesIO(valid_pdf),
                        "baseline.pdf",
                    )
                },
            )

            passed = response.status_code == 401

            print(
                f"{label}: HTTP {response.status_code} | "
                f"Expected: 401 | "
                f"{'PASS' if passed else 'FAIL'}",
                flush=True,
            )

    finally:
        cleanup_test_documents()

    print("=== Baseline tests completed ===\n", flush=True)

def main():
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    if not PDF_SEED_PATH.is_file():
        raise FileNotFoundError(
            f"PDF seed not found: {PDF_SEED_PATH}"
        )

    seed_destination = CORPUS_DIR / PDF_SEED_PATH.name

    if not seed_destination.exists():
        shutil.copyfile(PDF_SEED_PATH, seed_destination)

    fuzz_args = [
        sys.argv[0],
        str(CORPUS_DIR),
        "-max_total_time=60",
        "-max_len=4096",
        "-print_final_stats=1",
        *sys.argv[1:],
    ]

    run_baseline_tests()
    
    atheris.Setup(fuzz_args, TestOneInput)
    atheris.Fuzz()

atexit.register(cleanup_test_user)

if __name__ == "__main__":
    main()
