import time


class SecurityMonitor:
    """Monitor security-relevant events and evaluate detection rules."""

    def __init__(self):
        # Detection rule configuration
        self.failed_login_window_seconds = 60
        self.failed_login_threshold = 3

        self.denied_document_window_seconds = 60
        self.denied_document_threshold = 3

        self.server_error_window_seconds = 60
        self.server_error_threshold = 3

        self.rmap_auth_failure_window_seconds = 60
        self.rmap_auth_failure_threshold = 3

        self.token_multi_ip_window_seconds = 600
        self.token_multi_ip_threshold = 2

        # In-memory event state
        self.failed_login_attempts = {}
        self.denied_document_attempts = {}
        self.server_error_attempts = []
        self.rmap_auth_failures = {}
        self.token_ip_activity = {}
    
    def record_failed_login(self, ip, logger):
        """Record a failed login and alert on repeated attempts."""
        now = time.monotonic()

        attempts = self.failed_login_attempts.setdefault(ip, [])
        attempts[:] = [
            attempt_time
            for attempt_time in attempts
            if now - attempt_time < self.failed_login_window_seconds
        ]
        attempts.append(now)

        logger.warning(
            "Login failed: invalid credentials ip=%s attempts_last_60s=%s",
            ip,
            len(attempts),
        )

        if len(attempts) == self.failed_login_threshold:
            logger.warning(
                "SECURITY ALERT event=repeated_failed_login severity=warning "
                "ip=%s attempts=%s window_seconds=%s",
                ip,
                len(attempts),
                self.failed_login_window_seconds,
            )
        
    def record_denied_document_access(self, ip, user_id, document_id, logger):
        """Record denied document access and alert on repeated attempts."""
        now = time.monotonic()

        attempts = self.denied_document_attempts.setdefault(ip, [])
        attempts[:] = [
            attempt_time
            for attempt_time in attempts
            if now - attempt_time < self.denied_document_window_seconds
        ]
        attempts.append(now)

        logger.warning(
            "Document access denied: user_id=%s document_id=%s ip=%s "
            "reason=not_found_or_not_owned attempts_last_60s=%s",
            user_id,
            document_id,
            ip,
            len(attempts),
        )

        if len(attempts) == self.denied_document_threshold:
            logger.warning(
                "SECURITY ALERT event=repeated_denied_document_access severity=warning "
                "ip=%s attempts=%s window_seconds=%s",
                ip,
                len(attempts),
                self.denied_document_window_seconds,
            )
    
    def record_server_error(self, status_code, path, logger):
        """Record server errors and alert on repeated availability failures."""
        now = time.monotonic()

        self.server_error_attempts[:] = [
            event_time
            for event_time in self.server_error_attempts
            if now - event_time < self.server_error_window_seconds
        ]
        self.server_error_attempts.append(now)

        logger.warning(
            "Server error: status=%s path=%s errors_last_60s=%s",
            status_code,
            path,
            len(self.server_error_attempts),
        )

        if len(self.server_error_attempts) == self.server_error_threshold:
            logger.warning(
                "SECURITY ALERT event=repeated_server_errors severity=warning "
                "errors=%s window_seconds=%s",
                len(self.server_error_attempts),
                self.server_error_window_seconds,
            )
    
    def record_rmap_auth_failure(self, ip, endpoint, logger):
        """Record RMAP authentication failures and alert on repeated failures."""
        now = time.monotonic()

        attempts = self.rmap_auth_failures.setdefault(ip, [])
        attempts[:] = [
            attempt_time
            for attempt_time in attempts
            if now - attempt_time < self.rmap_auth_failure_window_seconds
        ]
        attempts.append(now)

        logger.warning(
            "RMAP authentication failed: endpoint=%s ip=%s attempts_last_60s=%s",
            endpoint,
            ip,
            len(attempts),
        )

        if len(attempts) == self.rmap_auth_failure_threshold:
            logger.warning(
                "SECURITY ALERT event=repeated_rmap_authentication_failures "
                "severity=warning ip=%s attempts=%s window_seconds=%s",
                ip,
                len(attempts),
                self.rmap_auth_failure_window_seconds,
            )
    
    def record_token_use(self, token_id, user_id, ip, logger):
        """Detect use of the same token from multiple observed IP addresses."""
        now = time.monotonic()

        events = self.token_ip_activity.setdefault(token_id, [])
        events[:] = [
            (event_time, event_ip)
            for event_time, event_ip in events
            if now - event_time < self.token_multi_ip_window_seconds
        ]

        previous_ips = {event_ip for _, event_ip in events}
        events.append((now, ip))
        observed_ips = previous_ips | {ip}

        if len(observed_ips) >= self.token_multi_ip_threshold and ip not in previous_ips:
            logger.warning(
                "SECURITY ALERT event=token_multi_ip_use severity=warning "
                "user_id=%s token_id=%s observed_ips=%s window_seconds=%s",
                user_id,
                token_id,
                len(observed_ips),
                self.token_multi_ip_window_seconds,
            )