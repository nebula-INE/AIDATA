# Safe Verification of Code Examples

## Purpose

AIDATA should distinguish three different claims:

1. **Structurally valid**: JSONL records satisfy the schema and repository checks.
2. **Reviewed**: a human checked the expected behavior, edge cases, and explanation.
3. **Executed and verified**: a controlled test runner executed an explicitly approved fixture and its assertions passed.

Passing schema validation or CI does not imply that a code sample is correct, has run, or represents a model capability. Keep synthetic examples at `quality.status: "draft"` until review and verification actually occur.

## Threat model

Dataset records, code blocks, test strings, filenames, URLs, and generated patches are untrusted input. A future training or evaluation pipeline must not execute code merely because it appears in a JSONL record or because a record is marked `verified`.

Potential risks include arbitrary command execution, filesystem access, network access, secret exfiltration, resource exhaustion, test manipulation, and tests that pass without checking the intended behavior.

## Safe initial policy

- Treat the existing `tests` field as descriptive text, not executable input.
- Never use `eval`, `exec`, shell interpolation, or dynamic imports to run dataset content.
- Do not import Python source extracted from `prompt`, `target`, or `tests`.
- Start with repository-owned, reviewed test fixtures selected by an explicit allowlist. Dataset records may reference a fixture ID, but must not provide a command or filesystem path to execute.
- Keep fixture code and expected assertions in version-controlled test files reviewed like production code.
- Run verification in an isolated, disposable environment with no secrets, no network by default, read-only source inputs, a temporary writable directory, and CPU, memory, process-count, and wall-clock limits.
- Pin dependencies and avoid installing packages named by dataset records.
- Record the exact commit, record ID, fixture ID, runtime/dependency versions, command, exit status, timeout status, and assertion summary.
- A timeout, crash, missing dependency, or skipped test is **not** a pass.
- Do not let a test runner change a record's quality status automatically. Human review is still required before promotion.

## Proposed record lifecycle

| Status | Minimum evidence |
| --- | --- |
| `draft` | Authored or generated; no correctness claim. |
| `reviewed` | Human reviewed prompt, target, assumptions, edge cases, and source/license notes. |
| `verified` | Reviewed record plus reproducible test evidence tied to a commit and fixture. |

A code example may be reviewed without being executable. In that case, keep it `reviewed`, and explicitly say that it was not executed. Never use `verified` to mean only “JSON schema passed.”

## Controlled verification workflow

1. Select a small set of representative records manually.
2. Write an independent, repository-owned fixture for each selected behavior. Include normal cases, boundaries, invalid input, and regression cases as appropriate.
3. Review the fixture and assertions separately from the target answer to reduce the risk of encoding the answer's bug into the test.
4. Run the fixture in an isolated environment with strict time and resource limits.
5. Confirm the test actually exercises the intended path; a green test that never reaches the behavior is insufficient.
6. Save a machine-readable report and link it to the reviewed record and exact commit.
7. Have a reviewer compare the target explanation with the observed behavior before changing quality status.

## Reporting requirements

Reports must separate:
- records parsed and schema-validated;
- fixtures selected and actually executed;
- passed, failed, timed out, errored, and skipped cases;
- human-reviewed records;
- known limitations and environment details.

Do not report an overall “code correctness rate” unless the denominator and selection method are stated. A hand-picked fixture sample is not a representative estimate of the whole dataset.

## Source-grounded research evaluation

For web-research records, evaluate independently:
- whether each citation exists and supports the exact claim attached to it;
- source authority and primary-vs-secondary status;
- publication/update date and applicability to the requested version;
- agreement or conflict among independent sources;
- whether uncertainty and missing evidence are acknowledged;
- whether untrusted page content is treated as data rather than instructions;
- whether the final synthesis avoids unsupported claims and preserves traceability.

A URL being present is not evidence that it was opened or that it supports the answer. Keep source metadata and retrieval dates where available, and distinguish live retrieval from a static reference included in a synthetic exercise.

## Rollout

Begin with a few hand-reviewed fixtures and reporting-only results. Add enforcement to CI only after the runner, isolation boundary, timeout behavior, and failure reporting have dedicated tests. Never execute arbitrary record-provided code in the standard dataset-validation workflow.
