import uuid

from sqlalchemy import text
from server import app

def main():
    client = app.test_client()
    unique = uuid.uuid4().hex

    email = f"a03-{unique}@example.com"
    login = f"a03-{unique}"
    password = "a03-test-password"
    user_id = None

    try:
        # Create an isolated test user.
        response = client.post(
            "/api/create-user",
            json={
                "email": email,
                "login": login,
                "password": password,
            },
        )

        assert response.status_code == 201, (
            f"User creation failed: "
            f"{response.status_code} {response.get_json()}"
        )

        user_id = response.get_json()["id"]
        print(f"Test user created: ID {user_id}")

        cases = [
            (
                "VALID LOGIN",
                {"email": email, "password": password},
            ),
            (
                "MISSING EMAIL",
                {"password": password},
            ),
            (
                "MISSING PASSWORD",
                {"email": email},
            ),
            (
                "WRONG PASSWORD",
                {"email": email, "password": "wrong-password"},
            ),
            (
                "UNKNOWN EMAIL",
                {
                    "email": f"unknown-{unique}@example.com",
                    "password": password,
                },
            ),
            (
                "EMAIL AS LIST",
                {"email": [email], "password": password},
            ),
            (
                "EMAIL AS OBJECT",
                {"email": {"value": email}, "password": password},
            ),
            (
                "PASSWORD AS LIST",
                {"email": email, "password": [password]},
            ),
        ]

        for name, body in cases:
            response = client.post("/api/login", json=body)
            result = response.get_json(silent=True)

            if name == "VALID LOGIN":
                assert response.status_code == 200, (
                    f"Valid login failed: {response.status_code}"
                )
                assert isinstance(result, dict)
                assert isinstance(result.get("token"), str)
                assert isinstance(result.get("expires_in"), int)
                assert not isinstance(result.get("expires_in"), bool)
                assert result.get("token_type") == "bearer"

                print(
                    f"{name}: HTTP {response.status_code}; "
                    f"token=str; "
                    f"expires_in={result['expires_in']}"
                )
            else:
                print(
                    f"{name}: HTTP {response.status_code}; "
                    f"response={result}"
                )

                if name in ("MISSING EMAIL", "MISSING PASSWORD"):
                    assert response.status_code >= 400, (
                        f"{name} was not rejected"
                    )

                if response.status_code >= 500:
                    print(
                        f"POTENTIAL ROBUSTNESS BUG: {name} "
                        f"returned HTTP {response.status_code}"
                    )

    finally:
        if user_id is not None:
            engine = app.config["_ENGINE"]

            with engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM Users WHERE id = :id"),
                    {"id": user_id},
                )

            print("Baseline cleanup finished.")

if __name__ == "__main__":
    main()
