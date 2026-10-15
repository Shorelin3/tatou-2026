# Mutation Testing - Melissa

## Objective

The purpose of this specialization was to evaluate the effectiveness of the existing test suite using mutation testing. The goal was not to achieve a perfect mutation score, but to inspect surviving mutants, identify weaknesses in the tests, and improve the test suite based on those findings.

The analysis focused on the `AddAfterEOF` watermarking implementation in:

`server/src/add_after_eof.py`

Mutation testing was performed using **Mutmut 3.8.0**.

## Mutation Tool Configuration

Mutmut was configured in `server/pyproject.toml`:

```toml
[tool.mutmut]
source_paths = ["src/add_after_eof.py"]
also_copy = ["src/watermarking_method.py"]
pytest_add_cli_args_test_selection = ["test/test_add_after_eof_mutation.py"]
debug = true
```

A focused test file was used for the mutation analysis:

`server/test/test_add_after_eof_mutation.py`

The mutation analysis was deliberately limited to `add_after_eof.py`. This made it possible to manually inspect surviving mutants and use them to identify concrete weaknesses in the tests instead of only reporting an overall mutation score.

## Initial Mutation Testing Results

The initial Mutmut run generated **192 mutants**.

The result was:

- **110 killed**
- **78 survived**
- **4 with no tests**

A killed mutant means that the tests detected the change introduced by Mutmut. A surviving mutant means that the modified code still passed the tests, indicating that the test suite may not sufficiently verify that particular behavior.

The survivor list from the initial run is preserved in:

`mutation-results-before.txt`

Rather than attempting to eliminate every surviving mutant, selected survivors were manually inspected to identify meaningful weaknesses in the test suite.

## Interesting Mutants

### Mutant 1 - Key Validation

One of the surviving mutants was:

`add_watermark__mutmut_8`

The original condition in `add_watermark` was:

```python
if not isinstance(key, str) or not key:
```

Mutmut changed it to:

```python
if not isinstance(key, str) and not key:
```

**Initial result: SURVIVED**

This mutation weakened the validation of the key. Since the mutant survived, the existing tests did not sufficiently exercise invalid key handling.

To address this weakness, the following test was added:

`test_empty_key_rejected`

The test verifies that an empty key is rejected and raises `ValueError`.

After improving the test suite, `add_watermark__mutmut_8` no longer appeared among the surviving mutants.

### Mutant 2 - Newline Handling

Another surviving mutant was:

`add_watermark__mutmut_21`

The original condition was:

```python
if not out.endswith(b"\n"):
```

Mutmut changed it to:

```python
if out.endswith(b"\n"):
```

**Initial result: SURVIVED**

This mutation inverted the condition responsible for adding a newline before the watermark data. Its survival showed that the existing tests did not verify the exact output structure around the end of the PDF and the appended watermark.

To address this weakness, the following test was added:

`test_watermark_newline_structure`

The test uses PDF data ending directly with `%%EOF` and verifies that the expected newline and watermark structure is present in the generated output.

After improving the test suite, `add_watermark__mutmut_21` no longer appeared among the surviving mutants.

## Test Suite Improvements

A focused mutation-testing test file was created at:

`server/test/test_add_after_eof_mutation.py`

It contains five tests:

- `test_add_watermark`
- `test_read_secret_roundtrip`
- `test_read_secret_without_watermark_raises`
- `test_empty_key_rejected`
- `test_watermark_newline_structure`

These tests verify:

- basic watermark creation;
- that a secret can be added and then successfully read again;
- that reading a PDF without a watermark raises the expected exception;
- that an empty key is rejected;
- that the expected newline structure is used when the watermark is appended.

All five focused tests passed against the original implementation.

The most important mutation-driven improvements were `test_empty_key_rejected` and `test_watermark_newline_structure`, since these directly addressed weaknesses identified by inspecting surviving mutants.

The analysis did not confirm a production-code defect in `add_after_eof.py`. Instead, the selected mutants revealed weaknesses in the **test suite**, so the improvements were made to the tests.

## Results After Improvement

After strengthening the test suite, mutation testing was run again.

The second run generated the same **192 mutants** and produced the following result:

- **115 killed**
- **73 survived**
- **4 with no tests**

### Before and After

| Result | Before | After |
| --- | ---: | ---: |
| Total mutants | 192 | 192 |
| Killed | 110 | 115 |
| Survived | 78 | 73 |
| No tests | 4 | 4 |

The improved test suite therefore killed **5 additional mutants** that had previously survived.

The survivor list after the improvements is preserved in:

`mutation-results-after.txt`

Both specifically analyzed mutants, `add_watermark__mutmut_8` and `add_watermark__mutmut_21`, appeared among the initial surviving mutants but no longer appeared among the survivors after the test improvements.

## Findings

The mutation analysis demonstrated that passing tests alone do not necessarily mean that the test suite effectively verifies all important behavior.

The analysis identified two concrete weaknesses in the tests:

1. Invalid and empty key handling was not sufficiently tested.
2. The exact newline structure of the generated watermark was not sufficiently verified.

Mutation testing therefore exposed weaknesses that were not obvious simply from running the existing tests successfully.

By inspecting the surviving mutants, it was possible to identify specific missing test cases and add targeted tests for those behaviors.

## Limitations

The mutation analysis was limited to `src/add_after_eof.py`. The results therefore do not represent the effectiveness of the test suite for the entire Tatou project.

After the improvements, **73 mutants still survived**. These remaining mutants were not all manually analyzed. A surviving mutant does not automatically represent a real bug, and further investigation would be required to determine which of the remaining survivors represent meaningful weaknesses in the tests.

The goal of this specialization was therefore not to achieve a perfect mutation score. The focus was on analyzing selected surviving mutants and using them to make meaningful improvements to the test suite.

Mutation testing was not integrated into CI as part of this specialization.

## Conclusion

Mutation testing with Mutmut was used to evaluate the tests for the `AddAfterEOF` watermarking implementation.

The initial mutation-testing run generated 192 mutants, of which **110 were killed and 78 survived**. By manually inspecting selected surviving mutants, weaknesses were identified in the testing of key validation and watermark newline handling.

Targeted tests were then added to address these weaknesses. After the improvements, **115 mutants were killed and 73 survived**, meaning that the strengthened test suite detected **5 additionell mutants**.

The main value of the exercise was not the mutation score itself, but using surviving mutants to identify specific weaknesses and guide targeted improvements to the test suite.
