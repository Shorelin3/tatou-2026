import logging

from server import create_app

def test_repeated_failed_logins_trigger_alert(monkeypatch, caplog):
    class EmptyResult:
        def first(self):
            return None

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, statement, params=None):
            return EmptyResult()

    class FakeEngine:
        def connect(self):
            return FakeConnection()

    test_app = create_app()
    monkeypatch.setitem(test_app.config, "_ENGINE", FakeEngine())
    client = test_app.test_client()

    with caplog.at_level(logging.WARNING, logger="server"):
        for _ in range(3):
            response = client.post(
                "/api/login",
                json={
                    "email": "nonexistent-test@example.invalid",
                    "password": "wrong-test-password",
                },
            )
            assert response.status_code == 401

    assert "attempts_last_60s=1" in caplog.text
    assert "attempts_last_60s=2" in caplog.text
    assert "attempts_last_60s=3" in caplog.text
    assert (
        "SECURITY ALERT event=repeated_failed_login severity=warning"
        in caplog.text
    )
    assert "attempts=3 window_seconds=60" in caplog.text


def test_get_document_database_error_is_logged_and_hidden(monkeypatch, caplog):
    class FailingEngine:
        def connect(self):
            raise RuntimeError(
                "simulated database failure with internal details"
            )

    test_app = create_app()
    monkeypatch.setitem(test_app.config, "_ENGINE", FailingEngine())
    client = test_app.test_client()

    # Create a valid test token using the application's serializer.
    with test_app.test_request_context():
        from flask import current_app
        from itsdangerous import URLSafeTimedSerializer

        serializer = URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"],
            salt="tatou-auth",
        )
        token = serializer.dumps({"uid": 3, "login": "test-user"})

    with caplog.at_level(logging.ERROR, logger="server"):
        response = client.get(
            "/api/get-document/999999",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 503
    assert response.get_json()["error"] == "service unavailable"
    assert "Document retrieval failed: db error" in caplog.text
    assert (
        "simulated database failure with internal details"
        not in response.get_data(as_text=True)
    )


def test_repeated_denied_document_access_triggers_alert(caplog):
    from security_monitoring import SecurityMonitor

    monitor = SecurityMonitor()
    logger = logging.getLogger("test_security_monitor")

    with caplog.at_level(logging.WARNING):
        monitor.record_denied_document_access(
            "127.0.0.1", 3, 1, logger
        )
        monitor.record_denied_document_access(
            "127.0.0.1", 3, 1, logger
        )
        monitor.record_denied_document_access(
            "127.0.0.1", 3, 1, logger
        )

    assert (
        "SECURITY ALERT event=repeated_denied_document_access "
        "severity=warning"
        in caplog.text
    )


def test_repeated_server_errors_trigger_alert(caplog):
    from security_monitoring import SecurityMonitor

    monitor = SecurityMonitor()
    logger = logging.getLogger("test_security_monitor")

    with caplog.at_level(logging.WARNING):
        monitor.record_server_error(503, "/healthz", logger)
        monitor.record_server_error(503, "/healthz", logger)
        monitor.record_server_error(503, "/healthz", logger)

    assert (
        "SECURITY ALERT event=repeated_server_errors severity=warning"
        in caplog.text
    )


def test_repeated_rmap_auth_failures_trigger_alert(caplog):
    from security_monitoring import SecurityMonitor

    monitor = SecurityMonitor()
    logger = logging.getLogger("test-rmap-monitoring")

    for _ in range(3):
        monitor.record_rmap_auth_failure(
            "192.0.2.10",
            "/rmap-initiate",
            logger,
        )

    assert "event=repeated_rmap_authentication_failures" in caplog.text


def test_same_token_from_multiple_ips_triggers_alert(caplog):
    from security_monitoring import SecurityMonitor

    monitor = SecurityMonitor()
    logger = logging.getLogger("test-token-monitoring")

    monitor.record_token_use(
        "abc123def456",
        42,
        "192.0.2.10",
        logger,
    )

    monitor.record_token_use(
        "abc123def456",
        42,
        "192.0.2.20",
        logger,
    )

    assert "event=token_multi_ip_use" in caplog.text


def test_same_token_from_same_ip_does_not_trigger_alert(caplog):
    from security_monitoring import SecurityMonitor

    monitor = SecurityMonitor()
    logger = logging.getLogger("test-token-monitoring-same-ip")

    for _ in range(3):
        monitor.record_token_use(
            "abc123def456",
            42,
            "192.0.2.10",
            logger,
        )

    assert "event=token_multi_ip_use" not in caplog.text