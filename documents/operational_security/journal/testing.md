# Testing and Validation

The security logging and monitoring functionality was tested using controlled
security events and automated tests.

# Repeated Failed Login Attempts

Repeated failed login attempts were generated against the local deployment.
After three failed attempts from the same observed IP within 60 seconds, the
monitor generated a security alert.
The logs showed the number of failed attempts increasing before the alert was
triggered.

Result: Detection and alert generation worked as expected.


# Repeated Denied Document Access

Two different test users were used to test document ownership enforcement.

One user attempted to access a document belonging to the other user. The
requests were denied without returning the document.
After three denied requests, the monitor generated:
repeated_denied_document_access
The logs contained the authenticated user ID, requested document ID, observed
IP and reason for the denial.

Result: Unauthorized access was denied and repeated attempts were detected.


# Repeated RMAP Authentication Failures

Invalid requests were sent to the RMAP functionality.
Three failed authentication attempts within the configured 60-second window
generated:
repeated_rmap_authentication_failures

Result: Repeated RMAP authentication failures were detected as expected.


# Token Use From Multiple IP Addresses

The token monitoring rule was tested using automated tests that simulated the
same valid token fingerprint being used from different IP addresses.
The test verified that use from two different IP addresses generated:
token_multi_ip_use
A separate test verified that repeated use of the same token from the same IP
address did not generate the alert.

Result: Both the positive and negative cases passed.

## Repeated Server Errors

The repeated server error rule was tested using an automated test.
The test verified that the configured number of server errors generated the
expected security alert.

Result: The automated test passed.

# Secret Link Redaction

Testing of the general HTTP logging revealed that secret document links were
included in request paths.
A redaction mechanism was added. The first implementation did not correctly
remove the sensitive value from the actual log output.
After correcting the implementation, the test confirmed that the sensitive
part of the path was replaced with:

<redacted>
Result: Secret document links are no longer included in the tested HTTP
log output.


# Health Check

The /healthz endpoint was used during local testing to check application and
database connectivity.
The endpoint performs a database connectivity check and is intended to return
a successful health response when the application can communicate with the
database.
