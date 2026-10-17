# Japanese coding dataset scale-up: target of 2,000 records

## Goal

Grow the Japanese coding/software-engineering **training seed corpus to approximately 2,000 records total** only after the current audit tooling is exercised and its findings are triaged. This is a corpus-size target, not a claim that 2,000 synthetic records improve model capability. Keep evaluation records in `data/eval/` and never count them toward training volume.

The current PR describes 367 synthetic training records, all still `quality.status: draft`. Before adding roughly 1,600 more records, use the record-quality audit to measure the existing baseline and distinguish structural defects from content-review work.

## Phase 0 — finish the quality-audit loop

1. Run unit tests and JSONL/schema validation.
2. Run `scripts/audit_record_quality.py --json data/seeds/*.jsonl` and retain the report as a CI artifact or review attachment.
3. Group findings by kind and source batch. Fix malformed data and duplicate IDs; inspect duplicate prompts, missing targets, missing checks, generic placeholder checks, and escaped-newline findings.
4. Do not bulk-dismiss findings: a non-empty `tests` field is not evidence that an answer is correct or executable.
5. Keep synthetic data in `draft`; record reviewer identity, evidence, and disposition for every manually reviewed item.

## Phase 1 — establish the 2,000-record mix

Treat the following as **planning allocations**, not records already authored. Adjust after reviewing coverage and duplication reports.

| Area | Target records | Focus |
| --- | ---: | --- |
| Japanese instruction interpretation | 250 | Negation, conditions, exceptions, scope, ambiguous referents, constraints |
| Programming foundations | 250 | Python, JavaScript/TypeScript, SQL, data structures, errors, edge cases |
| Debugging and root-cause analysis | 300 | Minimal reproductions, logs, hypotheses, regression prevention |
| Tests and verification | 250 | Unit/integration tests, fixtures, property/boundary tests, expected outcomes |
| Git, CI, packaging, cross-platform | 200 | Branches, merge conflicts, reproducible builds, environment differences |
| APIs, networking, async, reliability | 200 | Timeouts, retries, idempotency, cancellation, races, queues |
| Data engineering and databases | 150 | Migrations, transactions, schemas, encodings, data validation |
| Security, privacy, and safe tool use | 150 | Injection, secrets, permissions, untrusted input, least privilege |
| Research and source-grounded answers | 150 | Official docs, version checks, provenance, conflict resolution, uncertainty |
| Model/data evaluation and code review | 100 | Leakage, deduplication, rubric design, ablations, review comments |
| **Total** | **2,000** | Includes existing records after triage; evaluation remains separate |

The allocation is intentionally varied. Do not fill a quota with near-identical paraphrases; move the quota if the audit shows that a topic is already saturated.

## Phase 2 — author in small batches

- Add batches of 100–200 records, each with stable IDs, a clear learning objective, a realistic prompt, a specific target, and record-specific checks.
- Use contrastive pairs for Japanese scope and polarity only when the changed wording changes the expected interpretation.
- Prefer concrete repository-style failures and minimal reproducible examples over generic advice prompts.
- For code tasks, checks should state observable outcomes, edge cases, and assumptions. Do not use generic placeholders such as “review expected behavior.”
- Label provenance honestly. Synthetic scenarios must say they are synthetic; do not imply that sample logs, benchmark outcomes, or code execution happened unless evidence is stored.
- Avoid including secrets, personal data, unlicensed copied code, or unverified claims about current APIs.

## Phase 3 — quality gates per batch

Before a batch is considered ready for review:

1. JSONL parse and repository schema validation pass.
2. IDs are globally unique across all seed files.
3. Exact normalized prompt duplicates are removed or explicitly justified; near-duplicate candidates receive human review.
4. Train/eval exact-prompt leakage check passes; held-out evaluation targets remain private from training material where applicable.
5. Every record has a non-empty target and record-specific checks. Checks are reviewed for whether they could actually distinguish a correct answer from a plausible but wrong one.
6. Technical claims are tied to a versioned source, a reproducible test, or explicitly labeled assumptions.
7. A human reviewer samples each batch and reviews high-risk technical/security claims; reviewed status is only assigned with reviewer and evidence metadata.
8. Report coverage, duplicate counts, quality-status distribution, and unresolved findings. Do not report only raw record count.

Keep the automated audit advisory until existing findings have been triaged. Then make stable, high-confidence checks hard CI failures (at minimum invalid JSON, duplicate IDs, and train/eval leakage). Do not make “has tests” synonymous with “verified.”

## Phase 4 — evaluation before capability claims

- Freeze a held-out evaluation set separate from training, with a Tier A baseline suited to the intended small model, then Tier B practical tasks and Tier C advanced reasoning tasks.
- Store model outputs, model/checkpoint identity, inference settings, scoring rubric, and per-task results.
- Compare against the current corpus using controlled ablations: baseline corpus, baseline plus reviewed batch, and baseline plus candidate batch where practical.
- Report accuracy by task family, error type, and difficulty; include uncertainty and regression results.
- A larger corpus is not automatically better. Keep, revise, or discard batches based on measured marginal value.

## Exit criteria for the 2,000-record milestone

- Approximately 2,000 training records exist, but all unreviewed synthetic entries remain marked `draft`.
- Global schema/ID/split-leakage checks pass.
- Duplicate and placeholder findings are triaged with a saved report.
- A documented human-review sample and disposition log exists.
- The fixed evaluation set has reproducible baseline results. Any improvement claim is limited to what the measured evaluation supports.
