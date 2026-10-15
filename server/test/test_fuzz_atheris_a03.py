import atexit
import sys
import uuid
import atheris
from sqlalchemy import text
from collections import Counter

with atheris.instrument_imports():
    from server import app

client = app.test_client()

stats = Counter()
examples = []

user_id = None
email = None
password = None

def cleanup():
    """Delete the isolated test user."""

    print("\nA-03 FINAL STATISTICS", dict(stats), flush=True)

    for example in examples:
        print("EXAMPLE", example, flush=True)

    if user_id is None:
        return

    try:
        with app.config["_ENGINE"].begin() as conn:
            conn.execute(
                text("DELETE FROM Users WHERE id = :id"),
                {"id": user_id},
            )

        print("A-03 cleanup finished.", flush=True)

    except Exception as exc:
        print("CLEANUP ERROR:", repr(exc), flush=True)


def prepare():
    """Create one user and verify that normal login works."""

    global user_id, email, password

    unique = uuid.uuid4().hex

    email = f"a03-{unique}@example.com"
    login = f"a03-{unique}"
    password = "a03-test-password"

    response = client.post(
        "/api/create-user",
        json={
            "email": email,
            "login": login,
            "password": password,
        },
    )

    assert response.status_code == 201, (
        "Could not create test user",
        response.status_code,
        response.get_json(silent=True),
    )

    user_id = response.get_json()["id"]

    response = client.post(
        "/api/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200, (
        "Valid login control failed",
        response.status_code,
        response.get_json(silent=True),
    )

    result = response.get_json()

    assert isinstance(result.get("token"), str)
    assert isinstance(result.get("expires_in"), int)
    assert not isinstance(result.get("expires_in"), bool)

    print(
        f"Prepared user={user_id}; "
        "valid login control HTTP 200",
        flush=True,
    )

def record_issue(mode, body, status, result, reason):
    """Record interesting behavior without stopping fuzzing."""

    stats[f"issue:{reason}"] += 1

    if len(examples) < 15:
        example = {
            "mode": mode,
            "reason": reason,
            "status": status,
            "body": repr(body)[:250],
            "response": repr(result)[:250],
        }

        examples.append(example)
        print("A03_FINDING", example, flush=True)

def fuzz_one(data):
    if not data:
        return

    fdp = atheris.FuzzedDataProvider(data)

    # First byte chooses a test scenario.
    # Remaining bytes are consumed as mutated inputs.
    mode_number = fdp.ConsumeIntInRange(0, 9)

    mutated_email = fdp.ConsumeUnicodeNoSurrogates(100)
    mutated_password = fdp.ConsumeUnicodeNoSurrogates(100)

    body = None
    mode = ""

    if mode_number == 0:
        mode = "valid_login"
        body = {
            "email": email,
            "password": password,
        }

    elif mode_number == 1:
        mode = "missing_email"
        body = {"password": password}

    elif mode_number == 2:
        mode = "missing_password"
        body = {"email": email}

    elif mode_number == 3:
        mode = "missing_both"
        body = {}

    elif mode_number == 4:
        mode = "wrong_password"
        body = {
            "email": email,
            "password": "incorrect-" + password,
        }

    elif mode_number == 5:
        mode = "unknown_email"
        body = {
            "email": "unknown-" + email,
            "password": password,
        }

    elif mode_number == 6:
        mode = "mutated_email"
        body = {
            "email": mutated_email,
            "password": password,
        }

    elif mode_number == 7:
        mode = "mutated_password"
        body = {
            "email": email,
            "password": mutated_password,
        }

    elif mode_number == 8:
        mode = "malformed_field_type"

        invalid_values = [
            None,
            0,
            True,
            [],
            {},
            [email],
            {"value": email},
        ]

        # Rotate values and fields so short fuzz inputs
        # still cover different malformed types.
        invalid_index = stats["malformed_count"]
        field = (
            "email" if invalid_index % 2 == 0
            else "password"
        )

        value = invalid_values[
            (invalid_index // 2) % len(invalid_values)
        ]

        stats["malformed_count"] += 1
        stats[f"malformed_field:{field}"] += 1

        body = {
            "email": email,
            "password": password,
        }

        body[field] = value

    else:
        mode = "non_object_json"

        values = [
            [],
            ["unexpected"],
            "unexpected",
            123,
            True,
        ]

        body = values[
            stats["non_object_count"] % len(values)
        ]

        stats["non_object_count"] += 1

    stats["cases"] += 1
    stats[f"mode:{mode}"] += 1

    response = client.post(
        "/api/login",
        json=body,
    )

    status = response.status_code
    result = response.get_json(silent=True)

    stats[f"http:{status}"] += 1
    stats[f"{mode}:http:{status}"] += 1

    # Oracle 1: successful login response structure.
    if status == 200:
        valid_response = (
            isinstance(result, dict)
            and isinstance(result.get("token"), str)
            and isinstance(result.get("expires_in"), int)
            and not isinstance(result.get("expires_in"), bool)
        )

        if not valid_response:
            record_issue(
                mode, body, status, result,
                "invalid_success_response",
            )

    # Oracle 2: the known valid credentials must work.
    if mode == "valid_login":
        if status == 200:
            stats["valid_login_success"] += 1
        else:
            record_issue(
                mode, body, status, result,
                "valid_login_rejected",
            )

    # Oracle 3: missing credentials must be rejected.
    if mode in (
        "missing_email",
        "missing_password",
        "missing_both",
    ):
        if status < 400:
            record_issue(
                mode, body, status, result,
                "missing_credentials_accepted",
            )
        else:
            stats["missing_credentials_rejected"] += 1

    # Security control: known invalid credentials
    # must not authenticate successfully.
    if mode in ("wrong_password", "unknown_email"):
        if status == 200:
            record_issue(
                mode, body, status, result,
                "invalid_credentials_accepted",
            )
        else:
            stats["invalid_credentials_denied"] += 1

    # Additional robustness observation.
    if status >= 500:
        stats["http_5xx"] += 1

        record_issue(
            mode, body, status, result,
            "server_error",
        )

    # Progress is printed during the campaign,
    # independently of the process exit behavior.
    if stats["cases"] % 500 == 0:
        print(
            "CHECKPOINT",
            stats["cases"],
            dict(stats),
            flush=True,
        )

if __name__ == "__main__":
    atexit.register(cleanup)

    prepare()

    defaults = {
        "max_total_time": "60",
        "max_len": "256",
        "print_final_stats": "1",
    }

    for option, value in defaults.items():
        if not any(
            arg.startswith(f"-{option}=")
            for arg in sys.argv[1:]
        ):
            sys.argv.append(f"-{option}={value}")

    atheris.Setup(sys.argv, fuzz_one)
    atheris.Fuzz()
