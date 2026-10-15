# Security Incident report

## 1. Incident information

Incident ID: FLAG1-2026-09-11
Date of discovery: 2026-09-11
Date of reporting: 2026-10-10
Reported by: Ebba
Responsible person: Ebba
Status: Resolved


## 2. Incident summary

Flag 1 was exposed through the projects GitHub repository and was captured by another group. The flag file had been included in the repository, making the secret accessible outside the intended deployment environmet. 

## 3. Detection 

The incident was discovered when the group got a notification from the Nicolas, that the flag 1 had been captured. 
Alert: No automated security alert. 

## 4. Classification
Type: Sensitive information exposure/ flag exposure

Severity:
High

Reason for classification:
A secret flag was exposed and obtained by another group.This was therefore a confirmed confidentiality breach rather than only an attempted attack.

## 5. Timeline
|Time/Date.          |  Event                                |  
--------------------------------------------------------------
Before 2026-09-11.   | Flag 1 was included in the GitHub repository.
2026-09-11.          | Discovered flag 1 had been captured.  |
2026-09-12.          | Flag was replaced                     |
2026-09-12.          | The flag file was added to .gitignore |


## 6. Investigation
What was investigated?
The group investigated how Flag 1 could have been exposed and identified that the flag had been uploaded to the Github repository.

Evidence collected:
- The flag file had been included in the repository.
- Confirmation on email that the flag 1 had been captured.  

Was the attack successful: Yes

Suspected cause: Sensitive secret material was included in the soure control. 

## 7. Impact assessment
Data compromised: Flag 1
Service disruption: No known service disruption
Other impact: The flag could no longer be considered secret. 

## 8. Response 

Actions taken:
1. The compromsed flag was replaced
2. The flag file was added to .gitignore to reduce risk of accidentally commiting it again. 
3. Look at the repository that the flag file was no longer there. 

Git commit id: 064d083

## 9. Verification
How was the fix verified?
Look at the repository that the flag file was no longer there. 

- Security issue addressed: yes
- Application functionality verified: yes

## 10. Lessons learned and limitations
Secret such as flag should not be stored in the source control. Adding the flag to .gitignore helps prevent future accidental commits. 
Limitations: The compromise was not identifed troughout automated application monitoring. 

## 11. Final status

Incident status: Resolved

## 12. Other comments
