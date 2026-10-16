# Specialization A – Collection of Bugs Discovered

This document describes the bugs identified during Atheris fuzz testing of the Tatou API, their impact, the implemented fixes, and the subsequent verification.

The complete fuzzing results are documented in [fuzzing_results.md](fuzzing_results.md).

Regression tests and their outcomes are documented separately in [non_regression_tests.md](non_regression_tests.md).

## A-01 - Insufficient PDF Validation

Endpoint: POST /api/upload-document

### Bug Description

The upload endpoint accepted files with invalid PDF content.

Files containing plain text, empty content, or malformed PDF data could be accepted when uploaded as PDF files.

The original implementation did not adequately verify that uploaded files contained valid PDF structures.

### Impact

The endpoint could store files that were not valid PDF documents.

### Fix Implemented

PDF content validation was introduced using PyMuPDF (`fitz`).

The updated implementation:

- Attempts to open uploaded content as a PDF.
- Verifies that the document is a PDF containing at least one page.
- Rejects invalid PDF content with HTTP 400.
- Resets the file stream before continuing with the upload process.

### Verification

Before the fix, the Atheris campaigns demonstrated that invalid PDF content was accepted.

After the fix, no invalid PDFs were accepted at the recorded checkpoint of 2,000 test cases.

A later verification campaign also observed HTTP 400 responses for invalid content and HTTP 201 responses for valid PDF uploads.

See [A-01 – PDF Upload Results](fuzzing_results.md#a-01--pdf-upload-results).

## A-02 - Missing Document Ownership Verification

Endpoint: POST /api/create-watermark

### Bug Description

The endpoint required authentication but did not properly verify that the authenticated user owned the document being watermarked.

Consequently, an authenticated user could create a watermarked version of a document belonging to another user.

The database lookup identified the document by its ID without sufficiently restricting access based on its owner.

### Impact

This represented a broken access control vulnerability.

An authenticated user could perform an operation on another user's document without authorization, violating the intended document ownership restrictions.

### Fix Implemented

Document ownership verification was introduced in the database lookup.

The query was updated to require both the document ID and the authenticated user's ID:

```sql
WHERE id = :id AND ownerid = :ownerid
```

This prevents users from creating watermarked versions of documents they do not own.

### Verification

The initial Atheris campaign recorded 1,300 unauthorized watermark creations at checkpoint 1,300.

After the fix, a follow-up campaign recorded zero unauthorized watermark creations and 6,900 rejected unauthorized attempts at checkpoint 6,900.

Further fuzzing campaigns also observed no unauthorized watermark creations.

See [A-02 – Create Watermark Results](fuzzing_results.md#a-02--create-watermark-results).

## A-02 - Insufficient Input Validation in Watermark Creation 

Endpoint: POST /api/create-watermark

### Bug Description

Extended Atheris fuzzing identified additional input validation problems in the watermark creation endpoint.

Two types of malformed input caused unexpected HTTP 500 responses.

**Invalid intended_for data type**

When intended_for was supplied as a JSON list instead of a string, the endpoint passed the value to secure_filename().

This resulted in an unhandled TypeError because the function expected a string.

**Empty key and secret values**

The endpoint accepted empty strings for key and secret during its initial input validation.

These values subsequently caused errors in the watermarking implementation, resulting in HTTP 500 responses instead of controlled rejection.

### Impact

Malformed input could trigger unexpected server errors.

The issue demonstrated that invalid input was not consistently rejected before reaching the watermarking functions.

### Fix Implemented

Additional input validation was introduced for the relevant watermarking parameters.

The updated implementation validates the types and required values of:

- method
- intended_for
- secret
- key

Invalid data types and empty required values are rejected before the watermarking operation proceeds.

### Verification

During extended fuzzing, one campaign recorded 40 HTTP 500 responses at checkpoint 3,000.

Following the input validation fixes, the final Atheris campaign recorded:

- Zero unexpected HTTP 5xx responses.
- Zero unauthorized watermark creations.
- 710 rejected invalid parameter requests at checkpoint 2,500.

See [A-02 – Create Watermark Results](fuzzing_results.md#a-02--create-watermark-results).

## A-03 - Insufficient Login Input Validation

Endpoint: POST /api/login

### Bug Description

The login endpoint did not consistently validate the structure and data types of incoming JSON requests.

Atheris identified several malformed inputs that caused unexpected HTTP 500 responses.

Examples included:

- email supplied as a list, object, or Boolean value.
- password supplied as a list, object, or Boolean value.
- A JSON request body that was not an object.

The implementation attempted to perform string operations on values that were not strings, or accessed JSON fields using .get() on non-object values.

This resulted in unhandled exceptions.

### Impact

Malformed authentication requests could cause unexpected server errors instead of being rejected as invalid input.

### Fix Implemented

Additional validation was introduced to ensure that:

- The JSON request body is an object.
- email is a string.
- password is a string.
- Required fields are not empty.

Malformed requests are now rejected with HTTP 400 instead of causing unexpected HTTP 500 responses.

### Verification

Before the fix, Atheris recorded 264 HTTP 500 responses at checkpoint 2,000.

After the fix, the follow-up campaign recorded zero HTTP 500 responses at the same checkpoint.

Valid login requests continued to succeed.

See [A-03 – Login Results](fuzzing_results.md#a-03--login-results).

## Summary

| ID | Endpoint | Identified Bug | Verification After Fix |
|---|---|---|---|
| A-01 | `POST /api/upload-document` | Invalid PDF content accepted | 0 invalid PDFs accepted at checkpoint |
| A-02 | `POST /api/create-watermark` | Missing ownership verification | 0 unauthorized watermark creations |
| A-02 | `POST /api/create-watermark` | Invalid parameter types and empty values caused HTTP 500 | 0 unexpected HTTP 5xx |
| A-03 | `POST /api/login` | Malformed JSON inputs caused HTTP 500 | 0 HTTP 500 responses |

All four identified issues were addressed and evaluated through subsequent Atheris campaigns.

The results demonstrate that the observed issues were no longer reproduced in the documented follow-up runs. They do not establish that the tested endpoints are free from all possible vulnerabilities.

