# Detection rules
Rules will provide indicators for suspicious activity. An alert does not prove that an attack has happend.

# Repeated failed login attempts 
Detects: Repeated faild authentication attempts from the same observed IP.
Threshold: 3 faild attemps within 60 sec.
Alert: repeated_failed_login

# repeted denied document access
Detects: Repeated denied document access attempts from the sam observed IP.
Thresehold: 3 denied attempts - 60 sec
Alert: repeated_denied_document_access

# Repeated RMAP authentication failures
Detects: Repeated failed RMAP authentication attempts from the same IP.
Threshold: 3 failed attempts - 60 sec
Alert: repeated_rmap_authentication failures

# Repeated server errors
Detects: Multiple HTTP 5xx responses
Threshold: 3 server errors within 60 sec.
Alert: repeated_server_errors

# Token use from multiple IP addresses
Detects: Use of the same valid authentication token from multiple IP addresses.
Threshold: The same token observed from at least 2 different IP addresses within 10 min.
Alert: token_multi_ip_use

