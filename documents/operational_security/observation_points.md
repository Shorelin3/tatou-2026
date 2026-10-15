## Observation points

## Login & authentication
Failed login attempts and request with missing, invalid or expired authentication are logged.
Info including the source IP and authentication failure. Valid authentication tokens can also be correlated using a derived token fingerprint without logging the raw token.
Visibility: Credential guessing, authentication failures and token usage. 

## Document access
Successful and denied documents access i slogged with info:
- User ID
- Document ID
- Source IP
This will make it possible to investigate unauthorized document access attempts and repeated attempts to access document beloging to another user. 

# Document uploads
Document that are uploaded are logged:
- User ID
- Document ID
- Source IP
Provides an audit trail 
But the log event does not determine whether an file is malicious. 

# Watermark operations
Creation of watermarks logged:
- User ID
- Document ID
- Version
- Method
- Source IP
Secrets, keys and link are not included. 

# Plugin loading
Plugin loading is logged with info about the user, filename, watermark method and source IP. 
Provides an audit trail but does not determine whether a plugin is safe. 

# RMAP authentication
Failed RMAP authentication attemps are logged with the source IP. 

# HTTP request & server errors
HTTP telemetry:
- HTTP method
- Request path
- Response status
- Request duration
- Source IP

# Application and database health
The health endpoint checks application operation and database connectivity.

# Limitations
Older events may lack sufficient telemetry if they occured before the logging was implemented. 
A logged event does not prove malicious activity.
