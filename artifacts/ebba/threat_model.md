# Threat model
I used STRIDE and did a risk assessment and attack trees for attack scenarios. 

# Assets
PDF documents
User accounts and identities
Authentication tokens
Ownership metadata
Watermark data and secret
Document links
Database content
Security logs and telemetry

# STRIDE threat model

1. Spoofing

Threat: An attacker may impersonate a user by obtaining credentials or a bearer token, or by guessing login credentials.

Security requirement: Restricted routes require reliable authentication. Failures should be observable and repeated suspicious login attempts should be detectable.

Assets affected:
- User accounts and identities
- Authentication tokens
- PDF documents

2. Tampering 
Threat: An attacker who can modify stored documents or security-relevant metadata could undermine document integrity, ownership or watermark traceability.

Security requirement: Unauthorized modification of documents should be prevented and leave evidence for later investigation. 

Assets affected:
- PDF documents
- Ownership metdata
- Watermark data
- Database content

3. Repudiation
Threat: A user or attacker may deny having performed an action, e.g. uploaded a document and that should be traceable. 

Security requirement: Should leave an audit trail. 

Assets affected:
- PDF documents
- Ownership metadata
- Security logs and telemetry

4. Information disclosure
Threat: Unauthorized  disclosure of confidential PDFs, watermark secrets, authentication material. An authenticated user may also attempt to access another users document. 

Security requirement: Access to documents must be restricted to authorized users. Unauthorized access attempts should be observable. Sensitive info should not be exposed in security logs. 

Assets affected:
- PDF documents
- Authentication tokens
- Watermark data and secrets
- Document links
- Database content

5. Denial of service
Threat: An attacker could exhaust application workers, database or document resources and make Tatou unavailable. 

Security requirement: Application and database availability should be observable. 

Assets affected:
- Tatou application availability
- Database availability

6. Elevation of privilege
Threat: A user may try to use authenticated functionality outside the permissions intended for that identity, especially by supplying identifiers for documents owned by another user. 

Security requirement: Authorization must ensure that authenticated users have the right permissions.

Assets affected:
- PDF docuemnts
- Ownership metadata
- Database content

# Risk assessment 

Threat
1. Unauthorized access to another user's document - Likelihood: High, Impact: High, Risk: High
2. Credential guessing / repeated failed logins - Likelihood: medium, Impact: High, Risk: High
3. Disclosure of sensitive information - Likelihood: medium, Impact: High, Risk: High
4. Unauthorized modification of documents or metadata - Likelihood: medium, Impact: High, Risk: High
5. Service disruption / resource exhaustion - Likelihood: medium, Impact: medium/High, Risk: medium/High
6. Loss of security logs / insufficient log retention - Likelihood: medium, Impact: High, Risk: High

# Attack trees
see the svg files.










