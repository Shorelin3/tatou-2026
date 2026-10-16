# Specialization A – Fuzz Testing with Atheris

## Findings Summary

Atheris fuzz testing was performed on three Tatou API endpoints:
POST /api/upload-document, POST /api/create-watermark,
and POST /api/login.

The campaigns identified four security and robustness issues:

1. Insufficient PDF validation (A-01):
   The upload endpoint accepted invalid PDF content, including plain
   text, empty files, and malformed PDFs.

2. Missing document ownership verification (A-02):
   Authenticated users could create watermarked versions of documents
   belonging to other users, demonstrating a broken access control
   vulnerability.

3. Insufficient watermark input validation (A-02):
   Incorrect data types for intended_for and empty key or secret
   values caused unexpected HTTP 500 responses.

4. Insufficient login input validation (A-03):
   Malformed JSON requests, including incorrect data types and
   non-object JSON bodies, caused unexpected HTTP 500 responses.

## Findings Before and After Fixes

| Finding | Before Fix | After Fix |
|---|---|---|
| A-01 – PDF validation | 1,998 invalid PDFs accepted at checkpoint 2,000 | 0 invalid PDFs accepted at checkpoint 2,000 |
| A-02 – Ownership verification | 1,300 unauthorized watermark creations at checkpoint 1,300 | 0 unauthorized creations at checkpoint 6,900 |
| A-02 – Watermark input validation | 40 HTTP 500 responses at checkpoint 3,000 | 0 unexpected HTTP 5xx at checkpoint 2,500 |
| A-03 – Login input validation | 264 HTTP 500 responses at checkpoint 2,000 | 0 HTTP 500 responses at checkpoint 2,000 |

The identified issues were addressed through PDF content validation,
document ownership checks, and stricter validation of input types
and required values.

Follow-up Atheris campaigns no longer reproduced the observed
failures at the recorded checkpoints.

## Non-Regression Test Results

| Campaign | Passed Tests |
|---|---:|
| A-01 – PDF Upload | 6/6 |
| A-02 – Create Watermark | 7/7 |
| A-03 – Login | 15/15 |
| Total | 28/28 |

All 28 non-regression tests passed after the fixes, confirming
that the identified issues were no longer reproduced by the
corresponding test cases.

## Conclusion

The fuzzing campaigns revealed one access control vulnerability
and several input validation issues across the three tested
endpoints.

The findings led to concrete fixes, which were subsequently
verified through repeated Atheris campaigns and non-regression
testing.

## Supporting Artifacts

- [Fuzzer Configurations](fuzzer_configurations.md) – Atheris harness
  configurations, input generation, test scenarios, and test environment.
- [Fuzzing Results](fuzzing_results.md) – Detailed results from all
  documented Atheris campaigns before and after the fixes.
- [Bugs Discovered](bugs_discovered.md) – Descriptions of the identified
  bugs, their impact, implemented fixes, and verification.
- [Non-Regression Tests](non_regression_tests.md) – The 28 regression
  test cases, their expected behavior, and final results.

