# Specialization A – Atheris Fuzzing Results

This document contains the fuzzing results from the following tests:
[test_fuzz_atheris_a01.py](../../server/test/test_fuzz_atheris_a01.py)
[test_fuzz_atheris_a02.py](../../server/test/test_fuzz_atheris_a02.py)
[test_fuzz_atheris_extended_a02.py](../../server/test/test_fuzz_atheris_extended_a02.py)
[test_fuzz_atheris_a03.py](../../server/test/test_fuzz_atheris_a03.py)

The identified bugs and their corrections are documented separately in [bugs_discovered.md](bugs_discovered.md). Regression test cases and outcomes are documented in [non_regression_tests.md](non_regression_tests.md).

## A-01 – PDF Upload Results

### Test Scope

A-01 focused on fuzz testing POST /api/upload-document
using Atheris to explore its behavior under automatically
generated and malformed inputs.

The campaign was conducted before and after implementing
fixes for the issues discovered during testing.

### Initial Fuzzing – Before the Fix

Three Atheris runs were documented before the PDF validation fix.

| Metric | Initial Run | Additional Run | Extended Run |
|---|---:|---:|---:|
| Total Atheris iterations | 2,312 | 3,440 | 4,277 |
| Runtime | Not documented | ~61 s | ~61 s |
| Last recorded checkpoint | 2,000 | 3,000 | 4,000 |
| Invalid PDFs accepted at checkpoint | 1,998 | 3,000 | 3,998 |
| Valid PDFs accepted at checkpoint | Not documented | 0 | 2 |
| New corpus units | Not documented | 18 | 19 |
| libFuzzer coverage counter | Not documented | 1,013 | 1,013 |

In the extended run with 4,277 iterations, approximately 4,275 invalid PDFs and two valid PDFs were accepted by the end of the campaign.

The results demonstrated that the endpoint accepted files without adequately validating their PDF structure. Invalid content could be uploaded successfully when presented as a PDF file.

The checkpoint statistics should NOT be confused with the total number of Atheris iterations.

### Fuzzing After the Fix

The upload endpoint was updated to validate PDF content using PyMuPDF. Invalid PDF content was rejected with HTTP 400.

| Metric | Result |
|---|---:|
| Total Atheris iterations | 2,281 |
| Runtime | 61 s |
| Last recorded checkpoint | 2,000 |
| Invalid PDFs accepted at checkpoint | 0 |
| Valid PDF upload calls accepted | 2,311 |
| Valid PDF upload calls rejected | 0 |
| libFuzzer coverage counter | 1,018 |
| New corpus units | 28 |

The 2,311 accepted valid PDF uploads represent API calls made by the fuzzing harness, not 2,311 distinct Atheris iterations. A single iteration could generate multiple API calls.

At the recorded checkpoint, no invalid PDF content was accepted.

### Additional Verification Run

A later Atheris run was performed to verify the updated implementation.

| Metric | Result |
|---|---:|
| Atheris iterations | 1,509 |
| Runtime | 61 s |
| Execution speed | 24 iterations/s |
| New corpus units | 13 |
| Maximum RSS | 131 MB |
| Reported crashes | 0 |

The run observed HTTP 400 responses for invalid PDF content and HTTP 201 responses for valid uploads.

Complete per-category counters were not documented for this run.

### A-01 Summary

A-01 demonstrated that the original upload implementation accepted invalid PDF content. After implementing PDF validation, no invalid PDFs were accepted at the recorded post-fix checkpoint.

The findings support the effectiveness of the PDF validation fix for the tested inputs. However, it does not establish that every possible malformed PDF is rejected.

## A-02 – Create Watermark Results

### Test Scope

A-02 focused on fuzz testing POST /api/create-watermark
using Atheris to explore its behavior under automatically
generated and malformed inputs.

The campaign was conducted before and after implementing
fixes for the issues discovered during testing.

### Initial Fuzzing – Before the Ownership Fix

The initial Atheris campaign [test_fuzz_atheris_a02.py](../../server/test/test_fuzz_atheris_a02.py) was conducted against an implementation that did not properly enforce document ownership.

| Metric | Result |
|---|---:|
| Total Atheris iterations | 1,322 |
| Last recorded checkpoint | 1,300 |
| Unauthorized watermark creations at checkpoint | 1,300 |
| Execution speed | ~21 iterations/s |
| New corpus units | 0 |

At checkpoint 1,300, all 1,300 recorded attempts successfully created watermarked versions of documents belonging to another authenticated user.

The initial harness primarily exercised this specific authorization scenario. Atheris reported no new corpus units, indicating limited exploration of additional execution paths.

### Fuzzing After the Ownership Fix

After introducing document ownership verification, the same authorization scenario was tested again.

| Metric | Result |
|---|---:|
| Total Atheris iterations | 6,987 |
| Last recorded checkpoint | 6,900 |
| Unauthorized watermark creations | 0 |
| Unauthorized attempts rejected | 6,900 |
| Execution speed | ~114 iterations/s |
| New corpus units | 0 |

At checkpoint 6,900, all recorded unauthorized attempts were rejected, and no unauthorized watermark creations were observed.

Although the authorization behavior improved, the harness still provided limited input diversity. Further fuzzing was therefore performed with an expanded set of test scenarios.

### Improved Fuzzing – Expanded Test Scenarios

The improved [test_fuzz_atheris_extended_a02.py](../../server/test/test_fuzz_atheris_extended_a02.py) Atheris harness introduced additional scenarios involving authenticated document owners, authenticated non-owners, unauthenticated requests, nonexistent documents, and valid or invalid input parameters.

| Metric | Result |
|---|---:|
| Total Atheris iterations | 5,157 |
| Runtime | 61 s |
| Last recorded checkpoint | 5,000 |
| HTTP 5xx | 0 |
| New corpus units | 0 |

At checkpoint 5,000, the following results were recorded:

| Test Scenario | Count | Observed Result |
|---|---:|---|
| Owner with valid parameters | 794 | HTTP 201 |
| Non-owner with valid parameters | 363 | HTTP 404 |
| Owner with invalid parameters | 594 | HTTP 400 |
| Non-owner with invalid parameters | 2,220 | HTTP 400 |
| Unauthenticated requests | 651 | HTTP 401 |
| Nonexistent documents | 378 | HTTP 404 |

No unauthorized watermark creations or unexpected HTTP 5xx responses were observed at this checkpoint.

However, Atheris still reported no new corpus units. The harness was subsequently improved to provide coverage-guided feedback and vary more input parameters.

### Coverage-Guided Fuzzing – Additional Input Validation Issues

Following improvements to the harness, Atheris began reporting new coverage features and corpus units.

One run completed 3,347 iterations in approximately 61 seconds.

| Metric | Result |
|---|---:|
| Total Atheris iterations | 3,347 |
| Runtime | 61 s |
| New corpus units | 12 |
| Corpus size | 13 inputs |
| libFuzzer coverage counter | 2,382 |
| libFuzzer feature counter | 3,409 |

During this campaign, malformed JSON input caused HTTP 500 responses. In particular, supplying intended_for as a JSON list rather than a string resulted in an unhandled TypeError during filename sanitization.

This demonstrated that the endpoint did not adequately validate the data type of intended_for.

### Further Fuzzing – Remaining Server Errors

After addressing the identified input type issue, additional Atheris campaigns were conducted to investigate the endpoint's handling of invalid inputs.

| Metric | Intermediate Run | Extended Run |
|---|---:|---:|
| Total Atheris iterations | 3,413 | 3,452 |
| Runtime | 61 s | 61 s |
| Last recorded checkpoint | 3,000 | 3,000 |
| Successful owner requests at checkpoint | 640 | 534 |
| Unauthorized watermark creations | 0 | 0 |
| HTTP 500 at checkpoint | 37 | 40 |
| New corpus units | 10 | 15 |

The extended run with 3,452 iterations identified HTTP 500 responses when empty strings were supplied for the key or secret parameters.

Examples of the observed failures included:

```text
"key": ""     → HTTP 500: Key must be a non-empty string
"secret": ""  → HTTP 500: Secret must be a non-empty string
```

The parameters passed the initial server-side validation because they were strings, but subsequent watermarking functions rejected the empty values.

These findings showed that additional input validation was required, independently of the previously corrected document ownership issue.

### Final Fuzzing – After All Fixes

Following the ownership and input validation fixes, a final Atheris campaign was performed using the improved coverage-guided harness.

| Metric | Result |
|---|---:|
| Total Atheris iterations | 2,825 |
| Runtime | 61 s |
| Last recorded checkpoint | 2,500 |
| Successful owner requests | 585 |
| Invalid parameter requests rejected | 710 |
| Unauthorized watermark creations | 0 |
| Unexpected HTTP 5xx | 0 |
| Unauthenticated requests rejected | 416 |
| New corpus units | 5 |

At checkpoint 2,500, no unauthorized watermark creations or unexpected HTTP 5xx responses were observed.

The campaign exercised multiple authentication scenarios, varied the input parameters, and tested document identifiers supplied through both URL paths and JSON bodies.

### A-02 Summary

The initial campaign demonstrated that authenticated users could create watermarked versions of documents they did not own. After introducing ownership verification, no unauthorized creations were observed in the follow-up campaign.

Subsequent improvements to the fuzzing harness exposed additional input validation problems involving incorrect JSON data types and empty string parameters. Following the corresponding fixes, the final campaign recorded zero unauthorized watermark creations and zero unexpected HTTP 5xx responses at its last checkpoint.

These results support the effectiveness of the implemented fixes for the tested scenarios. However the recorded checkpoint values should not be interpreted as exhaustive testing of all possible inputs.

## A-03 – Login Results

### Test Scope

A-03 focused on fuzz testing POST /api/login
using Atheris to explore its behavior under automatically
generated and malformed inputs.

The campaign was conducted before and after implementing
fixes for the issues discovered during testing.

### Initial Fuzzing – Before the Fix

The initial Atheris campaign [test_fuzz_atheris_a03.py](../../server/test/test_fuzz_atheris_a03.py) was conducted against the original login implementation.

| Metric | Result |
|---|---:|
| Total Atheris iterations | 2,264 |
| Runtime | 61 s |
| Last recorded checkpoint | 2,000 |
| HTTP 500 at checkpoint | 264 |
| New corpus units | 8 |

At checkpoint 2,000, the following results were recorded:

| Test Scenario | Count | Observed Result |
|---|---:|---|
| Valid login credentials | 428 | Successful login |
| Missing credentials | 414 | Rejected |
| Incorrect credentials | 516 | Rejected |
| Unexpected HTTP 500 responses | 264 | HTTP 500 |

The campaign revealed that certain malformed JSON inputs caused unexpected HTTP 500 responses.

These included cases where email or password were supplied as lists, objects, or Boolean values rather than strings, as well as requests where the JSON body was not an object.

The failures occurred when the endpoint attempted to perform string operations on non-string values or access JSON fields using .get() on a non-object value.

The 264 HTTP 500 responses represent repeated observations of input handling failures, not 264 distinct bugs.

### Fuzzing After the Fix

After introducing additional input validation, the Atheris campaign was repeated against the updated login implementation.

| Metric | Result |
|---|---:|
| Total Atheris iterations | 2,271 |
| Runtime | 61 s |
| Last recorded checkpoint | 2,000 |
| HTTP 500 at checkpoint | 0 |
| New corpus units | 7 |

At checkpoint 2,000, the following results were recorded:

| Test Scenario | Count | Observed Result |
|---|---:|---|
| Valid login credentials | 389 | Successful login |
| Missing credentials | 342 | Rejected |
| Incorrect credentials | 364 | Rejected |
| Unexpected HTTP 500 responses | 0 | None observed |

The updated implementation rejected malformed JSON data types with HTTP 400 instead of producing unexpected HTTP 500 responses.

Valid login requests continued to succeed.

### Before-and-After Comparison

| Metric | Before Fix | After Fix |
|---|---:|---:|
| Total Atheris iterations | 2,264 | 2,271 |
| Runtime | 61 s | 61 s |
| Last recorded checkpoint | 2,000 | 2,000 |
| HTTP 500 at checkpoint | 264 | 0 |
| Successful logins at checkpoint | 428 | 389 |
| Missing credentials rejected | 414 | 342 |
| Incorrect credentials rejected | 516 | 364 |
| New corpus units | 8 | 7 |

The numbers of successful and rejected requests varied between runs because Atheris generated different inputs.

The key observation was that HTTP 500 responses decreased from 264 to 0 at the recorded checkpoints, while valid login requests continued to succeed.

### A-03 Summary

The initial Atheris campaign exposed insufficient input validation in the login endpoint. Malformed JSON data types caused unexpected HTTP 500 responses.

After implementing stricter input validation, no HTTP 500 responses were observed at the last recorded checkpoint, and valid login requests continued to succeed.

These findings support the effectiveness of the fix for the tested inputs. However, fuzzing campaigns do not establish that all possible malformed login requests are handled correctly.