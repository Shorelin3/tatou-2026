# Security Incident report

## 1. Incident information

Incident ID: Uploads-2026-09-25
Date of discovery: 2026-09-25
Date of reporting: 2026-10-12
Reported by: Ebba
Responsible person: Ebba
Status: Further verification required


## 2. Incident summary

During a review of the Tatou server storage, a large number of files were discovered that had previously been uploaded by other users or groups. Some of the discovered files had unexpected file types and names, including .pkl and .dill files.

The discovered files were removed from the server. Later, the upload functionality was changed to restrict document uploads to PDF files.
 
## 3. Detection 

The incident was discovered manually during a review of the server storage and database. 
Alert: No automated security alert. 

## 4. Classification
Type: Suspicious/unexpected file uploads

Severity:
Medium

Reason for classification:
A large number of unexpected files had been uploaded and stored on the deployed server. Some of the files had file types and names that were not expected for normal PDF document uploads. The purpose and impact of the files could not be determined.


## 5. Timeline
|Time/Date.          |  Event                                          |  
-----------------------------------------------------------------------
Before 2026-09-25    | Files were uploaded to the deployed server.     |
2026-09-25           | Discovered during a reviwe of the storage       |
2026-09-25.          | Disovred files were removed                     |
2026-10-12           | Upload was changes to restrict document uploads to PDF files|
Pending              | Further verification of the PDF upload restriction |


## 6. Investigation
What was investigated?
The group reviewed the server storage and database and discovered a large number of previously uploaded files from other users or groups.
Examples of discovered files included:
- Hacker1/method2
- g19test/g19probe.pdf
- flagreader.pkl
- evil.pkl
- svc_prob.dill
- test.pdf

Evidence collected:
- Files present in the server storage.
- Information about uploaded documents in the database.  

Was the attack successful: Unknown, they could upload files that we belived was malicoius but dont know if the attack then were successful.

Suspected cause: The upload functionality allowed unexpected file types to be uploaded and stored by the application. 

## 7. Impact assessment
Data compromised: No confirmed data compromise was identified. 
Service disruption: No known service disruption
Other impact: Unexpected files were stored on the server.  

## 8. Response 

Actions taken:
1. The discovered files were documented.
2. The discovered files were removed from the server.
3. The upload functionality was later changed to restrict document uploads to PDF files, (when writing this no commit has been made yet)

Git commit id: --

## 9. Verification
How was the fix verified?
The upload restriction has not yet been fully verified. Further testing is required to determine whether the application only accepts actual PDF files or whether a non-PDF file could still be accepted by using a .pdf filename.

- Security issue addressed: verification pending
- Application functionality verified: no

## 10. Lessons learned and limitations
Unexpected uploaded files should be investigated and documented to determine their possible impact. Upload functionality should restrict which types of files can be stored by the application.
Limitations: There was not enough historical logging and monitoring available to determine the purpose of all discovered files or exactly when and why they had been uploaded. The new PDF upload restriction also needs further verification to determine whether it validates the actual file or only its filename/extension.

## 11. Final status

Incident status: Further verification required

## 12. Other comments
The discovered files cannot all be confirmed as malicious. They are documented as suspicious or unexpected uploads based on the available evidence.