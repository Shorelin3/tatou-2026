# Monitoring

# Security monitoring
Security events are evaluted by the SecurityMonitor component. 

The monitor keeps tack of recent events and generates SECURITY ALERTS log entries when config conditions are reached. 
The implemented detection rules are documented in detection_rules.md

# Operator monitoring
The tool tool/security_monitor.py ca be used to follow the application logs and display events and alerts.
It filter:
- Security alerts
- Failed logins
- Denied document access
- Server errors
- RMAP authentication failures

This will give the operator a view of security events without requiring all log output to be reviewd manually. 

## Availability Monitoring

The /healthz endpoint provides a basic health check for the application and
database connectivity.

HTTP response status and request duration provide additional information when
investigating availability problems.

Repeated server errors can also be detected by the SecurityMonitor.


# Log Retention

Docker log rotation is configured for the application container using the
json-file logging driver.

The configured limits are:

- Maximum log file size: 10 MB
- Maximum number of log files: 5

This prevents container logs from growing without bounds.

The configuration provides bounded local log retention and should not be considered permanent or centralized log storage.


# Limitations

- Monitoring state is stored in memory and is lost when the application restarts, (wasent sure on how to exactly fix this)
- Log rotation means that older security evidence can eventually be removed.
- Security alerts indicate activity that should be investigated.
